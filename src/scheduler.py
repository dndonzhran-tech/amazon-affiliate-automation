"""Scheduler for automated posting."""

import datetime
import json
import logging
import signal
import sys
import threading
import time
from pathlib import Path
from typing import Callable, Optional

import schedule

from src.content_generator import ContentGenerator
from src.models import (
    PostDB,
    ScheduleDB,
    get_session,
    init_db,
)
from src.scraper import AmazonScraper
from src.social.telegram import TelegramPoster
from src.social.twitter import TwitterPoster
from src.utils import get_env_var

logger = logging.getLogger(__name__)


class AutomationScheduler:
    """Manages scheduled automation tasks."""

    def __init__(self, db_url: str = "sqlite:///affiliate.db"):
        self.db_url = db_url
        init_db(db_url)
        self.scraper = AmazonScraper()
        self.twitter = TwitterPoster()
        self.telegram = TelegramPoster()
        self.running = False
        self._stop_event = threading.Event()

    def add_schedule(
        self,
        name: str,
        interval_minutes: int,
        platform: str,
        language: str = "en",
        scenario: str = "product_review",
        category: str = "",
    ) -> ScheduleDB:
        """Add a new scheduled task."""
        session = get_session(self.db_url)
        sched = ScheduleDB(
            name=name,
            interval_minutes=interval_minutes,
            platform=platform,
            language=language,
            scenario=scenario,
            category=category,
            is_active=True,
        )
        session.add(sched)
        session.commit()
        sched_id = sched.id
        session.close()
        logger.info(f"Schedule added: {name} (every {interval_minutes} min on {platform})")
        return sched

    def remove_schedule(self, schedule_id: int) -> bool:
        """Remove a scheduled task."""
        session = get_session(self.db_url)
        sched = session.query(ScheduleDB).get(schedule_id)
        if sched:
            session.delete(sched)
            session.commit()
            session.close()
            logger.info(f"Schedule removed: {schedule_id}")
            return True
        session.close()
        return False

    def list_schedules(self) -> list[dict]:
        """List all scheduled tasks."""
        session = get_session(self.db_url)
        schedules = session.query(ScheduleDB).all()
        result = []
        for s in schedules:
            result.append({
                "id": s.id,
                "name": s.name,
                "interval_minutes": s.interval_minutes,
                "platform": s.platform,
                "language": s.language,
                "scenario": s.scenario,
                "category": s.category,
                "is_active": s.is_active,
                "last_run": str(s.last_run) if s.last_run else None,
            })
        session.close()
        return result

    def execute_task(self, sched: ScheduleDB):
        """Execute a scheduled posting task."""
        logger.info(f"Executing task: {sched.name}")

        keyword = sched.category or "bestseller products"
        products = self.scraper.search_products(
            keyword=keyword,
            category=sched.category,
            max_results=1,
        )

        if not products:
            logger.warning(f"No products found for task: {sched.name}")
            return

        product = products[0]
        generator = ContentGenerator(language=sched.language)
        post = generator.generate_post(
            product=product,
            platform=sched.platform,
            scenario=sched.scenario,
        )

        result = None
        if sched.platform == "twitter" and self.twitter.is_configured():
            result = self.twitter.post_tweet(
                text=post.full_text,
                image_path="",
            )
        elif sched.platform == "telegram" and self.telegram.is_configured():
            result = self.telegram.send_product_post(
                product_name=product.name,
                description=product.description,
                price=product.price,
                affiliate_url=product.affiliate_url,
                image_url=product.image_url,
                discount=product.discount,
                language=sched.language,
            )

        if result:
            session = get_session(self.db_url)
            post_db = post.to_db()
            post_db.posted = True
            post_db.posted_at = datetime.datetime.utcnow()
            session.add(post_db)

            db_sched = session.query(ScheduleDB).get(sched.id)
            if db_sched:
                db_sched.last_run = datetime.datetime.utcnow()
            session.commit()
            session.close()
            logger.info(f"Task completed: {sched.name} -> Posted to {sched.platform}")
        else:
            logger.error(f"Task failed: {sched.name} -> Could not post to {sched.platform}")

    def run(self):
        """Start the scheduler loop."""
        self.running = True
        self._stop_event.clear()

        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        session = get_session(self.db_url)
        active_schedules = session.query(ScheduleDB).filter_by(is_active=True).all()
        session.close()

        if not active_schedules:
            logger.warning("No active schedules found")
            return

        for sched in active_schedules:
            schedule.every(sched.interval_minutes).minutes.do(
                self.execute_task, sched=sched
            )
            logger.info(
                f"Scheduled: {sched.name} every {sched.interval_minutes} min "
                f"on {sched.platform}"
            )

        logger.info(f"Scheduler started with {len(active_schedules)} tasks")
        print(f"Scheduler running with {len(active_schedules)} active tasks. Press Ctrl+C to stop.")

        while not self._stop_event.is_set():
            schedule.run_pending()
            self._stop_event.wait(timeout=1)

        logger.info("Scheduler stopped")

    def run_once(self):
        """Run all active schedules once immediately."""
        session = get_session(self.db_url)
        active_schedules = session.query(ScheduleDB).filter_by(is_active=True).all()
        session.close()

        for sched in active_schedules:
            self.execute_task(sched)

    def stop(self):
        """Stop the scheduler."""
        self._stop_event.set()
        self.running = False
        schedule.clear()

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        logger.info("Shutdown signal received")
        self.stop()

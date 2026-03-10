"""نظام الجدولة - نشر تلقائي بدون n8n (بديل مستقل)."""

import logging
import time
from datetime import datetime

import schedule

from src.config import (
    MAX_POSTS_PER_DAY,
    POST_INTERVAL_HOURS,
    POSTING_HOURS_END,
    POSTING_HOURS_START,
)
from src.database import get_pending_posts, init_db
from src.social.publisher import publish_post

logger = logging.getLogger(__name__)

_posts_today = 0
_last_reset_date = ""


def _reset_daily_counter():
    """إعادة تعيين عداد المنشورات اليومية."""
    global _posts_today, _last_reset_date
    today = datetime.now().strftime("%Y-%m-%d")
    if today != _last_reset_date:
        _posts_today = 0
        _last_reset_date = today


def _is_posting_time() -> bool:
    """التحقق هل الوقت مناسب للنشر."""
    hour = datetime.now().hour
    return POSTING_HOURS_START <= hour < POSTING_HOURS_END


def process_pending_posts():
    """معالجة المنشورات المعلقة."""
    global _posts_today

    _reset_daily_counter()

    if _posts_today >= MAX_POSTS_PER_DAY:
        logger.info("وصلنا الحد اليومي للمنشورات")
        return

    if not _is_posting_time():
        logger.info("خارج أوقات النشر المحددة")
        return

    posts = get_pending_posts(limit=1)
    if not posts:
        logger.info("لا توجد منشورات معلقة")
        return

    post = posts[0]
    logger.info(f"نشر المنشور #{post['id']}: {post['content'][:50]}...")

    result = publish_post(post)
    if result.get("success"):
        _posts_today += 1
        logger.info(f"تم النشر بنجاح! ({_posts_today}/{MAX_POSTS_PER_DAY})")
    else:
        logger.error(f"فشل النشر: {result}")


def start_scheduler():
    """بدء تشغيل المجدول."""
    init_db()
    logger.info(
        f"بدء المجدول - كل {POST_INTERVAL_HOURS} ساعات, "
        f"حد {MAX_POSTS_PER_DAY} منشور يومياً, "
        f"أوقات النشر: {POSTING_HOURS_START}:00 - {POSTING_HOURS_END}:00"
    )

    schedule.every(POST_INTERVAL_HOURS).hours.do(process_pending_posts)
    # فحص أولي فوري
    process_pending_posts()

    while True:
        schedule.run_pending()
        time.sleep(60)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    )
    start_scheduler()

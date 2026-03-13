"""Analytics tracking for Amazon affiliate automation."""

import json
import logging
import os
import threading
from datetime import datetime, timedelta, timezone

logger = logging.getLogger(__name__)


class AnalyticsTracker:
    """Tracks performance metrics and stores them in a JSON file."""

    def __init__(self, filepath: str = "output/analytics.json"):
        self.filepath = filepath
        self._lock = threading.Lock()
        self._ensure_directory()

    def _ensure_directory(self):
        """Create the output directory if it doesn't exist."""
        directory = os.path.dirname(self.filepath)
        if directory:
            os.makedirs(directory, exist_ok=True)

    def _load(self) -> list[dict]:
        """Load existing analytics data from the JSON file."""
        if not os.path.exists(self.filepath):
            return []
        try:
            with open(self.filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data if isinstance(data, list) else []
        except (json.JSONDecodeError, OSError):
            logger.warning("Could not read analytics file, starting fresh.")
            return []

    def _save(self, data: list[dict]):
        """Save analytics data to the JSON file."""
        with open(self.filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def track_run(
        self,
        products_count: int,
        social_posts: int,
        youtube_uploads: int,
        errors: int,
    ):
        """Record metrics for a single automation run."""
        total_actions = social_posts + youtube_uploads + errors
        success_rate = (
            ((social_posts + youtube_uploads) / total_actions * 100)
            if total_actions > 0
            else 100.0
        )

        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "products_count": products_count,
            "social_posts": social_posts,
            "youtube_uploads": youtube_uploads,
            "errors": errors,
            "success_rate": round(success_rate, 2),
        }

        with self._lock:
            data = self._load()
            data.append(entry)
            self._save(data)

        logger.info(
            "Analytics recorded: %d products, %d posts, %d uploads, %d errors (%.1f%% success)",
            products_count,
            social_posts,
            youtube_uploads,
            errors,
            success_rate,
        )

    def get_summary(self, days: int = 7) -> dict:
        """Return aggregated summary for the last N days."""
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)

        with self._lock:
            data = self._load()

        recent = []
        for entry in data:
            try:
                ts = datetime.fromisoformat(entry["timestamp"])
                if ts >= cutoff:
                    recent.append(entry)
            except (KeyError, ValueError):
                continue

        total_runs = len(recent)
        total_products = sum(e.get("products_count", 0) for e in recent)
        total_posts = sum(e.get("social_posts", 0) for e in recent)
        total_uploads = sum(e.get("youtube_uploads", 0) for e in recent)
        total_errors = sum(e.get("errors", 0) for e in recent)

        total_actions = total_posts + total_uploads + total_errors
        success_rate = (
            ((total_posts + total_uploads) / total_actions * 100)
            if total_actions > 0
            else 100.0
        )
        avg_products = total_products / total_runs if total_runs > 0 else 0.0

        return {
            "days": days,
            "total_runs": total_runs,
            "total_products": total_products,
            "total_posts": total_posts,
            "total_uploads": total_uploads,
            "total_errors": total_errors,
            "success_rate": round(success_rate, 2),
            "avg_products_per_run": round(avg_products, 2),
        }

    def get_daily_stats(self) -> list[dict]:
        """Return a daily breakdown of analytics."""
        with self._lock:
            data = self._load()

        daily: dict[str, dict] = {}
        for entry in data:
            try:
                ts = datetime.fromisoformat(entry["timestamp"])
                day_key = ts.strftime("%Y-%m-%d")
            except (KeyError, ValueError):
                continue

            if day_key not in daily:
                daily[day_key] = {
                    "date": day_key,
                    "runs": 0,
                    "products": 0,
                    "social_posts": 0,
                    "youtube_uploads": 0,
                    "errors": 0,
                }

            daily[day_key]["runs"] += 1
            daily[day_key]["products"] += entry.get("products_count", 0)
            daily[day_key]["social_posts"] += entry.get("social_posts", 0)
            daily[day_key]["youtube_uploads"] += entry.get("youtube_uploads", 0)
            daily[day_key]["errors"] += entry.get("errors", 0)

        return sorted(daily.values(), key=lambda d: d["date"])

"""Duplicate product detection module with persistent storage."""

import json
import logging
import os
import threading
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class DuplicateDetector:
    """Detects duplicate products using a JSON file for persistent storage."""

    def __init__(self, storage_path: str = "output/posted_products.json"):
        self.storage_path = storage_path
        self._lock = threading.Lock()
        self._ensure_storage()

    def _ensure_storage(self):
        """Create the output directory and storage file if they don't exist."""
        directory = os.path.dirname(self.storage_path)
        if directory:
            os.makedirs(directory, exist_ok=True)
        if not os.path.exists(self.storage_path):
            self._write_data({})

    def _read_data(self) -> dict:
        """Read the posted products data from the JSON file."""
        try:
            with open(self.storage_path, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {}

    def _write_data(self, data: dict):
        """Write the posted products data to the JSON file."""
        with open(self.storage_path, "w") as f:
            json.dump(data, f, indent=2)

    def is_duplicate(self, asin: str) -> bool:
        """Check if a product ASIN has already been posted."""
        with self._lock:
            data = self._read_data()
            return asin in data

    def mark_posted(self, asin: str, platform: str):
        """Record that a product has been posted to a platform."""
        with self._lock:
            data = self._read_data()
            if asin not in data:
                data[asin] = []
            data[asin].append({
                "platform": platform,
                "timestamp": datetime.utcnow().isoformat(),
            })
            self._write_data(data)
            logger.info("Marked ASIN %s as posted to %s", asin, platform)

    def get_posted_count(self) -> int:
        """Return the number of unique products that have been posted."""
        with self._lock:
            data = self._read_data()
            return len(data)

    def cleanup(self, days: int = 30):
        """Remove entries older than the specified number of days."""
        with self._lock:
            data = self._read_data()
            cutoff = datetime.utcnow() - timedelta(days=days)
            cleaned = {}
            for asin, entries in data.items():
                recent = [
                    entry for entry in entries
                    if datetime.fromisoformat(entry["timestamp"]) > cutoff
                ]
                if recent:
                    cleaned[asin] = recent
            removed = len(data) - len(cleaned)
            self._write_data(cleaned)
            if removed:
                logger.info("Cleaned up %d old entries (older than %d days)", removed, days)

"""اختبارات قاعدة البيانات."""

import os
import tempfile
import unittest
from unittest.mock import patch

from src import database


class TestDatabase(unittest.TestCase):
    def setUp(self):
        """إنشاء قاعدة بيانات مؤقتة للاختبارات."""
        self.tmp_dir = tempfile.mkdtemp()
        self.patcher = patch.object(
            database, "DATA_DIR", type(database.DATA_DIR)(self.tmp_dir)
        )
        self.patcher.start()
        database.DB_PATH = database.DATA_DIR / "test_affiliate.db"
        database.init_db()

    def tearDown(self):
        self.patcher.stop()
        db_path = os.path.join(self.tmp_dir, "test_affiliate.db")
        if os.path.exists(db_path):
            os.remove(db_path)
        # cleanup WAL files
        for suffix in ("-wal", "-shm"):
            p = db_path + suffix
            if os.path.exists(p):
                os.remove(p)
        os.rmdir(self.tmp_dir)

    def test_save_and_get_product(self):
        product = {
            "asin": "B123TEST",
            "name": "منتج اختبار",
            "price": 29.99,
            "category": "إلكترونيات",
        }
        database.save_product(product)
        result = database.get_product("B123TEST")
        self.assertIsNotNone(result)
        self.assertEqual(result["name"], "منتج اختبار")
        self.assertEqual(result["price"], 29.99)

    def test_get_nonexistent_product(self):
        result = database.get_product("NONEXISTENT")
        self.assertIsNone(result)

    def test_get_all_products(self):
        for i in range(3):
            database.save_product({
                "asin": f"B{i}",
                "name": f"منتج {i}",
                "price": float(i * 10),
            })
        products = database.get_all_products()
        self.assertEqual(len(products), 3)

    def test_save_and_get_post(self):
        post_id = database.save_post({
            "content": "منشور اختبار",
            "product_asin": "B123",
            "hashtags": ["#تست"],
            "language": "ar",
            "content_type": "product_review",
        })
        self.assertIsNotNone(post_id)
        self.assertGreater(post_id, 0)

    def test_update_post_status(self):
        post_id = database.save_post({
            "content": "منشور للتحديث",
        })
        database.update_post_status(post_id, "published", twitter_id="12345")

        posts = database.get_posts_by_status("published")
        self.assertEqual(len(posts), 1)
        self.assertEqual(posts[0]["content"], "منشور للتحديث")

    def test_pending_posts(self):
        database.save_post({"content": "معلق 1", "status": "draft"})
        database.save_post({"content": "معلق 2", "status": "draft"})
        database.save_post({"content": "منشور", "status": "published"})

        pending = database.get_pending_posts()
        self.assertEqual(len(pending), 2)

    def test_log_event(self):
        database.log_event({
            "event_type": "click",
            "product_asin": "B123",
            "platform": "twitter",
        })
        # verify no error occurred
        stats = database.get_daily_stats()
        self.assertIn("clicks", stats)

    def test_daily_stats(self):
        stats = database.get_daily_stats()
        self.assertIn("date", stats)
        self.assertIn("posts_today", stats)
        self.assertIn("clicks", stats)
        self.assertIn("impressions", stats)
        self.assertIn("estimated_revenue", stats)


if __name__ == "__main__":
    unittest.main()

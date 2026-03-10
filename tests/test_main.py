"""اختبارات النظام الرئيسي."""

import os
import tempfile
import unittest
from unittest.mock import patch

from src import database
from src.content.ai_generator import _generate_fallback


class TestGenerateFallback(unittest.TestCase):
    def test_arabic_fallback(self):
        product = {
            "name": "سماعات بلوتوث",
            "description": "سماعات لاسلكية",
            "affiliate_link": "https://amazon.com/dp/B123?tag=test-20",
            "category": "إلكترونيات",
            "discount": 30,
            "use_case": "الموسيقى",
        }
        result = _generate_fallback(product, "ar", "product_review")
        self.assertIsNotNone(result)
        self.assertIn("سماعات بلوتوث", result["content"])
        self.assertEqual(result["language"], "ar")

    def test_english_fallback(self):
        product = {
            "name": "Bluetooth Headphones",
            "description": "Wireless",
            "affiliate_link": "https://amazon.com/dp/B123?tag=test-20",
            "category": "Electronics",
            "discount": 20,
            "use_case": "Music",
        }
        result = _generate_fallback(product, "en", "deal_alert")
        self.assertIsNotNone(result)
        self.assertIn("Bluetooth Headphones", result["content"])

    def test_invalid_scenario_fallback(self):
        product = {"name": "تست"}
        result = _generate_fallback(product, "ar", "nonexistent")
        self.assertIsNone(result)

    def test_fallback_has_hashtags(self):
        product = {
            "name": "كاميرا",
            "description": "كاميرا احترافية",
            "affiliate_link": "https://amazon.com",
            "category": "كاميرات",
            "discount": 10,
            "use_case": "التصوير",
        }
        result = _generate_fallback(product, "ar", "recommendation")
        self.assertIsNotNone(result)
        self.assertGreater(len(result["hashtags"]), 0)


class TestGenerateContentWithoutAPI(unittest.TestCase):
    """اختبار توليد المحتوى بدون مفتاح API (يستخدم القوالب)."""

    @patch("src.content.ai_generator.OPENAI_API_KEY", "")
    @patch("src.content.ai_generator.ANTHROPIC_API_KEY", "")
    def test_generate_uses_fallback(self):
        from src.content.ai_generator import generate_content
        product = {
            "asin": "B123",
            "name": "سماعات",
            "price": 50,
            "currency": "USD",
            "description": "سماعات لاسلكية",
            "affiliate_link": "https://amazon.com",
            "category": "إلكترونيات",
            "discount": 20,
            "use_case": "الموسيقى",
            "rating": 4.5,
            "review_count": 100,
            "features": ["بلوتوث 5.0"],
        }
        posts = generate_content(product, "ar", ["product_review", "deal_alert"])
        self.assertGreater(len(posts), 0)
        for post in posts:
            self.assertIn("content", post)
            self.assertIn("سماعات", post["content"])


class TestAPIServerEndpoints(unittest.TestCase):
    """اختبار API endpoints."""

    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.patcher = patch.object(
            database, "DATA_DIR", type(database.DATA_DIR)(self.tmp_dir)
        )
        self.patcher.start()
        database.DB_PATH = database.DATA_DIR / "test_api.db"
        database.init_db()

        from src.api_server import app
        app.config["TESTING"] = True
        self.client = app.test_client()

    def tearDown(self):
        self.patcher.stop()
        db_path = os.path.join(self.tmp_dir, "test_api.db")
        for suffix in ("", "-wal", "-shm"):
            p = db_path + suffix
            if os.path.exists(p):
                os.remove(p)
        if os.path.isdir(self.tmp_dir):
            os.rmdir(self.tmp_dir)

    def test_health_endpoint(self):
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.get_json()["ok"])

    def test_status_endpoint(self):
        response = self.client.get("/api/status")
        data = response.get_json()
        self.assertEqual(data["status"], "running")
        self.assertIn("platforms", data)

    def test_add_product(self):
        response = self.client.post("/api/products/add", json={
            "asin": "BTEST123",
            "name": "منتج اختبار API",
            "price": 19.99,
        })
        data = response.get_json()
        self.assertTrue(data["success"])

    def test_add_product_missing_fields(self):
        response = self.client.post("/api/products/add", json={
            "price": 19.99,
        })
        self.assertEqual(response.status_code, 400)

    def test_list_products(self):
        self.client.post("/api/products/add", json={
            "asin": "BLIST1", "name": "منتج 1", "price": 10,
        })
        response = self.client.get("/api/products")
        data = response.get_json()
        self.assertTrue(data["success"])
        self.assertGreater(len(data["products"]), 0)

    def test_daily_report(self):
        response = self.client.get("/api/analytics/daily-report")
        data = response.get_json()
        self.assertIn("posts_today", data)
        self.assertIn("clicks", data)

    def test_log_analytics(self):
        response = self.client.post("/api/analytics/log", json={
            "results": {"twitter": {"success": True, "post_id": "123"}},
            "product": "B123",
        })
        data = response.get_json()
        self.assertTrue(data["success"])


if __name__ == "__main__":
    unittest.main()

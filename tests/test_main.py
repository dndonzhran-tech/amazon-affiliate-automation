"""اختبارات التطبيق الرئيسي."""

import unittest

from src.main import create_post, generate_posts
from src.models import Product


class TestCreatePost(unittest.TestCase):
    def setUp(self):
        self.product = Product(
            name="سماعات بلوتوث",
            affiliate_link="https://amazon.com/dp/B123?tag=test-20",
            category="إلكترونيات",
            description="سماعات لاسلكية بجودة عالية",
            discount=30,
            use_case="الاستماع للموسيقى",
        )

    def test_create_arabic_post(self):
        post = create_post(self.product, scenario="product_review", language="ar")
        self.assertIn("سماعات بلوتوث", post.content)
        self.assertEqual(post.language, "ar")
        self.assertEqual(post.scenario, "product_review")

    def test_create_english_post(self):
        post = create_post(self.product, scenario="deal_alert", language="en")
        self.assertIn("سماعات بلوتوث", post.content)
        self.assertEqual(post.language, "en")

    def test_invalid_scenario(self):
        with self.assertRaises(ValueError):
            create_post(self.product, scenario="nonexistent", language="ar")

    def test_post_has_hashtags(self):
        post = create_post(self.product, hashtag_count=3)
        self.assertGreater(len(post.hashtags), 0)


class TestGeneratePosts(unittest.TestCase):
    def setUp(self):
        self.product = Product(
            name="كاميرا رقمية",
            affiliate_link="https://amazon.com/dp/B456?tag=test-20",
            category="كاميرات",
            description="كاميرا احترافية",
            discount=20,
            use_case="التصوير",
        )

    def test_generate_all_posts(self):
        posts = generate_posts(self.product, language="ar")
        self.assertEqual(len(posts), 4)

    def test_generate_english_posts(self):
        posts = generate_posts(self.product, language="en")
        self.assertEqual(len(posts), 4)


if __name__ == "__main__":
    unittest.main()

"""Tests for content generator."""

import unittest

from src.content_generator import ContentGenerator
from src.models import Product


class TestContentGenerator(unittest.TestCase):
    def setUp(self):
        self.product = Product(
            name="Wireless Headphones",
            url="https://amazon.com/dp/B001",
            price=49.99,
            category="Electronics",
            description="High quality wireless headphones",
            discount=20,
            affiliate_tag="test-20",
            asin="B001TEST",
        )
        self.generator_en = ContentGenerator(language="en")
        self.generator_ar = ContentGenerator(language="ar")

    def test_generate_post_english(self):
        post = self.generator_en.generate_post(self.product)
        self.assertIn("Wireless Headphones", post.content)
        self.assertTrue(len(post.hashtags) > 0)

    def test_generate_post_arabic(self):
        post = self.generator_ar.generate_post(self.product)
        self.assertIn("Wireless Headphones", post.content)

    def test_generate_deal_alert(self):
        post = self.generator_en.generate_post(
            self.product, scenario="deal_alert"
        )
        self.assertIn("20", post.content)

    def test_generate_for_twitter(self):
        post = self.generator_en.generate_post(
            self.product, platform="twitter"
        )
        self.assertEqual(post.platform, "twitter")
        self.assertLessEqual(len(post.full_text), 280)

    def test_generate_for_telegram(self):
        post = self.generator_en.generate_post(
            self.product, platform="telegram"
        )
        self.assertEqual(post.platform, "telegram")

    def test_generate_multi_platform(self):
        posts = self.generator_en.generate_multi_platform(
            self.product, platforms=["twitter", "telegram"]
        )
        self.assertIn("twitter", posts)
        self.assertIn("telegram", posts)

    def test_generate_batch(self):
        products = [self.product, self.product]
        posts = self.generator_en.generate_batch(products)
        self.assertEqual(len(posts), 2)

    def test_generate_batch_rotate(self):
        products = [self.product] * 4
        posts = self.generator_en.generate_batch(products, scenario="rotate")
        self.assertEqual(len(posts), 4)

    def test_category_hashtag_added(self):
        post = self.generator_en.generate_post(self.product)
        self.assertIn("#Electronics", post.hashtags)

    def test_price_included(self):
        post = self.generator_en.generate_post(
            self.product, include_price=True
        )
        self.assertIn("49.99", post.content)

    def test_no_template_fallback(self):
        gen = ContentGenerator(language="xx")
        post = gen.generate_post(self.product)
        self.assertIn("Wireless Headphones", post.content)


class TestContentGeneratorNoDiscount(unittest.TestCase):
    def setUp(self):
        self.product = Product(
            name="Simple Item",
            url="https://amazon.com/dp/B002",
            price=19.99,
            category="Books",
            description="A good book",
        )
        self.generator = ContentGenerator(language="en")

    def test_deal_alert_no_discount_falls_back(self):
        post = self.generator.generate_post(
            self.product, scenario="deal_alert"
        )
        self.assertIsNotNone(post.content)


if __name__ == "__main__":
    unittest.main()

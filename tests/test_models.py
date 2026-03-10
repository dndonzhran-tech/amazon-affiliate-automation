"""Tests for data models."""

import unittest

from src.models import Campaign, Post, Product


class TestProduct(unittest.TestCase):
    def test_basic_product(self):
        product = Product(
            name="Test Product",
            url="https://amazon.com/dp/B001",
            price=29.99,
            category="Electronics",
        )
        self.assertEqual(product.name, "Test Product")
        self.assertEqual(product.price, 29.99)

    def test_affiliate_url_with_tag(self):
        product = Product(
            name="Test",
            url="https://amazon.com/dp/B001",
            price=10.0,
            category="Books",
            affiliate_tag="mytag-20",
        )
        self.assertIn("tag=mytag-20", product.affiliate_url)

    def test_affiliate_url_without_tag(self):
        product = Product(
            name="Test",
            url="https://amazon.com/dp/B001",
            price=10.0,
            category="Books",
        )
        self.assertEqual(product.affiliate_url, "https://amazon.com/dp/B001")

    def test_affiliate_url_with_existing_query(self):
        product = Product(
            name="Test",
            url="https://amazon.com/dp/B001?ref=home",
            price=10.0,
            category="Books",
            affiliate_tag="mytag-20",
        )
        self.assertIn("&tag=mytag-20", product.affiliate_url)

    def test_to_dict(self):
        product = Product(
            name="Test",
            url="https://amazon.com/dp/B001",
            price=10.0,
            category="Books",
            description="A great book",
        )
        d = product.to_dict()
        self.assertEqual(d["name"], "Test")
        self.assertEqual(d["price"], 10.0)
        self.assertIn("affiliate_url", d)


class TestPost(unittest.TestCase):
    def setUp(self):
        self.product = Product(
            name="Test",
            url="https://amazon.com/dp/B001",
            price=10.0,
            category="Books",
        )

    def test_full_text_with_hashtags(self):
        post = Post(
            content="Check this out!",
            product=self.product,
            hashtags=["#Test", "#Amazon"],
        )
        self.assertIn("#Test", post.full_text)
        self.assertIn("Check this out!", post.full_text)

    def test_full_text_without_hashtags(self):
        post = Post(content="Check this out!", product=self.product)
        self.assertEqual(post.full_text, "Check this out!")


class TestCampaign(unittest.TestCase):
    def test_add_post(self):
        campaign = Campaign(name="Test Campaign")
        product = Product(
            name="Test",
            url="https://amazon.com/dp/B001",
            price=10.0,
            category="Books",
        )
        post = Post(content="Test post", product=product)
        campaign.add_post(post)
        self.assertEqual(campaign.post_count, 1)

    def test_empty_campaign(self):
        campaign = Campaign(name="Empty")
        self.assertEqual(campaign.post_count, 0)


if __name__ == "__main__":
    unittest.main()

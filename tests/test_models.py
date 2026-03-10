"""Tests for data models."""

import os
import tempfile
import unittest

from src.models import (
    Campaign,
    Post,
    PostDB,
    Product,
    ProductDB,
    get_engine,
    get_session,
    init_db,
    Base,
)


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
            asin="B001",
        )
        d = product.to_dict()
        self.assertEqual(d["name"], "Test")
        self.assertEqual(d["price"], 10.0)
        self.assertIn("affiliate_url", d)
        self.assertEqual(d["asin"], "B001")

    def test_to_db(self):
        product = Product(
            name="Test",
            url="https://amazon.com/dp/B001",
            price=10.0,
            category="Books",
            asin="B001TEST",
        )
        db_product = product.to_db()
        self.assertIsInstance(db_product, ProductDB)
        self.assertEqual(db_product.name, "Test")
        self.assertEqual(db_product.asin, "B001TEST")


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

    def test_post_platform(self):
        post = Post(
            content="Test",
            product=self.product,
            platform="telegram",
        )
        self.assertEqual(post.platform, "telegram")

    def test_to_db(self):
        post = Post(
            content="Test content",
            product=self.product,
            platform="twitter",
            scenario="deal_alert",
        )
        db_post = post.to_db()
        self.assertIsInstance(db_post, PostDB)
        self.assertEqual(db_post.platform, "twitter")
        self.assertEqual(db_post.scenario, "deal_alert")


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

    def test_multiple_posts(self):
        campaign = Campaign(name="Multi")
        product = Product(name="P", url="http://x.com", price=1, category="C")
        for i in range(5):
            campaign.add_post(Post(content=f"Post {i}", product=product))
        self.assertEqual(campaign.post_count, 5)


class TestDatabaseModels(unittest.TestCase):
    def setUp(self):
        self.db_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.db_file.close()
        self.db_url = f"sqlite:///{self.db_file.name}"
        init_db(self.db_url)

    def tearDown(self):
        from src.models import _engines
        if self.db_url in _engines:
            _engines[self.db_url].dispose()
            del _engines[self.db_url]
        os.unlink(self.db_file.name)

    def test_init_db_creates_tables(self):
        engine = get_engine(self.db_url)
        tables = Base.metadata.tables.keys()
        self.assertIn("products", tables)
        self.assertIn("posts", tables)
        self.assertIn("schedules", tables)

    def test_save_and_retrieve_product(self):
        session = get_session(self.db_url)
        product = ProductDB(
            name="Test Product",
            url="https://amazon.com/dp/B001",
            price=29.99,
            category="Electronics",
            asin="B001TEST",
        )
        session.add(product)
        session.commit()

        retrieved = session.query(ProductDB).filter_by(asin="B001TEST").first()
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.name, "Test Product")
        session.close()

    def test_save_and_retrieve_post(self):
        session = get_session(self.db_url)
        post = PostDB(
            content="Test post content",
            platform="twitter",
            language="en",
        )
        session.add(post)
        session.commit()

        retrieved = session.query(PostDB).first()
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.content, "Test post content")
        self.assertFalse(retrieved.posted)
        session.close()


if __name__ == "__main__":
    unittest.main()

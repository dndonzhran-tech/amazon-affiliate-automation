"""Tests for database operations."""

import os
import tempfile
import unittest

from src.database import Database
from src.models import Post, Product, init_db


class TestDatabase(unittest.TestCase):
    def setUp(self):
        self.db_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.db_file.close()
        self.db_url = f"sqlite:///{self.db_file.name}"
        init_db(self.db_url)
        self.db = Database(self.db_url)

        self.product = Product(
            name="Test Product",
            url="https://amazon.com/dp/B001",
            price=29.99,
            category="Electronics",
            description="A great product",
            asin="B001TEST",
            affiliate_tag="test-20",
        )

    def tearDown(self):
        from src.models import _engines
        if self.db_url in _engines:
            _engines[self.db_url].dispose()
            del _engines[self.db_url]
        os.unlink(self.db_file.name)

    def test_save_product(self):
        product_id = self.db.save_product(self.product)
        self.assertGreater(product_id, 0)

    def test_save_and_get_product(self):
        product_id = self.db.save_product(self.product)
        retrieved = self.db.get_product(product_id)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.name, "Test Product")

    def test_get_product_by_asin(self):
        self.db.save_product(self.product)
        retrieved = self.db.get_product_by_asin("B001TEST")
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.price, 29.99)

    def test_update_existing_product(self):
        self.db.save_product(self.product)
        self.product.price = 19.99
        self.db.save_product(self.product)
        retrieved = self.db.get_product_by_asin("B001TEST")
        self.assertEqual(retrieved.price, 19.99)

    def test_save_products_batch(self):
        products = [
            Product(name=f"Product {i}", url=f"http://x.com/{i}",
                    price=float(i * 10), category="Test", asin=f"ASIN{i}")
            for i in range(5)
        ]
        ids = self.db.save_products(products)
        self.assertEqual(len(ids), 5)

    def test_get_all_products(self):
        self.db.save_product(self.product)
        products = self.db.get_all_products()
        self.assertEqual(len(products), 1)

    def test_search_products(self):
        self.db.save_product(self.product)
        results = self.db.search_products(keyword="Test")
        self.assertEqual(len(results), 1)

    def test_search_products_by_category(self):
        self.db.save_product(self.product)
        results = self.db.search_products(category="Electronics")
        self.assertEqual(len(results), 1)
        results = self.db.search_products(category="Books")
        self.assertEqual(len(results), 0)

    def test_delete_product(self):
        product_id = self.db.save_product(self.product)
        self.db.delete_product(product_id)
        products = self.db.get_all_products(active_only=True)
        self.assertEqual(len(products), 0)

    def test_save_post(self):
        post = Post(
            content="Test post",
            product=self.product,
            platform="twitter",
        )
        post_id = self.db.save_post(post)
        self.assertGreater(post_id, 0)

    def test_get_posts(self):
        post = Post(content="Test", product=self.product, platform="twitter")
        self.db.save_post(post)
        posts = self.db.get_posts()
        self.assertEqual(len(posts), 1)

    def test_get_posts_by_platform(self):
        post1 = Post(content="Tweet", product=self.product, platform="twitter")
        post2 = Post(content="Msg", product=self.product, platform="telegram")
        self.db.save_post(post1)
        self.db.save_post(post2)
        twitter_posts = self.db.get_posts(platform="twitter")
        self.assertEqual(len(twitter_posts), 1)

    def test_mark_post_as_posted(self):
        post = Post(content="Test", product=self.product, platform="twitter")
        post_id = self.db.save_post(post)
        self.db.mark_post_as_posted(post_id)
        posts = self.db.get_posts(posted=True)
        self.assertEqual(len(posts), 1)

    def test_stats(self):
        self.db.save_product(self.product)
        post = Post(content="Test", product=self.product, platform="twitter")
        self.db.save_post(post, posted=True)
        stats = self.db.get_stats()
        self.assertEqual(stats["total_products"], 1)
        self.assertEqual(stats["posted_count"], 1)


if __name__ == "__main__":
    unittest.main()

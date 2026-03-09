"""اختبارات نماذج البيانات."""

import unittest

from src.models import Post, Product


class TestProduct(unittest.TestCase):
    def test_create_product(self):
        product = Product(
            name="سماعات بلوتوث",
            affiliate_link="https://amazon.com/dp/B123?tag=test-20",
            category="إلكترونيات",
        )
        self.assertEqual(product.name, "سماعات بلوتوث")
        self.assertEqual(product.category, "إلكترونيات")
        self.assertIsNone(product.price)

    def test_product_defaults(self):
        product = Product(name="تست", affiliate_link="http://test.com")
        self.assertEqual(product.category, "")
        self.assertEqual(product.description, "")
        self.assertIsNone(product.discount)


class TestPost(unittest.TestCase):
    def test_full_text_with_hashtags(self):
        post = Post(
            content="محتوى المنشور",
            hashtags=["#تسويق", "#أمازون"],
        )
        result = post.full_text()
        self.assertIn("محتوى المنشور", result)
        self.assertIn("#تسويق", result)
        self.assertIn("#أمازون", result)

    def test_full_text_without_hashtags(self):
        post = Post(content="محتوى فقط")
        result = post.full_text()
        self.assertEqual(result, "محتوى فقط")

    def test_default_language(self):
        post = Post(content="تست")
        self.assertEqual(post.language, "ar")


if __name__ == "__main__":
    unittest.main()

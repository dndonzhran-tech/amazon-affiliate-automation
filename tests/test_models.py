"""اختبارات نماذج البيانات."""

import unittest

from src.models import (
    AnalyticsEvent,
    Campaign,
    ContentType,
    Platform,
    Post,
    PostStatus,
    Product,
)


class TestProduct(unittest.TestCase):
    def test_create_product(self):
        product = Product(
            asin="B123",
            name="سماعات بلوتوث",
            price=49.99,
            category="إلكترونيات",
        )
        self.assertEqual(product.asin, "B123")
        self.assertEqual(product.name, "سماعات بلوتوث")
        self.assertEqual(product.price, 49.99)

    def test_product_defaults(self):
        product = Product(asin="B456", name="تست", price=10.0)
        self.assertEqual(product.category, "")
        self.assertEqual(product.currency, "USD")
        self.assertIsNone(product.discount)
        self.assertEqual(product.features, [])

    def test_product_with_features(self):
        product = Product(
            asin="B789", name="كاميرا", price=299.0,
            features=["4K", "WiFi", "مقاوم للماء"],
        )
        self.assertEqual(len(product.features), 3)


class TestPost(unittest.TestCase):
    def test_full_text_with_hashtags(self):
        post = Post(
            content="محتوى المنشور",
            hashtags=["#تسويق", "#أمازون"],
        )
        result = post.full_text()
        self.assertIn("محتوى المنشور", result)
        self.assertIn("#تسويق", result)

    def test_full_text_without_hashtags(self):
        post = Post(content="محتوى فقط")
        self.assertEqual(post.full_text(), "محتوى فقط")

    def test_default_language(self):
        post = Post(content="تست")
        self.assertEqual(post.language, "ar")

    def test_truncate_for_twitter(self):
        long_content = "أ" * 300
        post = Post(content=long_content, hashtags=["#تست"])
        result = post.truncate_for_twitter()
        self.assertLessEqual(len(result), 280)

    def test_truncate_short_content(self):
        post = Post(content="قصير", hashtags=["#تست"])
        result = post.truncate_for_twitter()
        self.assertIn("قصير", result)
        self.assertIn("#تست", result)


class TestEnums(unittest.TestCase):
    def test_post_status(self):
        self.assertEqual(PostStatus.DRAFT.value, "draft")
        self.assertEqual(PostStatus.PUBLISHED.value, "published")

    def test_platform(self):
        self.assertEqual(Platform.TWITTER.value, "twitter")
        self.assertEqual(Platform.TELEGRAM.value, "telegram")

    def test_content_type(self):
        self.assertEqual(ContentType.DEAL_ALERT.value, "deal_alert")


class TestCampaign(unittest.TestCase):
    def test_campaign_defaults(self):
        campaign = Campaign(name="حملة اختبار")
        self.assertEqual(campaign.posts_per_day, 4)
        self.assertEqual(campaign.language, "ar")
        self.assertEqual(campaign.status, "active")


class TestAnalyticsEvent(unittest.TestCase):
    def test_event_creation(self):
        event = AnalyticsEvent(
            event_type="click",
            product_asin="B123",
            platform="twitter",
        )
        self.assertEqual(event.event_type, "click")
        self.assertEqual(event.revenue, 0.0)


if __name__ == "__main__":
    unittest.main()

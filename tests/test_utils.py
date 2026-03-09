"""اختبارات الأدوات المساعدة."""

import unittest

from src.utils import (
    build_affiliate_link,
    format_post,
    get_hashtags,
    get_template,
    load_json,
)


class TestLoadJson(unittest.TestCase):
    def test_load_hashtags(self):
        data = load_json("hashtags.json")
        self.assertIn("hashtags", data)
        self.assertIn("ar", data["hashtags"])
        self.assertIn("en", data["hashtags"])

    def test_load_templates(self):
        data = load_json("templates.json")
        self.assertIn("scenarios", data)

    def test_load_nonexistent_file(self):
        with self.assertRaises(FileNotFoundError):
            load_json("nonexistent.json")


class TestGetHashtags(unittest.TestCase):
    def test_arabic_hashtags(self):
        tags = get_hashtags("ar", 3)
        self.assertEqual(len(tags), 3)
        for tag in tags:
            self.assertTrue(tag.startswith("#"))

    def test_english_hashtags(self):
        tags = get_hashtags("en", 3)
        self.assertEqual(len(tags), 3)

    def test_unknown_language(self):
        tags = get_hashtags("fr", 3)
        self.assertEqual(tags, [])

    def test_count_exceeds_available(self):
        tags = get_hashtags("ar", 100)
        self.assertGreater(len(tags), 0)


class TestGetTemplate(unittest.TestCase):
    def test_arabic_template(self):
        template = get_template("product_review", "ar")
        self.assertIn("{product_name}", template)

    def test_english_template(self):
        template = get_template("deal_alert", "en")
        self.assertIn("{product_name}", template)

    def test_nonexistent_scenario(self):
        template = get_template("nonexistent", "ar")
        self.assertEqual(template, "")


class TestFormatPost(unittest.TestCase):
    def test_format_success(self):
        template = "منتج: {product_name} - رابط: {link}"
        result = format_post(template, product_name="تست", link="http://example.com")
        self.assertEqual(result, "منتج: تست - رابط: http://example.com")

    def test_format_missing_var(self):
        template = "منتج: {product_name} - {missing}"
        with self.assertRaises(ValueError):
            format_post(template, product_name="تست")


class TestBuildAffiliateLink(unittest.TestCase):
    def test_url_without_params(self):
        result = build_affiliate_link("https://amazon.com/dp/B123", "mytag-20")
        self.assertEqual(result, "https://amazon.com/dp/B123?tag=mytag-20")

    def test_url_with_params(self):
        result = build_affiliate_link("https://amazon.com/dp/B123?ref=sr", "mytag-20")
        self.assertEqual(result, "https://amazon.com/dp/B123?ref=sr&tag=mytag-20")


if __name__ == "__main__":
    unittest.main()

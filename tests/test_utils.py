"""Tests for utility functions."""

import unittest

from src.utils import (
    build_affiliate_url,
    format_template,
    get_hashtags,
    get_template,
    load_json_config,
)


class TestLoadJsonConfig(unittest.TestCase):
    def test_load_hashtags(self):
        config = load_json_config("hashtags.json")
        self.assertIn("hashtags", config)
        self.assertIn("en", config["hashtags"])
        self.assertIn("ar", config["hashtags"])

    def test_load_templates(self):
        config = load_json_config("templates.json")
        self.assertIn("scenarios", config)

    def test_invalid_file(self):
        with self.assertRaises(FileNotFoundError):
            load_json_config("nonexistent.json")


class TestGetHashtags(unittest.TestCase):
    def test_english_hashtags(self):
        hashtags = get_hashtags("en", 3)
        self.assertEqual(len(hashtags), 3)
        for tag in hashtags:
            self.assertTrue(tag.startswith("#"))

    def test_arabic_hashtags(self):
        hashtags = get_hashtags("ar", 2)
        self.assertEqual(len(hashtags), 2)

    def test_invalid_language(self):
        hashtags = get_hashtags("xx", 3)
        self.assertEqual(hashtags, [])

    def test_count_exceeds_available(self):
        hashtags = get_hashtags("en", 100)
        self.assertGreater(len(hashtags), 0)


class TestGetTemplate(unittest.TestCase):
    def test_english_template(self):
        template = get_template("en", "product_review")
        self.assertIn("{product_name}", template)

    def test_arabic_template(self):
        template = get_template("ar", "deal_alert")
        self.assertIn("{product_name}", template)

    def test_invalid_scenario(self):
        template = get_template("en", "nonexistent")
        self.assertEqual(template, "")


class TestFormatTemplate(unittest.TestCase):
    def test_basic_format(self):
        result = format_template("Hello {name}!", name="World")
        self.assertEqual(result, "Hello World!")

    def test_missing_key(self):
        result = format_template("Hello {name}!")
        self.assertEqual(result, "Hello {name}!")


class TestBuildAffiliateUrl(unittest.TestCase):
    def test_with_tag(self):
        url = build_affiliate_url("https://amazon.com/dp/B001", "mytag-20")
        self.assertEqual(url, "https://amazon.com/dp/B001?tag=mytag-20")

    def test_without_tag(self):
        url = build_affiliate_url("https://amazon.com/dp/B001", "")
        self.assertEqual(url, "https://amazon.com/dp/B001")

    def test_with_existing_query_params(self):
        url = build_affiliate_url("https://amazon.com/dp/B001?ref=home", "mytag-20")
        self.assertEqual(url, "https://amazon.com/dp/B001?ref=home&tag=mytag-20")


if __name__ == "__main__":
    unittest.main()

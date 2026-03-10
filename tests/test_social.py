"""Tests for social media posting modules."""

import unittest
from unittest.mock import MagicMock, patch

from src.social.twitter import TwitterPoster
from src.social.telegram import TelegramPoster


class TestTwitterPoster(unittest.TestCase):
    def test_not_configured_without_credentials(self):
        poster = TwitterPoster(
            api_key="", api_secret="",
            access_token="", access_token_secret="",
        )
        self.assertFalse(poster.is_configured())

    def test_configured_with_credentials(self):
        poster = TwitterPoster(
            api_key="key", api_secret="secret",
            access_token="token", access_token_secret="token_secret",
        )
        self.assertTrue(poster.is_configured())

    def test_post_tweet_without_config(self):
        poster = TwitterPoster()
        result = poster.post_tweet("Test tweet")
        self.assertIsNone(result)

    def test_split_short_text(self):
        poster = TwitterPoster()
        chunks = poster.split_for_thread("Short text")
        self.assertEqual(len(chunks), 1)

    def test_split_long_text(self):
        poster = TwitterPoster()
        long_text = "This is a test. " * 50
        chunks = poster.split_for_thread(long_text)
        self.assertGreater(len(chunks), 1)
        for chunk in chunks:
            self.assertLessEqual(len(chunk), 280)


class TestTelegramPoster(unittest.TestCase):
    def test_not_configured_without_credentials(self):
        poster = TelegramPoster(bot_token="", chat_id="")
        self.assertFalse(poster.is_configured())

    def test_configured_with_credentials(self):
        poster = TelegramPoster(bot_token="token", chat_id="123")
        self.assertTrue(poster.is_configured())

    def test_send_message_without_config(self):
        poster = TelegramPoster(bot_token="", chat_id="")
        result = poster.send_message("Test message")
        self.assertIsNone(result)

    def test_format_product_en(self):
        poster = TelegramPoster(bot_token="t", chat_id="c")
        text = poster._format_product_en(
            "Headphones", "Great sound", 49.99,
            "https://amazon.com/test", 20
        )
        self.assertIn("Headphones", text)
        self.assertIn("49.99", text)
        self.assertIn("20% OFF", text)
        self.assertIn("Buy Now", text)

    def test_format_product_ar(self):
        poster = TelegramPoster(bot_token="t", chat_id="c")
        text = poster._format_product_ar(
            "سماعات", "صوت رائع", 49.99,
            "https://amazon.com/test", 20
        )
        self.assertIn("سماعات", text)
        self.assertIn("49.99", text)
        self.assertIn("اشتري الآن", text)

    @patch("src.social.telegram.requests.post")
    def test_send_message_success(self, mock_post):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "ok": True,
            "result": {"message_id": 123},
        }
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        poster = TelegramPoster(bot_token="test_token", chat_id="test_chat")
        result = poster.send_message("Test message")
        self.assertIsNotNone(result)
        self.assertEqual(result["id"], 123)

    @patch("src.social.telegram.requests.post")
    def test_send_photo_success(self, mock_post):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "ok": True,
            "result": {"message_id": 456},
        }
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        poster = TelegramPoster(bot_token="test_token", chat_id="test_chat")
        result = poster.send_photo("https://img.com/photo.jpg", caption="Nice!")
        self.assertIsNotNone(result)
        self.assertEqual(result["id"], 456)


if __name__ == "__main__":
    unittest.main()

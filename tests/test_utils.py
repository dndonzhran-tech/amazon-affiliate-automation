"""Tests for src/utils.py utility functions."""

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

import pytest
import requests

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from models import GeneratedContent, Product, PostResult
from utils import (
    build_affiliate_link,
    fetch_trending_products,
    generate_content_with_ai,
    get_hashtags,
    get_template,
    load_config,
    post_to_platform,
    rate_limit_wait,
    send_notification,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_product(**overrides):
    defaults = dict(
        asin="B001",
        title="Test Product",
        price="29.99",
        currency="USD",
        affiliate_link="https://www.amazon.com/dp/B001?tag=test-20",
        rating=4.5,
    )
    defaults.update(overrides)
    return Product(**defaults)


# ---------------------------------------------------------------------------
# load_config
# ---------------------------------------------------------------------------

class TestLoadConfig:
    @patch("builtins.open", mock_open(read_data='{"key": "value"}'))
    def test_returns_parsed_json(self):
        result = load_config("test.json")
        assert result == {"key": "value"}

    @patch("builtins.open", side_effect=FileNotFoundError("missing"))
    def test_raises_on_missing_file(self, _):
        with pytest.raises(FileNotFoundError):
            load_config("nonexistent.json")


# ---------------------------------------------------------------------------
# get_hashtags
# ---------------------------------------------------------------------------

class TestGetHashtags:
    @patch("utils.load_config")
    def test_returns_english_hashtags(self, mock_cfg):
        mock_cfg.return_value = {"hashtags": {"en": ["#deal", "#amazon"], "ar": ["#عرض"]}}
        assert get_hashtags("en") == ["#deal", "#amazon"]

    @patch("utils.load_config")
    def test_returns_empty_for_unknown_language(self, mock_cfg):
        mock_cfg.return_value = {"hashtags": {"en": ["#a"]}}
        assert get_hashtags("fr") == []


# ---------------------------------------------------------------------------
# get_template
# ---------------------------------------------------------------------------

class TestGetTemplate:
    @patch("utils.load_config")
    def test_returns_random_template(self, mock_cfg):
        mock_cfg.return_value = {
            "scenarios": {"en": {"s1": "Template A", "s2": "Template B"}}
        }
        result = get_template("en")
        assert result in ("Template A", "Template B")

    @patch("utils.load_config")
    def test_returns_default_when_no_scenarios(self, mock_cfg):
        mock_cfg.return_value = {"scenarios": {}}
        result = get_template("en")
        assert "{product_name}" in result
        assert "{affiliate_link}" in result


# ---------------------------------------------------------------------------
# build_affiliate_link
# ---------------------------------------------------------------------------

class TestBuildAffiliateLink:
    def test_basic(self):
        link = build_affiliate_link("B001ABC", "mytag-20")
        assert link == "https://www.amazon.com/dp/B001ABC?tag=mytag-20"

    def test_special_characters_in_asin(self):
        link = build_affiliate_link("B0-TEST", "tag-20")
        assert "B0-TEST" in link


# ---------------------------------------------------------------------------
# fetch_trending_products
# ---------------------------------------------------------------------------

class TestFetchTrendingProducts:
    @patch("utils.requests.get")
    def test_success_with_deals_key(self, mock_get):
        mock_get.return_value = MagicMock(
            status_code=200,
            json=lambda: {
                "deals": [
                    {"asin": "B001", "title": "Deal 1", "price": {"current_price": "10.00", "currency": "USD"}},
                    {"asin": "B002", "title": "Deal 2", "price": 20},
                ]
            },
        )
        mock_get.return_value.raise_for_status = MagicMock()
        products = fetch_trending_products("key", "host.example.com")
        assert len(products) == 2
        assert products[0].asin == "B001"
        assert products[1].price == "20"

    @patch("utils.requests.get")
    def test_success_with_products_key(self, mock_get):
        mock_get.return_value = MagicMock(
            status_code=200,
            json=lambda: {"products": [{"asin": "B010", "title": "P1"}]},
        )
        mock_get.return_value.raise_for_status = MagicMock()
        products = fetch_trending_products("key", "host.example.com")
        assert len(products) == 1

    @patch("utils.requests.get", side_effect=requests.RequestException("timeout"))
    def test_returns_empty_on_error(self, _):
        products = fetch_trending_products("key", "host")
        assert products == []

    @patch("utils.requests.get")
    def test_passes_correct_headers_and_params(self, mock_get):
        mock_get.return_value = MagicMock(
            status_code=200, json=lambda: {"deals": []}
        )
        mock_get.return_value.raise_for_status = MagicMock()
        fetch_trending_products("mykey", "myhost", category="books", country="UK")
        call_kwargs = mock_get.call_args
        assert call_kwargs.kwargs["headers"]["X-RapidAPI-Key"] == "mykey"
        assert call_kwargs.kwargs["headers"]["X-RapidAPI-Host"] == "myhost"
        assert call_kwargs.kwargs["params"]["country"] == "UK"
        assert call_kwargs.kwargs["params"]["category"] == "books"


# ---------------------------------------------------------------------------
# generate_content_with_ai
# ---------------------------------------------------------------------------

class TestGenerateContentWithAI:
    @patch("utils.get_hashtags", return_value=["#deal", "#amazon", "#sale", "#hot", "#buy"])
    @patch("utils.get_template", return_value="Check out {product_name} at {affiliate_link}")
    @patch("utils.requests.post")
    def test_success(self, mock_post, mock_tpl, mock_ht):
        mock_post.return_value = MagicMock(
            status_code=200,
            json=lambda: {
                "choices": [{"message": {"content": "Amazing product! Buy now!"}}]
            },
        )
        mock_post.return_value.raise_for_status = MagicMock()
        product = _make_product()
        result = generate_content_with_ai(product, "groq_key")
        assert isinstance(result, GeneratedContent)
        assert result.text == "Amazing product! Buy now!"
        assert result.product is product
        assert len(result.hashtags) <= 5

    @patch("utils.get_hashtags", return_value=["#a", "#b", "#c"])
    @patch("utils.get_template", return_value="{product_name} - {affiliate_link}")
    @patch("utils.requests.post", side_effect=requests.RequestException("fail"))
    def test_fallback_on_api_error(self, *_):
        product = _make_product()
        result = generate_content_with_ai(product, "bad_key")
        assert isinstance(result, GeneratedContent)
        # Fallback should use template with product name
        assert product.title in result.text

    @patch("utils.get_hashtags", return_value=["#a", "#b", "#c"])
    @patch("utils.get_template", return_value="{product_name} - {affiliate_link}")
    @patch("utils.requests.post")
    def test_fallback_on_key_error(self, mock_post, *_):
        mock_post.return_value = MagicMock(
            status_code=200,
            json=lambda: {"choices": []},  # KeyError when accessing [0]
        )
        mock_post.return_value.raise_for_status = MagicMock()
        product = _make_product()
        result = generate_content_with_ai(product, "key")
        assert product.title in result.text

    @patch("utils.get_hashtags", return_value=["#one", "#two"])
    @patch("utils.get_template", return_value="T")
    @patch("utils.requests.post")
    def test_hashtag_sampling(self, mock_post, *_):
        mock_post.return_value = MagicMock(
            status_code=200,
            json=lambda: {"choices": [{"message": {"content": "text"}}]},
        )
        mock_post.return_value.raise_for_status = MagicMock()
        result = generate_content_with_ai(_make_product(), "key")
        # Only 2 hashtags available, min(5, 2) = 2
        assert len(result.hashtags) == 2

    @patch("utils.get_hashtags", return_value=["#a"] * 10)
    @patch("utils.get_template", return_value="T")
    @patch("utils.requests.post")
    def test_sends_correct_payload(self, mock_post, *_):
        mock_post.return_value = MagicMock(
            status_code=200,
            json=lambda: {"choices": [{"message": {"content": "ok"}}]},
        )
        mock_post.return_value.raise_for_status = MagicMock()
        generate_content_with_ai(_make_product(), "gkey", language="ar", model="custom-model")
        call_kwargs = mock_post.call_args
        payload = call_kwargs.kwargs["json"]
        assert payload["model"] == "custom-model"
        assert payload["temperature"] == 0.8
        assert "Arabic" in payload["messages"][0]["content"]


# ---------------------------------------------------------------------------
# post_to_platform
# ---------------------------------------------------------------------------

class TestPostToPlatform:
    @patch("utils.requests.post")
    def test_success(self, mock_post):
        mock_post.return_value = MagicMock(
            status_code=200,
            json=lambda: {"id": "post_123"},
        )
        mock_post.return_value.raise_for_status = MagicMock()
        content = GeneratedContent(
            product=_make_product(),
            text="Buy this!",
            hashtags=["#deal"],
        )
        result = post_to_platform(content, "https://api.example.com/post", "token123")
        assert isinstance(result, PostResult)
        assert result.success is True
        assert result.post_id == "post_123"

    @patch("utils.requests.post")
    def test_success_with_post_id_key(self, mock_post):
        mock_post.return_value = MagicMock(
            status_code=200,
            json=lambda: {"post_id": "p456"},
        )
        mock_post.return_value.raise_for_status = MagicMock()
        content = GeneratedContent(product=_make_product(), text="Hello")
        result = post_to_platform(content, "https://api.example.com", "tk")
        assert result.post_id == "p456"

    @patch("utils.requests.post", side_effect=requests.RequestException("network error"))
    def test_failure(self, _):
        content = GeneratedContent(product=_make_product(), text="Hello")
        result = post_to_platform(content, "https://api.example.com", "tk")
        assert result.success is False
        assert "network error" in result.error

    @patch("utils.requests.post")
    def test_sends_correct_payload(self, mock_post):
        mock_post.return_value = MagicMock(status_code=200, json=lambda: {"id": "1"})
        mock_post.return_value.raise_for_status = MagicMock()
        product = _make_product(affiliate_link="https://amzn.to/test")
        content = GeneratedContent(product=product, text="Great deal!", hashtags=["#wow"])
        post_to_platform(content, "https://api.example.com", "bearer_token")
        call_kwargs = mock_post.call_args
        assert call_kwargs.kwargs["headers"]["Authorization"] == "Bearer bearer_token"
        body = call_kwargs.kwargs["json"]
        assert body["link"] == "https://amzn.to/test"
        assert "#wow" in body["message"]


# ---------------------------------------------------------------------------
# send_notification
# ---------------------------------------------------------------------------

class TestSendNotification:
    @patch("utils.requests.post")
    def test_success(self, mock_post):
        mock_post.return_value = MagicMock(status_code=200)
        mock_post.return_value.raise_for_status = MagicMock()
        assert send_notification("hello", "https://hooks.example.com/abc") is True

    @patch("utils.requests.post", side_effect=requests.RequestException("timeout"))
    def test_failure(self, _):
        assert send_notification("hello", "https://hooks.example.com/abc") is False

    @patch("utils.requests.post")
    def test_sends_both_text_and_message_fields(self, mock_post):
        mock_post.return_value = MagicMock(status_code=200)
        mock_post.return_value.raise_for_status = MagicMock()
        send_notification("hi", "https://hooks.example.com")
        payload = mock_post.call_args.kwargs["json"]
        assert payload["text"] == "hi"
        assert payload["message"] == "hi"


# ---------------------------------------------------------------------------
# rate_limit_wait
# ---------------------------------------------------------------------------

class TestRateLimitWait:
    @patch("utils.time.sleep")
    @patch("utils.random.uniform", return_value=3.0)
    def test_waits_random_interval(self, mock_uniform, mock_sleep):
        rate_limit_wait(2.0, 5.0)
        mock_uniform.assert_called_once_with(2.0, 5.0)
        mock_sleep.assert_called_once_with(3.0)

    @patch("utils.time.sleep")
    @patch("utils.random.uniform", return_value=1.0)
    def test_default_bounds(self, mock_uniform, mock_sleep):
        rate_limit_wait()
        mock_uniform.assert_called_once_with(2.0, 5.0)

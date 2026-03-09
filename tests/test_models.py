"""Tests for src/models.py dataclasses."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from models import GeneratedContent, PostResult, Product, ShortsScript


# ---------------------------------------------------------------------------
# Product
# ---------------------------------------------------------------------------

class TestProduct:
    """Tests for the Product dataclass."""

    def test_defaults(self):
        p = Product(asin="B001", title="Widget")
        assert p.asin == "B001"
        assert p.title == "Widget"
        assert p.price is None
        assert p.currency is None
        assert p.image_url is None
        assert p.affiliate_link is None
        assert p.rating is None
        assert p.review_count is None
        assert p.category is None
        assert p.description is None
        assert p.features == []
        assert p.discount_percent is None

    def test_from_api_response_full_dict_price(self):
        data = {
            "asin": "B099",
            "title": "Test Product",
            "price": {"current_price": "29.99", "currency": "USD"},
            "image": "https://img.example.com/pic.jpg",
            "rating": 4.5,
            "reviews_count": 1200,
            "category": "Electronics",
            "description": "A great product",
            "features": ["Feature A", "Feature B"],
            "discount_percent": 15,
        }
        p = Product.from_api_response(data)
        assert p.asin == "B099"
        assert p.title == "Test Product"
        assert p.price == "29.99"
        assert p.currency == "USD"
        assert p.image_url == "https://img.example.com/pic.jpg"
        assert p.rating == 4.5
        assert p.review_count == 1200
        assert p.category == "Electronics"
        assert p.description == "A great product"
        assert p.features == ["Feature A", "Feature B"]
        assert p.discount_percent == 15

    def test_from_api_response_scalar_price(self):
        data = {
            "asin": "B100",
            "title": "Cheap Item",
            "price": 9.99,
        }
        p = Product.from_api_response(data)
        assert p.price == "9.99"
        assert p.currency is None

    def test_from_api_response_price_none(self):
        data = {"asin": "B101", "title": "Free Item", "price": None}
        p = Product.from_api_response(data)
        assert p.price is None
        assert p.currency is None

    def test_from_api_response_empty_price_dict(self):
        data = {"asin": "B102", "title": "No Price", "price": {}}
        p = Product.from_api_response(data)
        assert p.price is None
        assert p.currency is None

    def test_from_api_response_thumbnail_fallback(self):
        data = {"asin": "B103", "title": "Thumb", "thumbnail": "https://thumb.jpg"}
        p = Product.from_api_response(data)
        assert p.image_url == "https://thumb.jpg"

    def test_from_api_response_image_takes_priority_over_thumbnail(self):
        data = {
            "asin": "B104",
            "title": "Both",
            "image": "https://image.jpg",
            "thumbnail": "https://thumb.jpg",
        }
        p = Product.from_api_response(data)
        assert p.image_url == "https://image.jpg"

    def test_from_api_response_review_count_fallback(self):
        data = {"asin": "B105", "title": "Reviews", "review_count": 500}
        p = Product.from_api_response(data)
        assert p.review_count == 500

    def test_from_api_response_savings_percent_fallback(self):
        data = {"asin": "B106", "title": "Sale", "savings_percent": 25}
        p = Product.from_api_response(data)
        assert p.discount_percent == 25

    def test_from_api_response_missing_fields(self):
        data = {}
        p = Product.from_api_response(data)
        assert p.asin == ""
        assert p.title == ""
        assert p.features == []

    def test_from_api_response_features_default(self):
        data = {"asin": "B107", "title": "No Features"}
        p = Product.from_api_response(data)
        assert p.features == []


# ---------------------------------------------------------------------------
# GeneratedContent
# ---------------------------------------------------------------------------

class TestGeneratedContent:
    """Tests for the GeneratedContent dataclass."""

    def _make_product(self):
        return Product(asin="B001", title="Widget")

    def test_full_post_with_hashtags(self):
        gc = GeneratedContent(
            product=self._make_product(),
            text="Buy this now!",
            hashtags=["#deal", "#amazon"],
        )
        assert gc.full_post == "Buy this now!\n\n#deal #amazon"

    def test_full_post_no_hashtags(self):
        gc = GeneratedContent(product=self._make_product(), text="Hello world")
        assert gc.full_post == "Hello world"

    def test_full_post_strips_trailing_whitespace(self):
        gc = GeneratedContent(product=self._make_product(), text="Text", hashtags=[])
        # strip() on "Text\n\n" should return "Text"
        assert gc.full_post == "Text"

    def test_defaults(self):
        gc = GeneratedContent(product=self._make_product(), text="T")
        assert gc.hashtags == []
        assert gc.language == "en"


# ---------------------------------------------------------------------------
# ShortsScript
# ---------------------------------------------------------------------------

class TestShortsScript:
    """Tests for the ShortsScript dataclass."""

    def _make_product(self):
        return Product(asin="B001", title="Widget")

    def _make_script(self, **overrides):
        defaults = dict(
            product=self._make_product(),
            hook="Hook text",
            body="Body text",
            cta="CTA text",
            title="My Title",
            description="My desc",
            tags=["tag1", "tag2"],
        )
        defaults.update(overrides)
        return ShortsScript(**defaults)

    def test_full_script_default_duration(self):
        s = self._make_script()
        expected = (
            "[HOOK - 0-3s]\nHook text\n\n"
            "[BODY - 3-25s]\nBody text\n\n"
            "[CTA - 25-30s]\nCTA text"
        )
        assert s.full_script == expected

    def test_full_script_custom_duration(self):
        s = self._make_script(duration_seconds=45)
        assert "[CTA - 25-45s]" in s.full_script

    def test_full_description_with_tags(self):
        s = self._make_script(tags=["tag1", "#tag2", "tag3"])
        desc = s.full_description
        assert desc.startswith("My desc\n\n")
        assert "#tag1" in desc
        assert "#tag2" in desc
        assert "#tag3" in desc
        # Ensure no double hash
        assert "##" not in desc

    def test_full_description_max_15_tags(self):
        s = self._make_script(tags=[f"t{i}" for i in range(20)])
        tag_line = s.full_description.split("\n\n")[1]
        assert len(tag_line.split()) == 15

    def test_defaults(self):
        s = ShortsScript(
            product=self._make_product(),
            hook="H",
            body="B",
            cta="C",
            title="T",
            description="D",
        )
        assert s.tags == []
        assert s.language == "en"
        assert s.duration_seconds == 30


# ---------------------------------------------------------------------------
# PostResult
# ---------------------------------------------------------------------------

class TestPostResult:
    """Tests for the PostResult dataclass."""

    def test_success(self):
        pr = PostResult(platform="twitter", success=True, post_id="123", url="https://t.co/123")
        assert pr.platform == "twitter"
        assert pr.success is True
        assert pr.post_id == "123"
        assert pr.url == "https://t.co/123"
        assert pr.error is None

    def test_failure(self):
        pr = PostResult(platform="youtube", success=False, error="timeout")
        assert pr.success is False
        assert pr.error == "timeout"
        assert pr.post_id is None
        assert pr.url is None

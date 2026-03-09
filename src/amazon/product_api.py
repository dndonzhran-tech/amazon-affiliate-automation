"""نظام جلب المنتجات من Amazon Product Advertising API."""

import hashlib
import hmac
import json
import logging
from datetime import datetime, timezone
from urllib.parse import quote

import httpx

from src.config import (
    AMAZON_ACCESS_KEY,
    AMAZON_MARKETPLACE,
    AMAZON_PARTNER_TAG,
    AMAZON_REGION,
    AMAZON_SECRET_KEY,
)
from src.models import Product

logger = logging.getLogger(__name__)

# Amazon PA-API 5.0 endpoints
PAAPI_HOST = f"webservices.{AMAZON_MARKETPLACE}"
PAAPI_ENDPOINT = f"https://{PAAPI_HOST}/paapi5"


def _sign_request(payload: str, target: str) -> dict:
    """توقيع طلب PA-API 5.0 باستخدام AWS Signature V4."""
    now = datetime.now(timezone.utc)
    datestamp = now.strftime("%Y%m%d")
    amz_date = now.strftime("%Y%m%dT%H%M%SZ")
    service = "ProductAdvertisingAPI"

    headers = {
        "host": PAAPI_HOST,
        "content-type": "application/json; charset=utf-8",
        "x-amz-date": amz_date,
        "x-amz-target": f"com.amazon.paapi5.v1.ProductAdvertisingAPIv1.{target}",
        "content-encoding": "amz-1.0",
    }

    credential_scope = f"{datestamp}/{AMAZON_REGION}/{service}/aws4_request"

    signed_headers = ";".join(sorted(headers.keys()))
    canonical_headers = "".join(
        f"{k}:{v}\n" for k, v in sorted(headers.items())
    )
    payload_hash = hashlib.sha256(payload.encode("utf-8")).hexdigest()

    canonical_request = (
        f"POST\n/paapi5/{target.lower()}\n\n"
        f"{canonical_headers}\n{signed_headers}\n{payload_hash}"
    )

    string_to_sign = (
        f"AWS4-HMAC-SHA256\n{amz_date}\n{credential_scope}\n"
        f"{hashlib.sha256(canonical_request.encode('utf-8')).hexdigest()}"
    )

    def _hmac_sign(key, msg):
        return hmac.new(key, msg.encode("utf-8"), hashlib.sha256).digest()

    signing_key = _hmac_sign(
        _hmac_sign(
            _hmac_sign(
                _hmac_sign(
                    f"AWS4{AMAZON_SECRET_KEY}".encode("utf-8"),
                    datestamp,
                ),
                AMAZON_REGION,
            ),
            service,
        ),
        "aws4_request",
    )

    signature = hmac.new(
        signing_key, string_to_sign.encode("utf-8"), hashlib.sha256
    ).hexdigest()

    headers["authorization"] = (
        f"AWS4-HMAC-SHA256 Credential={AMAZON_ACCESS_KEY}/{credential_scope}, "
        f"SignedHeaders={signed_headers}, Signature={signature}"
    )

    return headers


def search_products(
    keywords: str,
    category: str = "All",
    min_price: float = 0,
    max_price: float = 0,
    min_rating: float = 0,
    item_count: int = 10,
) -> list[Product]:
    """البحث عن منتجات على أمازون."""
    payload = {
        "Keywords": keywords,
        "SearchIndex": category,
        "ItemCount": min(item_count, 10),
        "PartnerTag": AMAZON_PARTNER_TAG,
        "PartnerType": "Associates",
        "Resources": [
            "ItemInfo.Title",
            "ItemInfo.Features",
            "ItemInfo.ByLineInfo",
            "Images.Primary.Large",
            "Offers.Listings.Price",
            "Offers.Listings.SavingBasis",
            "CustomerReviews.Count",
            "CustomerReviews.StarRating",
        ],
    }

    if min_price > 0:
        payload["MinPrice"] = int(min_price * 100)
    if max_price > 0:
        payload["MaxPrice"] = int(max_price * 100)
    if min_rating > 0:
        payload["MinReviewsRating"] = min_rating

    payload_str = json.dumps(payload)
    headers = _sign_request(payload_str, "SearchItems")

    try:
        response = httpx.post(
            f"{PAAPI_ENDPOINT}/searchitems",
            content=payload_str,
            headers=headers,
            timeout=30.0,
        )
        response.raise_for_status()
        data = response.json()
        return _parse_search_results(data)
    except httpx.HTTPError as e:
        logger.error(f"خطأ في البحث عن المنتجات: {e}")
        return []


def get_product_by_asin(asin: str) -> Product | None:
    """جلب معلومات منتج محدد باستخدام ASIN."""
    payload = {
        "ItemIds": [asin],
        "PartnerTag": AMAZON_PARTNER_TAG,
        "PartnerType": "Associates",
        "Resources": [
            "ItemInfo.Title",
            "ItemInfo.Features",
            "ItemInfo.ByLineInfo",
            "ItemInfo.ContentInfo",
            "Images.Primary.Large",
            "Offers.Listings.Price",
            "Offers.Listings.SavingBasis",
            "CustomerReviews.Count",
            "CustomerReviews.StarRating",
        ],
    }

    payload_str = json.dumps(payload)
    headers = _sign_request(payload_str, "GetItems")

    try:
        response = httpx.post(
            f"{PAAPI_ENDPOINT}/getitems",
            content=payload_str,
            headers=headers,
            timeout=30.0,
        )
        response.raise_for_status()
        data = response.json()
        items = data.get("ItemsResult", {}).get("Items", [])
        if items:
            return _parse_item(items[0])
        return None
    except httpx.HTTPError as e:
        logger.error(f"خطأ في جلب المنتج {asin}: {e}")
        return None


def get_browse_node_products(
    browse_node_id: str, item_count: int = 10
) -> list[Product]:
    """جلب منتجات من فئة محددة (Browse Node)."""
    payload = {
        "BrowseNodeId": browse_node_id,
        "ItemCount": min(item_count, 10),
        "PartnerTag": AMAZON_PARTNER_TAG,
        "PartnerType": "Associates",
        "Resources": [
            "ItemInfo.Title",
            "ItemInfo.Features",
            "Images.Primary.Large",
            "Offers.Listings.Price",
            "Offers.Listings.SavingBasis",
            "CustomerReviews.Count",
            "CustomerReviews.StarRating",
        ],
    }

    payload_str = json.dumps(payload)
    headers = _sign_request(payload_str, "GetBrowseNodes")

    try:
        response = httpx.post(
            f"{PAAPI_ENDPOINT}/getbrowsenodes",
            content=payload_str,
            headers=headers,
            timeout=30.0,
        )
        response.raise_for_status()
        data = response.json()
        return _parse_search_results(data)
    except httpx.HTTPError as e:
        logger.error(f"خطأ في جلب منتجات الفئة {browse_node_id}: {e}")
        return []


def _parse_search_results(data: dict) -> list[Product]:
    """تحليل نتائج البحث من الـ API."""
    items = data.get("SearchResult", {}).get("Items", [])
    return [_parse_item(item) for item in items]


def _parse_item(item: dict) -> Product:
    """تحليل عنصر واحد من الـ API وتحويله لنموذج Product."""
    asin = item.get("ASIN", "")
    info = item.get("ItemInfo", {})
    title = info.get("Title", {}).get("DisplayValue", "")
    features = [
        f.get("DisplayValue", "")
        for f in info.get("Features", {}).get("DisplayValues", [])
    ]

    images = item.get("Images", {})
    image_url = images.get("Primary", {}).get("Large", {}).get("URL", "")

    offers = item.get("Offers", {}).get("Listings", [{}])
    listing = offers[0] if offers else {}
    price_info = listing.get("Price", {})
    price = price_info.get("Amount", 0.0)
    currency = price_info.get("Currency", "USD")

    saving_basis = listing.get("SavingBasis", {})
    original_price = saving_basis.get("Amount", 0)
    discount = None
    if original_price and price:
        discount = int(((original_price - price) / original_price) * 100)

    reviews = item.get("CustomerReviews", {})
    rating = reviews.get("StarRating", {}).get("Value", 0.0)
    review_count = reviews.get("Count", 0)

    detail_url = item.get("DetailPageURL", "")

    return Product(
        asin=asin,
        name=title,
        price=price,
        currency=currency,
        description=" | ".join(features[:3]) if features else "",
        image_url=image_url,
        affiliate_link=detail_url,
        rating=rating,
        review_count=review_count,
        discount=discount,
        features=features,
    )

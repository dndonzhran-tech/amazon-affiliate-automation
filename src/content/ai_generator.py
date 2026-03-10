"""نظام توليد المحتوى بالذكاء الاصطناعي."""

import json
import logging
import random

import httpx

from src.config import (
    AI_MODEL,
    AI_PROVIDER,
    ANTHROPIC_API_KEY,
    OPENAI_API_KEY,
)
from src.utils import get_hashtags, load_json

logger = logging.getLogger(__name__)

# قوالب البرومبت لكل نوع محتوى
PROMPTS = {
    "product_review": {
        "ar": """اكتب مراجعة قصيرة وجذابة لهذا المنتج على أمازون بالعربية.
المنتج: {name}
السعر: {price} {currency}
التقييم: {rating}/5 ({review_count} تقييم)
المميزات: {features}
{discount_text}

اكتب منشور سوشيال ميديا (أقل من 250 حرف) يشجع الناس على الشراء. اذكر رابط الشراء: {affiliate_link}
لا تستخدم إيموجي أكثر من 3. اجعله طبيعي وليس إعلاني بشكل مبالغ.""",
        "en": """Write a short engaging product review for this Amazon product.
Product: {name}
Price: {price} {currency}
Rating: {rating}/5 ({review_count} reviews)
Features: {features}
{discount_text}

Write a social media post (under 250 chars) that encourages purchase. Include link: {affiliate_link}
Use max 3 emojis. Keep it natural, not overly promotional.""",
    },
    "deal_alert": {
        "ar": """اكتب تنبيه عرض قصير وعاجل لهذا المنتج بالعربية.
المنتج: {name}
السعر: {price} {currency}
الخصم: {discount}%
الرابط: {affiliate_link}

اكتب منشور قصير (أقل من 200 حرف) يخلق إحساس بالعجلة. استخدم كلمات مثل: عرض محدود، لا تفوت، خصم حصري.""",
        "en": """Write a short urgent deal alert for this product.
Product: {name}
Price: {price} {currency}
Discount: {discount}%
Link: {affiliate_link}

Write a short post (under 200 chars) creating urgency. Use words like: limited deal, don't miss, exclusive discount.""",
    },
    "recommendation": {
        "ar": """اكتب توصية شخصية لهذا المنتج بالعربية كأنك تنصح صديقك.
المنتج: {name}
التقييم: {rating}/5
المميزات: {features}
الرابط: {affiliate_link}

اكتب منشور قصير (أقل من 250 حرف) بأسلوب شخصي وصادق.""",
        "en": """Write a personal recommendation for this product as if advising a friend.
Product: {name}
Rating: {rating}/5
Features: {features}
Link: {affiliate_link}

Write a short post (under 250 chars) in a personal, honest tone.""",
    },
}


def generate_content(product: dict, language: str = "ar",
                     content_types: list[str] | None = None) -> list[dict]:
    """توليد محتوى لمنتج باستخدام الذكاء الاصطناعي."""
    if content_types is None:
        content_types = ["product_review", "deal_alert", "recommendation"]

    posts = []
    for content_type in content_types:
        try:
            content = _generate_single(product, language, content_type)
            if content:
                hashtags = get_hashtags(language, count=5)
                posts.append({
                    "content": content,
                    "content_type": content_type,
                    "hashtags": hashtags,
                    "language": language,
                    "product_asin": product.get("asin", ""),
                    "image_url": product.get("image_url", ""),
                })
            else:
                # fallback للقوالب الثابتة عند عدم توفر AI
                fallback = _generate_fallback(product, language, content_type)
                if fallback:
                    posts.append(fallback)
        except Exception as e:
            logger.error(f"خطأ في توليد محتوى {content_type}: {e}")
            fallback = _generate_fallback(product, language, content_type)
            if fallback:
                posts.append(fallback)
    return posts


def _generate_single(product: dict, language: str, content_type: str) -> str:
    """توليد محتوى واحد باستخدام AI API."""
    prompt_template = PROMPTS.get(content_type, {}).get(language)
    if not prompt_template:
        return ""

    discount_text = ""
    if product.get("discount"):
        discount_text = f"خصم: {product['discount']}%" if language == "ar" else f"Discount: {product['discount']}%"

    prompt = prompt_template.format(
        name=product.get("name", ""),
        price=product.get("price", 0),
        currency=product.get("currency", "USD"),
        rating=product.get("rating", 0),
        review_count=product.get("review_count", 0),
        features=", ".join(product.get("features", [])[:5]),
        discount=product.get("discount", 0),
        discount_text=discount_text,
        affiliate_link=product.get("affiliate_link", ""),
    )

    if AI_PROVIDER == "openai" and OPENAI_API_KEY:
        return _call_openai(prompt)
    elif AI_PROVIDER == "anthropic" and ANTHROPIC_API_KEY:
        return _call_anthropic(prompt)
    else:
        logger.warning("لا يوجد مفتاح AI API - استخدام القوالب الثابتة")
        return ""


def _call_openai(prompt: str) -> str:
    """استدعاء OpenAI API."""
    try:
        response = httpx.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": AI_MODEL,
                "messages": [
                    {
                        "role": "system",
                        "content": "أنت خبير تسويق بالعمولة. اكتب منشورات قصيرة وجذابة للسوشيال ميديا.",
                    },
                    {"role": "user", "content": prompt},
                ],
                "max_tokens": 300,
                "temperature": 0.8,
            },
            timeout=30.0,
        )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"].strip()
    except Exception as e:
        logger.error(f"خطأ OpenAI: {e}")
        return ""


def _call_anthropic(prompt: str) -> str:
    """استدعاء Anthropic API."""
    try:
        response = httpx.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": ANTHROPIC_API_KEY,
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json",
            },
            json={
                "model": "claude-sonnet-4-20250514",
                "max_tokens": 300,
                "system": "أنت خبير تسويق بالعمولة. اكتب منشورات قصيرة وجذابة للسوشيال ميديا.",
                "messages": [{"role": "user", "content": prompt}],
            },
            timeout=30.0,
        )
        response.raise_for_status()
        data = response.json()
        return data["content"][0]["text"].strip()
    except Exception as e:
        logger.error(f"خطأ Anthropic: {e}")
        return ""


def _generate_fallback(product: dict, language: str,
                       content_type: str) -> dict | None:
    """توليد محتوى بديل من القوالب الثابتة عند عدم توفر AI."""
    try:
        data = load_json("templates.json")
        templates = data.get("scenarios", {}).get(language, {})
        template = templates.get(content_type)
        if not template:
            return None

        content = template.format(
            product_name=product.get("name", ""),
            description=product.get("description", ""),
            affiliate_link=product.get("affiliate_link", ""),
            category=product.get("category", ""),
            discount=product.get("discount", 0),
            use_case=product.get("use_case", ""),
        )

        hashtags = get_hashtags(language, count=5)
        return {
            "content": content,
            "content_type": content_type,
            "hashtags": hashtags,
            "language": language,
            "product_asin": product.get("asin", ""),
            "image_url": product.get("image_url", ""),
        }
    except Exception as e:
        logger.error(f"خطأ في القالب البديل: {e}")
        return None

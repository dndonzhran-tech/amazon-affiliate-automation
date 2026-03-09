"""Utility functions for Amazon affiliate automation."""

import json
import logging
import os
import random
import time
from pathlib import Path

import requests

from models import GeneratedContent, Product, PostResult

logger = logging.getLogger(__name__)

CONFIG_DIR = Path(__file__).parent.parent / "config"


def load_config(filename: str) -> dict:
    """Load a JSON configuration file."""
    config_path = CONFIG_DIR / filename
    with open(config_path) as f:
        return json.load(f)


def get_hashtags(language: str = "en") -> list[str]:
    """Get hashtags for the specified language."""
    config = load_config("hashtags.json")
    return config.get("hashtags", {}).get(language, [])


def get_template(language: str = "en") -> str:
    """Get a random scenario template for the specified language."""
    config = load_config("templates.json")
    scenarios = config.get("scenarios", {}).get(language, {})
    if not scenarios:
        return "{product_name} - {affiliate_link}"
    return random.choice(list(scenarios.values()))


def fetch_trending_products(
    api_key: str,
    api_host: str,
    category: str = "electronics",
    country: str = "US",
) -> list[Product]:
    """Fetch trending/deal products from Amazon via RapidAPI."""
    url = f"https://{api_host}/deals"
    headers = {
        "X-RapidAPI-Key": api_key,
        "X-RapidAPI-Host": api_host,
    }
    params = {"country": country, "category": category}

    try:
        response = requests.get(url, headers=headers, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        products = []
        for item in data.get("deals", data.get("products", [])):
            products.append(Product.from_api_response(item))
        return products
    except requests.RequestException as e:
        logger.error("Failed to fetch products: %s", e)
        return []


def build_affiliate_link(asin: str, affiliate_tag: str) -> str:
    """Build an Amazon affiliate link from an ASIN."""
    return f"https://www.amazon.com/dp/{asin}?tag={affiliate_tag}"


def generate_content_with_ai(
    product: Product,
    groq_api_key: str,
    language: str = "en",
    model: str = "llama-3.3-70b-versatile",
) -> GeneratedContent:
    """Use Groq AI to generate marketing content for a product."""
    template = get_template(language)
    hashtags = get_hashtags(language)

    lang_name = "English" if language == "en" else "Arabic"

    system_prompt = (
        f"You are a world-class affiliate marketing copywriter with 20 years of experience. "
        f"You specialize in writing high-converting social media posts that drive clicks and sales. "
        f"Your copy follows proven direct-response marketing principles: attention-grabbing hooks, "
        f"clear value propositions, social proof, urgency, and strong calls-to-action. "
        f"You write exclusively in {lang_name}. "
        f"Rules:\n"
        f"- Never use misleading claims or fake discounts\n"
        f"- Focus on genuine product benefits and value\n"
        f"- Use power words that trigger emotion and action\n"
        f"- Keep posts concise and scannable for mobile readers\n"
        f"- Include a natural call-to-action that drives clicks"
    )

    prompt = (
        f"Write a high-converting promotional post in {lang_name} for this Amazon product.\n\n"
        f"Product: {product.title}\n"
        f"Price: {product.price} {product.currency or ''}\n"
        f"Rating: {product.rating or 'N/A'}/5\n"
        f"Link: {product.affiliate_link}\n\n"
        f"Template style for inspiration (adapt creatively, don't copy exactly): {template}\n\n"
        f"Requirements:\n"
        f"- Maximum 280 characters (excluding hashtags and link)\n"
        f"- Start with an attention-grabbing hook (emoji + power words)\n"
        f"- Highlight the key benefit or value proposition\n"
        f"- Include social proof if rating is available (e.g., 'rated 4.5/5')\n"
        f"- End with a clear call-to-action pointing to the link\n"
        f"- Tone: enthusiastic, trustworthy, conversational\n"
        f"- Output ONLY the post text, nothing else"
    )

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {groq_api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ],
        "max_tokens": 400,
        "temperature": 0.8,
        "top_p": 0.9,
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        result = response.json()
        text = result["choices"][0]["message"]["content"].strip()
    except (requests.RequestException, KeyError) as e:
        logger.error("AI content generation failed: %s", e)
        text = template.format(
            product_name=product.title,
            affiliate_link=product.affiliate_link or "",
        )

    selected_hashtags = random.sample(hashtags, min(5, len(hashtags)))
    return GeneratedContent(
        product=product,
        text=text,
        hashtags=selected_hashtags,
        language=language,
    )


def post_to_platform(
    content: GeneratedContent,
    platform_api_url: str,
    api_token: str,
) -> PostResult:
    """Post generated content to a social media platform via API."""
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json",
    }
    payload = {
        "message": content.full_post,
        "link": content.product.affiliate_link,
    }

    try:
        response = requests.post(
            platform_api_url, headers=headers, json=payload, timeout=30
        )
        response.raise_for_status()
        result = response.json()
        return PostResult(
            platform=platform_api_url,
            success=True,
            post_id=result.get("id", result.get("post_id")),
        )
    except requests.RequestException as e:
        logger.error("Failed to post to %s: %s", platform_api_url, e)
        return PostResult(platform=platform_api_url, success=False, error=str(e))


def send_notification(
    message: str,
    webhook_url: str,
) -> bool:
    """Send a notification via webhook (Slack, Telegram, etc.)."""
    payload = {"text": message, "message": message}
    try:
        response = requests.post(webhook_url, json=payload, timeout=15)
        response.raise_for_status()
        return True
    except requests.RequestException as e:
        logger.error("Failed to send notification: %s", e)
        return False


def rate_limit_wait(min_seconds: float = 2.0, max_seconds: float = 5.0):
    """Wait a random interval to respect rate limits."""
    wait_time = random.uniform(min_seconds, max_seconds)
    logger.debug("Rate limiting: waiting %.1f seconds", wait_time)
    time.sleep(wait_time)

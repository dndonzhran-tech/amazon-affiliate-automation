"""Utility functions for Amazon Affiliate Automation."""

import json
import os
import random
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

CONFIG_DIR = Path(__file__).parent.parent / "config"


def load_json_config(filename: str) -> dict:
    """Load a JSON configuration file from the config directory."""
    filepath = CONFIG_DIR / filename
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def get_hashtags(language: str = "en", count: int = 5) -> list[str]:
    """Get random hashtags for the specified language."""
    config = load_json_config("hashtags.json")
    hashtags = config.get("hashtags", {}).get(language, [])
    if not hashtags:
        return []
    return random.sample(hashtags, min(count, len(hashtags)))


def get_template(language: str = "en", scenario: str = "product_review") -> str:
    """Get a post template for the specified language and scenario."""
    config = load_json_config("templates.json")
    templates = config.get("scenarios", {}).get(language, {})
    return templates.get(scenario, "")


def format_template(template: str, **kwargs) -> str:
    """Format a template string with the provided values."""
    try:
        return template.format(**kwargs)
    except KeyError:
        return template


def get_env_var(key: str, default: str = "") -> str:
    """Get an environment variable with a default value."""
    return os.getenv(key, default)


def build_affiliate_url(product_url: str, affiliate_tag: str) -> str:
    """Build an affiliate URL by appending the affiliate tag."""
    if not affiliate_tag:
        return product_url
    separator = "&" if "?" in product_url else "?"
    return f"{product_url}{separator}tag={affiliate_tag}"


def generate_post_content(
    product_name: str,
    description: str,
    link: str,
    category: str = "",
    discount: float = 0,
    language: str = "en",
    scenario: str = "product_review",
) -> str:
    """Generate post content from a template."""
    template = get_template(language, scenario)
    if not template:
        return ""
    return format_template(
        template,
        product_name=product_name,
        description=description,
        link=link,
        category=category,
        discount=discount,
    )

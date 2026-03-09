"""أدوات مساعدة لأتمتة التسويق بالعمولة على أمازون."""

import json
import os
import random
from pathlib import Path

CONFIG_DIR = Path(__file__).resolve().parent.parent / "config"


def load_json(filename: str) -> dict:
    """تحميل ملف JSON من مجلد الإعدادات."""
    filepath = CONFIG_DIR / filename
    with open(filepath, encoding="utf-8") as f:
        return json.load(f)


def get_hashtags(language: str = "ar", count: int = 5) -> list[str]:
    """الحصول على هاشتاقات عشوائية حسب اللغة."""
    data = load_json("hashtags.json")
    tags = data.get("hashtags", {}).get(language, [])
    if not tags:
        return []
    return random.sample(tags, min(count, len(tags)))


def get_template(scenario: str, language: str = "ar") -> str:
    """الحصول على قالب سيناريو حسب اللغة."""
    data = load_json("templates.json")
    templates = data.get("scenarios", {}).get(language, {})
    return templates.get(scenario, "")


def format_post(template: str, **kwargs) -> str:
    """تنسيق المنشور باستخدام القالب والمتغيرات."""
    try:
        return template.format(**kwargs)
    except KeyError as e:
        raise ValueError(f"متغير مفقود في القالب: {e}") from e


def build_affiliate_link(base_url: str, tag: str) -> str:
    """بناء رابط الأفلييت بإضافة تاق التتبع."""
    separator = "&" if "?" in base_url else "?"
    return f"{base_url}{separator}tag={tag}"

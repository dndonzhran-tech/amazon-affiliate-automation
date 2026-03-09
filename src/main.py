"""التطبيق الرئيسي لأتمتة التسويق بالعمولة على أمازون."""

import argparse
import os
import sys

from dotenv import load_dotenv

from src.models import Post, Product
from src.utils import (
    build_affiliate_link,
    format_post,
    get_hashtags,
    get_template,
)

load_dotenv()


def create_post(product: Product, scenario: str = "product_review",
                language: str = "ar", hashtag_count: int = 5) -> Post:
    """إنشاء منشور من منتج وسيناريو محدد."""
    template = get_template(scenario, language)
    if not template:
        raise ValueError(
            f"السيناريو '{scenario}' غير موجود للغة '{language}'"
        )

    content = format_post(
        template,
        product_name=product.name,
        description=product.description,
        affiliate_link=product.affiliate_link,
        category=product.category,
        discount=product.discount or 0,
        use_case=product.use_case,
    )

    hashtags = get_hashtags(language, hashtag_count)

    return Post(
        content=content,
        hashtags=hashtags,
        language=language,
        scenario=scenario,
    )


def generate_posts(product: Product, language: str = "ar") -> list[Post]:
    """توليد منشورات لجميع السيناريوهات المتاحة."""
    scenarios = ["product_review", "deal_alert", "comparison", "recommendation"]
    posts = []
    for scenario in scenarios:
        try:
            post = create_post(product, scenario=scenario, language=language)
            posts.append(post)
        except ValueError:
            continue
    return posts


def main():
    """نقطة الدخول الرئيسية للتطبيق."""
    parser = argparse.ArgumentParser(
        description="أتمتة التسويق بالعمولة على أمازون"
    )
    parser.add_argument("--name", required=True, help="اسم المنتج")
    parser.add_argument("--url", required=True, help="رابط المنتج على أمازون")
    parser.add_argument("--description", default="", help="وصف المنتج")
    parser.add_argument("--category", default="", help="فئة المنتج")
    parser.add_argument("--discount", type=int, default=None, help="نسبة الخصم")
    parser.add_argument("--use-case", default="", help="حالة الاستخدام")
    parser.add_argument(
        "--lang", default="ar", choices=["ar", "en"], help="اللغة"
    )
    parser.add_argument(
        "--scenario",
        default=None,
        choices=["product_review", "deal_alert", "comparison", "recommendation"],
        help="نوع السيناريو (اتركه فارغ لتوليد الكل)",
    )

    args = parser.parse_args()

    affiliate_tag = os.getenv("API_KEY", "affiliate-tag-20")
    affiliate_link = build_affiliate_link(args.url, affiliate_tag)

    product = Product(
        name=args.name,
        affiliate_link=affiliate_link,
        category=args.category,
        description=args.description,
        discount=args.discount,
        use_case=args.use_case,
    )

    if args.scenario:
        post = create_post(product, scenario=args.scenario, language=args.lang)
        print(post.full_text())
    else:
        posts = generate_posts(product, language=args.lang)
        for i, post in enumerate(posts, 1):
            print(f"--- منشور {i} ---")
            print(post.full_text())
            print()


if __name__ == "__main__":
    main()

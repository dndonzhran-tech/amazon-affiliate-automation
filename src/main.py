"""Main application for Amazon Affiliate Automation."""

import argparse
import json
import sys

from src.models import Campaign, Post, Product
from src.utils import (
    build_affiliate_url,
    generate_post_content,
    get_env_var,
    get_hashtags,
)


def create_product(
    name: str,
    url: str,
    price: float,
    category: str,
    description: str = "",
    discount: float = None,
) -> Product:
    """Create a product with affiliate URL."""
    affiliate_tag = get_env_var("AFFILIATE_TAG")
    return Product(
        name=name,
        url=url,
        price=price,
        category=category,
        description=description,
        discount=discount,
        affiliate_tag=affiliate_tag,
    )


def generate_post(
    product: Product,
    language: str = "en",
    scenario: str = "product_review",
    hashtag_count: int = 5,
) -> Post:
    """Generate a social media post for a product."""
    content = generate_post_content(
        product_name=product.name,
        description=product.description,
        link=product.affiliate_url,
        category=product.category,
        discount=product.discount or 0,
        language=language,
        scenario=scenario,
    )
    hashtags = get_hashtags(language, hashtag_count)
    return Post(content=content, product=product, hashtags=hashtags, language=language)


def create_campaign(
    name: str,
    products: list[Product],
    language: str = "en",
    scenario: str = "product_review",
) -> Campaign:
    """Create a campaign with posts for multiple products."""
    campaign = Campaign(name=name, language=language)
    for product in products:
        post = generate_post(product, language=language, scenario=scenario)
        campaign.add_post(post)
    return campaign


def load_products_from_json(filepath: str) -> list[Product]:
    """Load products from a JSON file."""
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    products = []
    affiliate_tag = get_env_var("AFFILIATE_TAG")
    for item in data.get("products", []):
        product = Product(
            name=item["name"],
            url=item["url"],
            price=item["price"],
            category=item.get("category", ""),
            description=item.get("description", ""),
            discount=item.get("discount"),
            affiliate_tag=affiliate_tag,
        )
        products.append(product)
    return products


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Amazon Affiliate Automation")
    parser.add_argument(
        "--products", type=str, help="Path to products JSON file"
    )
    parser.add_argument(
        "--language", type=str, default="en", choices=["en", "ar"],
        help="Language for generated content (default: en)"
    )
    parser.add_argument(
        "--scenario", type=str, default="product_review",
        choices=["product_review", "deal_alert", "comparison", "recommendation"],
        help="Post scenario template (default: product_review)"
    )
    parser.add_argument(
        "--campaign", type=str, default="My Campaign",
        help="Campaign name"
    )
    parser.add_argument(
        "--output", type=str, help="Output file path for generated posts"
    )
    args = parser.parse_args()

    if not args.products:
        print("Error: --products argument is required")
        print("Usage: python -m src.main --products products.json")
        sys.exit(1)

    products = load_products_from_json(args.products)
    if not products:
        print("No products found in the input file.")
        sys.exit(1)

    campaign = create_campaign(
        name=args.campaign,
        products=products,
        language=args.language,
        scenario=args.scenario,
    )

    print(f"Campaign: {campaign.name}")
    print(f"Language: {campaign.language}")
    print(f"Posts generated: {campaign.post_count}")
    print("-" * 50)

    output_data = []
    for i, post in enumerate(campaign.posts, 1):
        print(f"\n--- Post {i} ---")
        print(post.full_text)
        print()
        output_data.append({
            "post_number": i,
            "content": post.full_text,
            "product": post.product.to_dict(),
            "language": post.language,
        })

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        print(f"\nPosts saved to {args.output}")


if __name__ == "__main__":
    main()

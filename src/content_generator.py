"""Content generator for creating social media posts."""

import logging
import random
from typing import Optional

from src.models import Post, Product
from src.utils import (
    format_template,
    get_hashtags,
    get_template,
    load_json_config,
)

logger = logging.getLogger(__name__)


class ContentGenerator:
    """Generates social media content for products."""

    PLATFORM_LIMITS = {
        "twitter": 280,
        "telegram": 4096,
        "instagram": 2200,
    }

    EMOJI_SETS = {
        "product_review": ["⭐", "✨", "🔥", "💯", "👌", "🎯"],
        "deal_alert": ["🚨", "💰", "🔥", "⚡", "💥", "🏷️"],
        "comparison": ["🔍", "📊", "✅", "🏆", "💡", "📋"],
        "recommendation": ["👍", "💎", "🌟", "❤️", "🎁", "✨"],
    }

    def __init__(self, language: str = "en"):
        self.language = language

    def generate_post(
        self,
        product: Product,
        platform: str = "twitter",
        scenario: str = "product_review",
        hashtag_count: int = 5,
        include_emoji: bool = True,
        include_price: bool = True,
    ) -> Post:
        """Generate a complete social media post for a product."""
        template = get_template(self.language, scenario)
        if not template:
            content = self._generate_fallback(product, scenario)
        else:
            content = format_template(
                template,
                product_name=product.name,
                description=product.description or product.name,
                link=product.affiliate_url,
                category=product.category,
                discount=product.discount or 0,
            )

        if include_price and product.price > 0:
            content = self._add_price_info(content, product)

        if include_emoji:
            content = self._add_emojis(content, scenario)

        hashtags = get_hashtags(self.language, hashtag_count)
        category_hashtag = f"#{product.category.replace(' ', '')}" if product.category else ""
        if category_hashtag and category_hashtag not in hashtags:
            hashtags.append(category_hashtag)

        post = Post(
            content=content,
            product=product,
            hashtags=hashtags,
            language=self.language,
            platform=platform,
            scenario=scenario,
        )

        max_length = self.PLATFORM_LIMITS.get(platform, 4096)
        if len(post.full_text) > max_length:
            post = self._trim_post(post, max_length)

        return post

    def generate_multi_platform(
        self,
        product: Product,
        platforms: list[str] = None,
        scenario: str = "product_review",
    ) -> dict[str, Post]:
        """Generate posts optimized for multiple platforms."""
        if platforms is None:
            platforms = ["twitter", "telegram"]

        posts = {}
        for platform in platforms:
            posts[platform] = self.generate_post(
                product=product,
                platform=platform,
                scenario=scenario,
                hashtag_count=5 if platform == "twitter" else 8,
                include_price=True,
            )
        return posts

    def generate_batch(
        self,
        products: list[Product],
        platform: str = "twitter",
        scenario: str = "product_review",
    ) -> list[Post]:
        """Generate posts for multiple products."""
        posts = []
        scenarios = ["product_review", "deal_alert", "comparison", "recommendation"]

        for i, product in enumerate(products):
            current_scenario = scenario if scenario != "rotate" else scenarios[i % len(scenarios)]

            if current_scenario == "deal_alert" and not product.discount:
                current_scenario = "product_review"

            post = self.generate_post(
                product=product,
                platform=platform,
                scenario=current_scenario,
            )
            posts.append(post)

        return posts

    def _generate_fallback(self, product: Product, scenario: str) -> str:
        """Generate fallback content when no template is available."""
        if self.language == "ar":
            return self._fallback_ar(product, scenario)
        return self._fallback_en(product, scenario)

    def _fallback_en(self, product: Product, scenario: str) -> str:
        templates = {
            "product_review": f"Check out {product.name}! {product.description}. {product.affiliate_url}",
            "deal_alert": f"DEAL! {product.name} - {product.discount or 0}% OFF! {product.affiliate_url}",
            "comparison": f"Why {product.name} is the best in {product.category}: {product.description}. {product.affiliate_url}",
            "recommendation": f"I recommend {product.name} for {product.category}. {product.affiliate_url}",
        }
        return templates.get(scenario, templates["product_review"])

    def _fallback_ar(self, product: Product, scenario: str) -> str:
        templates = {
            "product_review": f"اكتشف {product.name}! {product.description}. {product.affiliate_url}",
            "deal_alert": f"عرض! {product.name} - خصم {product.discount or 0}%! {product.affiliate_url}",
            "comparison": f"لماذا {product.name} الأفضل في {product.category}: {product.description}. {product.affiliate_url}",
            "recommendation": f"أنصح بـ {product.name} لـ {product.category}. {product.affiliate_url}",
        }
        return templates.get(scenario, templates["product_review"])

    def _add_price_info(self, content: str, product: Product) -> str:
        """Add price information to the content."""
        if self.language == "ar":
            price_text = f"\n💰 السعر: ${product.price:.2f}"
            if product.discount:
                price_text += f" (خصم {product.discount:.0f}%)"
        else:
            price_text = f"\n💰 Price: ${product.price:.2f}"
            if product.discount:
                price_text += f" ({product.discount:.0f}% OFF)"
        return content + price_text

    def _add_emojis(self, content: str, scenario: str) -> str:
        """Add relevant emojis to the content."""
        emojis = self.EMOJI_SETS.get(scenario, ["✨"])
        emoji = random.choice(emojis)
        return f"{emoji} {content}"

    def _trim_post(self, post: Post, max_length: int) -> Post:
        """Trim post to fit platform character limit."""
        hashtag_text = " ".join(post.hashtags)
        available = max_length - len(hashtag_text) - 2  # 2 for newlines

        if len(post.content) > available:
            post.content = post.content[: available - 3] + "..."

        return post

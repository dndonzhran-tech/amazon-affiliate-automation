"""Data models for Amazon Affiliate Automation."""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Product:
    """Represents an Amazon product."""

    name: str
    url: str
    price: float
    category: str
    description: str = ""
    discount: Optional[float] = None
    affiliate_tag: str = ""

    @property
    def affiliate_url(self) -> str:
        """Generate the affiliate URL with tag."""
        separator = "&" if "?" in self.url else "?"
        return f"{self.url}{separator}tag={self.affiliate_tag}" if self.affiliate_tag else self.url

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "url": self.url,
            "price": self.price,
            "category": self.category,
            "description": self.description,
            "discount": self.discount,
            "affiliate_url": self.affiliate_url,
        }


@dataclass
class Post:
    """Represents a generated social media post."""

    content: str
    product: Product
    hashtags: list[str] = field(default_factory=list)
    language: str = "en"

    @property
    def full_text(self) -> str:
        """Get the complete post text with hashtags."""
        hashtag_text = " ".join(self.hashtags)
        return f"{self.content}\n\n{hashtag_text}" if self.hashtags else self.content


@dataclass
class Campaign:
    """Represents a marketing campaign with multiple posts."""

    name: str
    posts: list[Post] = field(default_factory=list)
    language: str = "en"

    def add_post(self, post: Post) -> None:
        self.posts.append(post)

    @property
    def post_count(self) -> int:
        return len(self.posts)

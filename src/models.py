"""نماذج البيانات الشاملة للمشروع."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class PostStatus(Enum):
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    PUBLISHED = "published"
    FAILED = "failed"


class Platform(Enum):
    TWITTER = "twitter"
    INSTAGRAM = "instagram"
    TELEGRAM = "telegram"
    ALL = "all"


class ContentType(Enum):
    PRODUCT_REVIEW = "product_review"
    DEAL_ALERT = "deal_alert"
    COMPARISON = "comparison"
    RECOMMENDATION = "recommendation"
    TOP_LIST = "top_list"
    SEASONAL = "seasonal"


@dataclass
class Product:
    """نموذج بيانات المنتج من أمازون."""

    asin: str
    name: str
    price: float
    currency: str = "USD"
    category: str = ""
    description: str = ""
    image_url: str = ""
    affiliate_link: str = ""
    rating: float = 0.0
    review_count: int = 0
    discount: Optional[int] = None
    features: list[str] = field(default_factory=list)
    use_case: str = ""
    fetched_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class Post:
    """نموذج بيانات المنشور."""

    content: str
    product_asin: str = ""
    hashtags: list[str] = field(default_factory=list)
    language: str = "ar"
    content_type: str = "product_review"
    platform: str = "all"
    status: str = "draft"
    image_url: str = ""
    scheduled_at: Optional[str] = None
    published_at: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    engagement: dict = field(default_factory=dict)

    def full_text(self) -> str:
        """إرجاع النص الكامل للمنشور مع الهاشتاقات."""
        tags = " ".join(self.hashtags)
        if tags:
            return f"{self.content}\n\n{tags}"
        return self.content

    def truncate_for_twitter(self) -> str:
        """اقتطاع المنشور ليناسب تويتر (280 حرف)."""
        full = self.full_text()
        if len(full) <= 280:
            return full
        tags = " ".join(self.hashtags)
        max_content = 280 - len(tags) - 5  # مساحة لـ "...\n\n"
        return f"{self.content[:max_content]}...\n\n{tags}"


@dataclass
class Campaign:
    """نموذج بيانات الحملة التسويقية."""

    name: str
    products: list[Product] = field(default_factory=list)
    platforms: list[str] = field(default_factory=lambda: ["all"])
    language: str = "ar"
    content_types: list[str] = field(
        default_factory=lambda: ["product_review", "deal_alert"]
    )
    posts_per_day: int = 4
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    status: str = "active"
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class AnalyticsEvent:
    """نموذج بيانات حدث التحليلات."""

    event_type: str  # click, impression, conversion
    product_asin: str = ""
    platform: str = ""
    post_id: str = ""
    revenue: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: dict = field(default_factory=dict)

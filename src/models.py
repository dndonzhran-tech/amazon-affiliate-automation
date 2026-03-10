"""Data models for Amazon Affiliate Automation."""

import datetime
from dataclasses import dataclass, field
from typing import Optional

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    Integer,
    String,
    Text,
    create_engine,
)
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


class Base(DeclarativeBase):
    pass


class ProductDB(Base):
    """SQLAlchemy model for products stored in database."""

    __tablename__ = "products"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(500), nullable=False)
    url = Column(String(2000), nullable=False)
    price = Column(Float, nullable=False)
    category = Column(String(200), default="")
    description = Column(Text, default="")
    discount = Column(Float, nullable=True)
    image_url = Column(String(2000), default="")
    asin = Column(String(20), unique=True, nullable=True)
    rating = Column(Float, nullable=True)
    review_count = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)


class PostDB(Base):
    """SQLAlchemy model for generated posts."""

    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    product_asin = Column(String(20), nullable=True)
    content = Column(Text, nullable=False)
    platform = Column(String(50), nullable=False)
    language = Column(String(10), default="en")
    scenario = Column(String(50), default="product_review")
    posted = Column(Boolean, default=False)
    posted_at = Column(DateTime, nullable=True)
    scheduled_at = Column(DateTime, nullable=True)
    engagement = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class ScheduleDB(Base):
    """SQLAlchemy model for scheduled tasks."""

    __tablename__ = "schedules"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False)
    cron_expression = Column(String(100), nullable=True)
    interval_minutes = Column(Integer, nullable=True)
    platform = Column(String(50), nullable=False)
    language = Column(String(10), default="en")
    scenario = Column(String(50), default="product_review")
    category = Column(String(200), default="")
    is_active = Column(Boolean, default=True)
    last_run = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


_engines: dict[str, object] = {}


def get_engine(db_url: str = "sqlite:///affiliate.db"):
    """Create or get cached database engine."""
    if db_url not in _engines:
        _engines[db_url] = create_engine(db_url, echo=False)
    return _engines[db_url]


def get_session(db_url: str = "sqlite:///affiliate.db") -> Session:
    """Create a new database session."""
    engine = get_engine(db_url)
    SessionLocal = sessionmaker(bind=engine)
    return SessionLocal()


def init_db(db_url: str = "sqlite:///affiliate.db"):
    """Initialize database tables."""
    engine = get_engine(db_url)
    Base.metadata.create_all(engine)


# --- Dataclass models for in-memory use ---


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
    image_url: str = ""
    asin: str = ""
    rating: Optional[float] = None
    review_count: int = 0

    @property
    def affiliate_url(self) -> str:
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
            "image_url": self.image_url,
            "asin": self.asin,
            "rating": self.rating,
            "review_count": self.review_count,
        }

    def to_db(self) -> ProductDB:
        return ProductDB(
            name=self.name,
            url=self.url,
            price=self.price,
            category=self.category,
            description=self.description,
            discount=self.discount,
            image_url=self.image_url,
            asin=self.asin,
            rating=self.rating,
            review_count=self.review_count,
        )


@dataclass
class Post:
    """Represents a generated social media post."""

    content: str
    product: Product
    hashtags: list[str] = field(default_factory=list)
    language: str = "en"
    platform: str = "twitter"
    scenario: str = "product_review"

    @property
    def full_text(self) -> str:
        hashtag_text = " ".join(self.hashtags)
        return f"{self.content}\n\n{hashtag_text}" if self.hashtags else self.content

    def to_db(self) -> PostDB:
        return PostDB(
            product_asin=self.product.asin,
            content=self.full_text,
            platform=self.platform,
            language=self.language,
            scenario=self.scenario,
        )


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

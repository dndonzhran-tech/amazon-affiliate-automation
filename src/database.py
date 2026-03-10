"""Database operations for product and post management."""

import datetime
import logging
from typing import Optional

from src.models import (
    Post,
    PostDB,
    Product,
    ProductDB,
    get_session,
    init_db,
)

logger = logging.getLogger(__name__)


class Database:
    """Handles all database operations."""

    def __init__(self, db_url: str = "sqlite:///affiliate.db"):
        self.db_url = db_url
        init_db(db_url)

    def save_product(self, product: Product) -> int:
        """Save a product to the database. Returns product ID."""
        session = get_session(self.db_url)
        try:
            if product.asin:
                existing = session.query(ProductDB).filter_by(asin=product.asin).first()
                if existing:
                    existing.name = product.name
                    existing.price = product.price
                    existing.description = product.description
                    existing.discount = product.discount
                    existing.image_url = product.image_url
                    existing.rating = product.rating
                    existing.review_count = product.review_count
                    existing.updated_at = datetime.datetime.utcnow()
                    session.commit()
                    product_id = existing.id
                    logger.info(f"Product updated: {product.name} (ID: {product_id})")
                    return product_id

            db_product = product.to_db()
            session.add(db_product)
            session.commit()
            product_id = db_product.id
            logger.info(f"Product saved: {product.name} (ID: {product_id})")
            return product_id
        except Exception as e:
            session.rollback()
            logger.error(f"Error saving product: {e}")
            return -1
        finally:
            session.close()

    def save_products(self, products: list[Product]) -> list[int]:
        """Save multiple products. Returns list of IDs."""
        return [self.save_product(p) for p in products]

    def get_product(self, product_id: int) -> Optional[ProductDB]:
        """Get a product by ID."""
        session = get_session(self.db_url)
        product = session.query(ProductDB).get(product_id)
        session.close()
        return product

    def get_product_by_asin(self, asin: str) -> Optional[ProductDB]:
        """Get a product by ASIN."""
        session = get_session(self.db_url)
        product = session.query(ProductDB).filter_by(asin=asin).first()
        session.close()
        return product

    def get_all_products(self, active_only: bool = True) -> list[ProductDB]:
        """Get all products."""
        session = get_session(self.db_url)
        query = session.query(ProductDB)
        if active_only:
            query = query.filter_by(is_active=True)
        products = query.all()
        session.close()
        return products

    def search_products(
        self,
        keyword: str = "",
        category: str = "",
        min_price: float = 0,
        max_price: float = 0,
    ) -> list[ProductDB]:
        """Search products in database."""
        session = get_session(self.db_url)
        query = session.query(ProductDB).filter_by(is_active=True)

        if keyword:
            query = query.filter(ProductDB.name.ilike(f"%{keyword}%"))
        if category:
            query = query.filter(ProductDB.category.ilike(f"%{category}%"))
        if min_price > 0:
            query = query.filter(ProductDB.price >= min_price)
        if max_price > 0:
            query = query.filter(ProductDB.price <= max_price)

        products = query.all()
        session.close()
        return products

    def delete_product(self, product_id: int) -> bool:
        """Soft delete a product."""
        session = get_session(self.db_url)
        product = session.query(ProductDB).get(product_id)
        if product:
            product.is_active = False
            session.commit()
            session.close()
            return True
        session.close()
        return False

    def save_post(self, post: Post, posted: bool = False) -> int:
        """Save a generated post to the database."""
        session = get_session(self.db_url)
        try:
            db_post = post.to_db()
            db_post.posted = posted
            if posted:
                db_post.posted_at = datetime.datetime.utcnow()
            session.add(db_post)
            session.commit()
            post_id = db_post.id
            logger.info(f"Post saved (ID: {post_id})")
            return post_id
        except Exception as e:
            session.rollback()
            logger.error(f"Error saving post: {e}")
            return -1
        finally:
            session.close()

    def get_posts(
        self,
        platform: str = "",
        posted: bool = None,
        limit: int = 50,
    ) -> list[PostDB]:
        """Get posts with optional filters."""
        session = get_session(self.db_url)
        query = session.query(PostDB)

        if platform:
            query = query.filter_by(platform=platform)
        if posted is not None:
            query = query.filter_by(posted=posted)

        posts = query.order_by(PostDB.created_at.desc()).limit(limit).all()
        session.close()
        return posts

    def mark_post_as_posted(self, post_id: int) -> bool:
        """Mark a post as posted."""
        session = get_session(self.db_url)
        post = session.query(PostDB).get(post_id)
        if post:
            post.posted = True
            post.posted_at = datetime.datetime.utcnow()
            session.commit()
            session.close()
            return True
        session.close()
        return False

    def get_stats(self) -> dict:
        """Get database statistics."""
        session = get_session(self.db_url)
        stats = {
            "total_products": session.query(ProductDB).count(),
            "active_products": session.query(ProductDB).filter_by(is_active=True).count(),
            "total_posts": session.query(PostDB).count(),
            "posted_count": session.query(PostDB).filter_by(posted=True).count(),
            "pending_count": session.query(PostDB).filter_by(posted=False).count(),
        }
        session.close()
        return stats

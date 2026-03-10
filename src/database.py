"""قاعدة البيانات - تخزين المنتجات والمنشورات والتحليلات."""

import json
import logging
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta
from pathlib import Path

from src.config import DATA_DIR

logger = logging.getLogger(__name__)

DB_PATH = DATA_DIR / "affiliate.db"


def _ensure_data_dir():
    DATA_DIR.mkdir(parents=True, exist_ok=True)


@contextmanager
def get_db():
    """الحصول على اتصال بقاعدة البيانات."""
    _ensure_data_dir()
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    """إنشاء جداول قاعدة البيانات."""
    _ensure_data_dir()
    with get_db() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS products (
                asin TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                price REAL DEFAULT 0,
                currency TEXT DEFAULT 'USD',
                category TEXT DEFAULT '',
                description TEXT DEFAULT '',
                image_url TEXT DEFAULT '',
                affiliate_link TEXT DEFAULT '',
                rating REAL DEFAULT 0,
                review_count INTEGER DEFAULT 0,
                discount INTEGER,
                features TEXT DEFAULT '[]',
                use_case TEXT DEFAULT '',
                fetched_at TEXT DEFAULT (datetime('now')),
                created_at TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_asin TEXT,
                content TEXT NOT NULL,
                hashtags TEXT DEFAULT '[]',
                language TEXT DEFAULT 'ar',
                content_type TEXT DEFAULT 'product_review',
                platform TEXT DEFAULT 'all',
                status TEXT DEFAULT 'draft',
                image_url TEXT DEFAULT '',
                scheduled_at TEXT,
                published_at TEXT,
                created_at TEXT DEFAULT (datetime('now')),
                twitter_id TEXT,
                telegram_id TEXT,
                instagram_id TEXT,
                FOREIGN KEY (product_asin) REFERENCES products(asin)
            );

            CREATE TABLE IF NOT EXISTS analytics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type TEXT NOT NULL,
                product_asin TEXT DEFAULT '',
                platform TEXT DEFAULT '',
                post_id INTEGER,
                revenue REAL DEFAULT 0,
                metadata TEXT DEFAULT '{}',
                timestamp TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (post_id) REFERENCES posts(id)
            );

            CREATE TABLE IF NOT EXISTS campaigns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                platforms TEXT DEFAULT '["all"]',
                language TEXT DEFAULT 'ar',
                content_types TEXT DEFAULT '["product_review"]',
                posts_per_day INTEGER DEFAULT 4,
                status TEXT DEFAULT 'active',
                start_date TEXT,
                end_date TEXT,
                created_at TEXT DEFAULT (datetime('now'))
            );

            CREATE INDEX IF NOT EXISTS idx_posts_status ON posts(status);
            CREATE INDEX IF NOT EXISTS idx_posts_platform ON posts(platform);
            CREATE INDEX IF NOT EXISTS idx_posts_scheduled ON posts(scheduled_at);
            CREATE INDEX IF NOT EXISTS idx_analytics_type ON analytics(event_type);
            CREATE INDEX IF NOT EXISTS idx_analytics_timestamp ON analytics(timestamp);
        """)
    logger.info("تم تهيئة قاعدة البيانات بنجاح")


# ===== عمليات المنتجات =====

def save_product(product: dict) -> str:
    """حفظ أو تحديث منتج."""
    with get_db() as conn:
        conn.execute("""
            INSERT OR REPLACE INTO products
            (asin, name, price, currency, category, description, image_url,
             affiliate_link, rating, review_count, discount, features, use_case)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            product["asin"],
            product["name"],
            product.get("price", 0),
            product.get("currency", "USD"),
            product.get("category", ""),
            product.get("description", ""),
            product.get("image_url", ""),
            product.get("affiliate_link", ""),
            product.get("rating", 0),
            product.get("review_count", 0),
            product.get("discount"),
            json.dumps(product.get("features", []), ensure_ascii=False),
            product.get("use_case", ""),
        ))
    return product["asin"]


def get_product(asin: str) -> dict | None:
    """جلب منتج بواسطة ASIN."""
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM products WHERE asin = ?", (asin,)
        ).fetchone()
        if row:
            result = dict(row)
            result["features"] = json.loads(result.get("features", "[]"))
            return result
    return None


def get_all_products(limit: int = 50) -> list[dict]:
    """جلب جميع المنتجات."""
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM products ORDER BY created_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
        products = []
        for row in rows:
            p = dict(row)
            p["features"] = json.loads(p.get("features", "[]"))
            products.append(p)
        return products


# ===== عمليات المنشورات =====

def save_post(post: dict) -> int:
    """حفظ منشور جديد."""
    with get_db() as conn:
        cursor = conn.execute("""
            INSERT INTO posts
            (product_asin, content, hashtags, language, content_type, platform,
             status, image_url, scheduled_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            post.get("product_asin", ""),
            post["content"],
            json.dumps(post.get("hashtags", []), ensure_ascii=False),
            post.get("language", "ar"),
            post.get("content_type", "product_review"),
            post.get("platform", "all"),
            post.get("status", "draft"),
            post.get("image_url", ""),
            post.get("scheduled_at"),
        ))
        return cursor.lastrowid


def update_post_status(post_id: int, status: str, **kwargs):
    """تحديث حالة منشور."""
    with get_db() as conn:
        updates = ["status = ?"]
        values = [status]
        if status == "published":
            updates.append("published_at = datetime('now')")
        for key, value in kwargs.items():
            if key in ("twitter_id", "telegram_id", "instagram_id"):
                updates.append(f"{key} = ?")
                values.append(value)
        values.append(post_id)
        conn.execute(
            f"UPDATE posts SET {', '.join(updates)} WHERE id = ?",
            values,
        )


def get_pending_posts(limit: int = 10) -> list[dict]:
    """جلب المنشورات المجدولة الجاهزة للنشر."""
    with get_db() as conn:
        rows = conn.execute("""
            SELECT * FROM posts
            WHERE status IN ('draft', 'scheduled')
            AND (scheduled_at IS NULL OR scheduled_at <= datetime('now'))
            ORDER BY created_at ASC LIMIT ?
        """, (limit,)).fetchall()
        posts = []
        for row in rows:
            p = dict(row)
            p["hashtags"] = json.loads(p.get("hashtags", "[]"))
            posts.append(p)
        return posts


def get_posts_by_status(status: str, limit: int = 50) -> list[dict]:
    """جلب المنشورات حسب الحالة."""
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM posts WHERE status = ? ORDER BY created_at DESC LIMIT ?",
            (status, limit),
        ).fetchall()
        posts = []
        for row in rows:
            p = dict(row)
            p["hashtags"] = json.loads(p.get("hashtags", "[]"))
            posts.append(p)
        return posts


# ===== عمليات التحليلات =====

def log_event(event: dict):
    """تسجيل حدث تحليلات."""
    with get_db() as conn:
        conn.execute("""
            INSERT INTO analytics
            (event_type, product_asin, platform, post_id, revenue, metadata)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            event["event_type"],
            event.get("product_asin", ""),
            event.get("platform", ""),
            event.get("post_id"),
            event.get("revenue", 0),
            json.dumps(event.get("metadata", {}), ensure_ascii=False),
        ))


def get_daily_stats(date: str | None = None) -> dict:
    """جلب إحصائيات يوم محدد."""
    if not date:
        date = datetime.now().strftime("%Y-%m-%d")

    with get_db() as conn:
        posts_today = conn.execute("""
            SELECT COUNT(*) as count FROM posts
            WHERE date(published_at) = ? AND status = 'published'
        """, (date,)).fetchone()["count"]

        impressions = conn.execute("""
            SELECT COUNT(*) as count FROM analytics
            WHERE event_type = 'impression' AND date(timestamp) = ?
        """, (date,)).fetchone()["count"]

        clicks = conn.execute("""
            SELECT COUNT(*) as count FROM analytics
            WHERE event_type = 'click' AND date(timestamp) = ?
        """, (date,)).fetchone()["count"]

        revenue = conn.execute("""
            SELECT COALESCE(SUM(revenue), 0) as total FROM analytics
            WHERE event_type = 'conversion' AND date(timestamp) = ?
        """, (date,)).fetchone()["total"]

        top_product_row = conn.execute("""
            SELECT product_asin, COUNT(*) as cnt FROM analytics
            WHERE date(timestamp) = ? AND product_asin != ''
            GROUP BY product_asin ORDER BY cnt DESC LIMIT 1
        """, (date,)).fetchone()

        top_product = ""
        if top_product_row:
            product = get_product(top_product_row["product_asin"])
            if product:
                top_product = product["name"]

        return {
            "date": date,
            "posts_today": posts_today,
            "impressions": impressions,
            "clicks": clicks,
            "estimated_revenue": round(revenue, 2),
            "top_product": top_product,
        }

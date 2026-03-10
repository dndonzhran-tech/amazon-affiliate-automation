"""نظام تتبع الأداء والتحليلات."""

import logging
from datetime import datetime, timedelta

from src.database import get_daily_stats, get_db, log_event

logger = logging.getLogger(__name__)


def track_click(product_asin: str, platform: str, post_id: int | None = None):
    """تسجيل نقرة على رابط."""
    log_event({
        "event_type": "click",
        "product_asin": product_asin,
        "platform": platform,
        "post_id": post_id,
    })


def track_impression(product_asin: str, platform: str,
                     post_id: int | None = None):
    """تسجيل مشاهدة."""
    log_event({
        "event_type": "impression",
        "product_asin": product_asin,
        "platform": platform,
        "post_id": post_id,
    })


def track_conversion(product_asin: str, revenue: float,
                     platform: str = "", post_id: int | None = None):
    """تسجيل عملية شراء (تحويل)."""
    log_event({
        "event_type": "conversion",
        "product_asin": product_asin,
        "platform": platform,
        "post_id": post_id,
        "revenue": revenue,
    })


def get_weekly_report() -> dict:
    """تقرير أسبوعي."""
    today = datetime.now()
    days = []
    total_clicks = 0
    total_impressions = 0
    total_revenue = 0.0
    total_posts = 0

    for i in range(7):
        date = (today - timedelta(days=i)).strftime("%Y-%m-%d")
        stats = get_daily_stats(date)
        days.append(stats)
        total_clicks += stats["clicks"]
        total_impressions += stats["impressions"]
        total_revenue += stats["estimated_revenue"]
        total_posts += stats["posts_today"]

    return {
        "period": "weekly",
        "start_date": days[-1]["date"],
        "end_date": days[0]["date"],
        "total_posts": total_posts,
        "total_clicks": total_clicks,
        "total_impressions": total_impressions,
        "total_revenue": round(total_revenue, 2),
        "daily_breakdown": list(reversed(days)),
    }


def get_top_products(limit: int = 10) -> list[dict]:
    """أفضل المنتجات أداءً."""
    with get_db() as conn:
        rows = conn.execute("""
            SELECT
                a.product_asin,
                p.name as product_name,
                COUNT(CASE WHEN a.event_type = 'click' THEN 1 END) as clicks,
                COUNT(CASE WHEN a.event_type = 'impression' THEN 1 END) as impressions,
                COUNT(CASE WHEN a.event_type = 'conversion' THEN 1 END) as conversions,
                COALESCE(SUM(CASE WHEN a.event_type = 'conversion' THEN a.revenue END), 0) as revenue
            FROM analytics a
            LEFT JOIN products p ON a.product_asin = p.asin
            WHERE a.product_asin != ''
            GROUP BY a.product_asin
            ORDER BY revenue DESC, clicks DESC
            LIMIT ?
        """, (limit,)).fetchall()

        return [dict(row) for row in rows]


def get_platform_performance() -> dict:
    """أداء كل منصة."""
    with get_db() as conn:
        rows = conn.execute("""
            SELECT
                platform,
                COUNT(CASE WHEN event_type = 'publish' THEN 1 END) as posts,
                COUNT(CASE WHEN event_type = 'click' THEN 1 END) as clicks,
                COUNT(CASE WHEN event_type = 'conversion' THEN 1 END) as conversions,
                COALESCE(SUM(CASE WHEN event_type = 'conversion' THEN revenue END), 0) as revenue
            FROM analytics
            WHERE platform != ''
            GROUP BY platform
        """).fetchall()

        return {row["platform"]: dict(row) for row in rows}

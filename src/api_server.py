"""API Server - الخادم اللي يتكامل مع n8n workflow."""

import logging
import os
import sys

from flask import Flask, jsonify, request

from src.config import LOG_LEVEL
from src.database import (
    get_all_products,
    get_daily_stats,
    get_pending_posts,
    get_product,
    init_db,
    log_event,
    save_post,
    save_product,
    update_post_status,
)

# إعداد اللوقينق
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger(__name__)

app = Flask(__name__)


# ===== تهيئة قاعدة البيانات عند البدء =====
with app.app_context():
    init_db()


# ===== API للمنتجات =====

@app.route("/api/products/search", methods=["POST"])
def api_search_products():
    """البحث عن منتجات أمازون."""
    data = request.get_json(force=True)
    keywords = data.get("keywords", "best sellers")
    category = data.get("category", "All")
    min_rating = data.get("min_rating", 4.0)
    count = data.get("count", 5)

    try:
        from src.amazon.product_api import search_products
        products = search_products(
            keywords=keywords,
            category=category,
            min_rating=min_rating,
            item_count=count,
        )
        # حفظ المنتجات في قاعدة البيانات
        results = []
        for p in products:
            product_dict = {
                "asin": p.asin,
                "name": p.name,
                "price": p.price,
                "currency": p.currency,
                "category": p.category,
                "description": p.description,
                "image_url": p.image_url,
                "affiliate_link": p.affiliate_link,
                "rating": p.rating,
                "review_count": p.review_count,
                "discount": p.discount,
                "features": p.features,
            }
            save_product(product_dict)
            results.append(product_dict)

        return jsonify({"success": True, "products": results})
    except Exception as e:
        logger.error(f"خطأ في البحث: {e}")
        # إرجاع منتجات من قاعدة البيانات كبديل
        cached = get_all_products(limit=count)
        return jsonify({"success": True, "products": cached, "source": "cache"})


@app.route("/api/products/add", methods=["POST"])
def api_add_product():
    """إضافة منتج يدوياً."""
    data = request.get_json(force=True)

    if not data.get("asin") or not data.get("name"):
        return jsonify({"success": False, "error": "ASIN واسم المنتج مطلوبين"}), 400

    asin = save_product(data)
    return jsonify({"success": True, "asin": asin})


@app.route("/api/products", methods=["GET"])
def api_list_products():
    """عرض جميع المنتجات."""
    limit = request.args.get("limit", 50, type=int)
    products = get_all_products(limit=limit)
    return jsonify({"success": True, "products": products})


@app.route("/api/products/<asin>", methods=["GET"])
def api_get_product(asin):
    """جلب منتج محدد."""
    product = get_product(asin)
    if product:
        return jsonify({"success": True, "product": product})
    return jsonify({"success": False, "error": "منتج غير موجود"}), 404


# ===== API لتوليد المحتوى =====

@app.route("/api/content/generate", methods=["POST"])
def api_generate_content():
    """توليد محتوى بالذكاء الاصطناعي."""
    data = request.get_json(force=True)
    product = data.get("product", {})
    language = data.get("language", "ar")
    content_types = data.get("content_types", ["product_review", "deal_alert"])

    try:
        from src.content.ai_generator import generate_content
        posts = generate_content(product, language, content_types)

        # حفظ المنشورات في قاعدة البيانات
        saved_posts = []
        for post in posts:
            post_id = save_post(post)
            post["id"] = post_id
            saved_posts.append(post)

        return jsonify({"success": True, "posts": saved_posts})
    except Exception as e:
        logger.error(f"خطأ في توليد المحتوى: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


# ===== API للنشر =====

@app.route("/api/publish/twitter", methods=["POST"])
def api_publish_twitter():
    """نشر على تويتر."""
    data = request.get_json(force=True)
    text = data.get("text", "")
    hashtags = data.get("hashtags", "")
    image_url = data.get("image_url", "")

    full_text = f"{text}\n\n{hashtags}" if hashtags else text

    from src.social.twitter import post_tweet
    result = post_tweet(full_text, image_url)
    return jsonify(result)


@app.route("/api/publish/telegram", methods=["POST"])
def api_publish_telegram():
    """نشر على تيليجرام."""
    data = request.get_json(force=True)
    text = data.get("text", "")
    hashtags = data.get("hashtags", "")
    image_url = data.get("image_url", "")
    parse_mode = data.get("parse_mode", "HTML")

    full_text = f"{text}\n\n{hashtags}" if hashtags else text

    from src.social.telegram import send_message
    result = send_message(full_text, image_url, parse_mode)
    return jsonify(result)


@app.route("/api/publish/instagram", methods=["POST"])
def api_publish_instagram():
    """نشر على إنستغرام."""
    data = request.get_json(force=True)
    caption = data.get("caption", "")
    image_url = data.get("image_url", "")

    from src.social.instagram import post_image
    result = post_image(caption, image_url)
    return jsonify(result)


@app.route("/api/publish/all", methods=["POST"])
def api_publish_all():
    """نشر على جميع المنصات."""
    data = request.get_json(force=True)
    platforms = data.get("platforms", ["twitter", "telegram", "instagram"])

    from src.social.publisher import publish_post
    result = publish_post(data, platforms)
    return jsonify(result)


# ===== API للتحليلات =====

@app.route("/api/analytics/log", methods=["POST"])
def api_log_analytics():
    """تسجيل حدث تحليلات."""
    data = request.get_json(force=True)

    results = data.get("results", {})
    product = data.get("product", "")
    content_type = data.get("content_type", "")

    for platform, result in results.items():
        log_event({
            "event_type": "publish" if result.get("success") else "publish_failed",
            "product_asin": product,
            "platform": platform,
            "metadata": result,
        })

    return jsonify({"success": True})


@app.route("/api/analytics/daily-report", methods=["GET"])
def api_daily_report():
    """التقرير اليومي."""
    date = request.args.get("date")
    stats = get_daily_stats(date)
    return jsonify(stats)


@app.route("/api/analytics/weekly-report", methods=["GET"])
def api_weekly_report():
    """التقرير الأسبوعي."""
    from src.analytics.tracker import get_weekly_report
    report = get_weekly_report()
    return jsonify(report)


@app.route("/api/analytics/top-products", methods=["GET"])
def api_top_products():
    """أفضل المنتجات أداءً."""
    from src.analytics.tracker import get_top_products
    limit = request.args.get("limit", 10, type=int)
    products = get_top_products(limit)
    return jsonify({"success": True, "products": products})


@app.route("/api/analytics/platforms", methods=["GET"])
def api_platform_performance():
    """أداء المنصات."""
    from src.analytics.tracker import get_platform_performance
    performance = get_platform_performance()
    return jsonify({"success": True, "platforms": performance})


# ===== API للإشعارات =====

@app.route("/api/notify/error", methods=["POST"])
def api_notify_error():
    """إشعار بخطأ."""
    data = request.get_json(force=True)
    message = data.get("message", "خطأ غير معروف")
    logger.error(f"إشعار خطأ من n8n: {message}")

    # إرسال إشعار على تيليجرام
    from src.social.telegram import send_message, is_configured
    if is_configured():
        send_message(f"🚨 تنبيه خطأ:\n{message}")

    return jsonify({"success": True, "logged": True})


# ===== API للحالة =====

@app.route("/api/status", methods=["GET"])
def api_status():
    """حالة النظام."""
    from src.social.publisher import get_platform_status
    return jsonify({
        "status": "running",
        "platforms": get_platform_status(),
        "version": "1.0.0",
    })


@app.route("/api/health", methods=["GET"])
def api_health():
    """فحص صحة الخادم."""
    return jsonify({"ok": True})


def run_server(host: str = "0.0.0.0", port: int = 8000, debug: bool = False):
    """تشغيل الخادم."""
    logger.info(f"بدء تشغيل API Server على {host}:{port}")
    app.run(host=host, port=port, debug=debug)


if __name__ == "__main__":
    run_server(debug=True)

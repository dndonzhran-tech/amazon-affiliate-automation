"""النشر الموحد على جميع المنصات."""

import logging

from src.database import log_event, update_post_status
from src.social import instagram, telegram, twitter

logger = logging.getLogger(__name__)


PUBLISHERS = {
    "twitter": twitter.post_tweet,
    "telegram": telegram.send_message,
    "instagram": instagram.post_image,
}


def publish_post(post: dict, platforms: list[str] | None = None) -> dict:
    """نشر منشور على المنصات المحددة."""
    if platforms is None:
        platforms = ["twitter", "telegram", "instagram"]

    results = {}

    for platform in platforms:
        publisher = PUBLISHERS.get(platform)
        if not publisher:
            logger.warning(f"منصة غير معروفة: {platform}")
            continue

        # تجهيز النص حسب المنصة
        text = _prepare_text(post, platform)
        image_url = post.get("image_url", "")

        if platform == "instagram" and not image_url:
            results[platform] = {"success": False, "error": "الصورة مطلوبة"}
            continue

        result = publisher(text, image_url)
        results[platform] = result

        # تحديث حالة المنشور في قاعدة البيانات
        if post.get("id"):
            if result.get("success"):
                id_field = f"{platform}_id"
                id_value = (
                    result.get("post_id")
                    or result.get("message_id")
                    or result.get("media_id")
                    or ""
                )
                update_post_status(
                    post["id"], "published", **{id_field: id_value}
                )

                # تسجيل حدث نشر ناجح
                log_event({
                    "event_type": "publish",
                    "product_asin": post.get("product_asin", ""),
                    "platform": platform,
                    "post_id": post["id"],
                    "metadata": {"result_id": id_value},
                })
            else:
                log_event({
                    "event_type": "publish_failed",
                    "product_asin": post.get("product_asin", ""),
                    "platform": platform,
                    "post_id": post["id"],
                    "metadata": {"error": result.get("error", "")},
                })

    # تحديد النجاح الكلي
    any_success = any(r.get("success") for r in results.values())
    if post.get("id") and not any_success:
        update_post_status(post["id"], "failed")

    return {
        "success": any_success,
        "results": results,
    }


def _prepare_text(post: dict, platform: str) -> str:
    """تجهيز النص حسب حدود المنصة."""
    content = post.get("content", "")
    hashtags = post.get("hashtags", [])
    tags_text = " ".join(hashtags)

    if platform == "twitter":
        # حد 280 حرف
        full = f"{content}\n\n{tags_text}" if tags_text else content
        if len(full) > 280:
            max_len = 280 - len(tags_text) - 5
            full = f"{content[:max_len]}...\n\n{tags_text}"
        return full

    elif platform == "telegram":
        # حد 4096 حرف
        full = f"{content}\n\n{tags_text}" if tags_text else content
        return full[:4096]

    elif platform == "instagram":
        # حد 2200 حرف
        full = f"{content}\n\n{tags_text}" if tags_text else content
        return full[:2200]

    return content


def get_platform_status() -> dict:
    """التحقق من حالة المنصات المُعدة."""
    return {
        "twitter": twitter.is_configured(),
        "telegram": telegram.is_configured(),
        "instagram": instagram.is_configured(),
    }

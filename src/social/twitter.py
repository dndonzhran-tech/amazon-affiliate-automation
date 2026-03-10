"""نظام النشر على تويتر/X."""

import logging

import httpx

from src.config import (
    TWITTER_ACCESS_SECRET,
    TWITTER_ACCESS_TOKEN,
    TWITTER_API_KEY,
    TWITTER_API_SECRET,
    TWITTER_BEARER_TOKEN,
)

logger = logging.getLogger(__name__)

TWITTER_API_V2 = "https://api.twitter.com/2"


def is_configured() -> bool:
    """التحقق من إعدادات تويتر."""
    return bool(TWITTER_BEARER_TOKEN and TWITTER_API_KEY)


def post_tweet(text: str, image_url: str = "") -> dict:
    """نشر تغريدة."""
    if not is_configured():
        return {"success": False, "error": "تويتر غير مُعد"}

    try:
        # رفع الصورة أولاً إذا وُجدت
        media_id = None
        if image_url:
            media_id = _upload_media(image_url)

        payload = {"text": text}
        if media_id:
            payload["media"] = {"media_ids": [media_id]}

        response = httpx.post(
            f"{TWITTER_API_V2}/tweets",
            headers={
                "Authorization": f"Bearer {TWITTER_BEARER_TOKEN}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=30.0,
        )
        response.raise_for_status()
        data = response.json()
        tweet_id = data.get("data", {}).get("id", "")

        logger.info(f"تم نشر تغريدة: {tweet_id}")
        return {"success": True, "post_id": tweet_id}

    except httpx.HTTPError as e:
        logger.error(f"خطأ في نشر التغريدة: {e}")
        return {"success": False, "error": str(e)}


def _upload_media(image_url: str) -> str | None:
    """رفع صورة لتويتر."""
    try:
        # تحميل الصورة
        img_response = httpx.get(image_url, timeout=30.0)
        img_response.raise_for_status()

        # رفع عبر v1.1 media upload
        upload_response = httpx.post(
            "https://upload.twitter.com/1.1/media/upload.json",
            headers={
                "Authorization": f"Bearer {TWITTER_BEARER_TOKEN}",
            },
            files={"media_data": img_response.content},
            timeout=60.0,
        )
        upload_response.raise_for_status()
        return upload_response.json().get("media_id_string")

    except Exception as e:
        logger.error(f"خطأ في رفع الصورة: {e}")
        return None

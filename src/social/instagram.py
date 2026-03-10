"""نظام النشر على إنستغرام."""

import logging
import tempfile

import httpx

from src.config import INSTAGRAM_PASSWORD, INSTAGRAM_USERNAME

logger = logging.getLogger(__name__)


def is_configured() -> bool:
    """التحقق من إعدادات إنستغرام."""
    return bool(INSTAGRAM_USERNAME and INSTAGRAM_PASSWORD)


def post_image(caption: str, image_url: str) -> dict:
    """نشر صورة على إنستغرام."""
    if not is_configured():
        return {"success": False, "error": "إنستغرام غير مُعد"}

    if not image_url:
        return {"success": False, "error": "الصورة مطلوبة لإنستغرام"}

    try:
        from instagrapi import Client

        cl = Client()
        cl.login(INSTAGRAM_USERNAME, INSTAGRAM_PASSWORD)

        # تحميل الصورة مؤقتاً
        img_response = httpx.get(image_url, timeout=30.0)
        img_response.raise_for_status()

        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
            tmp.write(img_response.content)
            tmp_path = tmp.name

        media = cl.photo_upload(tmp_path, caption[:2200])
        media_id = media.pk

        logger.info(f"تم نشر على إنستغرام: {media_id}")
        return {"success": True, "media_id": str(media_id)}

    except ImportError:
        logger.error("مكتبة instagrapi غير مثبتة")
        return {"success": False, "error": "مكتبة instagrapi غير مثبتة"}
    except Exception as e:
        logger.error(f"خطأ في نشر إنستغرام: {e}")
        return {"success": False, "error": str(e)}


def post_story(image_url: str, link: str = "") -> dict:
    """نشر ستوري على إنستغرام."""
    if not is_configured():
        return {"success": False, "error": "إنستغرام غير مُعد"}

    try:
        from instagrapi import Client

        cl = Client()
        cl.login(INSTAGRAM_USERNAME, INSTAGRAM_PASSWORD)

        img_response = httpx.get(image_url, timeout=30.0)
        img_response.raise_for_status()

        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
            tmp.write(img_response.content)
            tmp_path = tmp.name

        media = cl.photo_upload_to_story(tmp_path)
        logger.info(f"تم نشر ستوري: {media.pk}")
        return {"success": True, "media_id": str(media.pk)}

    except ImportError:
        return {"success": False, "error": "مكتبة instagrapi غير مثبتة"}
    except Exception as e:
        logger.error(f"خطأ في نشر الستوري: {e}")
        return {"success": False, "error": str(e)}

"""نظام النشر على تيليجرام."""

import logging

import httpx

from src.config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHANNEL_ID

logger = logging.getLogger(__name__)

TELEGRAM_API = "https://api.telegram.org/bot{token}"


def is_configured() -> bool:
    """التحقق من إعدادات تيليجرام."""
    return bool(TELEGRAM_BOT_TOKEN and TELEGRAM_CHANNEL_ID)


def send_message(text: str, image_url: str = "",
                 parse_mode: str = "HTML") -> dict:
    """إرسال رسالة لقناة تيليجرام."""
    if not is_configured():
        return {"success": False, "error": "تيليجرام غير مُعد"}

    api_base = TELEGRAM_API.format(token=TELEGRAM_BOT_TOKEN)

    try:
        if image_url:
            # إرسال صورة مع نص
            response = httpx.post(
                f"{api_base}/sendPhoto",
                json={
                    "chat_id": TELEGRAM_CHANNEL_ID,
                    "photo": image_url,
                    "caption": text[:1024],  # حد تيليجرام للكابشن
                    "parse_mode": parse_mode,
                },
                timeout=30.0,
            )
        else:
            # إرسال نص فقط
            response = httpx.post(
                f"{api_base}/sendMessage",
                json={
                    "chat_id": TELEGRAM_CHANNEL_ID,
                    "text": text,
                    "parse_mode": parse_mode,
                    "disable_web_page_preview": False,
                },
                timeout=30.0,
            )

        response.raise_for_status()
        data = response.json()

        if data.get("ok"):
            message_id = data["result"]["message_id"]
            logger.info(f"تم إرسال رسالة تيليجرام: {message_id}")
            return {"success": True, "message_id": str(message_id)}
        else:
            return {"success": False, "error": data.get("description", "")}

    except httpx.HTTPError as e:
        logger.error(f"خطأ في إرسال رسالة تيليجرام: {e}")
        return {"success": False, "error": str(e)}


def send_poll(question: str, options: list[str]) -> dict:
    """إرسال استطلاع رأي."""
    if not is_configured():
        return {"success": False, "error": "تيليجرام غير مُعد"}

    api_base = TELEGRAM_API.format(token=TELEGRAM_BOT_TOKEN)

    try:
        response = httpx.post(
            f"{api_base}/sendPoll",
            json={
                "chat_id": TELEGRAM_CHANNEL_ID,
                "question": question,
                "options": [{"text": opt} for opt in options[:10]],
                "is_anonymous": True,
            },
            timeout=30.0,
        )
        response.raise_for_status()
        data = response.json()

        if data.get("ok"):
            return {"success": True, "message_id": str(data["result"]["message_id"])}
        return {"success": False, "error": data.get("description", "")}

    except httpx.HTTPError as e:
        logger.error(f"خطأ في إرسال الاستطلاع: {e}")
        return {"success": False, "error": str(e)}

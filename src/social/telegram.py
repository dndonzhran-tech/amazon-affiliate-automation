"""Telegram posting module."""

import logging
from typing import Optional

import requests

from src.utils import get_env_var

logger = logging.getLogger(__name__)


class TelegramPoster:
    """Handles posting content to Telegram channels/groups."""

    BASE_URL = "https://api.telegram.org/bot{token}"

    def __init__(self, bot_token: str = "", chat_id: str = ""):
        self.bot_token = bot_token or get_env_var("TELEGRAM_BOT_TOKEN")
        self.chat_id = chat_id or get_env_var("TELEGRAM_CHAT_ID")
        self.api_url = self.BASE_URL.format(token=self.bot_token)

    def is_configured(self) -> bool:
        """Check if Telegram credentials are configured."""
        return bool(self.bot_token and self.chat_id)

    def send_message(
        self,
        text: str,
        chat_id: str = "",
        parse_mode: str = "HTML",
        disable_preview: bool = False,
    ) -> Optional[dict]:
        """Send a text message to Telegram."""
        if not self.is_configured():
            logger.error("Telegram credentials not configured")
            return None

        target_chat = chat_id or self.chat_id
        url = f"{self.api_url}/sendMessage"
        payload = {
            "chat_id": target_chat,
            "text": text,
            "parse_mode": parse_mode,
            "disable_web_page_preview": disable_preview,
        }

        try:
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data.get("ok"):
                msg_id = data["result"]["message_id"]
                logger.info(f"Telegram message sent: {msg_id}")
                return {"id": msg_id, "text": text, "platform": "telegram"}
            else:
                logger.error(f"Telegram API error: {data.get('description')}")
                return None
        except requests.RequestException as e:
            logger.error(f"Failed to send Telegram message: {e}")
            return None

    def send_photo(
        self,
        photo_url: str,
        caption: str = "",
        chat_id: str = "",
        parse_mode: str = "HTML",
    ) -> Optional[dict]:
        """Send a photo with caption to Telegram."""
        if not self.is_configured():
            logger.error("Telegram credentials not configured")
            return None

        target_chat = chat_id or self.chat_id
        url = f"{self.api_url}/sendPhoto"
        payload = {
            "chat_id": target_chat,
            "photo": photo_url,
            "caption": caption,
            "parse_mode": parse_mode,
        }

        try:
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data.get("ok"):
                msg_id = data["result"]["message_id"]
                logger.info(f"Telegram photo sent: {msg_id}")
                return {"id": msg_id, "caption": caption, "platform": "telegram"}
            else:
                logger.error(f"Telegram API error: {data.get('description')}")
                return None
        except requests.RequestException as e:
            logger.error(f"Failed to send Telegram photo: {e}")
            return None

    def send_product_post(
        self,
        product_name: str,
        description: str,
        price: float,
        affiliate_url: str,
        image_url: str = "",
        discount: float = None,
        language: str = "en",
    ) -> Optional[dict]:
        """Send a formatted product post to Telegram."""
        if language == "ar":
            text = self._format_product_ar(
                product_name, description, price, affiliate_url, discount
            )
        else:
            text = self._format_product_en(
                product_name, description, price, affiliate_url, discount
            )

        if image_url:
            return self.send_photo(photo_url=image_url, caption=text)
        return self.send_message(text=text)

    def _format_product_en(
        self, name: str, desc: str, price: float, url: str, discount: float = None
    ) -> str:
        lines = [f"<b>{name}</b>", ""]
        if desc:
            lines.append(f"{desc}")
            lines.append("")
        lines.append(f"💰 Price: <b>${price:.2f}</b>")
        if discount:
            lines.append(f"🔥 Discount: <b>{discount:.0f}% OFF</b>")
        lines.append("")
        lines.append(f"🛒 <a href=\"{url}\">Buy Now</a>")
        return "\n".join(lines)

    def _format_product_ar(
        self, name: str, desc: str, price: float, url: str, discount: float = None
    ) -> str:
        lines = [f"<b>{name}</b>", ""]
        if desc:
            lines.append(f"{desc}")
            lines.append("")
        lines.append(f"💰 السعر: <b>${price:.2f}</b>")
        if discount:
            lines.append(f"🔥 خصم: <b>{discount:.0f}%</b>")
        lines.append("")
        lines.append(f"🛒 <a href=\"{url}\">اشتري الآن</a>")
        return "\n".join(lines)

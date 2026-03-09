"""الإعدادات المركزية للمشروع."""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# مسارات المشروع
BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_DIR = BASE_DIR / "config"
DATA_DIR = BASE_DIR / "data"
TEMPLATES_DIR = BASE_DIR / "templates"

# إعدادات أمازون
AMAZON_ACCESS_KEY = os.getenv("AMAZON_ACCESS_KEY", "")
AMAZON_SECRET_KEY = os.getenv("AMAZON_SECRET_KEY", "")
AMAZON_PARTNER_TAG = os.getenv("AMAZON_PARTNER_TAG", "")
AMAZON_REGION = os.getenv("AMAZON_REGION", "us-east-1")
AMAZON_MARKETPLACE = os.getenv("AMAZON_MARKETPLACE", "www.amazon.com")

# إعدادات الذكاء الاصطناعي
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
AI_PROVIDER = os.getenv("AI_PROVIDER", "openai")  # openai أو anthropic
AI_MODEL = os.getenv("AI_MODEL", "gpt-4o")

# إعدادات تويتر/X
TWITTER_API_KEY = os.getenv("TWITTER_API_KEY", "")
TWITTER_API_SECRET = os.getenv("TWITTER_API_SECRET", "")
TWITTER_ACCESS_TOKEN = os.getenv("TWITTER_ACCESS_TOKEN", "")
TWITTER_ACCESS_SECRET = os.getenv("TWITTER_ACCESS_SECRET", "")
TWITTER_BEARER_TOKEN = os.getenv("TWITTER_BEARER_TOKEN", "")

# إعدادات إنستغرام
INSTAGRAM_USERNAME = os.getenv("INSTAGRAM_USERNAME", "")
INSTAGRAM_PASSWORD = os.getenv("INSTAGRAM_PASSWORD", "")

# إعدادات تيليجرام
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHANNEL_ID = os.getenv("TELEGRAM_CHANNEL_ID", "")

# إعدادات قاعدة البيانات
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DATA_DIR}/affiliate.db")

# إعدادات الجدولة
POST_INTERVAL_HOURS = int(os.getenv("POST_INTERVAL_HOURS", "6"))
MAX_POSTS_PER_DAY = int(os.getenv("MAX_POSTS_PER_DAY", "4"))
POSTING_HOURS_START = int(os.getenv("POSTING_HOURS_START", "9"))
POSTING_HOURS_END = int(os.getenv("POSTING_HOURS_END", "22"))

# إعدادات n8n
N8N_WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL", "http://localhost:5678")
N8N_API_KEY = os.getenv("N8N_API_KEY", "")

# إعدادات عامة
DEFAULT_LANGUAGE = os.getenv("DEFAULT_LANGUAGE", "ar")
SUPPORTED_LANGUAGES = ["ar", "en"]
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

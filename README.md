# نظام أتمتة التسويق بالعمولة على أمازون

نظام متكامل يعمل مع **n8n** لأتمتة التسويق بالعمولة على أمازون - من جلب المنتجات، توليد المحتوى بالذكاء الاصطناعي، حتى النشر التلقائي على السوشيال ميديا.

## كيف يشتغل النظام

```
n8n Workflow (جدولة كل 6 ساعات)
    ↓
🔍 بحث منتجات أمازون (Amazon PA-API)
    ↓
🎯 فلترة المنتجات (تقييم + خصم + مراجعات)
    ↓
🤖 توليد محتوى بالذكاء الاصطناعي (OpenAI/Anthropic)
    ↓
📝 تحضير المنشورات لكل منصة
    ↓
┌──────────┬──────────┬──────────┐
│ 🐦 تويتر │ 📨 تيليجرام │ 📸 إنستغرام │
└──────────┴──────────┴──────────┘
    ↓
📊 تحليلات + تقارير يومية
```

## هيكل المشروع

```
amazon-affiliate-automation/
├── src/
│   ├── main.py              # نقطة الدخول الرئيسية + CLI
│   ├── api_server.py        # API Server يتكامل مع n8n
│   ├── config.py            # الإعدادات المركزية
│   ├── database.py          # قاعدة البيانات (SQLite)
│   ├── models.py            # نماذج البيانات
│   ├── utils.py             # أدوات مساعدة
│   ├── amazon/
│   │   └── product_api.py   # جلب منتجات أمازون (PA-API 5.0)
│   ├── content/
│   │   └── ai_generator.py  # توليد محتوى بالذكاء الاصطناعي
│   ├── social/
│   │   ├── twitter.py       # النشر على تويتر
│   │   ├── telegram.py      # النشر على تيليجرام
│   │   ├── instagram.py     # النشر على إنستغرام
│   │   └── publisher.py     # النشر الموحد
│   ├── analytics/
│   │   └── tracker.py       # تتبع الأداء والتحليلات
│   └── scheduler/
│       └── scheduler.py     # جدولة مستقلة (بدون n8n)
├── config/
│   ├── hashtags.json        # هاشتاقات بالعربي والإنجليزي
│   └── templates.json       # قوالب المنشورات
├── n8n/
│   └── amazon_affiliate_workflow.json  # workflow جاهز للاستيراد
├── data/                    # قاعدة البيانات (SQLite)
├── tests/                   # اختبارات
├── .env.example             # نموذج الإعدادات
└── requirements.txt
```

## التثبيت

```bash
# 1. استنسخ المستودع
git clone https://github.com/dndonzhran-tech/amazon-affiliate-automation.git
cd amazon-affiliate-automation

# 2. ثبّت المكتبات
pip install -r requirements.txt

# 3. انسخ ملف الإعدادات وعبّي المفاتيح
cp .env.example .env

# 4. هيّئ قاعدة البيانات
python -m src.main init
```

## إعداد المفاتيح

عدّل ملف `.env` وأضف المفاتيح:

| الخدمة | المطلوب | من أين تحصل عليه |
|--------|---------|-----------------|
| Amazon PA-API | AMAZON_ACCESS_KEY, AMAZON_SECRET_KEY, AMAZON_PARTNER_TAG | [Amazon Associates](https://affiliate-program.amazon.com/) |
| OpenAI | OPENAI_API_KEY | [OpenAI Platform](https://platform.openai.com/) |
| Twitter/X | TWITTER_BEARER_TOKEN + 4 مفاتيح | [Twitter Developer](https://developer.twitter.com/) |
| Telegram | TELEGRAM_BOT_TOKEN, TELEGRAM_CHANNEL_ID | [@BotFather](https://t.me/BotFather) |
| Instagram | INSTAGRAM_USERNAME, INSTAGRAM_PASSWORD | حسابك |

## التشغيل

### الطريقة 1: مع n8n (موصى بها)

```bash
# 1. شغّل API Server
python -m src.main server --port 8000

# 2. في n8n:
#    - افتح http://localhost:5678
#    - اضغط Import Workflow
#    - اختر ملف n8n/amazon_affiliate_workflow.json
#    - فعّل الـ Workflow
```

### الطريقة 2: بدون n8n (مجدول مستقل)

```bash
# شغّل المجدول المستقل
python -m src.main scheduler
```

### الطريقة 3: يدوياً (CLI)

```bash
# توليد محتوى لمنتج
python -m src.main generate --name "سماعات بلوتوث" --url "https://amazon.com/dp/B123" --discount 30 --save

# نشر المنشورات المعلقة
python -m src.main publish --count 1

# عرض حالة النظام
python -m src.main status
```

## n8n Workflow

الـ workflow يتكون من 3 مسارات:

### المسار الرئيسي (كل 6 ساعات)
بحث منتجات → فلترة → توليد محتوى → تحضير → نشر على 3 منصات → تحليلات

### التقرير اليومي (كل 24 ساعة)
جلب إحصائيات اليوم → إرسال تقرير على تيليجرام

### نشر يدوي (Webhook)
استدعاء webhook → نفس مسار النشر

## API Endpoints

| المسار | الطريقة | الوظيفة |
|--------|---------|---------|
| `/api/products/search` | POST | بحث منتجات أمازون |
| `/api/products/add` | POST | إضافة منتج يدوياً |
| `/api/products` | GET | عرض المنتجات |
| `/api/content/generate` | POST | توليد محتوى بالـ AI |
| `/api/publish/twitter` | POST | نشر على تويتر |
| `/api/publish/telegram` | POST | نشر على تيليجرام |
| `/api/publish/instagram` | POST | نشر على إنستغرام |
| `/api/publish/all` | POST | نشر على الكل |
| `/api/analytics/daily-report` | GET | التقرير اليومي |
| `/api/analytics/weekly-report` | GET | التقرير الأسبوعي |
| `/api/analytics/top-products` | GET | أفضل المنتجات |
| `/api/status` | GET | حالة النظام |
| `/api/health` | GET | فحص صحة الخادم |

## الاختبارات

```bash
python -m unittest discover -s tests -v
```

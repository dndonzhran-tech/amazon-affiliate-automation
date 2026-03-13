# Amazon Affiliate Automation PRO

نظام أتمتة التسويق بالعمولة لأمازون — يجلب المنتجات الرائجة، يولّد محتوى تسويقي احترافي بالذكاء الاصطناعي (Groq)، ينشر على السوشال ميديا، ويولّد سكريبتات YouTube Shorts جاهزة للتسجيل.

## سير العمل (Workflow)

```
Schedule Trigger → Fetch Products (Amazon API) → Process & Filter
    → AI Content Generation (Groq) → Post to Social Media
                                    → Generate YouTube Shorts Scripts
    → Send Telegram Notification
```

## المميزات

- **جلب تلقائي** لأفضل المنتجات والعروض من أمازون
- **AI احترافي** (Groq LLaMA 3.3 70B) لتوليد محتوى عالي التحويل
- **سوشال ميديا** — نشر تلقائي على Twitter/X، Facebook، وغيرها
- **YouTube Shorts** — سكريبتات كاملة (Hook + Body + CTA) جاهزة للتسجيل
- **دعم عربي + إنجليزي** مع لهجة خليجية طبيعية للـ Shorts
- **إشعارات تيليجرام** بملخص كل عملية
- **n8n Workflow جاهز** للاستيراد مباشرة

## هيكل المشروع

```
amazon-affiliate-automation/
├── src/
│   ├── main.py          # التطبيق الرئيسي (Python)
│   ├── utils.py         # أدوات API والنشر
│   ├── youtube.py       # توليد سكريبتات Shorts ورفع YouTube
│   └── models.py        # نماذج البيانات
├── n8n/
│   └── workflow_amazon_affiliate_pro.json  # n8n workflow جاهز للاستيراد
├── config/
│   ├── hashtags.json          # هاشتاقات (عربي + إنجليزي)
│   ├── templates.json         # قوالب المنشورات
│   ├── shorts_templates.json  # قوالب سكريبتات YouTube Shorts
│   └── youtube_tags.json      # تاقات YouTube
├── output/
│   ├── scripts/         # سكريبتات Shorts المحفوظة
│   └── videos/          # فيديوهات للرفع
├── .env.example
├── requirements.txt
└── README.md
```

## المتطلبات

- Python 3.10+
- حساب [RapidAPI](https://rapidapi.com/) مع اشتراك Amazon Data API
- [مفتاح Groq API](https://console.groq.com/)
- تاق Amazon Associates
- توكنات سوشال ميديا (اختياري)
- YouTube Data API v3 (اختياري — للرفع التلقائي)
- بوت تيليجرام (اختياري — للإشعارات)

## التثبيت

```bash
git clone https://github.com/dndonzhran-tech/amazon-affiliate-automation.git
cd amazon-affiliate-automation
pip install -r requirements.txt
cp .env.example .env
# عدّل .env بمفاتيحك الفعلية
```

## الاستخدام

### Python

```bash
# تشغيل كامل (سوشال + يوتيوب)
python src/main.py

# سوشال ميديا فقط
python src/main.py --mode social

# YouTube Shorts فقط
python src/main.py --mode youtube

# جدولة تلقائية كل 30 دقيقة
python src/main.py --schedule --interval 30
```

### n8n (الطريقة الموصى بها)

1. افتح n8n (`http://localhost:5678`)
2. اذهب لـ **Settings > Environment Variables** وأضف المتغيرات من `.env.example`
3. استورد الـ workflow:
   - اضغط على الثلاث نقط (...) أعلى يمين
   - اختر **Import from file**
   - اختر `n8n/workflow_amazon_affiliate_pro.json`
4. اربط credentials الـ Groq والتيليجرام
5. اضغط **Execute Workflow** للتجربة
6. فعّل **Publish** للجدولة التلقائية

## تخصيص المحتوى

### قوالب السوشال ميديا (`config/templates.json`)
6 أنماط مختلفة: تنبيه عرض، اختيار أفضل، مراجعة، مقارنة، استعجال، قيمة مقابل المال

### سكريبتات YouTube Shorts (`config/shorts_templates.json`)
5 أنماط فيروسية: صدمة، فضول، مشكلة-حل، إثبات اجتماعي، صياد العروض

### الهاشتاقات والتاقات
- `config/hashtags.json` — 15 هاشتاق لكل لغة (عربي + إنجليزي)
- `config/youtube_tags.json` — 20 تاق YouTube لكل لغة

## اللغات المدعومة

- **العربية** (`ar`) — مُحسّنة للسوق السعودي والإماراتي والخليجي
- **الإنجليزية** (`en`) — مُحسّنة للسوق الأمريكي والعالمي

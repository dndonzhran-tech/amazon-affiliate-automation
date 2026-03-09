# أتمتة التسويق بالعمولة على أمازون

أداة لتوليد منشورات تسويقية تلقائية لمنتجات أمازون باللغتين العربية والإنجليزية.

## هيكل المشروع

```
amazon-affiliate-automation/
├── src/
│   ├── main.py          # التطبيق الرئيسي
│   ├── utils.py         # الأدوات المساعدة
│   └── models.py        # نماذج البيانات
├── config/
│   ├── hashtags.json    # الهاشتاقات بالعربي والإنجليزي
│   └── templates.json   # قوالب السيناريوهات
├── tests/               # اختبارات الوحدة
├── .env.example         # نموذج متغيرات البيئة
├── README.md
└── requirements.txt
```

## المتطلبات

- Python 3.10 أو أحدث
- pip

## التثبيت

1. استنسخ المستودع:
   ```bash
   git clone https://github.com/dndonzhran-tech/amazon-affiliate-automation.git
   cd amazon-affiliate-automation
   ```

2. ثبّت المكتبات المطلوبة:
   ```bash
   pip install -r requirements.txt
   ```

3. انسخ ملف البيئة وعدّل القيم:
   ```bash
   cp .env.example .env
   ```

## الاستخدام

### توليد منشور واحد (بالعربي):
```bash
python -m src.main --name "سماعات بلوتوث" --url "https://amazon.com/dp/B123" --description "سماعات لاسلكية" --scenario product_review
```

### توليد جميع المنشورات:
```bash
python -m src.main --name "سماعات بلوتوث" --url "https://amazon.com/dp/B123" --description "سماعات لاسلكية" --category "إلكترونيات" --discount 30
```

### توليد منشورات بالإنجليزي:
```bash
python -m src.main --name "Bluetooth Headphones" --url "https://amazon.com/dp/B123" --description "Wireless headphones" --lang en
```

## السيناريوهات المتاحة

| السيناريو | الوصف |
|-----------|-------|
| `product_review` | مراجعة منتج |
| `deal_alert` | تنبيه عرض/خصم |
| `comparison` | مقارنة/ترشيح أفضل منتج |
| `recommendation` | توصية شخصية |

## الاختبارات

```bash
python -m unittest discover -s tests -v
```

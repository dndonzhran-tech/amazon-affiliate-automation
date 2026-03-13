# تعليمات لـ Claude MCP — تنفيذ على n8n مباشرة

## المهمة
بناء أقوى نظام تسويق بالعمولة لأمازون مع YouTube Shorts على n8n.

## الـ Workflow المطلوب

### Node 1: Schedule Trigger
- كل ساعتين
- أو Manual Trigger للاختبار

### Node 2: HTTP Request — جلب المنتجات
```
Method: GET
URL: https://real-time-amazon-data.p.rapidapi.com/deals-v2
Headers:
  X-RapidAPI-Key: (من Environment Variables)
  X-RapidAPI-Host: real-time-amazon-data.p.rapidapi.com
Query Parameters:
  country: US (أو SA للسعودية)
  category_id: electronics
```

### Node 3: Code in JavaScript — معالجة المنتجات
```javascript
const data = $input.all()[0].json;
const products = data.deals || data.products || [];
const affiliateTag = $env.AMAZON_AFFILIATE_TAG || 'yourtag-20';
const maxProducts = parseInt($env.MAX_POSTS_PER_RUN || '3');
const language = $env.LANGUAGE || 'ar';

const processed = products
  .filter(p => p.title && p.asin)
  .filter(p => !p.rating || p.rating >= 3.5)
  .slice(0, maxProducts)
  .map((p, index) => {
    const price = typeof p.price === 'object' ? p.price.current_price : p.price;
    const currency = typeof p.price === 'object' ? p.price.currency : 'USD';
    return {
      asin: p.asin,
      title: p.title,
      price: price || 'Check price',
      currency: currency || 'USD',
      rating: p.rating || 'N/A',
      reviewCount: p.reviews_count || 'many',
      image: p.image || p.thumbnail || '',
      category: p.category || 'General',
      discount: p.discount_percent || p.savings_percent || 0,
      affiliateLink: `https://www.amazon.com/dp/${p.asin}?tag=${affiliateTag}`,
      language: language,
      features: (p.features || []).slice(0, 3).join('. ') || 'Premium quality'
    };
  });

if (processed.length === 0) throw new Error('No valid products found');
return processed.map(p => ({ json: p }));
```

### Node 4: AI Agent — توليد المحتوى
**System Prompt:**
```
You are an elite affiliate marketing content creator with 20 years of experience generating over $50M in affiliate revenue.

You deeply understand:
1. DIRECT RESPONSE COPYWRITING: Headlines that stop scrolls, power words, urgency
2. YOUTUBE ALGORITHM: Hook retention, watch time, CTR-boosting titles
3. SOCIAL MEDIA ALGORITHMS: Engagement triggers, hashtag strategy, viral patterns
4. CONSUMER PSYCHOLOGY: FOMO, social proof, anchoring, scarcity

Rules:
- Never use fake claims or misleading discounts
- Every sentence EARNS its place - zero fluff
- Short punchy sentences (max 10 words)
- Focus on TRANSFORMATION not features
- Always include social proof (ratings, reviews)

Write in Arabic (Gulf dialect for Shorts scripts).
```

**User Prompt:**
```
Create TWO pieces of content for this product:

Product: {{ $json.title }}
Price: {{ $json.price }} {{ $json.currency }}
Rating: {{ $json.rating }}/5 ({{ $json.reviewCount }} reviews)
Discount: {{ $json.discount }}%
Link: {{ $json.affiliateLink }}

TASK 1 - SOCIAL MEDIA POST:
- Max 280 chars, emoji hook, rating as social proof, strong CTA, 5 hashtags

TASK 2 - YOUTUBE SHORTS SCRIPT (30 seconds):
- HOOK (0-3s): Pattern interrupt that stops scrolling
- BODY (3-25s): Fast product showcase, benefits not features, short sentences
- CTA (25-30s): Urgency-driven, link in description

FORMAT:
---SOCIAL_POST---
[post with hashtags]
---SHORTS_HOOK---
[3 second hook]
---SHORTS_BODY---
[20 second body]
---SHORTS_CTA---
[call to action]
---YOUTUBE_TITLE---
[SEO title under 70 chars]
---YOUTUBE_DESCRIPTION---
[description with affiliate link]
---END---
```

### Node 5: Code — تقسيم محتوى AI
```javascript
const aiOutput = $input.all()[0].json.output || '';
const productData = $input.all()[0].json;

function extract(text, start, end) {
  const s = text.indexOf(start);
  if (s === -1) return '';
  const from = s + start.length;
  const e = end ? text.indexOf(end, from) : text.length;
  return text.substring(from, e === -1 ? text.length : e).trim();
}

return [{
  json: {
    asin: productData.asin,
    title: productData.title,
    price: productData.price,
    affiliateLink: productData.affiliateLink,
    image: productData.image,
    socialPost: extract(aiOutput, '---SOCIAL_POST---', '---SHORTS_HOOK---'),
    shortsHook: extract(aiOutput, '---SHORTS_HOOK---', '---SHORTS_BODY---'),
    shortsBody: extract(aiOutput, '---SHORTS_BODY---', '---SHORTS_CTA---'),
    shortsCta: extract(aiOutput, '---SHORTS_CTA---', '---YOUTUBE_TITLE---'),
    youtubeTitle: extract(aiOutput, '---YOUTUBE_TITLE---', '---YOUTUBE_DESCRIPTION---').substring(0, 70),
    youtubeDescription: extract(aiOutput, '---YOUTUBE_DESCRIPTION---', '---END---'),
    generatedAt: new Date().toISOString()
  }
}];
```

### Node 6 & 7: HTTP Requests — نشر على المنصات
- Platform 1 (Twitter/X): POST مع socialPost
- Platform 2 (Facebook): POST مع socialPost
- continueOnFail: true (ما يوقف لو فشل)

### Node 8: Limit
- maxItems: 3

### Node 9: Telegram Notification
```
✅ *تم التنفيذ بنجاح*

📦 *المنتج:* {{ $json.title }}
💰 *السعر:* {{ $json.price }}
🔗 *الرابط:* {{ $json.affiliateLink }}

📱 *منشور السوشال:* تم النشر
🎬 *سكريبت Shorts:* تم التوليد

📝 *سكريبت الشورت:*
[HOOK] {{ $json.shortsHook }}
[BODY] {{ $json.shortsBody }}
[CTA] {{ $json.shortsCta }}

🎯 *عنوان YouTube:* {{ $json.youtubeTitle }}
```

### Sub-nodes:
- **Groq Chat Model**: llama-3.3-70b-versatile, temp: 0.8, maxTokens: 1000
- **Simple Memory**: contextWindowLength: 5

## Environment Variables المطلوبة في n8n
اذهب لـ Settings > Environment Variables وأضف:
- RAPIDAPI_KEY
- AMAZON_AFFILIATE_TAG
- AMAZON_COUNTRY
- GROQ_API_KEY
- LANGUAGE
- PRODUCT_CATEGORY
- MAX_POSTS_PER_RUN
- PLATFORM1_API_URL
- PLATFORM1_API_TOKEN
- PLATFORM2_API_URL
- PLATFORM2_API_TOKEN
- TELEGRAM_CHAT_ID

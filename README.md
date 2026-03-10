# Amazon Affiliate Automation

Full automation system for Amazon affiliate marketing. Scrapes products, generates social media content in English and Arabic, posts to Twitter and Telegram, and schedules automated campaigns.

## Features

- **Product Scraping**: Search Amazon products, bestsellers, and deals
- **Content Generation**: Auto-generate posts with templates, hashtags, and emojis
- **Multi-Platform Posting**: Twitter/X and Telegram support
- **Scheduling**: Automated posting on intervals
- **Database**: SQLite storage for products, posts, and schedules
- **Bilingual**: Full English and Arabic support
- **CLI**: Complete command-line interface with rich output

## Project Structure

```
amazon-affiliate-automation/
├── src/
│   ├── main.py              # CLI entry point (Click)
│   ├── models.py            # Data models + SQLAlchemy ORM
│   ├── scraper.py           # Amazon product scraper
│   ├── content_generator.py # Post content generator
│   ├── database.py          # Database operations
│   ├── scheduler.py         # Automated task scheduler
│   ├── utils.py             # Utility functions
│   └── social/
│       ├── twitter.py       # Twitter/X integration
│       └── telegram.py      # Telegram integration
├── config/
│   ├── hashtags.json        # Hashtag sets (EN/AR)
│   └── templates.json       # Post templates (EN/AR)
├── examples/
│   └── products.json        # Example products file
├── tests/                   # Unit tests
├── requirements.txt         # Python dependencies
└── .env.example             # Environment variables template
```

## Setup

```bash
git clone https://github.com/dndonzhran-tech/amazon-affiliate-automation.git
cd amazon-affiliate-automation
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your credentials
```

## Usage

### Scrape Products
```bash
# Search products by keyword
python -m src.main scrape "wireless headphones" -n 10

# Filter by price and rating
python -m src.main scrape "laptop stand" --min-price 20 --max-price 50 --min-rating 4.0

# Save results to file
python -m src.main scrape "usb hub" -o results.json
```

### Generate Posts
```bash
# Generate from scraped products in database
python -m src.main generate --platform twitter --language en

# Generate from keyword (scrape + generate)
python -m src.main generate -k "bluetooth speaker" -s deal_alert -l ar

# Generate from products file
python -m src.main generate -p examples/products.json -o posts.json

# Rotate through scenarios
python -m src.main generate -k "tech gadgets" -s rotate -n 10
```

### Post to Social Media
```bash
# Post to Twitter
python -m src.main post -k "wireless earbuds" --platform twitter

# Post to Telegram
python -m src.main post -k "smart watch" --platform telegram -l ar

# Post from products file
python -m src.main post -p examples/products.json --platform telegram
```

### Schedule Automated Posts
```bash
# Add a schedule (every 60 minutes)
python -m src.main schedule-cmd add "Tech Deals" -i 60 --platform twitter -c "tech gadgets"

# Add Arabic Telegram schedule
python -m src.main schedule-cmd add "عروض يومية" -i 120 --platform telegram -l ar -c "electronics"

# List all schedules
python -m src.main schedule-cmd list

# Run scheduler (continuous)
python -m src.main schedule-cmd run

# Run all tasks once
python -m src.main schedule-cmd run --once

# Remove a schedule
python -m src.main schedule-cmd remove 1
```

### Database Management
```bash
# View statistics
python -m src.main stats

# List products
python -m src.main products -c "Electronics"

# List generated posts
python -m src.main posts --platform twitter --pending
```

## Environment Variables

| Variable | Description |
|---|---|
| `AFFILIATE_TAG` | Your Amazon affiliate tag |
| `TWITTER_API_KEY` | Twitter API key |
| `TWITTER_API_SECRET` | Twitter API secret |
| `TWITTER_ACCESS_TOKEN` | Twitter access token |
| `TWITTER_ACCESS_TOKEN_SECRET` | Twitter access token secret |
| `TWITTER_BEARER_TOKEN` | Twitter bearer token |
| `TELEGRAM_BOT_TOKEN` | Telegram bot token |
| `TELEGRAM_CHAT_ID` | Telegram channel/group ID |

## Running Tests

```bash
python -m pytest tests/ -v
```

## Post Templates

8 scenarios available in both English and Arabic:
- `product_review` - Standard product review
- `deal_alert` - Discount/deal notification
- `comparison` - Category comparison
- `recommendation` - Personal recommendation
- `flash_sale` - Limited time offer
- `top_pick` - Top pick highlight
- `trending` - Trending product
- `budget_friendly` - Value for money

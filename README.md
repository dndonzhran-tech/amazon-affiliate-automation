# Amazon Affiliate Automation

Automated Amazon affiliate marketing system that fetches trending products, generates high-converting promotional content using AI (Groq), and posts to social media platforms — all on a configurable schedule.

This project is the Python equivalent of the n8n workflow, designed to run standalone without n8n dependency.

## Workflow

```
Schedule Trigger → Fetch Products (Amazon API) → Process & Filter
    → AI Content Generation (Groq) → Post to Platforms → Send Notification
```

### Workflow Steps

1. **Schedule Trigger** — Runs automatically at configurable intervals
2. **HTTP Request** — Fetches trending/deal products from Amazon via RapidAPI
3. **Process Data** — Filters products, builds affiliate links, applies limits
4. **AI Agent (Groq)** — Generates high-converting marketing copy using expert prompts
5. **Post to Platforms** — Publishes content to configured social media APIs
6. **Notification** — Sends a summary report via Telegram/Slack webhook

## Project Structure

```
amazon-affiliate-automation/
├── src/
│   ├── main.py          # Main application & workflow orchestration
│   ├── utils.py         # API calls, AI generation, posting utilities
│   └── models.py        # Data models (Product, GeneratedContent, PostResult)
├── config/
│   ├── hashtags.json    # Hashtags for English and Arabic
│   └── templates.json   # Post templates for English and Arabic
├── tests/               # Unit tests
├── .env.example         # Environment variables template
├── requirements.txt     # Python dependencies
└── README.md
```

## Prerequisites

- Python 3.10+
- [RapidAPI account](https://rapidapi.com/) with Amazon Data API subscription
- [Groq API key](https://console.groq.com/) for AI content generation
- Amazon Associates affiliate tag
- Social media API tokens (Twitter/X, Facebook, etc.)
- Telegram bot token or Slack webhook URL (for notifications)

## Installation

```bash
git clone https://github.com/dndonzhran-tech/amazon-affiliate-automation.git
cd amazon-affiliate-automation
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your actual API keys and configuration
```

## Configuration

Copy `.env.example` to `.env` and configure:

| Variable | Description |
|----------|-------------|
| `RAPIDAPI_KEY` | Your RapidAPI key for Amazon product data |
| `RAPIDAPI_HOST` | RapidAPI host for the Amazon API |
| `AMAZON_AFFILIATE_TAG` | Your Amazon Associates tag (e.g., `yourtag-20`) |
| `GROQ_API_KEY` | Groq API key for AI content generation |
| `LANGUAGE` | Content language: `en` or `ar` |
| `PRODUCT_CATEGORY` | Product category to fetch (e.g., `electronics`) |
| `MAX_POSTS_PER_RUN` | Maximum products to process per run |
| `PLATFORM1_API_URL` | First platform API endpoint |
| `PLATFORM1_API_TOKEN` | First platform auth token |
| `PLATFORM2_API_URL` | Second platform API endpoint |
| `PLATFORM2_API_TOKEN` | Second platform auth token |
| `NOTIFICATION_WEBHOOK_URL` | Telegram/Slack webhook for notifications |

## Usage

### Run once
```bash
python src/main.py
```

### Run on a schedule (every 60 minutes)
```bash
python src/main.py --schedule --interval 60
```

## Customization

### Templates (`config/templates.json`)
Add or modify post templates per language. Templates use `{product_name}` and `{affiliate_link}` placeholders.

### Hashtags (`config/hashtags.json`)
Add or modify hashtags per language. 5 random hashtags are selected per post.

## Supported Languages

- **English** (`en`) — Optimized for US/global audiences
- **Arabic** (`ar`) — Optimized for Saudi Arabia, UAE, and Arabic-speaking markets

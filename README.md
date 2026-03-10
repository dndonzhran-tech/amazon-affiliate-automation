# Amazon Affiliate Automation

Automate the generation of social media posts for Amazon affiliate products. Supports English and Arabic content with customizable templates and hashtags.

## Project Structure

```
amazon-affiliate-automation/
├── src/
│   ├── main.py          # Main application entry point
│   ├── utils.py         # Utility functions (templates, hashtags, formatting)
│   └── models.py        # Data models (Product, Post, Campaign)
├── config/
│   ├── hashtags.json    # Hashtag sets (EN/AR)
│   └── templates.json   # Post templates (EN/AR)
├── examples/
│   └── products.json    # Example products file
├── tests/               # Unit tests
├── requirements.txt     # Python dependencies
└── .env.example         # Environment variables template
```

## Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/dndonzhran-tech/amazon-affiliate-automation.git
   cd amazon-affiliate-automation
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Configure environment:
   ```bash
   cp .env.example .env
   # Edit .env and set your AFFILIATE_TAG
   ```

## Usage

```bash
# Generate posts in English
python -m src.main --products examples/products.json --language en --scenario product_review

# Generate posts in Arabic
python -m src.main --products examples/products.json --language ar --scenario deal_alert

# Save output to file
python -m src.main --products examples/products.json --output output.json

# Available scenarios: product_review, deal_alert, comparison, recommendation
```

## Running Tests

```bash
python -m pytest tests/ -v
```

## Configuration

### Templates (`config/templates.json`)
Post templates with placeholders: `{product_name}`, `{description}`, `{link}`, `{category}`, `{discount}`

### Hashtags (`config/hashtags.json`)
Hashtag sets per language, randomly selected for each post.

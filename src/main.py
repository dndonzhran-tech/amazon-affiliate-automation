"""
Amazon Affiliate Automation - Main Application

Replicates the n8n workflow:
  Schedule Trigger → HTTP Request (fetch products) → Code (process data)
  → AI Agent (generate content via Groq) → HTTP Requests (post to platforms)
  → Send notification

Usage:
  python src/main.py              # Run once
  python src/main.py --schedule   # Run on a schedule
"""

import argparse
import logging
import os
import sys
import time

from dotenv import load_dotenv

from models import Product
from utils import (
    build_affiliate_link,
    fetch_trending_products,
    generate_content_with_ai,
    post_to_platform,
    rate_limit_wait,
    send_notification,
)

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def get_env(key: str, required: bool = True) -> str:
    """Get an environment variable."""
    value = os.getenv(key, "")
    if required and not value:
        logger.error("Missing required environment variable: %s", key)
        sys.exit(1)
    return value


def run_workflow():
    """Execute the full automation workflow once."""
    # --- Configuration from environment ---
    rapidapi_key = get_env("RAPIDAPI_KEY")
    rapidapi_host = get_env("RAPIDAPI_HOST")
    affiliate_tag = get_env("AMAZON_AFFILIATE_TAG")
    groq_api_key = get_env("GROQ_API_KEY")
    language = os.getenv("LANGUAGE", "en")
    category = os.getenv("PRODUCT_CATEGORY", "electronics")
    country = os.getenv("AMAZON_COUNTRY", "US")
    max_posts = int(os.getenv("MAX_POSTS_PER_RUN", "3"))

    # Platform API endpoints (optional)
    platform1_url = os.getenv("PLATFORM1_API_URL", "")
    platform1_token = os.getenv("PLATFORM1_API_TOKEN", "")
    platform2_url = os.getenv("PLATFORM2_API_URL", "")
    platform2_token = os.getenv("PLATFORM2_API_TOKEN", "")
    notification_webhook = os.getenv("NOTIFICATION_WEBHOOK_URL", "")

    # --- Step 1: Fetch trending products (HTTP Request node) ---
    logger.info("Fetching trending products from Amazon...")
    products = fetch_trending_products(
        api_key=rapidapi_key,
        api_host=rapidapi_host,
        category=category,
        country=country,
    )

    if not products:
        logger.warning("No products found. Exiting.")
        return

    logger.info("Found %d products.", len(products))

    # --- Step 2: Process products (Code in JavaScript node) ---
    # Add affiliate links, filter, and limit
    for product in products:
        product.affiliate_link = build_affiliate_link(product.asin, affiliate_tag)

    products = products[:max_posts]
    logger.info("Processing %d products for posting.", len(products))

    # --- Step 3 & 4: Generate content and post (AI Agent + HTTP Request nodes) ---
    results = []
    for product in products:
        # Generate AI content (AI Agent node with Groq)
        logger.info("Generating content for: %s", product.title)
        content = generate_content_with_ai(
            product=product,
            groq_api_key=groq_api_key,
            language=language,
        )
        logger.info("Generated post:\n%s", content.full_post)

        # Post to platform 1 (HTTP Request1 node)
        if platform1_url and platform1_token:
            result = post_to_platform(content, platform1_url, platform1_token)
            results.append(result)
            logger.info("Platform 1 post: %s", "success" if result.success else result.error)

        # Post to platform 2 (HTTP Request2 node)
        if platform2_url and platform2_token:
            result = post_to_platform(content, platform2_url, platform2_token)
            results.append(result)
            logger.info("Platform 2 post: %s", "success" if result.success else result.error)

        # Rate limiting (Limit node)
        rate_limit_wait()

    # --- Step 5: Send notification (Send a text message node) ---
    successful = sum(1 for r in results if r.success)
    failed = sum(1 for r in results if not r.success)
    summary = (
        f"Automation complete.\n"
        f"Products processed: {len(products)}\n"
        f"Posts successful: {successful}\n"
        f"Posts failed: {failed}"
    )
    logger.info(summary)

    if notification_webhook:
        send_notification(summary, notification_webhook)
        logger.info("Notification sent.")


def run_scheduled(interval_minutes: int = 60):
    """Run the workflow on a schedule (Schedule Trigger node)."""
    logger.info("Starting scheduled automation (every %d minutes)...", interval_minutes)
    while True:
        try:
            run_workflow()
        except Exception:
            logger.exception("Workflow execution failed")
        logger.info("Next run in %d minutes.", interval_minutes)
        time.sleep(interval_minutes * 60)


def main():
    parser = argparse.ArgumentParser(description="Amazon Affiliate Automation")
    parser.add_argument(
        "--schedule",
        action="store_true",
        help="Run on a repeating schedule",
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=60,
        help="Schedule interval in minutes (default: 60)",
    )
    args = parser.parse_args()

    if args.schedule:
        run_scheduled(args.interval)
    else:
        run_workflow()


if __name__ == "__main__":
    main()

"""
Amazon Affiliate Automation - Main Application

Full workflow:
  Schedule Trigger → Fetch Products → Process Data → AI Content Generation
  → Post to Social Media → Generate YouTube Shorts Scripts → Upload to YouTube
  → Send Notification

Usage:
  python src/main.py                          # Full workflow (social + YouTube)
  python src/main.py --mode social            # Social media posts only
  python src/main.py --mode youtube           # YouTube Shorts only
  python src/main.py --schedule               # Run on a schedule
  python src/main.py --schedule --interval 30 # Every 30 minutes
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
from analytics import AnalyticsTracker
from validators import validate_product
from tts import generate_voiceover
from video import create_short_video
from youtube import (
    generate_shorts_script,
    save_script_to_file,
    upload_to_youtube,
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


def run_social_workflow(products: list[Product], groq_api_key: str, language: str) -> list:
    """Generate AI content and post to social media platforms."""
    platform1_url = os.getenv("PLATFORM1_API_URL", "")
    platform1_token = os.getenv("PLATFORM1_API_TOKEN", "")
    platform2_url = os.getenv("PLATFORM2_API_URL", "")
    platform2_token = os.getenv("PLATFORM2_API_TOKEN", "")

    results = []
    for product in products:
        logger.info("Generating social media content for: %s", product.title)
        content = generate_content_with_ai(
            product=product,
            groq_api_key=groq_api_key,
            language=language,
        )
        logger.info("Generated post:\n%s", content.full_post)

        if platform1_url and platform1_token:
            result = post_to_platform(content, platform1_url, platform1_token)
            results.append(result)
            logger.info("Platform 1: %s", "success" if result.success else result.error)

        if platform2_url and platform2_token:
            result = post_to_platform(content, platform2_url, platform2_token)
            results.append(result)
            logger.info("Platform 2: %s", "success" if result.success else result.error)

        rate_limit_wait()

    return results


def run_youtube_workflow(products: list[Product], groq_api_key: str, language: str) -> list:
    """Full YouTube Shorts pipeline: Script → Voice → Video → Upload."""
    youtube_api_key = os.getenv("YOUTUBE_API_KEY", "")
    youtube_channel_id = os.getenv("YOUTUBE_CHANNEL_ID", "")
    elevenlabs_api_key = os.getenv("ELEVENLABS_API_KEY", "")
    elevenlabs_voice_id = os.getenv("ELEVENLABS_VOICE_ID", "pNInz6obpgDQGcFmaJgB")
    creatomate_api_key = os.getenv("CREATOMATE_API_KEY", "")
    creatomate_template_id = os.getenv("CREATOMATE_TEMPLATE_ID", "")
    videos_dir = os.getenv("VIDEOS_DIR", "output/videos")

    results = []
    for product in products:
        logger.info("=== Processing: %s ===", product.title)

        # Step 1: Generate script
        logger.info("[1/4] Generating script...")
        script = generate_shorts_script(
            product=product,
            groq_api_key=groq_api_key,
            language=language,
        )
        script_path = save_script_to_file(script)
        logger.info("Script saved: %s", script_path)

        safe_title = "".join(
            c if c.isalnum() or c in " -_" else "" for c in product.title
        )[:50].strip()

        # Step 2: Generate voiceover with ElevenLabs
        audio_path = None
        if elevenlabs_api_key:
            logger.info("[2/4] Generating Arabic voiceover (ElevenLabs)...")
            audio_path = generate_voiceover(
                text=script.full_script,
                api_key=elevenlabs_api_key,
                voice_id=elevenlabs_voice_id,
                output_path=f"output/audio/{safe_title}.mp3",
            )
            if audio_path:
                logger.info("Voiceover ready: %s", audio_path)
            else:
                logger.warning("Voiceover failed, continuing without audio...")
        else:
            logger.info("[2/4] Skipping voiceover (ELEVENLABS_API_KEY not set)")

        # Step 3: Generate video with Creatomate
        video_path = os.path.join(videos_dir, f"{safe_title}.mp4")
        if creatomate_api_key:
            logger.info("[3/4] Generating video (Creatomate)...")
            generated_video = create_short_video(
                api_key=creatomate_api_key,
                template_id=creatomate_template_id or None,
                script_text=script.body,
                audio_path=audio_path,
                product_image_url=product.image_url,
                title_text=script.hook,
                cta_text=script.cta,
                output_dir=videos_dir,
            )
            if generated_video:
                video_path = generated_video
                logger.info("Video ready: %s", video_path)
            else:
                logger.warning("Video generation failed")
        else:
            logger.info("[3/4] Skipping video generation (CREATOMATE_API_KEY not set)")

        # Step 4: Upload to YouTube
        if youtube_api_key and youtube_channel_id and os.path.exists(video_path):
            logger.info("[4/4] Uploading to YouTube...")
            result = upload_to_youtube(
                script=script,
                video_path=video_path,
                youtube_api_key=youtube_api_key,
                channel_id=youtube_channel_id,
            )
            results.append(result)
            if result.success:
                logger.info("YouTube upload success: %s", result.url)
            else:
                logger.error("YouTube upload failed: %s", result.error)
        else:
            logger.info("[4/4] Skipping upload (no API key or no video file)")

        rate_limit_wait()

    return results


def run_workflow(mode: str = "all"):
    """Execute the full automation workflow."""
    # --- Configuration ---
    rapidapi_key = get_env("RAPIDAPI_KEY")
    rapidapi_host = get_env("RAPIDAPI_HOST")
    affiliate_tag = get_env("AMAZON_AFFILIATE_TAG")
    groq_api_key = get_env("GROQ_API_KEY")
    language = os.getenv("LANGUAGE", "en")
    category = os.getenv("PRODUCT_CATEGORY", "electronics")
    country = os.getenv("AMAZON_COUNTRY", "US")
    max_posts = int(os.getenv("MAX_POSTS_PER_RUN", "3"))
    notification_webhook = os.getenv("NOTIFICATION_WEBHOOK_URL", "")

    # --- Step 1: Fetch trending products ---
    logger.info("Fetching trending products from Amazon (%s / %s)...", category, country)
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

    # --- Step 2: Validate and process products ---
    valid_products = []
    for product in products:
        is_valid, reason = validate_product(product)
        if not is_valid:
            logger.warning("Skipping invalid product (ASIN=%s): %s", product.asin, reason)
            continue
        product.affiliate_link = build_affiliate_link(product.asin, affiliate_tag)
        valid_products.append(product)

    products = valid_products[:max_posts]
    logger.info("Processing %d products.", len(products))

    # --- Step 3: Run workflows based on mode ---
    social_results = []
    youtube_results = []

    if mode in ("all", "social"):
        logger.info("=== SOCIAL MEDIA WORKFLOW ===")
        social_results = run_social_workflow(products, groq_api_key, language)

    if mode in ("all", "youtube"):
        logger.info("=== YOUTUBE SHORTS WORKFLOW ===")
        youtube_results = run_youtube_workflow(products, groq_api_key, language)

    # --- Step 4: Send notification ---
    social_ok = sum(1 for r in social_results if r.success)
    social_fail = sum(1 for r in social_results if not r.success)
    yt_ok = sum(1 for r in youtube_results if r.success)
    yt_fail = sum(1 for r in youtube_results if not r.success)

    summary = (
        f"Automation complete!\n"
        f"Products: {len(products)}\n"
        f"Social posts: {social_ok} ok / {social_fail} failed\n"
        f"YouTube Shorts: {yt_ok} uploaded / {yt_fail} failed\n"
        f"Scripts saved: {len(products) if mode in ('all', 'youtube') else 0}"
    )
    logger.info(summary)

    if notification_webhook:
        send_notification(summary, notification_webhook)
        logger.info("Notification sent.")

    # --- Step 5: Track analytics ---
    tracker = AnalyticsTracker()
    tracker.track_run(
        products_count=len(products),
        social_posts=social_ok,
        youtube_uploads=yt_ok,
        errors=social_fail + yt_fail,
    )


def run_scheduled(mode: str = "all", interval_minutes: int = 60):
    """Run the workflow on a schedule."""
    logger.info("Starting scheduled automation (every %d min, mode=%s)...", interval_minutes, mode)
    while True:
        try:
            run_workflow(mode=mode)
        except Exception:
            logger.exception("Workflow execution failed")
        logger.info("Next run in %d minutes.", interval_minutes)
        time.sleep(interval_minutes * 60)


def main():
    parser = argparse.ArgumentParser(description="Amazon Affiliate Automation")
    parser.add_argument(
        "--mode",
        choices=["all", "social", "youtube"],
        default="all",
        help="Workflow mode: all (default), social, or youtube",
    )
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
        run_scheduled(mode=args.mode, interval_minutes=args.interval)
    else:
        run_workflow(mode=args.mode)


if __name__ == "__main__":
    main()

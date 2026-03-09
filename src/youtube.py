"""YouTube Shorts generation and upload for Amazon affiliate automation."""

import json
import logging
import os
from pathlib import Path

import requests

from models import Product, ShortsScript, PostResult

logger = logging.getLogger(__name__)

CONFIG_DIR = Path(__file__).parent.parent / "config"


def load_shorts_templates(language: str = "en") -> dict:
    """Load YouTube Shorts script templates."""
    config_path = CONFIG_DIR / "shorts_templates.json"
    with open(config_path) as f:
        config = json.load(f)
    return config.get("shorts", {}).get(language, {})


def load_youtube_tags(language: str = "en") -> list[str]:
    """Load YouTube-specific tags."""
    config_path = CONFIG_DIR / "youtube_tags.json"
    with open(config_path) as f:
        config = json.load(f)
    return config.get("tags", {}).get(language, [])


def generate_shorts_script(
    product: Product,
    groq_api_key: str,
    language: str = "en",
    model: str = "llama-3.3-70b-versatile",
) -> ShortsScript:
    """Generate a YouTube Shorts script using AI for a product."""
    templates = load_shorts_templates(language)
    tags = load_youtube_tags(language)
    lang_name = "English" if language == "en" else "Arabic"

    system_prompt = (
        f"You are an elite YouTube Shorts content strategist and scriptwriter with "
        f"20 years of experience in affiliate marketing and viral video creation. "
        f"You understand the YouTube algorithm deeply — watch time, engagement, CTR. "
        f"You write scripts that hook viewers in the first second, deliver value fast, "
        f"and drive massive click-through to affiliate links. "
        f"You write exclusively in {lang_name}.\n\n"
        f"Your scripts follow the proven viral Shorts formula:\n"
        f"1. HOOK (0-3 seconds): Pattern interrupt — shocking statement, bold claim, or curiosity gap\n"
        f"2. BODY (3-25 seconds): Fast-paced product showcase with benefits, not features\n"
        f"3. CTA (25-30 seconds): Urgency-driven call-to-action that drives link clicks\n\n"
        f"Rules:\n"
        f"- Write for spoken delivery (natural, conversational tone)\n"
        f"- Use short punchy sentences (max 10 words per sentence)\n"
        f"- Include pauses marked with [...] for dramatic effect\n"
        f"- Never use misleading claims\n"
        f"- Focus on transformation and emotional benefits\n"
        f"- Every sentence must earn its place — remove fluff ruthlessly"
    )

    prompt = (
        f"Create a complete YouTube Shorts script (30 seconds) in {lang_name} for:\n\n"
        f"Product: {product.title}\n"
        f"Price: {product.price} {product.currency or ''}\n"
        f"Rating: {product.rating or 'N/A'}/5 ({product.review_count or 'many'} reviews)\n"
        f"Category: {product.category or 'General'}\n"
        f"Discount: {product.discount_percent or 'N/A'}%\n"
        f"Link: {product.affiliate_link}\n\n"
        f"Respond in this EXACT JSON format (no markdown, no explanation):\n"
        f'{{\n'
        f'  "hook": "The attention-grabbing first 3 seconds script",\n'
        f'  "body": "The main 20-second product showcase script",\n'
        f'  "cta": "The final 5-second call-to-action script",\n'
        f'  "title": "SEO-optimized YouTube title (under 70 chars, include emoji)",\n'
        f'  "description": "YouTube description with product details and affiliate link"\n'
        f'}}'
    )

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {groq_api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ],
        "max_tokens": 800,
        "temperature": 0.85,
        "top_p": 0.9,
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        result = response.json()
        content = result["choices"][0]["message"]["content"].strip()

        # Parse JSON response
        script_data = json.loads(content)

        return ShortsScript(
            product=product,
            hook=script_data.get("hook", ""),
            body=script_data.get("body", ""),
            cta=script_data.get("cta", ""),
            title=script_data.get("title", product.title)[:70],
            description=script_data.get("description", ""),
            tags=tags,
            language=language,
        )
    except (requests.RequestException, KeyError, json.JSONDecodeError) as e:
        logger.error("Shorts script generation failed: %s", e)
        return _fallback_script(product, templates, tags, language)


def _fallback_script(
    product: Product,
    templates: dict,
    tags: list[str],
    language: str,
) -> ShortsScript:
    """Generate a fallback script when AI generation fails."""
    if language == "ar":
        hook = f"هل تبحث عن {product.title}؟ لازم تشوف هذا!"
        body = f"هذا المنتج حاصل على تقييم {product.rating or 'عالي'} من آلاف المستخدمين. السعر الآن {product.price} {product.currency or ''} فقط!"
        cta = f"الرابط في الوصف! لا تفوّت العرض قبل ما يخلص!"
        title = f"{product.title} - عرض لا يفوتك!"[:70]
        desc = f"{product.title}\nالسعر: {product.price}\nاشتري الآن: {product.affiliate_link}"
    else:
        hook = f"Stop scrolling! You NEED to see this {product.title}!"
        body = f"This product has {product.rating or 'amazing'} rating from thousands of buyers. Right now it's only {product.price} {product.currency or ''}!"
        cta = f"Link in the description! Grab it before this deal ends!"
        title = f"{product.title} - Insane Deal!"[:70]
        desc = f"{product.title}\nPrice: {product.price}\nBuy now: {product.affiliate_link}"

    return ShortsScript(
        product=product,
        hook=hook,
        body=body,
        cta=cta,
        title=title,
        description=desc,
        tags=tags,
        language=language,
    )


def upload_to_youtube(
    script: ShortsScript,
    video_path: str,
    youtube_api_key: str,
    channel_id: str,
) -> PostResult:
    """
    Upload a YouTube Short via the YouTube Data API v3.

    Note: Full OAuth2 upload requires google-auth + google-api-python-client.
    This function provides the metadata preparation and upload via resumable upload API.
    For production use, configure OAuth2 credentials in .env.
    """
    # Prepare metadata for YouTube Data API v3
    metadata = {
        "snippet": {
            "title": script.title,
            "description": script.full_description,
            "tags": script.tags[:15],
            "categoryId": "22",  # People & Blogs (best for affiliate content)
            "defaultLanguage": script.language,
        },
        "status": {
            "privacyStatus": "public",
            "selfDeclaredMadeForKids": False,
            "shorts": {"isShort": True},
        },
    }

    # Check if video file exists
    if not os.path.exists(video_path):
        return PostResult(
            platform="youtube",
            success=False,
            error=f"Video file not found: {video_path}",
        )

    try:
        # YouTube Data API v3 - videos.insert with resumable upload
        upload_url = "https://www.googleapis.com/upload/youtube/v3/videos"
        params = {
            "uploadType": "resumable",
            "part": "snippet,status",
            "key": youtube_api_key,
        }
        headers = {
            "Authorization": f"Bearer {youtube_api_key}",
            "Content-Type": "application/json",
            "X-Upload-Content-Type": "video/*",
        }

        # Step 1: Initiate resumable upload
        init_response = requests.post(
            upload_url,
            params=params,
            headers=headers,
            json=metadata,
            timeout=30,
        )
        init_response.raise_for_status()

        upload_location = init_response.headers.get("Location")
        if not upload_location:
            return PostResult(
                platform="youtube",
                success=False,
                error="Failed to get upload URL from YouTube API",
            )

        # Step 2: Upload video data
        with open(video_path, "rb") as video_file:
            upload_response = requests.put(
                upload_location,
                data=video_file,
                headers={"Content-Type": "video/*"},
                timeout=300,
            )
            upload_response.raise_for_status()
            result = upload_response.json()

        video_id = result.get("id", "")
        return PostResult(
            platform="youtube",
            success=True,
            post_id=video_id,
            url=f"https://youtube.com/shorts/{video_id}",
        )

    except requests.RequestException as e:
        logger.error("YouTube upload failed: %s", e)
        return PostResult(platform="youtube", success=False, error=str(e))


def save_script_to_file(script: ShortsScript, output_dir: str = "output/scripts") -> str:
    """Save a Shorts script to a text file for manual video creation."""
    os.makedirs(output_dir, exist_ok=True)
    safe_title = "".join(c if c.isalnum() or c in " -_" else "" for c in script.product.title)[:50]
    filename = f"{safe_title.strip()}.txt"
    filepath = os.path.join(output_dir, filename)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(f"=== YOUTUBE SHORTS SCRIPT ===\n")
        f.write(f"Title: {script.title}\n")
        f.write(f"Duration: {script.duration_seconds}s\n")
        f.write(f"Language: {script.language}\n\n")
        f.write(f"--- SCRIPT ---\n\n")
        f.write(script.full_script)
        f.write(f"\n\n--- DESCRIPTION ---\n\n")
        f.write(script.full_description)
        f.write(f"\n\n--- TAGS ---\n")
        f.write(", ".join(script.tags))
        f.write(f"\n\n--- AFFILIATE LINK ---\n")
        f.write(script.product.affiliate_link or "N/A")

    logger.info("Script saved to: %s", filepath)
    return filepath

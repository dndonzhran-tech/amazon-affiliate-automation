"""Creatomate video generation for YouTube Shorts."""

import logging
import os
import time

import requests

logger = logging.getLogger(__name__)

CREATOMATE_API_URL = "https://api.creatomate.com/v1/renders"


def create_short_video(
    api_key: str,
    template_id: str | None = None,
    script_text: str = "",
    audio_url: str | None = None,
    audio_path: str | None = None,
    product_image_url: str | None = None,
    title_text: str = "",
    cta_text: str = "",
    output_dir: str = "output/videos",
    poll_interval: int = 5,
    max_wait: int = 300,
) -> str | None:
    """
    Generate a YouTube Shorts video using Creatomate API.

    Supports two modes:
    1. Template-based: Pass a template_id and override text/media elements.
    2. Dynamic: Build video from scratch with text overlays and audio.

    Args:
        api_key: Creatomate API key.
        template_id: Creatomate template ID (optional for dynamic renders).
        script_text: Main script text for video overlay.
        audio_url: URL to voiceover audio (from ElevenLabs or hosted).
        audio_path: Local path to audio file (will be uploaded).
        product_image_url: Product image URL for background/overlay.
        title_text: Title text overlay.
        cta_text: Call-to-action text.
        output_dir: Directory to save the final video.
        poll_interval: Seconds between render status checks.
        max_wait: Maximum seconds to wait for render.

    Returns:
        Path to the generated video file, or None on failure.
    """
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    # Build render payload
    if template_id:
        payload = _build_template_payload(
            template_id, script_text, audio_url, product_image_url, title_text, cta_text
        )
    else:
        payload = _build_dynamic_payload(
            script_text, audio_url, product_image_url, title_text, cta_text
        )

    # If we have a local audio file but no URL, upload it first
    if audio_path and not audio_url and os.path.exists(audio_path):
        audio_url = _upload_audio(api_key, audio_path)
        if audio_url:
            payload = _inject_audio_url(payload, audio_url)

    try:
        # Start render
        response = requests.post(CREATOMATE_API_URL, headers=headers, json=[payload], timeout=30)
        response.raise_for_status()
        renders = response.json()

        if not renders:
            logger.error("Creatomate returned empty response")
            return None

        render_id = renders[0]["id"]
        logger.info("Render started: %s", render_id)

        # Poll for completion
        video_url = _poll_render(api_key, render_id, poll_interval, max_wait)
        if not video_url:
            return None

        # Download video
        return _download_video(video_url, output_dir, title_text)

    except requests.RequestException as e:
        logger.error("Creatomate render failed: %s", e)
        return None


def _build_template_payload(
    template_id: str,
    script_text: str,
    audio_url: str | None,
    product_image_url: str | None,
    title_text: str,
    cta_text: str,
) -> dict:
    """Build payload for template-based render."""
    modifications = {}

    if title_text:
        modifications["Title"] = title_text
    if script_text:
        modifications["Script"] = script_text
    if cta_text:
        modifications["CTA"] = cta_text
    if product_image_url:
        modifications["Product-Image"] = product_image_url
    if audio_url:
        modifications["Audio"] = audio_url

    return {
        "template_id": template_id,
        "modifications": modifications,
    }


def _build_dynamic_payload(
    script_text: str,
    audio_url: str | None,
    product_image_url: str | None,
    title_text: str,
    cta_text: str,
) -> dict:
    """Build payload for dynamic (no template) render — 9:16 vertical Shorts."""
    elements = []

    # Background
    if product_image_url:
        elements.append({
            "type": "image",
            "source": product_image_url,
            "width": "100%",
            "height": "100%",
            "fit": "cover",
        })
    else:
        elements.append({
            "type": "shape",
            "shape": "rectangle",
            "width": "100%",
            "height": "100%",
            "fill_color": "#1a1a2e",
        })

    # Title overlay
    if title_text:
        elements.append({
            "type": "text",
            "text": title_text,
            "y": "15%",
            "width": "90%",
            "x_alignment": "50%",
            "y_alignment": "50%",
            "font_family": "Cairo",
            "font_weight": "700",
            "font_size": "7.5 vmin",
            "fill_color": "#ffffff",
            "stroke_color": "#000000",
            "stroke_width": "0.3 vmin",
            "text_alignment": "center",
        })

    # Script text overlay
    if script_text:
        elements.append({
            "type": "text",
            "text": script_text,
            "y": "45%",
            "width": "85%",
            "x_alignment": "50%",
            "y_alignment": "50%",
            "font_family": "Cairo",
            "font_weight": "400",
            "font_size": "5 vmin",
            "fill_color": "#ffffff",
            "text_alignment": "center",
            "line_height": "140%",
        })

    # CTA overlay
    if cta_text:
        elements.append({
            "type": "text",
            "text": cta_text,
            "y": "80%",
            "width": "90%",
            "x_alignment": "50%",
            "y_alignment": "50%",
            "font_family": "Cairo",
            "font_weight": "700",
            "font_size": "6 vmin",
            "fill_color": "#FFD700",
            "text_alignment": "center",
        })

    # Audio
    if audio_url:
        elements.append({
            "type": "audio",
            "source": audio_url,
        })

    return {
        "output_format": "mp4",
        "width": 1080,
        "height": 1920,
        "duration": 30,
        "elements": elements,
    }


def _inject_audio_url(payload: dict, audio_url: str) -> dict:
    """Inject audio URL into an existing payload."""
    if "modifications" in payload:
        payload["modifications"]["Audio"] = audio_url
    elif "elements" in payload:
        payload["elements"].append({"type": "audio", "source": audio_url})
    return payload


def _upload_audio(api_key: str, audio_path: str) -> str | None:
    """Upload a local audio file to Creatomate and return its URL."""
    url = "https://api.creatomate.com/v1/uploads"
    headers = {"Authorization": f"Bearer {api_key}"}

    try:
        with open(audio_path, "rb") as f:
            response = requests.post(
                url, headers=headers, files={"file": f}, timeout=60
            )
        response.raise_for_status()
        result = response.json()
        return result.get("url")
    except requests.RequestException as e:
        logger.error("Audio upload to Creatomate failed: %s", e)
        return None


def _poll_render(
    api_key: str,
    render_id: str,
    poll_interval: int,
    max_wait: int,
) -> str | None:
    """Poll Creatomate render status until complete."""
    url = f"https://api.creatomate.com/v1/renders/{render_id}"
    headers = {"Authorization": f"Bearer {api_key}"}
    elapsed = 0

    while elapsed < max_wait:
        try:
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            data = response.json()
            status = data.get("status")

            if status == "succeeded":
                video_url = data.get("url")
                logger.info("Render complete: %s", video_url)
                return video_url
            elif status == "failed":
                logger.error("Render failed: %s", data.get("error_message", "unknown"))
                return None

            logger.info("Render status: %s (%ds elapsed)", status, elapsed)

        except requests.RequestException as e:
            logger.warning("Poll error: %s", e)

        time.sleep(poll_interval)
        elapsed += poll_interval

    logger.error("Render timed out after %ds", max_wait)
    return None


def _download_video(video_url: str, output_dir: str, title: str) -> str | None:
    """Download rendered video from Creatomate."""
    os.makedirs(output_dir, exist_ok=True)
    safe_title = "".join(c if c.isalnum() or c in " -_" else "" for c in title)[:50].strip()
    filename = f"{safe_title or 'short'}.mp4"
    filepath = os.path.join(output_dir, filename)

    try:
        response = requests.get(video_url, timeout=120)
        response.raise_for_status()
        with open(filepath, "wb") as f:
            f.write(response.content)
        logger.info("Video saved: %s (%.1f MB)", filepath, len(response.content) / (1024 * 1024))
        return filepath
    except requests.RequestException as e:
        logger.error("Video download failed: %s", e)
        return None

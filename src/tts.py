"""ElevenLabs Text-to-Speech integration for Arabic voiceover."""

import logging
import os

import requests

logger = logging.getLogger(__name__)


def generate_voiceover(
    text: str,
    api_key: str,
    voice_id: str = "pNInz6obpgDQGcFmaJgB",  # Arabic-compatible voice (Adam)
    model_id: str = "eleven_multilingual_v2",
    output_path: str = "output/audio/voiceover.mp3",
) -> str | None:
    """
    Generate Arabic voiceover audio using ElevenLabs API.

    Args:
        text: The script text to convert to speech.
        api_key: ElevenLabs API key.
        voice_id: ElevenLabs voice ID (default: Adam - multilingual).
        model_id: TTS model (eleven_multilingual_v2 supports Arabic).
        output_path: Where to save the MP3 file.

    Returns:
        Path to the generated audio file, or None on failure.
    """
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    headers = {
        "xi-api-key": api_key,
        "Content-Type": "application/json",
    }
    payload = {
        "text": text,
        "model_id": model_id,
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.75,
            "style": 0.4,
            "use_speaker_boost": True,
        },
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        response.raise_for_status()

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "wb") as f:
            f.write(response.content)

        logger.info("Voiceover saved: %s (%.1f KB)", output_path, len(response.content) / 1024)
        return output_path

    except requests.RequestException as e:
        logger.error("ElevenLabs TTS failed: %s", e)
        return None


def list_voices(api_key: str) -> list[dict]:
    """List available ElevenLabs voices."""
    url = "https://api.elevenlabs.io/v1/voices"
    headers = {"xi-api-key": api_key}

    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        voices = response.json().get("voices", [])
        return [{"id": v["voice_id"], "name": v["name"]} for v in voices]
    except requests.RequestException as e:
        logger.error("Failed to list voices: %s", e)
        return []

"""Content validation for Amazon affiliate automation."""

import re

# Placeholder list of prohibited words
PROHIBITED_WORDS = [
    "guaranteed",
    "miracle",
    "risk-free",
    "act now",
    "limited time only",
]


def validate_product(product) -> tuple[bool, str]:
    """Validate that a product has the required fields.

    Returns:
        (is_valid, reason) where reason describes any validation failure.
    """
    if not getattr(product, "asin", None):
        return False, "Product ASIN is empty"
    if not getattr(product, "title", None):
        return False, "Product title is empty"
    if getattr(product, "price", None) is None:
        return False, "Product price is missing"
    return True, "Valid"


def validate_content(content: str, max_length: int = 280) -> tuple[bool, str]:
    """Validate social media content text.

    Args:
        content: The text content to validate.
        max_length: Maximum allowed length (excluding hashtags).

    Returns:
        (is_valid, reason) where reason describes any validation failure.
    """
    if not content or not content.strip():
        return False, "Content text is empty"

    # Strip hashtags for length check
    text_without_hashtags = re.sub(r"#\S+", "", content).strip()
    if len(text_without_hashtags) > max_length:
        return False, f"Content text exceeds {max_length} characters (got {len(text_without_hashtags)})"

    # Check for prohibited words (case-insensitive)
    content_lower = content.lower()
    for word in PROHIBITED_WORDS:
        if word.lower() in content_lower:
            return False, f"Content contains prohibited word: '{word}'"

    return True, "Valid"


def validate_shorts_script(script) -> tuple[bool, str]:
    """Validate a YouTube Shorts script.

    Returns:
        (is_valid, reason) where reason describes any validation failure.
    """
    if not getattr(script, "hook", None) or not script.hook.strip():
        return False, "Script hook is empty"
    if not getattr(script, "body", None) or not script.body.strip():
        return False, "Script body is empty"
    if not getattr(script, "cta", None) or not script.cta.strip():
        return False, "Script CTA is empty"

    title = getattr(script, "title", "")
    if title and len(title) > 70:
        return False, f"Script title exceeds 70 characters (got {len(title)})"

    return True, "Valid"


def sanitize_text(text: str) -> str:
    """Sanitize text by removing problematic characters.

    - Strip leading/trailing whitespace
    - Remove excessive newlines (more than 2 consecutive)
    - Remove null bytes
    """
    if not text:
        return ""
    # Remove null bytes
    text = text.replace("\x00", "")
    # Collapse 3+ consecutive newlines into 2
    text = re.sub(r"\n{3,}", "\n\n", text)
    # Strip leading/trailing whitespace
    text = text.strip()
    return text

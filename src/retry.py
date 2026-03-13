"""Retry decorator with exponential backoff for API calls."""

import functools
import logging
import random
import time

import requests

logger = logging.getLogger(__name__)


def retry_with_backoff(
    max_retries: int = 3,
    base_delay: float = 2.0,
    max_delay: float = 30.0,
    exceptions: tuple = (requests.RequestException,),
):
    """Decorator that retries a function with exponential backoff.

    Args:
        max_retries: Maximum number of retry attempts.
        base_delay: Base delay in seconds for backoff calculation.
        max_delay: Maximum delay in seconds between retries.
        exceptions: Tuple of exception types to catch and retry on.
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_retries:
                        delay = min(base_delay * (2 ** attempt), max_delay)
                        jitter = random.uniform(0, 1)
                        total_delay = delay + jitter
                        logger.warning(
                            "Retry %d/%d for %s after %.1fs: %s",
                            attempt + 1,
                            max_retries,
                            func.__name__,
                            total_delay,
                            e,
                        )
                        time.sleep(total_delay)
            raise last_exception

        return wrapper

    return decorator

"""Twitter/X posting module."""

import logging
from typing import Optional

import tweepy

from src.utils import get_env_var

logger = logging.getLogger(__name__)


class TwitterPoster:
    """Handles posting content to Twitter/X."""

    MAX_TWEET_LENGTH = 280

    def __init__(
        self,
        api_key: str = "",
        api_secret: str = "",
        access_token: str = "",
        access_token_secret: str = "",
        bearer_token: str = "",
    ):
        self.api_key = api_key or get_env_var("TWITTER_API_KEY")
        self.api_secret = api_secret or get_env_var("TWITTER_API_SECRET")
        self.access_token = access_token or get_env_var("TWITTER_ACCESS_TOKEN")
        self.access_token_secret = access_token_secret or get_env_var("TWITTER_ACCESS_TOKEN_SECRET")
        self.bearer_token = bearer_token or get_env_var("TWITTER_BEARER_TOKEN")
        self._client = None
        self._api = None

    @property
    def client(self) -> tweepy.Client:
        """Get or create the Tweepy v2 client."""
        if self._client is None:
            self._client = tweepy.Client(
                bearer_token=self.bearer_token,
                consumer_key=self.api_key,
                consumer_secret=self.api_secret,
                access_token=self.access_token,
                access_token_secret=self.access_token_secret,
            )
        return self._client

    @property
    def api(self) -> tweepy.API:
        """Get or create the Tweepy v1.1 API (for media uploads)."""
        if self._api is None:
            auth = tweepy.OAuth1UserHandler(
                self.api_key,
                self.api_secret,
                self.access_token,
                self.access_token_secret,
            )
            self._api = tweepy.API(auth)
        return self._api

    def is_configured(self) -> bool:
        """Check if Twitter credentials are configured."""
        return all([
            self.api_key,
            self.api_secret,
            self.access_token,
            self.access_token_secret,
        ])

    def post_tweet(self, text: str, image_path: str = "") -> Optional[dict]:
        """Post a tweet with optional image."""
        if not self.is_configured():
            logger.error("Twitter credentials not configured")
            return None

        if len(text) > self.MAX_TWEET_LENGTH:
            text = text[: self.MAX_TWEET_LENGTH - 3] + "..."
            logger.warning("Tweet truncated to 280 characters")

        try:
            media_ids = None
            if image_path:
                media = self.api.media_upload(image_path)
                media_ids = [media.media_id]

            response = self.client.create_tweet(text=text, media_ids=media_ids)
            tweet_id = response.data.get("id") if response.data else None
            logger.info(f"Tweet posted successfully: {tweet_id}")
            return {"id": tweet_id, "text": text, "platform": "twitter"}
        except tweepy.TweepyException as e:
            logger.error(f"Failed to post tweet: {e}")
            return None

    def post_thread(self, tweets: list[str]) -> list[dict]:
        """Post a thread of tweets."""
        results = []
        previous_id = None

        for tweet_text in tweets:
            try:
                if len(tweet_text) > self.MAX_TWEET_LENGTH:
                    tweet_text = tweet_text[: self.MAX_TWEET_LENGTH - 3] + "..."

                response = self.client.create_tweet(
                    text=tweet_text,
                    in_reply_to_tweet_id=previous_id,
                )
                tweet_id = response.data.get("id") if response.data else None
                previous_id = tweet_id
                results.append({"id": tweet_id, "text": tweet_text})
                logger.info(f"Thread tweet posted: {tweet_id}")
            except tweepy.TweepyException as e:
                logger.error(f"Failed to post thread tweet: {e}")
                break

        return results

    def split_for_thread(self, text: str) -> list[str]:
        """Split long text into thread-sized chunks."""
        if len(text) <= self.MAX_TWEET_LENGTH:
            return [text]

        chunks = []
        words = text.split()
        current = ""

        for word in words:
            test = f"{current} {word}".strip()
            if len(test) <= self.MAX_TWEET_LENGTH - 6:  # Reserve space for " (X/Y)"
                current = test
            else:
                chunks.append(current)
                current = word

        if current:
            chunks.append(current)

        total = len(chunks)
        return [f"{chunk} ({i + 1}/{total})" for i, chunk in enumerate(chunks)]

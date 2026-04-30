"""
telegram_sender.py — Handles all outgoing Telegram API calls.

Two public functions:
  - send_photo(image_url, caption)  → sends a photo with text caption
  - send_message(text)              → sends a plain text message (fallback)
"""

import os
import logging
import httpx

logger = logging.getLogger(__name__)

# ── Read config from environment ──────────────────────────────────────────────
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

# Base URL for all Telegram Bot API calls
TELEGRAM_API_BASE = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"


def _check_config() -> bool:
    """Verify that the required Telegram credentials are present."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        logger.error(
            "TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID is missing from environment. "
            "Check your .env file."
        )
        return False
    return True


async def send_photo(image_url: str, caption: str) -> bool:
    """
    Send a photo to Telegram using the sendPhoto API method.

    The image is passed as a URL (TradingView chart snapshot link).
    The formatted alert text is attached as the caption.

    Returns True on success, False on failure.
    """
    if not _check_config():
        return False

    endpoint = f"{TELEGRAM_API_BASE}/sendPhoto"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "photo": image_url,
        "caption": caption,
        "parse_mode": "Markdown",
    }

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.post(endpoint, json=payload)
            response.raise_for_status()
            logger.info("Photo sent to Telegram successfully.")
            return True
    except httpx.HTTPStatusError as http_error:
        logger.error(f"Telegram sendPhoto HTTP error: {http_error.response.text}")
        return False
    except Exception as error:
        logger.error(f"Telegram sendPhoto unexpected error: {error}")
        return False


async def send_message(text: str) -> bool:
    """
    Send a plain text (Markdown-formatted) message to Telegram.

    Used as a fallback when no chart screenshot is available,
    or when the sendPhoto call fails.

    Returns True on success, False on failure.
    """
    if not _check_config():
        return False

    endpoint = f"{TELEGRAM_API_BASE}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "Markdown",
    }

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.post(endpoint, json=payload)
            response.raise_for_status()
            logger.info("Text message sent to Telegram successfully.")
            return True
    except httpx.HTTPStatusError as http_error:
        logger.error(f"Telegram sendMessage HTTP error: {http_error.response.text}")
        return False
    except Exception as error:
        logger.error(f"Telegram sendMessage unexpected error: {error}")
        return False

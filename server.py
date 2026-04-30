"""
server.py — Main FastAPI webhook server for TradingView → Telegram alerts.

Receives POST requests from TradingView, validates the secret token,
parses the JSON payload, builds the formatted message, fetches a chart
screenshot, and sends everything to Telegram.
"""

import os
import logging
from fastapi import FastAPI, Request, HTTPException, Query
from dotenv import load_dotenv

from template_engine import render_template
from chart_capture import get_chart_image_url
from telegram_sender import send_photo, send_message

# ── Load environment variables from .env ──────────────────────────────────────
load_dotenv()

WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "")
PORT = int(os.getenv("PORT", 8000))

# ── Logging setup ─────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

# ── FastAPI app ───────────────────────────────────────────────────────────────
app = FastAPI(title="TradingView → Telegram Alert Bot")


@app.get("/")
async def health_check():
    """Simple health-check endpoint so Railway/uptime monitors can ping the server."""
    return {"status": "ok", "message": "TradingView Telegram Bot is running."}


@app.post("/webhook")
async def receive_alert(
    request: Request,
    token: str = Query(default=""),
):
    """
    Main webhook endpoint.

    TradingView sends a POST to /webhook?token=YOUR_SECRET.
    1. Validates the secret token.
    2. Parses the JSON payload.
    3. Renders the Telegram message using the matching template.
    4. Tries to fetch a chart screenshot URL.
    5. Sends the photo (or text-only fallback) to Telegram.
    """

    # ── 1. Token validation ───────────────────────────────────────────────────
    if not WEBHOOK_SECRET:
        logger.warning("WEBHOOK_SECRET is not set — running without token validation!")
    elif token != WEBHOOK_SECRET:
        logger.warning("Rejected request: invalid or missing token.")
        raise HTTPException(status_code=403, detail="Invalid or missing token.")

    # ── 2. Parse JSON body ────────────────────────────────────────────────────
    try:
        payload: dict = await request.json()
    except Exception as parse_error:
        logger.error(f"Failed to parse JSON body: {parse_error}")
        raise HTTPException(status_code=400, detail="Invalid JSON body.")

    logger.info(f"Received alert payload: {payload}")

    # ── 3. Render the message from templates.json ─────────────────────────────
    formatted_message = render_template(payload)

    # ── 4. Attempt to get chart screenshot URL ────────────────────────────────
    symbol = payload.get("symbol", "")
    interval = payload.get("interval", "")
    chart_url = get_chart_image_url(symbol=symbol, interval=interval)

    # ── 5. Send to Telegram ───────────────────────────────────────────────────
    if chart_url:
        success = await send_photo(image_url=chart_url, caption=formatted_message)
        if not success:
            logger.warning("Photo send failed — falling back to text-only message.")
            await send_message(text=formatted_message)
    else:
        logger.info("No chart URL available — sending text-only message.")
        await send_message(text=formatted_message)

    return {"status": "ok"}

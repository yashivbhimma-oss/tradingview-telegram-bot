"""
server.py — Main FastAPI webhook server for TradingView → Telegram alerts.
"""

import os
import json
import logging
from fastapi import FastAPI, Request, HTTPException, Query
from dotenv import load_dotenv

from template_engine import render_template
from chart_capture import get_chart_image_url
from telegram_sender import send_photo, send_message

load_dotenv()

WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "")
PORT = int(os.getenv("PORT", 8000))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(title="TradingView → Telegram Alert Bot")


@app.get("/")
async def health_check():
    return {"status": "ok", "message": "TradingView Telegram Bot is running."}


@app.post("/webhook")
async def receive_alert(
    request: Request,
    token: str = Query(default=""),
):
    if not WEBHOOK_SECRET:
        logger.warning("WEBHOOK_SECRET is not set!")
    elif token != WEBHOOK_SECRET:
        logger.warning("Rejected request: invalid or missing token.")
        raise HTTPException(status_code=403, detail="Invalid or missing token.")

    try:
        body = await request.body()
        text = body.decode("utf-8").strip()

        try:
            payload = json.loads(text)
            formatted_message = render_template(payload)
            symbol = payload.get("symbol", "")
            interval = payload.get("interval", "")
        except json.JSONDecodeError:
            formatted_message = f"🔔 *RYZE ALERT*\n\n{text}"
            symbol = ""
            interval = ""

    except Exception as e:
        logger.error(f"Failed to read body: {e}")
        raise HTTPException(status_code=400, detail="Could not read request body.")

    logger.info(f"Message: {formatted_message}")

    chart_url = get_chart_image_url(symbol=symbol, interval=interval)

    if chart_url:
        success = await send_photo(image_url=chart_url, caption=formatted_message)
        if not success:
            await send_message(text=formatted_message)
    else:
        await send_message(text=formatted_message)

    return {"status": "ok"}
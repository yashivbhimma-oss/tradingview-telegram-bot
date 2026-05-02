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

# Stores the latest market conditions received from the Market Conditions indicator
latest_conditions = {
    "trend": "—",
    "strength": "—",
    "momentum": "—",
    "price_action": "—",
    "bias": "—"
}


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

            # If this is a market conditions update — store it and return
            if payload.get("type") == "conditions":
                latest_conditions["trend"]        = payload.get("trend", "—")
                latest_conditions["strength"]     = payload.get("strength", "—")
                latest_conditions["momentum"]     = payload.get("momentum", "—")
                latest_conditions["price_action"] = payload.get("price_action", "—")
                latest_conditions["bias"]         = payload.get("bias", "—")
                logger.info(f"Market conditions updated: {latest_conditions}")
                return {"status": "ok", "updated": "conditions"}

            # Otherwise it's a trade alert — render template
            formatted_message = render_template(payload)
            symbol   = payload.get("symbol", "NQ1!")
            interval = payload.get("interval", "1")

        except json.JSONDecodeError:
            # Plain text Ryze alert — build message with stored market conditions
            symbol   = "NQ1!"
            interval = "1"
            formatted_message = (
                f"🔔 *RYZE ALERT*\n\n"
                f"{text}\n\n"
                f"📊 *Market Conditions:*\n"
                f"Trend: {latest_conditions['trend']}  |  Strength: {latest_conditions['strength']}\n"
                f"Momentum: {latest_conditions['momentum']}\n"
                f"Price Action: {latest_conditions['price_action']}\n"
                f"Overall Bias: {latest_conditions['bias']}"
            )

    except Exception as e:
        logger.error(f"Failed to read body: {e}")
        raise HTTPException(status_code=400, detail="Could not read request body.")

    logger.info(f"Sending message: {formatted_message}")

    # Send 1m chart
    chart_url_1m = get_chart_image_url(symbol=symbol, interval="1")
    # Send 5m chart
    chart_url_5m = get_chart_image_url(symbol=symbol, interval="5")

    if chart_url_1m:
        success = await send_photo(image_url=chart_url_1m, caption=formatted_message)
        if not success:
            await send_message(text=formatted_message)
    else:
        await send_message(text=formatted_message)

    # Send 5m chart as a second photo (no caption)
    if chart_url_5m:
        await send_photo(image_url=chart_url_5m, caption="5m chart")

    return {"status": "ok"}
"""
server.py — Main FastAPI webhook server for TradingView → Telegram alerts.
"""

import os
import re
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

# Stores the latest market conditions
latest_conditions = {
    "trend": "—",
    "strength": "—",
    "momentum": "—",
    "price_action": "—",
    "bias": "—"
}

def extract_symbol_and_interval(text: str):
    """
    Try to extract symbol and interval from plain text Ryze alert.
    Example: 'Bear RDM — NQ1!, 1m' → symbol='NQ1!', interval='1'
    """
    known_symbols = ["NQ1!", "ES1!", "MNQ1!", "MES1!", "BTCUSDT", "EURUSD"]
    symbol = "NQ1!"
    interval = "1"

    for s in known_symbols:
        if s in text:
            symbol = s
            break

    match = re.search(r'(\d+)m', text.lower())
    if match:
        interval = match.group(1)

    return symbol, interval


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

            # Market conditions update — store silently, no Telegram message
            if payload.get("type") == "conditions":
                latest_conditions["trend"]        = payload.get("trend", "—")
                latest_conditions["strength"]     = payload.get("strength", "—")
                latest_conditions["momentum"]     = payload.get("momentum", "—")
                latest_conditions["price_action"] = payload.get("price_action", "—")
                latest_conditions["bias"]         = payload.get("bias", "—")
                logger.info(f"Market conditions updated: {latest_conditions}")
                return {"status": "ok", "updated": "conditions"}

            # JSON trade alert
            formatted_message = render_template(payload)
            symbol   = payload.get("symbol", "NQ1!")
            interval = payload.get("interval", "1")

        except json.JSONDecodeError:
            # Plain text Ryze alert
            symbol, interval = extract_symbol_and_interval(text)
            chart_link = f"https://www.tradingview.com/chart/?symbol={symbol}"
            formatted_message = (
                f"🔔 *RYZE ALERT*\n\n"
                f"{text}\n\n"
                f"📊 *Market Conditions:*\n"
                f"Trend: {latest_conditions['trend']}  |  Strength: {latest_conditions['strength']}\n"
                f"Momentum: {latest_conditions['momentum']}\n"
                f"Price Action: {latest_conditions['price_action']}\n"
                f"Overall Bias: {latest_conditions['bias']}\n\n"
                f"📈 [Open Chart]({chart_link})"
            )

    except Exception as e:
        logger.error(f"Failed to read body: {e}")
        raise HTTPException(status_code=400, detail="Could not read request body.")

    logger.info(f"Symbol: {symbol} | Interval: {interval}")

    await send_message(text=formatted_message)

    return {"status": "ok"}
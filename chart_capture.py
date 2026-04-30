"""
chart_capture.py — Builds a TradingView chart snapshot URL for a given symbol + interval.

TradingView provides a public mini-chart image endpoint that can be used
to attach a chart screenshot to Telegram messages without needing a browser.

The URL format used here is TradingView's widget/chart snapshot endpoint.
It's publicly accessible and does not require authentication.

Supported intervals (TradingView codes):
  1, 3, 5, 15, 30, 60, 120, 240 = minutes
  D  = Daily
  W  = Weekly
  M  = Monthly
"""

import logging
from urllib.parse import quote

logger = logging.getLogger(__name__)

# TradingView mini-chart snapshot base URL
# Docs / reference: https://www.tradingview.com/widget/advanced-chart/
TRADINGVIEW_SNAPSHOT_BASE = "https://charts.tradingview.com/chart-image.png"


def _normalise_interval(raw_interval: str) -> str:
    """
    Convert common interval strings to TradingView's expected format.

    TradingView uses plain numbers for minutes (e.g. "30" for 30-minute)
    and letters for higher timeframes.

    Examples of input normalisation:
      "30m" → "30"
      "1h"  → "60"
      "4h"  → "240"
      "1d"  → "D"
      "1D"  → "D"
      "30"  → "30"   (already correct, passed through)
    """
    mapping = {
        "1m": "1", "3m": "3", "5m": "5", "15m": "15",
        "30m": "30", "1h": "60", "2h": "120", "4h": "240",
        "1d": "D", "d": "D", "1w": "W", "w": "W",
        "1M": "M", "M": "M",
    }
    normalised = mapping.get(raw_interval.lower(), raw_interval)
    return normalised


def get_chart_image_url(symbol: str, interval: str) -> str | None:
    """
    Build and return a TradingView chart snapshot image URL.

    Parameters:
        symbol   — e.g. "NQ1!", "ES1!", "BTCUSDT"
        interval — e.g. "30", "60", "D"

    Returns a URL string on success, or None if the symbol/interval are missing.
    The caller should treat None as "no chart available" and fall back to text-only.
    """
    if not symbol:
        logger.warning("No symbol provided — skipping chart screenshot.")
        return None

    if not interval:
        logger.warning("No interval provided — defaulting to 30-minute chart.")
        interval = "30"

    tv_interval = _normalise_interval(interval)
    encoded_symbol = quote(symbol, safe="")  # URL-encode special chars like !

    # Construct the chart image URL
    # Parameters:
    #   symbol   — the TradingView ticker symbol
    #   interval — candle interval in TV format
    #   theme    — "dark" or "light"
    #   style    — chart type: 1=candles, 2=bars, 3=line
    #   width/height — image dimensions in pixels
    chart_url = (
        f"{TRADINGVIEW_SNAPSHOT_BASE}"
        f"?symbol={encoded_symbol}"
        f"&interval={tv_interval}"
        f"&theme=dark"
        f"&style=1"
        f"&width=800"
        f"&height=450"
    )

    logger.info(f"Chart image URL: {chart_url}")
    return chart_url

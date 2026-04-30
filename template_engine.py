"""
template_engine.py — Loads templates.json and fills in {{variable}} placeholders.

How it works:
  1. Reads the `template` key from the incoming payload.
  2. Looks up that template name in templates.json.
  3. Replaces every {{variable}} in the message string with the matching
     value from the payload.
  4. Missing variables are replaced with an empty string (no crash).
  5. Falls back to the "default" template if the named template is not found.
"""

import json
import re
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# Path to the templates file (same directory as this script)
TEMPLATES_FILE = Path(__file__).parent / "templates.json"

# Cache the loaded templates so we don't re-read the file on every alert
_template_cache: dict | None = None


def _load_templates() -> dict:
    """
    Load templates.json from disk.

    Uses a simple in-memory cache so the file is only read once per process.
    Restart the server to pick up changes to templates.json.
    """
    global _template_cache
    if _template_cache is not None:
        return _template_cache

    try:
        with open(TEMPLATES_FILE, "r", encoding="utf-8") as file_handle:
            data = json.load(file_handle)
            _template_cache = data
            logger.info(f"Loaded {len(data)} templates from {TEMPLATES_FILE}")
            return _template_cache
    except FileNotFoundError:
        logger.error(f"templates.json not found at {TEMPLATES_FILE}")
        return {}
    except json.JSONDecodeError as json_error:
        logger.error(f"templates.json is not valid JSON: {json_error}")
        return {}


def _fill_placeholders(message_template: str, payload: dict) -> str:
    """
    Replace every {{variable}} in the template string with the
    corresponding value from the payload dict.

    If a key is missing from the payload, it's replaced with an empty string.
    """
    def replace_match(match: re.Match) -> str:
        variable_name = match.group(1).strip()
        # Return the value from payload, or empty string if missing
        return str(payload.get(variable_name, ""))

    # Match anything inside {{ }} — allows spaces around the variable name
    filled = re.sub(r"\{\{\s*(\w+)\s*\}\}", replace_match, message_template)
    return filled


def render_template(payload: dict) -> str:
    """
    Public function called by server.py.

    Given the full alert payload, finds the right template and returns
    the fully rendered message string ready to send to Telegram.
    """
    templates = _load_templates()

    # Which template did TradingView request?
    template_name = payload.get("template", "default")

    # Look up the template; fall back to "default" if not found
    template_data = templates.get(template_name)
    if template_data is None:
        logger.warning(
            f"Template '{template_name}' not found in templates.json. "
            "Falling back to 'default'."
        )
        template_data = templates.get("default", {})

    if not template_data:
        logger.error("No 'default' template found in templates.json. Sending raw payload.")
        return f"📊 *ALERT*\n\n```{json.dumps(payload, indent=2)}```"

    # Get the raw message string and fill in the variables
    raw_message: str = template_data.get("message", "")
    rendered_message = _fill_placeholders(raw_message, payload)

    logger.info(f"Rendered template: '{template_name}'")
    return rendered_message

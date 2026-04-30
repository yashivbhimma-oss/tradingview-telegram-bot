# TradingView → Telegram Alert Bot

Receives TradingView webhook alerts and forwards beautifully formatted messages + chart screenshots to a Telegram bot — in real time.

---

## File Structure

```
tradingview-telegram-bot/
├── server.py           ← FastAPI webhook server (entry point)
├── telegram_sender.py  ← All Telegram API calls
├── template_engine.py  ← Loads templates.json, fills {{variables}}
├── chart_capture.py    ← Builds TradingView chart screenshot URL
├── templates.json      ← All message templates (edit freely)
├── .env                ← Your secrets (create from .env.example)
├── .env.example        ← Template for .env
├── requirements.txt    ← Python dependencies
└── README.md           ← This file
```

---

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
```

Open `.env` and fill in:

| Variable | Description |
|---|---|
| `TELEGRAM_BOT_TOKEN` | Token from @BotFather |
| `TELEGRAM_CHAT_ID` | Chat/channel ID where alerts go |
| `WEBHOOK_SECRET` | A random secret string for URL auth |
| `PORT` | Server port (default: 8000) |

**Getting your Telegram Chat ID:**
1. Message your bot
2. Visit: `https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates`
3. Find `"chat":{"id": XXXXX}` — that's your Chat ID

### 3. Run Locally

```bash
uvicorn server:app --host 0.0.0.0 --port 8000 --reload
```

Your webhook URL will be: `http://localhost:8000/webhook?token=YOUR_SECRET`

For local testing with TradingView, use [ngrok](https://ngrok.com) to expose your port:
```bash
ngrok http 8000
```

---

## Deploy to Railway (Free Hosting)

1. Push this folder to a GitHub repo
2. Go to [railway.app](https://railway.app) → New Project → Deploy from GitHub
3. Select your repo
4. In the **Variables** tab, add all values from your `.env`
5. Railway gives you a public URL like: `https://yourapp.up.railway.app`

Your live webhook URL: `https://yourapp.up.railway.app/webhook?token=YOUR_SECRET`

---

## Setting Up TradingView Alerts

1. Open TradingView and find your indicator on the chart
2. Right-click the indicator → **Add Alert**
3. Set the trigger condition
4. Scroll to **Notifications** → enable **Webhook URL**
5. Paste your webhook URL with the token
6. In the **Message** box, paste your JSON payload:

**NQ Long example:**
```json
{
  "template": "NQ_long",
  "symbol": "NQ1!",
  "interval": "30",
  "entry": "{{close}}",
  "stop": "21440",
  "target": "21480",
  "rr": "1.5",
  "risk": "16",
  "timeframe": "30M",
  "confluence": "2",
  "notes": "+SMT divergence | +IFVG fill"
}
```

**ES Scalp example:**
```json
{
  "template": "ES_scalp",
  "symbol": "ES1!",
  "interval": "5",
  "entry": "{{close}}",
  "stop": "5420",
  "target": "5435",
  "rr": "1.5",
  "notes": "breakout above VWAP"
}
```

> The `"template"` value must exactly match a key in `templates.json`.
> TradingView variables like `{{close}}`, `{{high}}`, `{{low}}`, `{{volume}}`, `{{time}}` are automatically filled by TradingView before sending.

---

## Adding or Editing Templates

All templates live in `templates.json`. To add a new one:

```json
"BTC_long": {
  "emoji": "🟠",
  "message": "🟠 *BTC LONG*\n\n📍 Entry: {{entry}}\n🛑 Stop: {{stop}}\n🎯 Target: {{target}}\n📊 R:R: {{rr}}\n\n📝 {{notes}}"
}
```

Then push to GitHub — Railway auto-redeploys. No server restart needed.

### Modifying Templates with AI

Paste the relevant file into Claude and describe your change in plain English:

| What you want | What to say |
|---|---|
| New template | *"Add a template called 'MNQ_long' showing entry, stop, target, RR, and notes"* |
| Change format | *"Update NQ_long to show the daily bias at the top in bold"* |
| Remove a field | *"Remove the confluence score from all templates"* |
| Change emoji | *"Make NQ_short use ❌ instead of 🔴"* |
| Add a field | *"Add a 'session' field (e.g. London/NY) to the ES_scalp template"* |

---

## Troubleshooting

| Problem | Fix |
|---|---|
| No Telegram message received | Check `?token=` matches `WEBHOOK_SECRET` in `.env` |
| "Template not found" warning in logs | Template name in TradingView JSON must match key in `templates.json` exactly |
| No chart screenshot in message | Ensure `symbol` and `interval` are in the payload; chart URL is constructed from these |
| `{{close}}` shows as blank | Make sure TradingView alert message uses `{{close}}` (double braces, TradingView fills this) |
| 403 Forbidden | Wrong or missing `?token=` in your webhook URL |
| 400 Bad Request | The alert message in TradingView is not valid JSON |

---

## How It Works (Architecture)

```
TradingView Alert fires
        │
        ▼
POST /webhook?token=SECRET
        │
   server.py validates token
        │
   Parses JSON payload
        │
   template_engine.py renders message
        │
   chart_capture.py builds screenshot URL
        │
   telegram_sender.py sends photo + caption
        │
        ▼
   Telegram message received ✅
```

---

## License

MIT — use freely, modify as needed.

import os
import requests
import json
from telegram.ext import Updater, CommandHandler, CallbackContext
from telegram import Update

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

MARKETS_URL = "https://gamma-api.polymarket.com/markets?active=true&closed=false&limit=100"
POLL_INTERVAL = 30

subscribers = set()
last_prices = {}


def fetch_markets():
    try:
        r = requests.get(MARKETS_URL, timeout=10)
        data = r.json()
        if isinstance(data, dict) and "markets" in data:
            return data["markets"]
        return data
    except:
        return []


def parse_prices(raw):
    try:
        if isinstance(raw, str):
            return json.loads(raw)
        return raw
    except:
        return []


def build_url(m):
    slug = m.get("slug")
    if slug:
        return f"https://polymarket.com/market/{slug}"
    return "https://polymarket.com"


def detect_alerts(markets):
    alerts = []
    for m in markets:
        id_ = m.get("id")
        price = m.get("prices", [None])[0]

        if id_ not in last_prices:
            last_prices[id_] = price
            continue

        old = last_prices[id_]
        if old is not None and price is not None:
            change = abs(price - old)
            if change >= 0.05:
                alerts.append((m.get("question", "Market"), price, old, build_url(m)))

        last_prices[id_] = price

    return alerts


def broadcast(context: CallbackContext):
    markets = fetch_markets()
    if not markets:
        return

    alerts = detect_alerts(markets)
    if not alerts:
        return

    for sub in list(subscribers):
        for q, price, old, url in alerts:
            text = f"⚡ Update\n{q}\nOld: {old}\nNew: {price}\n{url}"
            context.bot.send_message(sub, text)


def cmd_start(update: Update, context: CallbackContext):
    subscribers.add(update.effective_chat.id)
    update.message.reply_text("Subscribed. You'll get alerts.")


def cmd_stop(update: Update, context: CallbackContext):
    subscribers.discard(update.effective_chat.id)
    update.message.reply_text("Unsubscribed.")


def start_bot():
    updater = Updater(TELEGRAM_BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", cmd_start))
    dp.add_handler(CommandHandler("stop", cmd_stop))

    # если job_queue отсутствует - создаём вручную
    if updater.job_queue is None:
        from telegram.ext import JobQueue
        updater.job_queue = JobQueue()
        updater.job_queue.set_dispatcher(dp)
        updater.job_queue.run_jobs()

    updater.job_queue.run_repeating(broadcast, interval=POLL_INTERVAL, first=10)
    updater.start_polling()
    updater.idle()

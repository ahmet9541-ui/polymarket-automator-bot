import logging
import os
from typing import Set

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
)

from ideas import fake_news_idea, get_latest_ideas, push_new_idea

logger = logging.getLogger(__name__)

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

subscribers: Set[int] = set()


def build_app():
    if not TELEGRAM_BOT_TOKEN:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is not set")

    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("stop", cmd_stop))
    app.add_handler(CommandHandler("ideas", cmd_ideas))

    job_queue = app.job_queue
    job_queue.run_repeating(job_broadcast_idea, interval=600, first=30)

    return app


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    subscribers.add(chat_id)
    await update.message.reply_text(
        "✅ Subscribed to Market Prediction Automator ideas.\n"
        "Use /ideas to get the latest ideas or /stop to unsubscribe."
    )


async def cmd_stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id in subscribers:
        subscribers.remove(chat_id)
        await update.message.reply_text("You are unsubscribed.")
    else:
        await update.message.reply_text("You are not subscribed yet.")


async def cmd_ideas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ideas = get_latest_ideas(limit=5)
    if not ideas:
        await update.message.reply_text("No fresh ideas yet, try again later.")
        return

    txt_parts = []
    for i, idea in enumerate(ideas, start=1):
        txt_parts.append(format_idea(idea, index=i))

    await update.message.reply_text(
        "\n\n".join(txt_parts),
        disable_web_page_preview=True,
        parse_mode="Markdown",
    )


def format_idea(idea: dict, index: int | None = None) -> str:
    prefix = f"{index}. " if index is not None else ""
    q = idea.get("question", "Untitled market")
    expiry = idea.get("expiry", "N/A")
    category = idea.get("category", "General")
    sources = idea.get("source_links", [])

    lines = [
        f"{prefix}*{q}*",
        f"Category: {category}",
        f"Expiry: {expiry}",
    ]
    if sources:
        lines.append("Sources:")
        for url in sources:
            lines.append(f"- {url}")

    return "\n".join(lines)


async def job_broadcast_idea(context: ContextTypes.DEFAULT_TYPE):
    if not subscribers:
        return

    idea = fake_news_idea()
    push_new_idea(idea)
    text = format_idea(idea)

    for chat_id in list(subscribers):
        try:
            await context.bot.send_message(
                chat_id=chat_id,
                text=text,
                disable_web_page_preview=True,
                parse_mode="Markdown",
            )
        except Exception as e:
            logger.error("Failed to send idea to %s: %s", chat_id, e)

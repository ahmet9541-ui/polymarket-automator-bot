import os
from telegram.ext import Updater, CommandHandler, CallbackContext
from telegram import Update
from ideas import generate_market_idea

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# интервал между авто-идеями (в секундах)
POLL_INTERVAL = int(os.getenv("IDEA_INTERVAL", "3600"))  # по умолчанию 1 час

subscribers = set()


def format_idea_text(idea: dict) -> str:
    title = idea["title"]
    category = idea["category"]
    resolution = idea["resolution"]
    notes = idea.get("notes", "")

    text = (
        "🧠 New market idea\n\n"
        f"Category: {category}\n"
        f"Title: {title}\n\n"
        f"Resolution criteria:\n{resolution}\n"
    )
    if notes:
        text += f"\nNotes: {notes}\n"

    text += (
        "\nYou can use this as a draft when creating a new market on Polymarket."
    )
    return text


def send_idea_to_chat(chat_id: int, context: CallbackContext):
    idea = generate_market_idea()
    text = format_idea_text(idea)
    context.bot.send_message(chat_id, text)


def broadcast(context: CallbackContext):
    # периодическая рассылка идей всем подписчикам
    if not subscribers:
        return
    for chat_id in list(subscribers):
        send_idea_to_chat(chat_id, context)


def cmd_start(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    subscribers.add(chat_id)
    update.message.reply_text(
        "You are subscribed to market ideas.\n"
        "I'll send you new Polymarket-style markets periodically.\n\n"
        "Use /idea to get one immediately, /stop to unsubscribe."
    )


def cmd_stop(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    subscribers.discard(chat_id)
    update.message.reply_text("You are unsubscribed from automatic ideas.")


def cmd_idea(update: Update, context: CallbackContext):
    # мгновенная идея по запросу
    send_idea_to_chat(update.effective_chat.id, context)


def start_bot():
    updater = Updater(TELEGRAM_BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", cmd_start))
    dp.add_handler(CommandHandler("stop", cmd_stop))
    dp.add_handler(CommandHandler("idea", cmd_idea))

    # настройка JobQueue (как мы делали раньше)
    if updater.job_queue is None:
        from telegram.ext import JobQueue
        updater.job_queue = JobQueue()
        updater.job_queue.set_dispatcher(dp)
        updater.job_queue.run_jobs()

    # периодическая рассылка идей
    updater.job_queue.run_repeating(broadcast, interval=POLL_INTERVAL, first=30)

    updater.start_polling()
    updater.idle()

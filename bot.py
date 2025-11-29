import os
from io import BytesIO

from telegram.ext import Updater, CommandHandler, CallbackContext
from telegram import Update
from PIL import Image, ImageDraw, ImageFont

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

    text += "\nYou can use this as a draft when creating a new market on Polymarket."
    return text


def generate_cover_image(idea: dict) -> BytesIO:
    title = idea["title"]
    category = idea["category"]

    width, height = 1024, 576
    img = Image.new("RGB", (width, height), color=(10, 12, 20))
    draw = ImageDraw.Draw(img)

    if "Crypto" in category:
        accent = (40, 160, 255)
    elif "Politics" in category:
        accent = (180, 90, 255)
    elif "Macro" in category:
        accent = (0, 200, 140)
    elif "News" in category:
        accent = (255, 160, 60)
    else:
        accent = (200, 200, 200)

    draw.rectangle([0, 0, width, height // 3], fill=accent)

    font_title = ImageFont.load_default()
    max_width = width - 80
    words = title.split()
    lines = []
    current = ""
    for w in words:
        test = (current + " " + w).strip()
        tw, th = draw.textsize(test, font=font_title)
        if tw <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            current = w
    if current:
        lines.append(current)

    y = height // 3 + 40
    for line in lines[:4]:
        tw, th = draw.textsize(line, font=font_title)
        x = (width - tw) // 2
        draw.text((x, y), line, font=font_title, fill=(255, 255, 255))
        y += th + 10

    cat_text = category.upper()
    ct_w, ct_h = draw.textsize(cat_text, font=font_title)
    draw.text((40, height - ct_h - 40), cat_text, font=font_title, fill=accent)

    buf = BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf


def send_idea_to_chat(chat_id: int, context: CallbackContext):
    idea = generate_market_idea()
    text = format_idea_text(idea)
    image_buf = generate_cover_image(idea)

    context.bot.send_photo(
        chat_id=chat_id,
        photo=image_buf,
        caption=text,
    )


def broadcast(context: CallbackContext):
    if not subscribers:
        return
    for chat_id in list(subscribers):
        send_idea_to_chat(chat_id, context)


def cmd_start(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    subscribers.add(chat_id)
    update.message.reply_text(
        "You are subscribed to market ideas.\n"
        "I'll send you new data-driven Polymarket-style markets periodically.\n\n"
        "Use /idea to get one immediately, /stop to unsubscribe."
    )


def cmd_stop(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    subscribers.discard(chat_id)
    update.message.reply_text("You are unsubscribed from automatic ideas.")


def cmd_idea(update: Update, context: CallbackContext):
    send_idea_to_chat(update.effective_chat.id, context)


def start_bot():
    updater = Updater(TELEGRAM_BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", cmd_start))
    dp.add_handler(CommandHandler("stop", cmd_stop))
    dp.add_handler(CommandHandler("idea", cmd_idea))

    # страховка: если job_queue нет, создаём
    if updater.job_queue is None:
        from telegram.ext import JobQueue
        updater.job_queue = JobQueue()
        updater.job_queue.set_dispatcher(dp)
        updater.job_queue.run_jobs()

    updater.job_queue.run_repeating(broadcast, interval=POLL_INTERVAL, first=30)

    updater.start_polling()
    updater.idle()

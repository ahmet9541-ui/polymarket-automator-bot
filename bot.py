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
    img = Image.new("RGB", (width, height), color=(16, 18, 24))
    draw = ImageDraw.Draw(img)

    # цвет по категории
    if "Crypto" in category:
        accent = (56, 189, 248)
    elif "Politics" in category:
        accent = (251, 113, 133)
    elif "Macro" in category:
        accent = (45, 212, 191)
    elif "News" in category:
        accent = (249, 168, 212)
    else:
        accent = (148, 163, 184)

    # верхняя полоса
    draw.rectangle([0, 0, width, height // 3], fill=accent)

    # нормальный шрифт
    try:
        font_title = ImageFont.truetype("DejaVuSans-Bold.ttf", 42)
        font_cat = ImageFont.truetype("DejaVuSans-Bold.ttf", 24)
    except Exception:
        font_title = ImageFont.load_default()
        font_cat = ImageFont.load_default()
def build_cover_image(idea):
    cover_url = idea.get("cover_url")
    if cover_url:
        try:
            r = requests.get(cover_url, timeout=10)
            r.raise_for_status()
            buf = BytesIO(r.content)
            buf.seek(0)
            return buf
        except:
            pass

    return generate_cover_image(idea)

    
    def measure(text: str, font) -> tuple[int, int]:
        bbox = draw.textbbox((0, 0), text, font=font)
        return bbox[2] - bbox[0], bbox[3] - bbox[1]

    # перенос заголовка
    max_width = width - 160
    words = title.split()
    lines = []
    current = ""
    for w in words:
        test = (current + " " + w).strip()
        tw, _ = measure(test, font_title)
        if tw <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            current = w
    if current:
        lines.append(current)

    # ограничим до 3 строк
    lines = lines[:3]

    # центрируем по вертикали во второй и третьей трети
    total_height = sum(measure(line, font_title)[1] + 10 for line in lines) - 10
    y = height // 3 + (height * 2 // 3 - total_height) // 2

    for line in lines:
        tw, th = measure(line, font_title)
        x = (width - tw) // 2
        draw.text((x, y), line, font=font_title, fill=(255, 255, 255))
        y += th + 10

    # подпись категории внизу
    cat_text = category.upper()
    ct_w, ct_h = measure(cat_text, font_cat)
    draw.text((40, height - ct_h - 40), cat_text, font=font_cat, fill=accent)

    buf = BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf


    def measure(text: str, font) -> tuple[int, int]:
        # заменяет устаревший textsize
        bbox = draw.textbbox((0, 0), text, font=font)
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]
        return w, h

    # перенос строки по ширине
    words = title.split()
    lines = []
    current = ""
    for w in words:
        test = (current + " " + w).strip()
        tw, th = measure(test, font_title)
        if tw <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            current = w
    if current:
        lines.append(current)

    # рисуем текст заголовка
    y = height // 3 + 40
    for line in lines[:4]:
        tw, th = measure(line, font_title)
        x = (width - tw) // 2
        draw.text((x, y), line, font=font_title, fill=(255, 255, 255))
        y += th + 10

    # подпись категории
    cat_text = category.upper()
    ct_w, ct_h = measure(cat_text, font_title)
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

import logging
import os
import threading

from flask import Flask
from bot import build_app

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

flask_app = Flask(__name__)


@flask_app.get("/healthz")
def health():
    return "ok", 200


def run_bot():
    """Запускаем Telegram-бота в отдельном потоке."""
    app = build_app()
    app.run_polling()


if __name__ == "__main__":
    # Стартуем бота в отдельном потоке
    threading.Thread(target=run_bot, daemon=True).start()

    # Render даёт порт в переменной PORT
    port = int(os.environ.get("PORT", 10000))
    flask_app.run(host="0.0.0.0", port=port)

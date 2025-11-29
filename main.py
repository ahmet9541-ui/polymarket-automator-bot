import os
import threading
from flask import Flask
from bot import start_bot  # бот запускается из bot.py

app = Flask(__name__)

@app.route("/healthz")
def healthz():
    return "ok", 200


def run_flask():
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)


if __name__ == "__main__":
    # запускаем Flask в отдельном потоке
    threading.Thread(target=run_flask).start()
    
    # запускаем Telegram-бота
    start_bot()

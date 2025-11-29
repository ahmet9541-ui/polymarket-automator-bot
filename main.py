import logging
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

def start_bot():
    tg_app = build_app()
    tg_app.run_polling()

if __name__ == "__main__":
    import threading
    t = threading.Thread(target=start_bot)
    t.start()
    flask_app.run(host="0.0.0.0", port=10000)

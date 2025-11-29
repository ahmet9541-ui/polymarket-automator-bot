import logging

from bot import build_app

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)


def main():
    app = build_app()
    app.run_polling()


if __name__ == "__main__":
    main()

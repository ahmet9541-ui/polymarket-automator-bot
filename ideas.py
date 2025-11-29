from datetime import datetime, timedelta, timezone
import random

_latest_cache: list[dict] = []


def fake_news_idea() -> dict:
    """Временная заглушка - просто генерим рандомную идею для теста."""
    now = datetime.now(timezone.utc)
    expiry = now + timedelta(days=random.randint(3, 30))

    samples = [
        "Will Bitcoin trade above $100,000 on December 31, 2026?",
        "Will the FED cut interest rates at least once before March 31, 2026?",
        "Will ETH reach a new all-time high before June 30, 2026?",
        "Will Trump win the 2028 US presidential election?",
        "Will Apple announce a foldable iPhone before December 31, 2027?",
    ]

    q = random.choice(samples)

    return {
        "question": q,
        "description": "Auto-generated market idea (demo mode).",
        "category": "Macro & Crypto",
        "expiry": expiry.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source_links": ["https://polymarket.com"],
    }


def get_latest_ideas(limit: int = 5) -> list[dict]:
    """Вернуть последние сгенерированные идеи."""
    return _latest_cache[:limit]


def push_new_idea(idea: dict):
    """Добавить новую идею в кеш и обрезать историю."""
    global _latest_cache
    _latest_cache.insert(0, idea)
    _latest_cache = _latest_cache[:50]

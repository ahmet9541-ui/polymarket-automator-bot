import os
import random
import datetime as dt
import requests

# ------------- CRYPTO (ончен сигнал через CoinGecko) -------------

COINGECKO_URL = "https://api.coingecko.com/api/v3/simple/price"
COIN_MAP = {
    "BTC": "bitcoin",
    "ETH": "ethereum",
    "SOL": "solana",
    "SUI": "sui",
}


def fetch_crypto_prices():
    try:
        ids = ",".join(COIN_MAP.values())
        params = {"ids": ids, "vs_currencies": "usd"}
        r = requests.get(COINGECKO_URL, params=params, timeout=10)
        return r.json()
    except Exception as e:
        print("fetch_crypto_prices error:", e)
        return {}


def generate_crypto_idea_real():
    prices = fetch_crypto_prices()
    if not prices:
        return None

    asset = random.choice(list(COIN_MAP.keys()))
    cg_id = COIN_MAP[asset]
    price = prices.get(cg_id, {}).get("usd")
    if not price:
        return None

    multiplier = random.uniform(1.05, 1.20)
    target = round(price * multiplier, 2)

    days_ahead = random.randint(7, 30)
    date = (dt.date.today() + dt.timedelta(days=days_ahead)).strftime("%Y-%m-%d")

    title = f"Will {asset} trade above ${target:,} on {date}?"

    resolution = (
        f"Resolves to YES if the {asset}/USD spot price on Coinbase or Binance "
        f"at 23:59 UTC on {date} is strictly above ${target:,}. Otherwise NO. "
        "If data is unavailable, use CoinGecko as a backup reference."
    )

    return {
        "category": "Crypto (price-based)",
        "title": title,
        "resolution": resolution,
        "notes": f"Target is set ~{multiplier*100:.1f}% above current market price (~${price:,}).",
    }


# ------------- POLYMARKET (crowd сигнал) -------------

POLY_URL = "https://gamma-api.polymarket.com/markets?active=true&closed=false&limit=200"


def fetch_polymarket_markets():
    try:
        r = requests.get(POLY_URL, timeout=10)
        data = r.json()
        if isinstance(data, dict) and "markets" in data:
            return data["markets"]
        if isinstance(data, list):
            return data
        return []
    except Exception as e:
        print("fetch_polymarket_markets error:", e)
        return []


def classify_market(m):
    q = (m.get("question") or "").lower()

    crypto_words = ["btc", "bitcoin", "eth", "ethereum", "sol", "solana", "crypto", "token"]
    politics_words = ["election", "vote", "president", "parliament", "senate", "congress", "prime minister"]
    macro_words = ["cpi", "inflation", "unemployment", "fed", "interest rate", "rate hike", "rate cut", "gdp"]

    if any(w in q for w in crypto_words):
        return "Crypto"
    if any(w in q for w in politics_words):
        return "Politics"
    if any(w in q for w in macro_words):
        return "Macro"
    return "Other"


def pick_real_market(category=None):
    markets = fetch_polymarket_markets()
    if not markets:
        return None

    enriched = []
    for m in markets:
        cat = classify_market(m)
        m["_category"] = cat
        enriched.append(m)

    if category:
        enriched = [m for m in enriched if m["_category"] == category]

    if not enriched:
        return None

    random.shuffle(enriched)
    return enriched[0]


def generate_macro_idea_real():
    m = pick_real_market("Macro")
    if not m:
        return None

    q = m.get("question", "Macro event")
    slug = m.get("slug")
    url = f"https://polymarket.com/market/{slug}" if slug else "https://polymarket.com"

    title = q
    resolution = (
        "Resolves using the same type of official data as the referenced Polymarket market "
        "on this topic (e.g. government statistics, central bank releases)."
    )

    return {
        "category": "Macro (Polymarket-based)",
        "title": title,
        "resolution": resolution,
        "notes": f"Inspired by an existing Polymarket market: {url}",
    }


def generate_politics_idea_real():
    m = pick_real_market("Politics")
    if not m:
        return None

    q = m.get("question", "Political event")
    slug = m.get("slug")
    url = f"https://polymarket.com/market/{slug}" if slug else "https://polymarket.com"

    title = q
    resolution = (
        "Resolves according to the same type of political outcome as the referenced Polymarket market, "
        "using official election results and reputable international media as sources."
    )

    return {
        "category": "Politics (Polymarket-based)",
        "title": title,
        "resolution": resolution,
        "notes": f"Inspired by a real Polymarket politics market: {url}",
    }


# ------------- NEWS (news сигнал, Currents API или аналог) -------------

# ------------- NEWS (news сигнал, Currents API или аналог) -------------

NEWS_API_KEY = os.getenv("NEWS_API_KEY")
LAST_NEWS_URL = None  # запоминаем последнюю использованную статью


def fetch_news():
    if not NEWS_API_KEY:
        return []

    url = "https://api.currentsapi.services/v1/latest-news"
    params = {
        "language": "en",
        "apiKey": NEWS_API_KEY,
    }
    try:
        r = requests.get(url, params=params, timeout=10)
        data = r.json()
        return data.get("news", []) or data.get("articles", [])
    except Exception as e:
        print("fetch_news error:", e)
        return []


def pick_geo_political_article():
    global LAST_NEWS_URL

    articles = fetch_news()
    if not articles:
        return None

    keywords = [
        "Ukraine", "Russia", "NATO", "ceasefire", "war", "invasion",
        "election", "vote", "president", "parliament", "senate", "congress",
        "sanctions", "referendum",
        "Bitcoin", "Ethereum", "crypto", "ETF", "SEC"
    ]

    candidates = []
    for a in articles:
        text = (a.get("title") or "") + " " + (a.get("description") or "")
        if any(k.lower() in text.lower() for k in keywords):
            candidates.append(a)

    if not candidates:
        return None

    # пробуем не брать ту же самую ссылку два раза подряд
    if LAST_NEWS_URL:
        filtered = [a for a in candidates if a.get("url") != LAST_NEWS_URL]
        if filtered:
            candidates = filtered

    article = random.choice(candidates)
    LAST_NEWS_URL = article.get("url")
    return article


def generate_news_idea():
    article = pick_geo_political_article()
    if not article:
        return None

    title_text = article.get("title", "Major event")
    url = article.get("url", "")
    full_text = (article.get("title") or "") + " " + (article.get("description") or "")
    text_low = full_text.lower()

    days_ahead = random.randint(14, 90)
    deadline = (dt.date.today() + dt.timedelta(days=days_ahead)).strftime("%Y-%m-%d")

    # чуть более разные шаблоны
    if "ceasefire" in text_low or "peace" in text_low or "truce" in text_low:
        q = f"Will an official ceasefire related to the following situation be signed before {deadline}?"
    elif "election" in text_low or "vote" in text_low or "poll" in text_low:
        q = (
            "Will the side that is generally favoured in reputable polls regarding the "
            f"following situation win the next relevant election before {deadline}?"
        )
    elif "sanction" in text_low:
        q = f"Will new major international sanctions related to the following situation be officially announced before {deadline}?"
    elif "etf" in text_low or "sec" in text_low or "bitcoin" in text_low or "ethereum" in text_low or "crypto" in text_low:
        q = f"Will a major regulatory decision related to the following crypto or markets situation be officially confirmed before {deadline}?"
    else:
        q = f"Will there be a verifiable escalation or resolution of the following situation before {deadline}?"

    resolution = (
        "Resolves to YES if reputable international media (e.g. Reuters, AP, Bloomberg) "
        f"or official government/agency sources confirm that the described outcome occurred "
        f"before 23:59 UTC on {deadline}. Otherwise NO."
    )

    return {
        "category": "News-based event",
        "title": q,
        "resolution": resolution,
        "notes": f"Based on real news: {title_text} ({url})",
    }


# ------------- Главная точка: комбинируем все сигналы -------------

def generate_market_idea():
    """
    Приоритет:
    1) новости
    2) макро / политика с Polymarket
    3) крипта от реальных цен
    """

    # 1. новости
    idea = generate_news_idea()
    if idea:
        return idea

    # 2. polymarket macro / politics, случайно одну категорию
    if random.random() < 0.5:
        idea = generate_macro_idea_real()
    else:
        idea = generate_politics_idea_real()
    if idea:
        return idea

    # 3. крипта по ценам
    idea = generate_crypto_idea_real()
    if idea:
        return idea

    # запасной вариант, если все API легли
    fallback = {
        "category": "Fallback",
        "title": "Will Bitcoin trade higher at the end of this month than it does today?",
        "resolution": (
            "Resolves to YES if BTC/USD spot price on Coinbase at 23:59 UTC on the last day "
            "of the current month is strictly above the BTC/USD price at the time this market "
            "is created. Otherwise NO."
        ),
        "notes": "Fallback idea used when external data sources are unavailable.",
    }
    return fallback

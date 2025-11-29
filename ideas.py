import random
import datetime as dt

CRYPTO_ASSETS = ["BTC", "ETH", "SOL", "SUI", "BASE", "POL"]
POLITICS_EXAMPLES = [
    "Will {country} hold a snap election before {date}?",
    "Will {country}'s leader leave office before {date}?",
]
COUNTRIES = ["the US", "the UK", "France", "Germany", "India", "Brazil"]
MACRO_INDICATORS = ["CPI", "unemployment rate", "Fed funds rate"]

def generate_crypto_idea():
    asset = random.choice(CRYPTO_ASSETS)

    days_ahead = random.randint(7, 45)
    date = (dt.date.today() + dt.timedelta(days=days_ahead)).strftime("%Y-%m-%d")

    # грубый диапазон уровней
    base_levels = {
        "BTC": [60000, 65000, 70000, 75000, 80000],
        "ETH": [2500, 3000, 3500, 4000],
        "SOL": [150, 175, 200, 250],
        "SUI": [1.5, 2.0, 2.5, 3.0],
        "BASE": [2.0, 3.0, 4.0],
        "POL": [0.8, 1.0, 1.2],
    }
    level = random.choice(base_levels.get(asset, [100, 200, 300]))

    title = f"Will {asset} trade above ${level:,} on {date}?"

    resolution = (
        f"Resolves to YES if the {asset}/USD price on a major USD spot exchange "
        f"(Coinbase or Binance) at 23:59 UTC on {date} is strictly above ${level:,}. "
        "Otherwise NO. If data is unavailable, use CoinGecko volume-weighted average."
    )

    return {
        "category": "Crypto",
        "title": title,
        "resolution": resolution,
        "notes": "You can adjust the level/date to fit current market conditions."
    }


def generate_politics_idea():
    country = random.choice(COUNTRIES)
    days_ahead = random.randint(30, 180)
    date = (dt.date.today() + dt.timedelta(days=days_ahead)).strftime("%Y-%m-%d")

    template = random.choice(POLITICS_EXAMPLES)
    title = template.format(country=country, date=date)

    resolution = (
        "Resolves to YES if a reputable source such as Reuters, AP or Bloomberg "
        "confirms that the event occurred before 23:59 UTC on the date in the title. "
        "Otherwise NO."
    )

    return {
        "category": "Politics",
        "title": title,
        "resolution": resolution,
        "notes": "You can replace the country or adjust the deadline."
    }


def generate_macro_idea():
    indicator = random.choice(MACRO_INDICATORS)
    days_ahead = random.randint(30, 120)
    date = (dt.date.today() + dt.timedelta(days=days_ahead)).strftime("%Y-%m-%d")

    title = f"Will the US {indicator} print come in above market consensus on {date}?"
    resolution = (
        "Resolves to YES if the official release from the relevant US agency "
        "(BLS, Fed, etc.) is strictly above the Bloomberg market consensus "
        "median forecast published the day before the release. Otherwise NO."
    )

    return {
        "category": "Macro",
        "title": title,
        "resolution": resolution,
        "notes": "Can be adapted to other countries or indicators."
    }


def generate_market_idea():
    """Главная функция: отдаёт одну идею для бота."""
    generators = [generate_crypto_idea, generate_politics_idea, generate_macro_idea]
    idea = random.choice(generators)()
    return idea

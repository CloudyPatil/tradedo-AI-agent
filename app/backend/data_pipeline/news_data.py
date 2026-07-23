# E:\tradedo\app\backend\data_pipeline\news_data.py

import feedparser
import requests
import logging
from datetime import datetime, timedelta
from typing import List, Dict
import time

logger = logging.getLogger("tradedo.news")

# ─── FREE News Sources (No API Key Needed) ────────────────────
RSS_SOURCES = {
    "moneycontrol": "https://www.moneycontrol.com/rss/business.xml",
    "economic_times": "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms",
    "livemint": "https://www.livemint.com/rss/markets",
    "business_standard": "https://www.business-standard.com/rss/markets-106.rss",
    "zeebiz": "https://www.zeebiz.com/markets/rss",
}

# NewsAPI (free tier = 100 req/day)
# Get key at: newsapi.org (free)
NEWSAPI_KEY = None  # Set in .env later


# ─── RSS Fetcher ──────────────────────────────────────────────
def fetch_rss_news(symbol: str, max_articles: int = 10) -> List[Dict]:
    """
    Fetch news from free RSS feeds.
    Filters articles mentioning the stock symbol.

    Args:
        symbol: e.g. "RELIANCE" (without .NS)
        max_articles: max news to return

    Returns:
        List of news dicts
    """
    # Clean symbol for search
    clean_symbol = symbol.replace(".NS", "").replace(".BO", "").upper()

    # Common company name mappings
    name_map = {
        "RELIANCE":   ["Reliance", "RIL", "Mukesh Ambani"],
        "TCS":        ["TCS", "Tata Consultancy"],
        "HDFCBANK":   ["HDFC Bank", "HDFC"],
        "INFY":       ["Infosys", "Infy"],
        "WIPRO":      ["Wipro"],
        "TATAMOTORS": ["Tata Motors", "TML"],
        "ADANIENT":   ["Adani", "Adani Enterprises"],
        "ICICIBANK":  ["ICICI Bank", "ICICI"],
        "SBIN":       ["SBI", "State Bank"],
        "BAJFINANCE": ["Bajaj Finance", "BajFin"],
    }

    # Search terms for this stock
    search_terms = name_map.get(clean_symbol, [clean_symbol])

    articles = []

    for source_name, rss_url in RSS_SOURCES.items():
        try:
            feed = feedparser.parse(rss_url)

            for entry in feed.entries[:30]:  # Check top 30 entries
                title   = entry.get("title", "")
                summary = entry.get("summary", "")
                link    = entry.get("link", "")
                pub_date = entry.get("published", "")

                # Check if any search term is in title/summary
                text = f"{title} {summary}".lower()
                matched = any(
                    term.lower() in text
                    for term in search_terms
                )

                if matched:
                    articles.append({
                        "title":     title,
                        "summary":   summary[:300],  # Trim long summaries
                        "source":    source_name,
                        "url":       link,
                        "published": pub_date,
                        "symbol":    clean_symbol,
                    })

                    if len(articles) >= max_articles:
                        break

            time.sleep(0.3)  # Be nice to servers

        except Exception as e:
            logger.warning(f"RSS fetch failed for {source_name}: {e}")
            continue

    logger.info(f"Found {len(articles)} news articles for {clean_symbol}")
    return articles[:max_articles]


def fetch_general_market_news(max_articles: int = 15) -> List[Dict]:
    """
    Fetch general market news (for market regime analysis).
    No stock filter — just top market news.
    """
    articles = []

    for source_name, rss_url in RSS_SOURCES.items():
        try:
            feed = feedparser.parse(rss_url)

            for entry in feed.entries[:5]:
                articles.append({
                    "title":     entry.get("title", ""),
                    "summary":   entry.get("summary", "")[:300],
                    "source":    source_name,
                    "url":       entry.get("link", ""),
                    "published": entry.get("published", ""),
                    "symbol":    "MARKET",
                })

            time.sleep(0.2)

        except Exception as e:
            logger.warning(f"Market news fetch failed: {e}")
            continue

    return articles[:max_articles]


# ─── Quick Test ───────────────────────────────────────────────
if __name__ == "__main__":
    print("Testing news fetcher...")
    news = fetch_rss_news("RELIANCE", max_articles=5)
    for i, n in enumerate(news, 1):
        print(f"\n{i}. [{n['source']}] {n['title']}")
        print(f"   {n['summary'][:100]}...")
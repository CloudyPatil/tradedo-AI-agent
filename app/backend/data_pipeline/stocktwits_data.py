# E:\tradedo\app\backend\data_pipeline\stocktwits_data.py

"""
StockTwits scraper - dedicated stock market social platform.
Uses their FREE public API endpoint.
"""

import logging
import requests
from typing import Dict, List, Optional
from datetime import datetime

logger = logging.getLogger("tradedo.stocktwits")

# StockTwits public API base
STOCKTWITS_API = "https://api.stocktwits.com/api/2"


def fetch_stocktwits_data(symbol: str) -> Dict:
    """
    Fetch StockTwits data for a stock.
    
    StockTwits uses their own symbols (e.g., RELIANCE.NSE not RELIANCE.NS).
    Also has native bullish/bearish tagging by users.
    """
    # Convert to StockTwits format
    clean = symbol.replace(".NS", "").replace(".BO", "").upper()
    
    # Try multiple symbol formats
    formats = [
        f"{clean}.NSE",     # Indian NSE format
        f"{clean}.BSE",     # BSE format
        clean,              # Plain symbol
    ]
    
    for st_symbol in formats:
        try:
            url = f"{STOCKTWITS_API}/streams/symbol/{st_symbol}.json"
            
            response = requests.get(
                url,
                timeout=10,
                headers={"User-Agent": "TradeAgent/1.0"},
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("response", {}).get("status") == 200:
                    return _parse_stocktwits_response(data, clean)
            
        except Exception as e:
            logger.debug(f"StockTwits failed for {st_symbol}: {e}")
            continue
    
    return _empty_response(clean)


def _parse_stocktwits_response(data: Dict, symbol: str) -> Dict:
    """Parse StockTwits API response."""
    messages = data.get("messages", [])
    
    if not messages:
        return _empty_response(symbol)
    
    bullish_count = 0
    bearish_count = 0
    neutral_count = 0
    total_engagement = 0
    
    top_messages = []
    
    for msg in messages[:30]:  # Latest 30 messages
        # User's own tag
        entities = msg.get("entities", {})
        sentiment = entities.get("sentiment", {})
        sentiment_val = sentiment.get("basic") if sentiment else None
        
        if sentiment_val == "Bullish":
            bullish_count += 1
        elif sentiment_val == "Bearish":
            bearish_count += 1
        else:
            neutral_count += 1
        
        # Engagement metrics
        likes = msg.get("likes", {}).get("total", 0)
        reshares = msg.get("reshares", {}).get("reshared_count", 0)
        engagement = likes + (reshares * 2)
        total_engagement += engagement
        
        top_messages.append({
            "body":       (msg.get("body", "") or "")[:200],
            "user":       msg.get("user", {}).get("username", "anon"),
            "followers":  msg.get("user", {}).get("followers", 0),
            "likes":      likes,
            "reshares":   reshares,
            "sentiment":  sentiment_val or "Neutral",
            "created_at": msg.get("created_at"),
        })
    
    # Calculate sentiment score
    total_tagged = bullish_count + bearish_count
    
    if total_tagged > 0:
        score = (bullish_count - bearish_count) / total_tagged
    else:
        score = 0.0
    
    # Label
    if score > 0.3:
        label = "BULLISH"
    elif score < -0.3:
        label = "BEARISH"
    else:
        label = "NEUTRAL"
    
    # Buzz score
    buzz_score = min(100, (len(messages) * 3) + (total_engagement // 5))
    
    # Sort top messages by engagement
    top_messages.sort(key=lambda x: x["likes"] + x["reshares"], reverse=True)
    
    return {
        "score":            round(score, 3),
        "label":            label,
        "message_count":    len(messages),
        "bullish_count":    bullish_count,
        "bearish_count":    bearish_count,
        "neutral_count":    neutral_count,
        "total_engagement": total_engagement,
        "buzz_score":       buzz_score,
        "top_messages":     top_messages[:3],
    }


def _empty_response(symbol: str) -> Dict:
    """Return empty response when no data available."""
    return {
        "score":            0.0,
        "label":            "NEUTRAL",
        "message_count":    0,
        "bullish_count":    0,
        "bearish_count":    0,
        "neutral_count":    0,
        "total_engagement": 0,
        "buzz_score":       0,
        "top_messages":     [],
    }


# ─── Quick Test ───────────────────────────────────────────────
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    result = fetch_stocktwits_data("RELIANCE")
    
    print("\n📱 StockTwits Analysis")
    print("=" * 50)
    print(f"Score:    {result['score']}")
    print(f"Label:    {result['label']}")
    print(f"Messages: {result['message_count']}")
    print(f"Bullish:  {result['bullish_count']}")
    print(f"Bearish:  {result['bearish_count']}")
    print(f"Neutral:  {result['neutral_count']}")
    print(f"Buzz:     {result['buzz_score']}/100")
    
    if result['top_messages']:
        print("\n💬 Top Messages:")
        for i, m in enumerate(result['top_messages'], 1):
            print(f"{i}. [{m['sentiment']}] @{m['user']}")
            print(f"   {m['body'][:150]}")
            print(f"   👍 {m['likes']}  🔁 {m['reshares']}")
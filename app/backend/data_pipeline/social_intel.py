# E:\tradedo\app\backend\data_pipeline\social_intel.py

"""
Unified social intelligence — aggregates Reddit + StockTwits.
This is the ONE function the agent calls for social sentiment.
"""

import logging
from typing import Dict
from concurrent.futures import ThreadPoolExecutor
from data_pipeline.reddit_data import fetch_reddit_sentiment
from data_pipeline.stocktwits_data import fetch_stocktwits_data

logger = logging.getLogger("tradedo.social")


def get_social_intelligence(symbol: str) -> Dict:
    """
    Fetch social sentiment from all sources in parallel.
    
    Returns unified social sentiment for the agent.
    """
    logger.info(f"🌐 Fetching social intel for {symbol}...")
    
    # Parallel fetch from all sources
    with ThreadPoolExecutor(max_workers=3) as executor:
        reddit_future     = executor.submit(fetch_reddit_sentiment, symbol)
        stocktwits_future = executor.submit(fetch_stocktwits_data, symbol)
        
        reddit_data     = reddit_future.result()
        stocktwits_data = stocktwits_future.result()
    
    # ── Combine scores (weighted) ────────────────────────────
    reddit_score  = reddit_data.get("score", 0)
    twits_score   = stocktwits_data.get("score", 0)
    
    reddit_posts  = reddit_data.get("post_count", 0)
    twits_msgs    = stocktwits_data.get("message_count", 0)
    
    # If no data anywhere, return neutral
    total_content = reddit_posts + twits_msgs
    if total_content == 0:
        return {
            "score":       0.0,
            "label":       "NO_DATA",
            "buzz_score":  0,
            "confidence":  "LOW",
            "sources":     {
                "reddit":     reddit_data,
                "stocktwits": stocktwits_data,
            },
        }
    
    # Weighted average (weighted by content volume)
    weighted_score = (
        (reddit_score * reddit_posts) + 
        (twits_score * twits_msgs)
    ) / total_content
    
    # ── Combined Buzz Score ──────────────────────────────────
    reddit_buzz = reddit_data.get("buzz_score", 0)
    twits_buzz  = stocktwits_data.get("buzz_score", 0)
    combined_buzz = min(100, (reddit_buzz + twits_buzz) // 2 + 10)
    
    # ── Label ────────────────────────────────────────────────
    if weighted_score > 0.3:
        label = "BULLISH"
    elif weighted_score < -0.3:
        label = "BEARISH"
    else:
        label = "NEUTRAL"
    
    # ── Confidence (how reliable is this sentiment) ──────────
    # Based on total content available
    if total_content >= 20:
        confidence = "HIGH"
    elif total_content >= 10:
        confidence = "MEDIUM"
    elif total_content >= 3:
        confidence = "LOW"
    else:
        confidence = "VERY_LOW"
    
    # ── Agreement Score (do both sources agree?) ─────────────
    # If both bullish or both bearish → agreement
    reddit_dir = 1 if reddit_score > 0.1 else -1 if reddit_score < -0.1 else 0
    twits_dir  = 1 if twits_score > 0.1 else -1 if twits_score < -0.1 else 0
    
    if reddit_dir == twits_dir and reddit_dir != 0:
        agreement = "STRONG"  # Both agree, non-neutral
    elif reddit_dir == twits_dir:
        agreement = "NEUTRAL"  # Both neutral
    else:
        agreement = "MIXED"    # Disagree
    
    logger.info(
        f"  → Reddit: {reddit_data.get('label')} ({reddit_posts} posts) | "
        f"StockTwits: {stocktwits_data.get('label')} ({twits_msgs} msgs) | "
        f"Combined: {label}"
    )
    
    return {
        "score":       round(weighted_score, 3),
        "label":       label,
        "buzz_score":  combined_buzz,
        "confidence":  confidence,
        "agreement":   agreement,
        "total_mentions": total_content,
        "sources": {
            "reddit": {
                "score":      reddit_score,
                "label":      reddit_data.get("label"),
                "posts":      reddit_posts,
                "engagement": reddit_data.get("total_engagement", 0),
                "top_posts":  reddit_data.get("top_posts", []),
            },
            "stocktwits": {
                "score":      twits_score,
                "label":      stocktwits_data.get("label"),
                "messages":   twits_msgs,
                "bullish":    stocktwits_data.get("bullish_count", 0),
                "bearish":    stocktwits_data.get("bearish_count", 0),
                "top_msgs":   stocktwits_data.get("top_messages", []),
            },
        },
    }


# ─── Quick Test ───────────────────────────────────────────────
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    import json
    
    for symbol in ["RELIANCE", "TCS", "ADANIENT"]:
        print(f"\n{'='*50}")
        print(f"Symbol: {symbol}")
        print('='*50)
        result = get_social_intelligence(symbol)
        print(json.dumps(result, indent=2))
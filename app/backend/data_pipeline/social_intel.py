# E:\tradedo\app\backend\data_pipeline\social_intel.py

"""
Unified social + video intelligence.
Aggregates Reddit + StockTwits + YouTube.
"""

import logging
from typing import Dict
from concurrent.futures import ThreadPoolExecutor
from data_pipeline.reddit_data import fetch_reddit_sentiment
from data_pipeline.stocktwits_data import fetch_stocktwits_data
from data_pipeline.youtube_data import fetch_youtube_intel

logger = logging.getLogger("tradedo.social")


def get_social_intelligence(symbol: str) -> Dict:
    """
    Fetch social + video intelligence from all sources in parallel.
    """
    logger.info(f"🌐 Fetching full social+video intel for {symbol}...")
    
    # Parallel fetch from all 3 sources
    with ThreadPoolExecutor(max_workers=3) as executor:
        reddit_future     = executor.submit(fetch_reddit_sentiment, symbol)
        stocktwits_future = executor.submit(fetch_stocktwits_data, symbol)
        youtube_future    = executor.submit(fetch_youtube_intel, symbol)
        
        reddit_data     = reddit_future.result()
        stocktwits_data = stocktwits_future.result()
        youtube_data    = youtube_future.result()
    
    # ── Weighted scoring ─────────────────────────────────────
    # YouTube from trusted channels = higher weight
    # Reddit/StockTwits = crowd sentiment (medium weight)
    
    scores = []
    weights = []
    
    # Reddit
    reddit_posts = reddit_data.get("post_count", 0)
    if reddit_posts > 0:
        scores.append(reddit_data.get("score", 0))
        weights.append(reddit_posts * 0.5)   # 0.5 weight per post
    
    # StockTwits
    twits_msgs = stocktwits_data.get("message_count", 0)
    if twits_msgs > 0:
        scores.append(stocktwits_data.get("score", 0))
        weights.append(twits_msgs * 0.5)
    
    # YouTube (weighted higher)
    yt_videos = youtube_data.get("videos_analyzed", 0)
    if yt_videos > 0:
        scores.append(youtube_data.get("score", 0))
        # YouTube weight: base 3 per video + trusted bonus
        yt_weight = (yt_videos * 3) + (youtube_data.get("trusted_videos", 0) * 5)
        weights.append(yt_weight)
    
    # Calculate weighted average
    if not scores:
        return _empty_response(reddit_data, stocktwits_data, youtube_data)
    
    total_weight = sum(weights)
    weighted_score = sum(s * w for s, w in zip(scores, weights)) / total_weight
    weighted_score = max(-1.0, min(1.0, weighted_score))
    
    # ── Combined Buzz Score ──────────────────────────────────
    reddit_buzz = reddit_data.get("buzz_score", 0)
    twits_buzz  = stocktwits_data.get("buzz_score", 0)
    yt_buzz     = min(100, yt_videos * 15)  # 15 per video
    
    combined_buzz = min(100, (reddit_buzz + twits_buzz + yt_buzz) // 3 + 10)
    
    # ── Label ────────────────────────────────────────────────
    if weighted_score > 0.3:
        label = "BULLISH"
    elif weighted_score < -0.3:
        label = "BEARISH"
    else:
        label = "NEUTRAL"
    
    # ── Confidence Level ─────────────────────────────────────
    total_content = reddit_posts + twits_msgs + (yt_videos * 5)
    trusted_yt = youtube_data.get("trusted_videos", 0)
    
    if total_content >= 30 and trusted_yt >= 2:
        confidence = "VERY_HIGH"
    elif total_content >= 20 and trusted_yt >= 1:
        confidence = "HIGH"
    elif total_content >= 10:
        confidence = "MEDIUM"
    elif total_content >= 3:
        confidence = "LOW"
    else:
        confidence = "VERY_LOW"
    
    # ── Agreement Analysis ───────────────────────────────────
    directions = []
    if reddit_posts > 0:
        r_score = reddit_data.get("score", 0)
        directions.append(1 if r_score > 0.1 else -1 if r_score < -0.1 else 0)
    if twits_msgs > 0:
        t_score = stocktwits_data.get("score", 0)
        directions.append(1 if t_score > 0.1 else -1 if t_score < -0.1 else 0)
    if yt_videos > 0:
        y_score = youtube_data.get("score", 0)
        directions.append(1 if y_score > 0.1 else -1 if y_score < -0.1 else 0)
    
    if directions:
        non_zero = [d for d in directions if d != 0]
        if non_zero and all(d == non_zero[0] for d in non_zero):
            agreement = "STRONG"
        elif len(set(directions)) == 1:
            agreement = "NEUTRAL"
        else:
            agreement = "MIXED"
    else:
        agreement = "NO_DATA"
    
    # ── Price Targets from YouTube ───────────────────────────
    consensus_target = youtube_data.get("consensus_target")
    
    logger.info(
        f"  Combined: {label} ({weighted_score:.2f}) | "
        f"Buzz: {combined_buzz} | Confidence: {confidence}"
    )
    
    return {
        "score":       round(weighted_score, 3),
        "label":       label,
        "buzz_score":  combined_buzz,
        "confidence":  confidence,
        "agreement":   agreement,
        "total_mentions": reddit_posts + twits_msgs + youtube_data.get("total_mentions", 0),
        "consensus_target": consensus_target,
        "sources": {
            "reddit": {
                "score":      reddit_data.get("score", 0),
                "label":      reddit_data.get("label"),
                "posts":      reddit_posts,
                "buzz":       reddit_buzz,
                "top_posts":  reddit_data.get("top_posts", []),
            },
            "stocktwits": {
                "score":      stocktwits_data.get("score", 0),
                "label":      stocktwits_data.get("label"),
                "messages":   twits_msgs,
                "bullish":    stocktwits_data.get("bullish_count", 0),
                "bearish":    stocktwits_data.get("bearish_count", 0),
                "buzz":       twits_buzz,
                "top_msgs":   stocktwits_data.get("top_messages", []),
            },
            "youtube": {
                "score":           youtube_data.get("score", 0),
                "label":           youtube_data.get("label"),
                "videos":          yt_videos,
                "trusted_videos":  trusted_yt,
                "consensus_target": consensus_target,
                "avg_target":      youtube_data.get("avg_target"),
                "all_targets":     youtube_data.get("all_targets", []),
                "top_videos":      youtube_data.get("top_videos", []),
            },
        },
    }


def _empty_response(reddit_data, stocktwits_data, youtube_data) -> Dict:
    """Return neutral response when no data anywhere."""
    return {
        "score":       0.0,
        "label":       "NO_DATA",
        "buzz_score":  0,
        "confidence":  "NONE",
        "agreement":   "NO_DATA",
        "total_mentions": 0,
        "consensus_target": None,
        "sources": {
            "reddit":     reddit_data,
            "stocktwits": stocktwits_data,
            "youtube":    youtube_data,
        },
    }


# ─── Quick Test ───────────────────────────────────────────────
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    import json
    
    for symbol in ["RELIANCE", "TCS", "ADANIENT"]:
        print(f"\n{'='*60}")
        print(f"Symbol: {symbol}")
        print("=" * 60)
        result = get_social_intelligence(symbol)
        
        print(f"\n📊 Combined Verdict: {result['label']} (score: {result['score']})")
        print(f"   Buzz:       {result['buzz_score']}/100")
        print(f"   Confidence: {result['confidence']}")
        print(f"   Agreement:  {result['agreement']}")
        print(f"   Mentions:   {result['total_mentions']}")
        print(f"   Target:     {result['consensus_target']}")
        
        for src_name, src_data in result['sources'].items():
            if isinstance(src_data, dict):
                print(f"\n   {src_name.upper()}:")
                for k, v in list(src_data.items())[:4]:
                    if not isinstance(v, (list, dict)):
                        print(f"     {k}: {v}")
# E:\tradedo\app\backend\data_pipeline\social_intel.py

"""
Unified social + video intelligence.
Aggregates: Reddit + StockTwits + YouTube + Twitter
"""

import logging
from typing import Dict
from concurrent.futures import ThreadPoolExecutor
from data_pipeline.reddit_data import fetch_reddit_sentiment
from data_pipeline.stocktwits_data import fetch_stocktwits_data
from data_pipeline.youtube_data import fetch_youtube_intel
from data_pipeline.twitter_data import fetch_twitter_intel

logger = logging.getLogger("tradedo.social")


def get_social_intelligence(symbol: str) -> Dict:
    """
    Fetch intelligence from ALL sources in parallel.
    Reddit + StockTwits + YouTube + Twitter
    """
    logger.info(f"🌐 Fetching complete social+video intel for {symbol}...")
    
    # Parallel fetch from all 4 sources
    with ThreadPoolExecutor(max_workers=4) as executor:
        reddit_future     = executor.submit(fetch_reddit_sentiment, symbol)
        stocktwits_future = executor.submit(fetch_stocktwits_data, symbol)
        youtube_future    = executor.submit(fetch_youtube_intel, symbol)
        twitter_future    = executor.submit(fetch_twitter_intel, symbol)
        
        reddit_data     = reddit_future.result()
        stocktwits_data = stocktwits_future.result()
        youtube_data    = youtube_future.result()
        twitter_data    = twitter_future.result()
    
    # ── Weighted scoring ─────────────────────────────────────
    scores = []
    weights = []
    
    # Reddit (retail sentiment)
    reddit_posts = reddit_data.get("post_count", 0)
    if reddit_posts > 0:
        scores.append(reddit_data.get("score", 0))
        weights.append(reddit_posts * 0.5)
    
    # StockTwits (dedicated stock crowd)
    twits_msgs = stocktwits_data.get("message_count", 0)
    if twits_msgs > 0:
        scores.append(stocktwits_data.get("score", 0))
        weights.append(twits_msgs * 0.5)
    
    # YouTube (expert opinion — heavier weight)
    yt_videos = youtube_data.get("videos_analyzed", 0)
    if yt_videos > 0:
        scores.append(youtube_data.get("score", 0))
        yt_weight = (yt_videos * 3) + (youtube_data.get("trusted_videos", 0) * 5)
        weights.append(yt_weight)
    
    # Twitter (real-time pulse + trusted analysts)
    tw_count = twitter_data.get("tweet_count", 0)
    if tw_count > 0:
        scores.append(twitter_data.get("score", 0))
        tw_weight = tw_count * 0.7 + (twitter_data.get("trusted_count", 0) * 4)
        weights.append(tw_weight)
    
    # No data anywhere?
    if not scores:
        return _empty_response(reddit_data, stocktwits_data, youtube_data, twitter_data)
    
    # Weighted average
    total_weight = sum(weights)
    weighted_score = sum(s * w for s, w in zip(scores, weights)) / total_weight
    weighted_score = max(-1.0, min(1.0, weighted_score))
    
    # ── Combined Buzz Score ──────────────────────────────────
    buzz_scores = [
        reddit_data.get("buzz_score", 0),
        stocktwits_data.get("buzz_score", 0),
        min(100, yt_videos * 15),
        twitter_data.get("buzz_score", 0),
    ]
    combined_buzz = min(100, sum(buzz_scores) // 4 + 15)
    
    # ── Label ────────────────────────────────────────────────
    if weighted_score > 0.3:
        label = "BULLISH"
    elif weighted_score < -0.3:
        label = "BEARISH"
    else:
        label = "NEUTRAL"
    
    # ── Confidence ───────────────────────────────────────────
    total_content = reddit_posts + twits_msgs + (yt_videos * 5) + tw_count
    trusted_yt    = youtube_data.get("trusted_videos", 0)
    trusted_tw    = twitter_data.get("trusted_count", 0)
    trusted_total = trusted_yt + trusted_tw
    
    if total_content >= 40 and trusted_total >= 3:
        confidence = "VERY_HIGH"
    elif total_content >= 25 and trusted_total >= 2:
        confidence = "HIGH"
    elif total_content >= 15:
        confidence = "MEDIUM"
    elif total_content >= 5:
        confidence = "LOW"
    else:
        confidence = "VERY_LOW"
    
    # ── Agreement Analysis (all 4 sources) ───────────────────
    directions = []
    for src_score, src_count in [
        (reddit_data.get("score", 0), reddit_posts),
        (stocktwits_data.get("score", 0), twits_msgs),
        (youtube_data.get("score", 0), yt_videos),
        (twitter_data.get("score", 0), tw_count),
    ]:
        if src_count > 0:
            directions.append(
                1 if src_score > 0.1 else -1 if src_score < -0.1 else 0
            )
    
    if directions:
        non_zero = [d for d in directions if d != 0]
        if len(non_zero) >= 3 and all(d == non_zero[0] for d in non_zero):
            agreement = "STRONG"   # 3+ sources agree
        elif non_zero and all(d == non_zero[0] for d in non_zero):
            agreement = "MODERATE"  # All non-neutral agree
        elif len(set(directions)) == 1:
            agreement = "NEUTRAL"
        else:
            agreement = "MIXED"
    else:
        agreement = "NO_DATA"
    
    # ── Consensus Target from YouTube ────────────────────────
    consensus_target = youtube_data.get("consensus_target")
    
    logger.info(
        f"  Verdict: {label} ({weighted_score:.2f}) | "
        f"Buzz: {combined_buzz} | Conf: {confidence} | "
        f"Agree: {agreement}"
    )
    
    return {
        "score":       round(weighted_score, 3),
        "label":       label,
        "buzz_score":  combined_buzz,
        "confidence":  confidence,
        "agreement":   agreement,
        "total_mentions": (
            reddit_posts + twits_msgs +
            youtube_data.get("total_mentions", 0) + tw_count
        ),
        "consensus_target": consensus_target,
        "sources": {
            "reddit": {
                "score":      reddit_data.get("score", 0),
                "label":      reddit_data.get("label"),
                "posts":      reddit_posts,
                "buzz":       reddit_data.get("buzz_score", 0),
                "top_posts":  reddit_data.get("top_posts", []),
            },
            "stocktwits": {
                "score":      stocktwits_data.get("score", 0),
                "label":      stocktwits_data.get("label"),
                "messages":   twits_msgs,
                "bullish":    stocktwits_data.get("bullish_count", 0),
                "bearish":    stocktwits_data.get("bearish_count", 0),
                "buzz":       stocktwits_data.get("buzz_score", 0),
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
            "twitter": {
                "score":         twitter_data.get("score", 0),
                "label":         twitter_data.get("label"),
                "tweets":        tw_count,
                "trusted":       trusted_tw,
                "engagement":    twitter_data.get("total_engagement", 0),
                "buzz":          twitter_data.get("buzz_score", 0),
                "top_tweets":    twitter_data.get("top_tweets", []),
            },
        },
    }


def _empty_response(reddit_data, stocktwits_data, youtube_data, twitter_data) -> Dict:
    """Neutral response when no data available."""
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
            "twitter":    twitter_data,
        },
    }


# ─── Quick Test ───────────────────────────────────────────────
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    for symbol in ["RELIANCE", "TCS"]:
        print(f"\n{'='*60}")
        print(f"Symbol: {symbol}")
        print("=" * 60)
        result = get_social_intelligence(symbol)
        
        print(f"\n📊 VERDICT: {result['label']} (score: {result['score']})")
        print(f"   Buzz:       {result['buzz_score']}/100")
        print(f"   Confidence: {result['confidence']}")
        print(f"   Agreement:  {result['agreement']}")
        print(f"   Target:     {result['consensus_target']}")
        
        print(f"\n   Sources:")
        for src_name in ['reddit', 'stocktwits', 'youtube', 'twitter']:
            src = result['sources'].get(src_name, {})
            count_key = {
                'reddit': 'posts', 'stocktwits': 'messages',
                'youtube': 'videos', 'twitter': 'tweets'
            }[src_name]
            print(f"     {src_name:12s}: {src.get('label', 'N/A'):12s} "
                  f"({src.get(count_key, 0)} items)")
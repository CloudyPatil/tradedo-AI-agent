# E:\tradedo\app\backend\data_pipeline\youtube_data.py

"""
YouTube Intelligence - New Version
Queries cached transcripts (fast!) instead of live scraping.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import re
import logging
import sqlite3
from typing import List, Dict, Optional
from datetime import datetime, timedelta

from data_pipeline.youtube_channels import get_channel_weight, is_trusted_channel

logger = logging.getLogger("tradedo.youtube")

YT_DB_PATH = Path(__file__).resolve().parent.parent.parent.parent / "data" / "youtube_cache.db"


# ═══════════════════════════════════════════════════════════════
#   STOCK NAME MAPPING
# ═══════════════════════════════════════════════════════════════

STOCK_ALIASES = {
    "RELIANCE":    ["reliance", "ril", "ambani", "reliance industries", "jio"],
    "TCS":         ["tcs", "tata consultancy"],
    "HDFCBANK":    ["hdfc bank", "hdfcbank"],
    "INFY":        ["infosys", "infy"],
    "WIPRO":       ["wipro"],
    "TATAMOTORS":  ["tata motors", "tatamotors", "tml"],
    "ADANIENT":    ["adani enterprises", "adani ent", "adani"],
    "ICICIBANK":   ["icici bank", "icicibank", "icici"],
    "SBIN":        ["sbi", "state bank", "state bank of india"],
    "BAJFINANCE":  ["bajaj finance", "bajfin"],
    "HDFCLIFE":    ["hdfc life", "hdfclife"],
    "KOTAKBANK":   ["kotak bank", "kotak mahindra", "kotakbank"],
    "AXISBANK":    ["axis bank", "axisbank"],
    "HINDUNILVR":  ["hindustan unilever", "hul", "hindunilvr"],
    "ITC":         ["itc"],
    "BHARTIARTL":  ["bharti airtel", "airtel"],
    "MARUTI":      ["maruti", "maruti suzuki"],
    "TITAN":       ["titan"],
    "SUNPHARMA":   ["sun pharma", "sunpharma"],
    "HCLTECH":     ["hcl tech", "hcl technologies", "hcltech"],
    "TECHM":       ["tech mahindra", "techm"],
    "ASIANPAINT":  ["asian paints", "asianpaint"],
    "IRCTC":       ["irctc"],
    "ZOMATO":      ["zomato"],
    "PAYTM":       ["paytm"],
    "IREDA":       ["ireda"],
    "SUZLON":      ["suzlon"],
    "IRFC":        ["irfc"],
    "YESBANK":     ["yes bank", "yesbank"],
    "TATASTEEL":   ["tata steel", "tatasteel"],
    "JSWSTEEL":    ["jsw steel", "jswsteel"],
    "NTPC":        ["ntpc"],
    "POWERGRID":   ["power grid", "powergrid"],
    "COALINDIA":   ["coal india", "coalindia"],
    "ONGC":        ["ongc"],
    "BPCL":        ["bpcl", "bharat petroleum"],
    "IOC":         ["ioc", "indian oil"],
    "TATAPOWER":   ["tata power", "tatapower"],
}


def get_stock_search_terms(symbol: str) -> List[str]:
    """Get search terms for a stock."""
    clean = symbol.replace(".NS", "").replace(".BO", "").upper()
    return STOCK_ALIASES.get(clean, [clean.lower()])


# ═══════════════════════════════════════════════════════════════
#   KEYWORD LISTS
# ═══════════════════════════════════════════════════════════════

BULLISH_KEYWORDS = [
    "buy", "long", "bullish", "target", "upside", "breakout",
    "accumulate", "positive", "strong", "growth", "outperform",
    "recommend", "invest", "opportunity", "rally", "surge", 
    "gain", "up", "moon", "hold", "add", "excellent"
]

BEARISH_KEYWORDS = [
    "sell", "short", "bearish", "avoid", "downside", "breakdown",
    "exit", "negative", "weak", "risk", "underperform",
    "correction", "crash", "fall", "book profit", "cut", 
    "reduce", "concern", "warning", "danger"
]


# ═══════════════════════════════════════════════════════════════
#   MAIN ANALYSIS FUNCTION
# ═══════════════════════════════════════════════════════════════

def fetch_youtube_intel(symbol: str) -> Dict:
    """
    Analyze cached YouTube transcripts for stock mentions.
    FAST - just DB queries, no live scraping.
    """
    if not YT_DB_PATH.exists():
        return _empty_response(symbol, error="YouTube cache not initialized. Run sync first.")
    
    clean_symbol = symbol.replace(".NS", "").replace(".BO", "").upper()
    search_terms = get_stock_search_terms(symbol)
    
    logger.info(f"🎥 YouTube: analyzing cached transcripts for {clean_symbol}...")
    
    # Query DB for videos mentioning this stock
    conn = sqlite3.connect(str(YT_DB_PATH))
    conn.row_factory = sqlite3.Row
    
    # Build LIKE query for all search terms
    conditions = []
    params = []
    for term in search_terms:
        conditions.append("LOWER(title) LIKE ? OR LOWER(transcript) LIKE ? OR LOWER(description) LIKE ?")
        term_pattern = f"%{term}%"
        params.extend([term_pattern, term_pattern, term_pattern])
    
    query = f"""
        SELECT * FROM videos
        WHERE transcript IS NOT NULL 
        AND transcript != ''
        AND ({' OR '.join(conditions)})
        ORDER BY published DESC
        LIMIT 15
    """
    
    videos = [dict(r) for r in conn.execute(query, params).fetchall()]
    conn.close()
    
    if not videos:
        return _empty_response(symbol)
    
    logger.info(f"  → Found {len(videos)} videos mentioning {clean_symbol}")
    
    # Analyze each video
    analyses = []
    for video in videos:
        analysis = analyze_video(video, search_terms, clean_symbol)
        if analysis["mentions"] > 0:
            analyses.append({**video, "analysis": analysis})
    
    if not analyses:
        return _empty_response(symbol)
    
    # Aggregate results
    return aggregate_analyses(analyses, clean_symbol)


def analyze_video(video: Dict, search_terms: List[str], symbol: str) -> Dict:
    """Analyze a single video transcript."""
    transcript = (video.get("transcript") or "").lower()
    title = (video.get("title") or "").lower()
    
    # Count mentions
    mentions = 0
    for term in search_terms:
        mentions += transcript.count(term)
        mentions += title.count(term) * 3   # Title mentions weight 3x
    
    if mentions == 0:
        return {
            "score": 0, "label": "NEUTRAL", "mentions": 0,
            "bullish_signals": 0, "bearish_signals": 0,
            "targets": [], "stop_losses": [],
        }
    
    # Count sentiment words (only near stock mentions)
    bullish = 0
    bearish = 0
    
    # Get context around each mention
    for term in search_terms:
        positions = [m.start() for m in re.finditer(re.escape(term), transcript)]
        for pos in positions:
            # 200 chars around mention
            start = max(0, pos - 200)
            end = min(len(transcript), pos + 200)
            context = transcript[start:end]
            
            bullish += sum(context.count(w) for w in BULLISH_KEYWORDS)
            bearish += sum(context.count(w) for w in BEARISH_KEYWORDS)
    
    # Extract price targets (looking for numbers after "target" or near stock name)
    targets = []
    stop_losses = []
    
    target_patterns = [
        r'target[s]?\s+(?:of\s+)?(?:rs\.?|₹|inr)?\s*(\d+(?:,\d+)*(?:\.\d+)?)',
        r'target\s+price\s+(?:of\s+)?(?:rs\.?|₹|inr)?\s*(\d+(?:,\d+)*(?:\.\d+)?)',
        r'(?:can|will|may|might)\s+(?:go|reach|hit|touch)\s+(?:rs\.?|₹)?\s*(\d+(?:,\d+)*(?:\.\d+)?)',
    ]
    
    for pattern in target_patterns:
        matches = re.findall(pattern, transcript)
        for m in matches:
            try:
                price = float(m.replace(",", ""))
                if 10 <= price <= 100000:  # Reasonable price range
                    targets.append(price)
            except ValueError:
                continue
    
    sl_pattern = r'(?:stop\s*loss|sl)\s+(?:at\s+)?(?:rs\.?|₹)?\s*(\d+(?:,\d+)*(?:\.\d+)?)'
    for m in re.findall(sl_pattern, transcript):
        try:
            price = float(m.replace(",", ""))
            if 10 <= price <= 100000:
                stop_losses.append(price)
        except ValueError:
            continue
    
    # Sentiment score
    total = bullish + bearish
    score = (bullish - bearish) / total if total > 0 else 0
    
    if score > 0.3:
        label = "BULLISH"
    elif score < -0.3:
        label = "BEARISH"
    else:
        label = "NEUTRAL"
    
    return {
        "score": round(score, 3),
        "label": label,
        "mentions": mentions,
        "bullish_signals": bullish,
        "bearish_signals": bearish,
        "targets": targets[:5],
        "stop_losses": stop_losses[:3],
    }


def aggregate_analyses(videos: List[Dict], symbol: str) -> Dict:
    """Aggregate all video analyses."""
    total_weight = 0
    weighted_score = 0
    all_targets = []
    all_stop_losses = []
    total_bullish = 0
    total_bearish = 0
    total_mentions = 0
    trusted_count = 0
    
    top_videos = []
    
    for video in videos:
        analysis = video["analysis"]
        base_weight = video.get("trust_weight", 0.5)
        
        # Recency bonus: newer videos count more
        try:
            pub_date = datetime.fromisoformat(video["published"])
            days_old = (datetime.now() - pub_date).days
            recency_multiplier = max(0.3, 1.5 - (days_old * 0.05))  # 100% at day 0, decays
        except:
            recency_multiplier = 1.0
        
        # Mentions weight
        mention_boost = min(2.0, 1 + (analysis["mentions"] * 0.1))
        
        final_weight = base_weight * recency_multiplier * mention_boost
        
        weighted_score += analysis["score"] * final_weight
        total_weight += final_weight
        
        all_targets.extend(analysis["targets"])
        all_stop_losses.extend(analysis["stop_losses"])
        total_bullish += analysis["bullish_signals"]
        total_bearish += analysis["bearish_signals"]
        total_mentions += analysis["mentions"]
        
        if base_weight >= 0.8:
            trusted_count += 1
        
        top_videos.append({
            "title": video["title"][:100],
            "channel": video["channel_name"],
            "url": f"https://youtube.com/watch?v={video['video_id']}",
            "published": video["published"],
            "is_trusted": base_weight >= 0.8,
            "sentiment": analysis["label"],
            "mentions": analysis["mentions"],
            "targets": analysis["targets"][:3],
        })
    
    # Final score
    final_score = weighted_score / total_weight if total_weight > 0 else 0
    final_score = max(-1.0, min(1.0, final_score))
    
    # Label
    if final_score > 0.3:
        label = "BULLISH"
    elif final_score < -0.3:
        label = "BEARISH"
    else:
        label = "NEUTRAL"
    
    # Consensus target
    consensus_target = None
    median_target = None
    if all_targets:
        # Filter outliers (targets should be within 30% of median)
        sorted_targets = sorted(all_targets)
        median_target = sorted_targets[len(sorted_targets) // 2]
        
        filtered = [t for t in all_targets if 0.7 * median_target <= t <= 1.3 * median_target]
        if filtered:
            consensus_target = round(sum(filtered) / len(filtered), 2)
    
    # Confidence
    if len(videos) >= 5 and trusted_count >= 3:
        confidence = "VERY_HIGH"
    elif len(videos) >= 3 and trusted_count >= 2:
        confidence = "HIGH"
    elif len(videos) >= 2:
        confidence = "MEDIUM"
    else:
        confidence = "LOW"
    
    return {
        "score":            round(final_score, 3),
        "label":            label,
        "confidence":       confidence,
        "videos_analyzed":  len(videos),
        "trusted_videos":   trusted_count,
        "total_mentions":   total_mentions,
        "bullish_signals":  total_bullish,
        "bearish_signals":  total_bearish,
        "consensus_target": consensus_target,
        "median_target":    median_target,
        "target_count":     len(all_targets),
        "all_targets":      sorted(list(set(all_targets)))[:10],
        "stop_losses":      sorted(list(set(all_stop_losses)))[:5],
        "top_videos":       top_videos[:5],
    }


def _empty_response(symbol: str, error: str = None) -> Dict:
    """Empty response when no data."""
    response = {
        "score":            0.0,
        "label":            "NO_DATA",
        "confidence":       "NONE",
        "videos_analyzed":  0,
        "trusted_videos":   0,
        "total_mentions":   0,
        "bullish_signals":  0,
        "bearish_signals":  0,
        "consensus_target": None,
        "median_target":    None,
        "target_count":     0,
        "all_targets":      [],
        "stop_losses":      [],
        "top_videos":       [],
    }
    
    if error:
        response["error"] = error
    
    return response


# Quick test
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    for symbol in ["RELIANCE", "TCS", "HDFCBANK"]:
        print(f"\n{'='*60}")
        print(f"YouTube Intel: {symbol}")
        print("="*60)
        result = fetch_youtube_intel(symbol)
        
        print(f"Score: {result['score']}")
        print(f"Label: {result['label']}")
        print(f"Confidence: {result['confidence']}")
        print(f"Videos: {result['videos_analyzed']}")
        print(f"Trusted: {result['trusted_videos']}")
        print(f"Mentions: {result['total_mentions']}")
        print(f"Target: {result['consensus_target']}")
        
        if result['top_videos']:
            print(f"\nTop videos:")
            for v in result['top_videos'][:3]:
                print(f"  - {v['title'][:80]}")
                print(f"    {v['channel']} · {v['sentiment']}")
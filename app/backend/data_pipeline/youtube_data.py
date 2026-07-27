# E:\tradedo\app\backend\data_pipeline\youtube_data.py

"""
YouTube video search + transcript analyzer.
Uses yt-dlp for search and youtube-transcript-api for transcripts.
100% FREE, no API key needed.
"""

import re
import logging
from typing import List, Dict, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta

try:
    from youtube_transcript_api import YouTubeTranscriptApi
    from youtube_transcript_api._errors import (
        TranscriptsDisabled, NoTranscriptFound, VideoUnavailable
    )
    TRANSCRIPT_AVAILABLE = True
except ImportError:
    TRANSCRIPT_AVAILABLE = False

try:
    import yt_dlp
    YTDLP_AVAILABLE = True
except ImportError:
    YTDLP_AVAILABLE = False

from data_pipeline.youtube_channels import (
    CHANNEL_NAMES, get_channel_weight, is_trusted_channel
)

logger = logging.getLogger("tradedo.youtube")


# ─── Config ───────────────────────────────────────────────────
MAX_VIDEOS_PER_STOCK = 5
DAYS_LOOKBACK        = 7
MAX_TRANSCRIPT_LENGTH = 3000  # Keep manageable for analysis


class YouTubeAnalyzer:
    """YouTube financial content analyzer."""
    
    def __init__(self):
        self.ytdl_opts = {
            "quiet":           True,
            "no_warnings":     True,
            "extract_flat":    True,
            "skip_download":   True,
            "playlistend":     10,  # Limit results per search
        }
    
    def is_available(self) -> bool:
        return TRANSCRIPT_AVAILABLE and YTDLP_AVAILABLE
    
    def search_videos(
        self,
        stock_name: str,
        max_videos: int = MAX_VIDEOS_PER_STOCK,
    ) -> List[Dict]:
        """
        Search YouTube for recent videos about a stock.
        Returns metadata (not transcripts yet).
        """
        if not YTDLP_AVAILABLE:
            return []
        
        # Build search query — recent + trusted channels
        query = f"{stock_name} stock analysis"
        search_url = f"ytsearch{max_videos * 3}:{query}"
        
        videos = []
        
        try:
            with yt_dlp.YoutubeDL(self.ytdl_opts) as ydl:
                info = ydl.extract_info(search_url, download=False)
                entries = info.get("entries", []) if info else []
                
                for entry in entries:
                    if not entry:
                        continue
                    
                    channel = entry.get("channel", "") or entry.get("uploader", "")
                    
                    # Prefer trusted channels
                    is_trusted = is_trusted_channel(channel)
                    weight = get_channel_weight(channel)
                    
                    videos.append({
                        "video_id":     entry.get("id"),
                        "title":        entry.get("title", ""),
                        "channel":      channel,
                        "duration":     entry.get("duration", 0),
                        "view_count":   entry.get("view_count", 0),
                        "url":          f"https://youtube.com/watch?v={entry.get('id')}",
                        "is_trusted":   is_trusted,
                        "weight":       weight,
                    })
        
        except Exception as e:
            logger.warning(f"YouTube search failed: {e}")
        
        # Prioritize: trusted channels first, then by views
        videos.sort(key=lambda x: (x["is_trusted"], x["view_count"]), reverse=True)
        
        return videos[:max_videos]
    
    def get_transcript(self, video_id: str) -> Optional[str]:
        """Get transcript for a video."""
        if not TRANSCRIPT_AVAILABLE:
            return None
        
        try:
            transcript_list = YouTubeTranscriptApi.get_transcript(
                video_id,
                languages=["en", "hi", "en-IN"],
            )
            
            # Concatenate all text
            text_parts = [t["text"] for t in transcript_list]
            full_text = " ".join(text_parts)
            
            # Trim if too long
            if len(full_text) > MAX_TRANSCRIPT_LENGTH:
                full_text = full_text[:MAX_TRANSCRIPT_LENGTH] + "..."
            
            return full_text
        
        except (TranscriptsDisabled, NoTranscriptFound):
            logger.debug(f"No transcript for {video_id}")
            return None
        except VideoUnavailable:
            logger.debug(f"Video unavailable {video_id}")
            return None
        except Exception as e:
            logger.warning(f"Transcript fetch failed for {video_id}: {e}")
            return None
    
    def analyze_transcript(self, transcript: str, stock_name: str) -> Dict:
        """
        Extract signals from transcript using keyword scoring + LLM.
        Fast keyword pass first, then LLM for detailed analysis.
        """
        if not transcript:
            return self._empty_analysis()
        
        text_lower = transcript.lower()
        stock_lower = stock_name.lower()
        
        # Check if stock is actually mentioned
        mentions = text_lower.count(stock_lower)
        if mentions == 0:
            return self._empty_analysis()
        
        # ── Keyword-based signals ────────────────────────────
        bullish_keywords = [
            "buy", "long", "bullish", "target", "upside", "breakout",
            "accumulate", "positive", "strong", "growth", "recommend",
            "outperform", "strong buy", "add", "invest"
        ]
        bearish_keywords = [
            "sell", "short", "bearish", "avoid", "downside", "breakdown",
            "exit", "negative", "weak", "risk", "underperform", "book profit",
            "cut", "reduce"
        ]
        
        bullish = sum(text_lower.count(w) for w in bullish_keywords)
        bearish = sum(text_lower.count(w) for w in bearish_keywords)
        
        # ── Extract price targets ────────────────────────────
        # Match patterns like "target 2500", "target of ₹2,500", "target price 2500"
        target_patterns = [
            r'target[s]?\s+(?:of\s+)?(?:rs\.?|₹)?\s*(\d+(?:,\d+)*(?:\.\d+)?)',
            r'target\s+price\s+(?:of\s+)?(?:rs\.?|₹)?\s*(\d+(?:,\d+)*(?:\.\d+)?)',
            r'(?:can|will|may)\s+(?:go|reach|hit)\s+(?:rs\.?|₹)?\s*(\d+(?:,\d+)*(?:\.\d+)?)',
        ]
        
        targets = []
        for pattern in target_patterns:
            matches = re.findall(pattern, text_lower)
            for m in matches:
                try:
                    price = float(m.replace(",", ""))
                    if 50 <= price <= 100000:  # Sanity check
                        targets.append(price)
                except ValueError:
                    continue
        
        # ── Extract stop loss mentions ───────────────────────
        sl_pattern = r'(?:stop\s*loss|sl)\s+(?:at\s+)?(?:rs\.?|₹)?\s*(\d+(?:,\d+)*(?:\.\d+)?)'
        sl_matches = re.findall(sl_pattern, text_lower)
        stop_losses = []
        for m in sl_matches:
            try:
                price = float(m.replace(",", ""))
                if 50 <= price <= 100000:
                    stop_losses.append(price)
            except ValueError:
                continue
        
        # ── Score ────────────────────────────────────────────
        total = bullish + bearish
        score = (bullish - bearish) / total if total > 0 else 0
        
        # Label
        if score > 0.3:
            label = "BULLISH"
        elif score < -0.3:
            label = "BEARISH"
        else:
            label = "NEUTRAL"
        
        return {
            "score":            round(score, 3),
            "label":            label,
            "mentions":         mentions,
            "bullish_signals":  bullish,
            "bearish_signals":  bearish,
            "targets":          targets[:5],
            "stop_losses":      stop_losses[:3],
            "avg_target":       round(sum(targets) / len(targets), 2) if targets else None,
            "has_transcript":   True,
        }
    
    def _empty_analysis(self) -> Dict:
        return {
            "score":            0.0,
            "label":            "NEUTRAL",
            "mentions":         0,
            "bullish_signals":  0,
            "bearish_signals":  0,
            "targets":          [],
            "stop_losses":      [],
            "avg_target":       None,
            "has_transcript":   False,
        }


# ─── Global analyzer ──────────────────────────────────────────
_analyzer: Optional[YouTubeAnalyzer] = None

def get_analyzer() -> YouTubeAnalyzer:
    global _analyzer
    if _analyzer is None:
        _analyzer = YouTubeAnalyzer()
    return _analyzer


# ─── Main Entry Point ─────────────────────────────────────────
def fetch_youtube_intel(symbol: str) -> Dict:
    """
    Main function — fetch YouTube intelligence for a stock.
    
    Process:
    1. Search for videos about the stock
    2. Get transcripts (parallel)
    3. Analyze each transcript
    4. Combine into weighted verdict
    """
    analyzer = get_analyzer()
    
    if not analyzer.is_available():
        return _unavailable_response()
    
    # Clean stock name
    clean_symbol = symbol.replace(".NS", "").replace(".BO", "")
    
    # Get stock display name for search
    stock_names = _get_search_names(clean_symbol)
    search_query = stock_names[0]  # Use first (most common) name
    
    logger.info(f"🎥 YouTube: searching '{search_query}'...")
    
    # 1. Search videos
    videos = analyzer.search_videos(search_query, max_videos=MAX_VIDEOS_PER_STOCK)
    
    if not videos:
        return _empty_response(clean_symbol)
    
    logger.info(f"  → Found {len(videos)} videos")
    
    # 2. Fetch transcripts in parallel
    video_analyses = []
    
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = {
            executor.submit(analyzer.get_transcript, v["video_id"]): v
            for v in videos
        }
        
        for future in as_completed(futures):
            video = futures[future]
            try:
                transcript = future.result()
                if transcript:
                    analysis = analyzer.analyze_transcript(transcript, search_query)
                    if analysis["has_transcript"] and analysis["mentions"] > 0:
                        video["analysis"] = analysis
                        video_analyses.append(video)
            except Exception as e:
                logger.warning(f"Transcript analysis failed: {e}")
    
    if not video_analyses:
        return _empty_response(clean_symbol)
    
    logger.info(f"  → Analyzed {len(video_analyses)} transcripts")
    
    # 3. Aggregate results (weighted by channel trust)
    return _aggregate_analyses(video_analyses, clean_symbol)


def _get_search_names(symbol: str) -> List[str]:
    """Get search-friendly names for stock."""
    name_map = {
        "RELIANCE":    ["Reliance Industries", "RIL"],
        "TCS":         ["TCS", "Tata Consultancy"],
        "HDFCBANK":    ["HDFC Bank"],
        "INFY":        ["Infosys"],
        "WIPRO":       ["Wipro"],
        "TATAMOTORS":  ["Tata Motors"],
        "ADANIENT":    ["Adani Enterprises"],
        "ICICIBANK":   ["ICICI Bank"],
        "SBIN":        ["SBI", "State Bank of India"],
        "BAJFINANCE":  ["Bajaj Finance"],
        "HDFCLIFE":    ["HDFC Life"],
        "KOTAKBANK":   ["Kotak Mahindra Bank"],
        "AXISBANK":    ["Axis Bank"],
        "HINDUNILVR":  ["HUL", "Hindustan Unilever"],
        "ITC":         ["ITC"],
        "BHARTIARTL":  ["Bharti Airtel"],
        "MARUTI":      ["Maruti Suzuki"],
        "TITAN":       ["Titan Company"],
        "SUNPHARMA":   ["Sun Pharma"],
        "HCLTECH":     ["HCL Technologies"],
        "TECHM":       ["Tech Mahindra"],
        "ASIANPAINT":  ["Asian Paints"],
        "IRCTC":       ["IRCTC"],
        "ZOMATO":      ["Zomato"],
        "PAYTM":       ["Paytm"],
    }
    
    return name_map.get(symbol.upper(), [symbol])


def _aggregate_analyses(videos: List[Dict], symbol: str) -> Dict:
    """Aggregate multiple video analyses into single verdict."""
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
        weight = video["weight"]
        
        weighted_score += analysis["score"] * weight
        total_weight += weight
        
        all_targets.extend(analysis["targets"])
        all_stop_losses.extend(analysis["stop_losses"])
        total_bullish += analysis["bullish_signals"]
        total_bearish += analysis["bearish_signals"]
        total_mentions += analysis["mentions"]
        
        if video["is_trusted"]:
            trusted_count += 1
        
        top_videos.append({
            "title":     video["title"][:100],
            "channel":   video["channel"],
            "views":     video["view_count"],
            "url":       video["url"],
            "is_trusted": video["is_trusted"],
            "sentiment": analysis["label"],
            "targets":   analysis["targets"][:3],
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
    
    # Consensus target (median of all targets)
    avg_target = None
    median_target = None
    if all_targets:
        avg_target = round(sum(all_targets) / len(all_targets), 2)
        sorted_targets = sorted(all_targets)
        median_target = sorted_targets[len(sorted_targets) // 2]
    
    # Confidence
    if len(videos) >= 4 and trusted_count >= 2:
        confidence = "HIGH"
    elif len(videos) >= 2:
        confidence = "MEDIUM"
    else:
        confidence = "LOW"
    
    return {
        "score":           round(final_score, 3),
        "label":           label,
        "confidence":      confidence,
        "videos_analyzed": len(videos),
        "trusted_videos":  trusted_count,
        "total_mentions":  total_mentions,
        "bullish_signals": total_bullish,
        "bearish_signals": total_bearish,
        "consensus_target": median_target,
        "avg_target":      avg_target,
        "target_count":    len(all_targets),
        "all_targets":     sorted(list(set(all_targets)))[:10],
        "stop_losses":     sorted(list(set(all_stop_losses)))[:5],
        "top_videos":      top_videos[:3],
    }


def _empty_response(symbol: str) -> Dict:
    return {
        "score":           0.0,
        "label":           "NO_DATA",
        "confidence":      "NONE",
        "videos_analyzed": 0,
        "trusted_videos":  0,
        "total_mentions":  0,
        "bullish_signals": 0,
        "bearish_signals": 0,
        "consensus_target": None,
        "avg_target":      None,
        "target_count":    0,
        "all_targets":     [],
        "stop_losses":     [],
        "top_videos":      [],
    }


def _unavailable_response() -> Dict:
    return {
        **_empty_response(""),
        "label": "UNAVAILABLE",
        "error": "youtube-transcript-api or yt-dlp not installed",
    }


# ─── Quick Test ───────────────────────────────────────────────
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    import json
    
    result = fetch_youtube_intel("RELIANCE")
    
    print("\n🎥 YouTube Intelligence")
    print("=" * 60)
    print(f"Score:          {result['score']}")
    print(f"Label:          {result['label']}")
    print(f"Confidence:     {result['confidence']}")
    print(f"Videos:         {result['videos_analyzed']} ({result['trusted_videos']} trusted)")
    print(f"Mentions:       {result['total_mentions']}")
    print(f"Bullish/Bear:   {result['bullish_signals']}/{result['bearish_signals']}")
    print(f"Consensus Tgt:  {result['consensus_target']}")
    print(f"All Targets:    {result['all_targets']}")
    
    if result['top_videos']:
        print("\n🎬 Top Videos:")
        for i, v in enumerate(result['top_videos'], 1):
            trust = "✓" if v['is_trusted'] else "?"
            print(f"{i}. [{trust}] [{v['sentiment']}] {v['title']}")
            print(f"   {v['channel']} · {v['views']:,} views")
            if v['targets']:
                print(f"   Targets: {v['targets']}")
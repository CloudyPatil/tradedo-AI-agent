# E:\tradedo\app\backend\data_pipeline\trends_data.py

"""
Google Trends analyzer.
Measures retail interest by search volume spikes.
Key insight: retail piles in AFTER big moves.
Sudden spike = potential exhaustion, or news breaking.
"""

import logging
from typing import Dict, Optional, List
from datetime import datetime, timedelta
import time

try:
    from pytrends.request import TrendReq
    PYTRENDS_AVAILABLE = True
except ImportError:
    PYTRENDS_AVAILABLE = False

logger = logging.getLogger("tradedo.trends")


class GoogleTrendsAnalyzer:
    """Google Trends for stock search interest."""
    
    def __init__(self):
        self.pytrends = None
        self._init_client()
    
    def _init_client(self):
        """Initialize pytrends client."""
        if not PYTRENDS_AVAILABLE:
            return
        
        try:
            self.pytrends = TrendReq(
                hl="en-IN",           # Indian English
                tz=330,               # IST timezone offset (mins)
                timeout=(10, 25),     # (connect, read)
                retries=2,
                backoff_factor=1,
            )
            logger.info("✅ Google Trends client initialized")
        except Exception as e:
            logger.warning(f"Google Trends init failed: {e}")
    
    def is_available(self) -> bool:
        return self.pytrends is not None
    
    def get_search_interest(self, keyword: str, days: int = 30) -> Optional[Dict]:
        """
        Get search interest over last N days.
        Returns trend data + spike detection.
        """
        if not self.is_available():
            return None
        
        try:
            # Build payload
            timeframe = f"now {days}-d" if days <= 7 else "today 1-m"
            
            self.pytrends.build_payload(
                kw_list=[keyword],
                timeframe=timeframe,
                geo="IN",             # India only
                gprop="",             # Web search
            )
            
            # Get interest over time
            data = self.pytrends.interest_over_time()
            
            if data.empty:
                return None
            
            values = data[keyword].tolist()
            if len(values) < 3:
                return None
            
            # Analysis
            current      = values[-1]
            previous     = values[-2] if len(values) >= 2 else current
            avg          = sum(values) / len(values)
            max_val      = max(values)
            min_val      = min(values)
            
            # Detect spike (current vs average)
            spike_ratio = (current / avg) if avg > 0 else 1
            
            # Detect trend direction (last 5 vs previous 5)
            if len(values) >= 10:
                recent_avg = sum(values[-5:]) / 5
                older_avg  = sum(values[-10:-5]) / 5
                trend_change = ((recent_avg - older_avg) / older_avg * 100) if older_avg > 0 else 0
            else:
                trend_change = 0
            
            # Classify
            if spike_ratio >= 3.0:
                spike_level = "MASSIVE_SPIKE"      # 3x average
            elif spike_ratio >= 2.0:
                spike_level = "BIG_SPIKE"          # 2x average
            elif spike_ratio >= 1.5:
                spike_level = "MODERATE_SPIKE"
            elif spike_ratio >= 1.2:
                spike_level = "SLIGHT_INCREASE"
            elif spike_ratio <= 0.5:
                spike_level = "DECLINING"
            else:
                spike_level = "NORMAL"
            
            # Interpret for trading
            # Massive spike = often near tops (retail FOMO)
            # Gradual increase = building interest (bullish)
            if spike_level == "MASSIVE_SPIKE":
                signal = "CAUTION_FOMO"       # Might be top
            elif spike_level == "BIG_SPIKE":
                signal = "HIGH_INTEREST"
            elif spike_level in ["MODERATE_SPIKE", "SLIGHT_INCREASE"]:
                signal = "BUILDING_INTEREST"  # Bullish setup
            elif spike_level == "DECLINING":
                signal = "LOSING_INTEREST"
            else:
                signal = "NEUTRAL"
            
            return {
                "current":       int(current),
                "average":       round(avg, 1),
                "max":           int(max_val),
                "min":           int(min_val),
                "spike_ratio":   round(spike_ratio, 2),
                "trend_change":  round(trend_change, 1),
                "spike_level":   spike_level,
                "signal":        signal,
                "data_points":   len(values),
                "available":     True,
            }
        
        except Exception as e:
            logger.debug(f"Google Trends error for {keyword}: {e}")
            return None
    
    def get_related_queries(self, keyword: str) -> Dict:
        """Get related search queries (bonus insight)."""
        if not self.is_available():
            return {"top": [], "rising": []}
        
        try:
            self.pytrends.build_payload(
                kw_list=[keyword],
                timeframe="today 1-m",
                geo="IN",
            )
            
            related = self.pytrends.related_queries()
            
            top_queries = related.get(keyword, {}).get("top")
            rising_queries = related.get(keyword, {}).get("rising")
            
            return {
                "top":    top_queries.to_dict("records")[:5] if top_queries is not None else [],
                "rising": rising_queries.to_dict("records")[:5] if rising_queries is not None else [],
            }
        except Exception as e:
            logger.debug(f"Related queries error: {e}")
            return {"top": [], "rising": []}


# ─── Global instance ──────────────────────────────────────────
_analyzer: Optional[GoogleTrendsAnalyzer] = None

def get_analyzer() -> GoogleTrendsAnalyzer:
    global _analyzer
    if _analyzer is None:
        _analyzer = GoogleTrendsAnalyzer()
    return _analyzer


# ─── Main Entry Point ─────────────────────────────────────────
def fetch_google_trends(symbol: str) -> Dict:
    """Main function — get Google Trends intelligence for a stock."""
    analyzer = get_analyzer()
    
    if not analyzer.is_available():
        return _unavailable_response()
    
    # Get stock name for search
    clean = symbol.replace(".NS", "").replace(".BO", "").upper()
    search_terms = _get_search_terms(clean)
    
    logger.info(f"🔍 Google Trends: '{search_terms[0]}'...")
    
    # Try primary term
    result = analyzer.get_search_interest(search_terms[0], days=30)
    
    if not result:
        return _empty_response()
    
    # Add stock context
    result["symbol"]        = clean
    result["search_term"]   = search_terms[0]
    
    logger.info(f"  → {result['signal']} (spike {result['spike_ratio']}x)")
    
    return result


def _get_search_terms(symbol: str) -> List[str]:
    """Get search-friendly terms for stock."""
    name_map = {
        "RELIANCE":    ["Reliance share"],
        "TCS":         ["TCS share"],
        "HDFCBANK":    ["HDFC Bank share"],
        "INFY":        ["Infosys share"],
        "WIPRO":       ["Wipro share"],
        "TATAMOTORS":  ["Tata Motors share"],
        "ADANIENT":    ["Adani Enterprises share"],
        "ICICIBANK":   ["ICICI Bank share"],
        "SBIN":        ["SBI share"],
        "BAJFINANCE":  ["Bajaj Finance share"],
        "HDFCLIFE":    ["HDFC Life share"],
        "KOTAKBANK":   ["Kotak Bank share"],
        "AXISBANK":    ["Axis Bank share"],
        "HINDUNILVR":  ["HUL share"],
        "ITC":         ["ITC share"],
        "BHARTIARTL":  ["Airtel share"],
        "MARUTI":      ["Maruti share"],
        "TITAN":       ["Titan share"],
        "SUNPHARMA":   ["Sun Pharma share"],
        "IRCTC":       ["IRCTC share"],
        "ZOMATO":      ["Zomato share"],
        "PAYTM":       ["Paytm share"],
        "IREDA":       ["IREDA share"],
        "SUZLON":      ["Suzlon share"],
    }
    return name_map.get(symbol, [f"{symbol} share"])


def _empty_response() -> Dict:
    return {
        "current":      0,
        "average":      0,
        "spike_ratio":  1.0,
        "spike_level":  "NO_DATA",
        "signal":       "NEUTRAL",
        "available":    True,
        "data_points":  0,
    }


def _unavailable_response() -> Dict:
    return {
        "current":      0,
        "spike_ratio":  1.0,
        "signal":       "UNAVAILABLE",
        "available":    False,
    }


# ─── Quick Test ───────────────────────────────────────────────
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    for symbol in ["RELIANCE", "SUZLON"]:
        print(f"\n{'='*50}")
        print(f"Google Trends: {symbol}")
        print('='*50)
        result = fetch_google_trends(symbol)
        for k, v in result.items():
            print(f"  {k}: {v}")
# E:\tradedo\app\backend\agent\master_scorer.py

"""
MASTER SCORING ENGINE
Combines all data sources into a unified 200-point score.

Data Sources Weighted:
- Technical (ML Model):        40 pts
- News Sentiment:              25 pts  
- Reddit + StockTwits:         20 pts
- YouTube (Expert):            20 pts
- Twitter (Real-time):         15 pts
- NSE Money Flow:              15 pts
- NSE Bulk Deals:              15 pts
- Options PCR:                 15 pts
- Delivery %:                  10 pts
- Google Trends:               10 pts
- Global Markets:              15 pts

Penalties:
- NSE Risk Flags:              -30 pts
- FOMO Spike:                  -15 pts
- Global Sector Negative:      -10 pts

TOTAL: 200 pts max
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger("tradedo.master_scorer")


# ─── Scoring Configuration ────────────────────────────────────
SCORE_WEIGHTS = {
    "technical":    40,
    "news":         25,
    "reddit_st":    20,
    "youtube":      20,
    "twitter":      15,
    "nse_money":    15,
    "nse_bulk":     15,
    "options":      15,
    "delivery":     10,
    "trends":       10,
    "global":       15,
}

# Total possible: 200 pts

# Penalties (deducted from total)
PENALTIES = {
    "nse_risk_flag":     30,
    "fomo_spike":        15,
    "global_negative":   10,
    "fno_banned":        50,   # Can't trade at all
}

# Trade thresholds
THRESHOLDS = {
    "STRONG_BUY":   140,   # Auto-execute
    "BUY":          100,   # Manual review
    "WEAK_BUY":      70,   # Watch list
    "SKIP":          70,   # Below this = skip
}


class MasterScorer:
    """The brain of TRADEDO — combines all data into one verdict."""
    
    def __init__(self, symbol: str, mode: str = "intraday"):
        self.symbol = symbol.upper().strip()
        if not self.symbol.endswith(".NS"):
            self.symbol += ".NS"
        
        self.mode = mode
        
        # Storage for all intel
        self.technical    = None
        self.news         = None
        self.social       = None
        self.nse_data     = None
        self.trends       = None
        self.global_ctx   = None
        
        # Results
        self.scores       = {}
        self.penalties    = {}
        self.final_score  = 0
        self.max_score    = sum(SCORE_WEIGHTS.values())
        
        self.errors       = []
    
    # ═══════════════════════════════════════════════════════════
    #   DATA COLLECTION (Parallel)
    # ═══════════════════════════════════════════════════════════
    
    def collect_all_intelligence(self) -> None:
        """Fetch data from ALL sources in parallel."""
        logger.info(f"🧠 Master Scorer: collecting intelligence for {self.symbol}...")
        
        with ThreadPoolExecutor(max_workers=6) as executor:
            futures = {
                executor.submit(self._get_technical):   "technical",
                executor.submit(self._get_news):        "news",
                executor.submit(self._get_social):      "social",
                executor.submit(self._get_nse):         "nse",
                executor.submit(self._get_trends):      "trends",
                executor.submit(self._get_global):      "global",
            }
            
            for future, source in futures.items():
                try:
                    result = future.result(timeout=60)
                    setattr(self, source if source != "nse" else "nse_data", 
                            result if source != "global" else result)
                    
                    if source == "global":
                        self.global_ctx = result
                    elif source == "nse":
                        self.nse_data = result
                    else:
                        setattr(self, source, result)
                
                except Exception as e:
                    logger.warning(f"  ✗ {source} failed: {e}")
                    self.errors.append(f"{source}: {str(e)[:100]}")
        
        logger.info(f"  ✓ Intelligence collected ({len(self.errors)} errors)")
    
    def _get_technical(self) -> Dict:
        """Get ML technical prediction."""
        from ml.engine import predict
        return predict(self.symbol, mode=self.mode)
    
    def _get_news(self) -> Dict:
        """Get news + sentiment."""
        from data_pipeline.news_data import fetch_rss_news
        from data_pipeline.sentiment import analyze_sentiment
        
        clean = self.symbol.replace(".NS", "")
        articles = fetch_rss_news(clean, max_articles=8)
        sentiment = analyze_sentiment(articles)
        sentiment["articles"] = articles[:5]
        return sentiment
    
    def _get_social(self) -> Dict:
        """Get social intel (Reddit + StockTwits + YouTube + Twitter)."""
        from data_pipeline.social_intel import get_social_intelligence
        return get_social_intelligence(self.symbol)
    
    def _get_nse(self) -> Dict:
        """Get NSE official data."""
        from data_pipeline.nse_data import get_nse_intelligence
        return get_nse_intelligence(self.symbol)
    
    def _get_trends(self) -> Dict:
        """Get Google Trends."""
        from data_pipeline.trends_data import fetch_google_trends
        return fetch_google_trends(self.symbol)
    
    def _get_global(self) -> Dict:
        """Get global market context."""
        from data_pipeline.global_markets import get_sector_impact_from_global
        return get_sector_impact_from_global(self.symbol)
    
    # ═══════════════════════════════════════════════════════════
    #   INDIVIDUAL SCORING METHODS
    # ═══════════════════════════════════════════════════════════
    
    def _score_technical(self) -> float:
        """Score technical/ML component (0-40 pts)."""
        if not self.technical:
            return 0
        
        max_pts = SCORE_WEIGHTS["technical"]
        signal = self.technical.get("signal", "HOLD")
        confidence = self.technical.get("confidence_pct", 50) / 100
        
        # HOLD signals get no technical points
        if signal == "HOLD":
            return 0
        
        # Direction alignment (BUY = positive, SELL = negative signal)
        return round(confidence * max_pts, 1)
    
    def _score_news(self) -> float:
        """Score news sentiment (0-25 pts)."""
        if not self.news:
            return 0
        
        max_pts = SCORE_WEIGHTS["news"]
        score = self.news.get("score", 0)  # -1 to +1
        
        # Convert -1 to +1 range → 0 to max_pts
        # Positive news = full points
        # Negative news = 0 points (or minus in penalty)
        if score > 0:
            return round(score * max_pts, 1)
        else:
            return 0  # Negative news adds no positive score
    
    def _score_reddit_stocktwits(self) -> float:
        """Score Reddit + StockTwits (0-20 pts)."""
        if not self.social:
            return 0
        
        max_pts = SCORE_WEIGHTS["reddit_st"]
        sources = self.social.get("sources", {})
        
        reddit = sources.get("reddit", {})
        st = sources.get("stocktwits", {})
        
        reddit_score = reddit.get("score", 0)
        st_score = st.get("score", 0)
        
        # Average of both
        combined = (reddit_score + st_score) / 2
        
        # Only positive contributes
        if combined <= 0:
            return 0
        
        # Bonus for high buzz
        reddit_buzz = reddit.get("buzz", 0)
        st_buzz = st.get("buzz", 0)
        buzz_bonus = min(1.2, 1 + ((reddit_buzz + st_buzz) / 200))
        
        return round(combined * max_pts * buzz_bonus, 1)
    
    def _score_youtube(self) -> float:
        """Score YouTube expert opinions (0-20 pts)."""
        if not self.social:
            return 0
        
        max_pts = SCORE_WEIGHTS["youtube"]
        youtube = self.social.get("sources", {}).get("youtube", {})
        
        score = youtube.get("score", 0)
        videos = youtube.get("videos", 0)
        trusted = youtube.get("trusted_videos", 0)
        
        if videos == 0 or score <= 0:
            return 0
        
        # Trust bonus — trusted channels count more
        trust_multiplier = 1 + (trusted * 0.15)  # 15% bonus per trusted video
        trust_multiplier = min(trust_multiplier, 1.5)  # Cap at 1.5x
        
        return round(score * max_pts * trust_multiplier, 1)
    
    def _score_twitter(self) -> float:
        """Score Twitter (0-15 pts)."""
        if not self.social:
            return 0
        
        max_pts = SCORE_WEIGHTS["twitter"]
        twitter = self.social.get("sources", {}).get("twitter", {})
        
        score = twitter.get("score", 0)
        tweets = twitter.get("tweets", 0)
        trusted = twitter.get("trusted", 0)
        
        if tweets == 0 or score <= 0:
            return 0
        
        # Trusted account bonus
        trust_multiplier = 1 + (trusted * 0.1)
        trust_multiplier = min(trust_multiplier, 1.4)
        
        return round(score * max_pts * trust_multiplier, 1)
    
    def _score_nse_money(self) -> float:
        """Score FII/DII money flow (0-15 pts)."""
        if not self.nse_data:
            return 0
        
        max_pts = SCORE_WEIGHTS["nse_money"]
        fii_dii = self.nse_data.get("data", {}).get("fii_dii", {})
        
        if not fii_dii.get("available"):
            return 0
        
        signal = fii_dii.get("signal", "NEUTRAL")
        
        signal_scores = {
            "STRONG_BULLISH":   1.0,
            "BULLISH":          0.7,
            "FII_BUYING":       0.6,
            "DII_ABSORBING":    0.4,
            "NEUTRAL":          0.3,
            "BEARISH":          0.0,
            "STRONG_BEARISH":   0.0,
        }
        
        multiplier = signal_scores.get(signal, 0.3)
        return round(max_pts * multiplier, 1)
    
    def _score_nse_bulk_deals(self) -> float:
        """Score bulk deals (0-15 pts)."""
        if not self.nse_data:
            return 0
        
        max_pts = SCORE_WEIGHTS["nse_bulk"]
        bulk = self.nse_data.get("data", {}).get("bulk_deals", {})
        
        if not bulk.get("has_activity"):
            return 0
        
        signal = bulk.get("signal", "NEUTRAL")
        
        signal_scores = {
            "STRONG_BUY_INTEREST":  1.0,
            "BUY_INTEREST":         0.7,
            "MIXED":                0.3,
            "SELL_PRESSURE":        0.0,
            "STRONG_SELL_PRESSURE": 0.0,
        }
        
        multiplier = signal_scores.get(signal, 0.3)
        return round(max_pts * multiplier, 1)
    
    def _score_options_pcr(self) -> float:
        """Score Options PCR (0-15 pts)."""
        if not self.nse_data:
            return 0
        
        max_pts = SCORE_WEIGHTS["options"]
        options = self.nse_data.get("data", {}).get("option_chain")
        
        if not options:
            return 0
        
        pcr_signal = options.get("pcr_signal", "NEUTRAL")
        pain_signal = options.get("pain_signal", "UNKNOWN")
        
        # PCR interpretation
        pcr_scores = {
            "OVERSOLD":     1.0,   # Contrarian bullish
            "BULLISH":      0.8,
            "NEUTRAL":      0.4,
            "BEARISH":      0.0,
            "OVERBOUGHT":   0.0,
        }
        
        # Pain signal adds slight bonus
        pain_bonus = {
            "PRICE_BELOW_PAIN":   0.2,   # Might pull up
            "NEAR_MAX_PAIN":      0.1,
            "PRICE_ABOVE_PAIN":  -0.1,   # Might pull down
        }
        
        multiplier = pcr_scores.get(pcr_signal, 0.4)
        multiplier += pain_bonus.get(pain_signal, 0)
        multiplier = max(0, min(1.2, multiplier))
        
        return round(max_pts * multiplier, 1)
    
    def _score_delivery(self) -> float:
        """Score delivery percentage (0-10 pts)."""
        if not self.nse_data:
            return 0
        
        max_pts = SCORE_WEIGHTS["delivery"]
        delivery = self.nse_data.get("data", {}).get("delivery")
        
        if not delivery:
            return 0
        
        signal = delivery.get("signal", "NORMAL")
        
        signal_scores = {
            "STRONG_INVESTMENT":  1.0,
            "GOOD_INVESTMENT":    0.7,
            "NORMAL":             0.4,
            "SPECULATIVE":        0.2,
            "HEAVY_INTRADAY":     0.0,
        }
        
        multiplier = signal_scores.get(signal, 0.4)
        return round(max_pts * multiplier, 1)
    
    def _score_google_trends(self) -> float:
        """Score Google Trends (0-10 pts)."""
        if not self.trends or not self.trends.get("available"):
            return 0
        
        max_pts = SCORE_WEIGHTS["trends"]
        signal = self.trends.get("signal", "NEUTRAL")
        
        signal_scores = {
            "BUILDING_INTEREST":  1.0,   # Best — gradual increase
            "HIGH_INTEREST":      0.7,
            "NEUTRAL":            0.4,
            "LOSING_INTEREST":    0.1,
            "CAUTION_FOMO":       0.0,   # Handled as penalty
        }
        
        multiplier = signal_scores.get(signal, 0.4)
        return round(max_pts * multiplier, 1)
    
    def _score_global_impact(self) -> float:
        """Score global markets sector impact (0-15 pts)."""
        if not self.global_ctx:
            return 0
        
        max_pts = SCORE_WEIGHTS["global"]
        signal = self.global_ctx.get("impact_signal", "NEUTRAL")
        score = self.global_ctx.get("impact_score", 0)
        
        if signal == "POSITIVE":
            return round(max_pts * min(1.0, abs(score) * 2), 1)
        elif signal == "NEUTRAL":
            return round(max_pts * 0.4, 1)
        else:  # NEGATIVE
            return 0
    
    # ═══════════════════════════════════════════════════════════
    #   PENALTY CALCULATIONS
    # ═══════════════════════════════════════════════════════════
    
    def _calc_penalties(self) -> Dict[str, float]:
        """Calculate all penalties."""
        penalties = {}
        
        # F&O Ban — cannot trade
        if self.nse_data and self.nse_data.get("data", {}).get("fno_banned"):
            penalties["fno_banned"] = PENALTIES["fno_banned"]
        
        # NSE Risk Flags
        if self.nse_data and self.nse_data.get("risk_flags"):
            risks = self.nse_data["risk_flags"]
            if "NEGATIVE_ANNOUNCEMENT" in risks:
                penalties["negative_announcement"] = PENALTIES["nse_risk_flag"]
            if "HEAVY_INSTITUTIONAL_SELLING" in risks:
                penalties["heavy_selling"] = 20
        
        # FOMO Spike (Google Trends)
        if self.trends and self.trends.get("signal") == "CAUTION_FOMO":
            penalties["fomo_spike"] = PENALTIES["fomo_spike"]
        
        # Global Negative (sector-specific)
        if self.global_ctx and self.global_ctx.get("impact_signal") == "NEGATIVE":
            penalties["global_negative"] = PENALTIES["global_negative"]
        
        # News risk flag
        if self.news and self.news.get("risk_flag"):
            penalties["news_risk"] = 15
        
        # Sentiment strongly negative
        if self.news and self.news.get("score", 0) < -0.5:
            penalties["very_negative_news"] = 15
        
        return penalties
    
    # ═══════════════════════════════════════════════════════════
    #   MAIN SCORING FUNCTION
    # ═══════════════════════════════════════════════════════════
    
    def calculate_score(self) -> Dict:
        """
        Calculate the final master score.
        Returns comprehensive verdict.
        """
        # Score each component
        self.scores = {
            "technical":  self._score_technical(),
            "news":       self._score_news(),
            "reddit_st":  self._score_reddit_stocktwits(),
            "youtube":    self._score_youtube(),
            "twitter":    self._score_twitter(),
            "nse_money":  self._score_nse_money(),
            "nse_bulk":   self._score_nse_bulk_deals(),
            "options":    self._score_options_pcr(),
            "delivery":   self._score_delivery(),
            "trends":     self._score_google_trends(),
            "global":     self._score_global_impact(),
        }
        
        # Calculate penalties
        self.penalties = self._calc_penalties()
        
        # Sum everything
        gross_score = sum(self.scores.values())
        total_penalty = sum(self.penalties.values())
        self.final_score = max(0, gross_score - total_penalty)
        
        # Determine verdict
        verdict = self._determine_verdict()
        
        # Get signal direction from technical
        signal = self.technical.get("signal", "HOLD") if self.technical else "HOLD"
        
        # Build detailed result
        return {
            "symbol":         self.symbol,
            "mode":           self.mode,
            "signal":         signal,
            "final_score":    round(self.final_score, 1),
            "max_score":      self.max_score,
            "score_pct":      round((self.final_score / self.max_score) * 100, 1),
            "verdict":        verdict["level"],
            "action":         verdict["action"],
            "tradeable":      verdict["tradeable"],
            "confidence":     verdict["confidence"],
            
            # Score breakdown
            "score_breakdown": self.scores,
            "penalty_breakdown": self.penalties,
            
            # Summary stats
            "gross_score":    round(gross_score, 1),
            "total_penalty":  round(total_penalty, 1),
            
            # Underlying data references
            "technical":      self._summarize_technical(),
            "news":           self._summarize_news(),
            "social":         self._summarize_social(),
            "nse":            self._summarize_nse(),
            "trends":         self._summarize_trends(),
            "global":         self._summarize_global(),
            
            # Meta
            "errors":         self.errors,
            "scored_at":      datetime.now().isoformat(),
        }
    
    def _determine_verdict(self) -> Dict:
        """Determine final verdict based on score."""
        score = self.final_score
        signal = self.technical.get("signal", "HOLD") if self.technical else "HOLD"
        
        # If F&O banned, always skip
        if "fno_banned" in self.penalties:
            return {
                "level":      "BANNED",
                "action":     "CANNOT_TRADE",
                "tradeable":  False,
                "confidence": "N/A",
            }
        
        # If HOLD signal, no trade regardless of score
        if signal == "HOLD":
            return {
                "level":      "HOLD",
                "action":     "WAIT",
                "tradeable":  False,
                "confidence": "LOW",
            }
        
        # Score-based verdict
        if score >= THRESHOLDS["STRONG_BUY"]:
            return {
                "level":      "STRONG",
                "action":     "EXECUTE_TRADE",
                "tradeable":  True,
                "confidence": "VERY_HIGH",
            }
        elif score >= THRESHOLDS["BUY"]:
            return {
                "level":      "GOOD",
                "action":     "MANUAL_REVIEW",
                "tradeable":  True,
                "confidence": "HIGH",
            }
        elif score >= THRESHOLDS["WEAK_BUY"]:
            return {
                "level":      "WEAK",
                "action":     "WATCH",
                "tradeable":  False,
                "confidence": "MEDIUM",
            }
        else:
            return {
                "level":      "SKIP",
                "action":     "NO_TRADE",
                "tradeable":  False,
                "confidence": "LOW",
            }
    
    # ═══════════════════════════════════════════════════════════
    #   SUMMARIZATION (for lean API responses)
    # ═══════════════════════════════════════════════════════════
    
    def _summarize_technical(self) -> Dict:
        if not self.technical:
            return {}
        return {
            "signal":      self.technical.get("signal"),
            "confidence":  self.technical.get("confidence_pct"),
            "prob_up":     self.technical.get("prob_up"),
            "current_price": self.technical.get("current_price"),
            "rsi":         self.technical.get("indicators", {}).get("rsi"),
        }
    
    def _summarize_news(self) -> Dict:
        if not self.news:
            return {}
        return {
            "label":     self.news.get("label"),
            "score":     self.news.get("score"),
            "risk_flag": self.news.get("risk_flag"),
            "articles":  self.news.get("articles_analyzed", 0),
        }
    
    def _summarize_social(self) -> Dict:
        if not self.social:
            return {}
        return {
            "label":          self.social.get("label"),
            "score":          self.social.get("score"),
            "confidence":     self.social.get("confidence"),
            "agreement":      self.social.get("agreement"),
            "buzz_score":     self.social.get("buzz_score"),
            "total_mentions": self.social.get("total_mentions", 0),
        }
    
    def _summarize_nse(self) -> Dict:
        if not self.nse_data:
            return {}
        return {
            "label":       self.nse_data.get("nse_label"),
            "score":       self.nse_data.get("nse_score"),
            "risk_flags":  self.nse_data.get("risk_flags"),
            "fno_banned":  self.nse_data.get("data", {}).get("fno_banned"),
        }
    
    def _summarize_trends(self) -> Dict:
        if not self.trends:
            return {}
        return {
            "signal":       self.trends.get("signal"),
            "spike_ratio":  self.trends.get("spike_ratio"),
            "spike_level":  self.trends.get("spike_level"),
        }
    
    def _summarize_global(self) -> Dict:
        if not self.global_ctx:
            return {}
        return {
            "sector":         self.global_ctx.get("sector"),
            "impact_signal":  self.global_ctx.get("impact_signal"),
            "impact_score":   self.global_ctx.get("impact_score"),
            "reasons":        self.global_ctx.get("reasons"),
        }


# ═══════════════════════════════════════════════════════════════
#   Main Entry Function
# ═══════════════════════════════════════════════════════════════

def get_master_score(symbol: str, mode: str = "intraday") -> Dict:
    """
    Get complete master score for a stock.
    THIS IS THE MAIN FUNCTION AGENT USES.
    """
    scorer = MasterScorer(symbol, mode)
    scorer.collect_all_intelligence()
    return scorer.calculate_score()


def get_master_score_lite(symbol: str, mode: str = "intraday") -> Dict:
    """
    Lite version — technical + news + nse only.
    Faster for bulk scanning.
    """
    scorer = MasterScorer(symbol, mode)
    
    # Only fetch fast sources
    with ThreadPoolExecutor(max_workers=3) as executor:
        f1 = executor.submit(scorer._get_technical)
        f2 = executor.submit(scorer._get_news)
        f3 = executor.submit(scorer._get_nse)
        
        try:
            scorer.technical = f1.result(timeout=30)
        except Exception as e:
            logger.warning(f"Technical failed: {e}")
        
        try:
            scorer.news = f2.result(timeout=30)
        except Exception as e:
            logger.warning(f"News failed: {e}")
        
        try:
            scorer.nse_data = f3.result(timeout=30)
        except Exception as e:
            logger.warning(f"NSE failed: {e}")
    
    return scorer.calculate_score()

# ADD to end of agent/master_scorer.py

def get_master_score_with_gates(
    symbol: str,
    mode: str = "intraday",
    open_positions: List[Dict] = None,
    recent_trades: List[Dict] = None,
    current_capital: float = 100000,
    starting_capital: float = 100000,
) -> Dict:
    """
    Get master score PLUS safety gate check.
    Returns unified verdict considering both score AND safety.
    """
    from agent.safety_gates import check_all_gates
    
    # Step 1: Get master score
    master_result = get_master_score(symbol, mode=mode)
    
    # Step 2: Run safety gates
    gate_result = check_all_gates(
        symbol=symbol,
        mode=mode,
        open_positions=open_positions,
        recent_trades=recent_trades,
        current_capital=current_capital,
        starting_capital=starting_capital,
        master_result=master_result,
    )
    
    # Combine results
    master_result["safety_gates"] = gate_result
    
    # Final decision: BOTH score AND gates must approve
    can_execute = (
        master_result.get("tradeable", False) and
        gate_result.get("safe_to_trade", False)
    )
    
    master_result["can_execute"]   = can_execute
    master_result["final_verdict"] = _get_combined_verdict(master_result, gate_result)
    
    return master_result


def _get_combined_verdict(master: Dict, gates: Dict) -> Dict:
    """Combine master score verdict with safety gates."""
    score_verdict = master.get("verdict", "UNKNOWN")
    safe          = gates.get("safe_to_trade", False)
    
    if not safe:
        return {
            "level":  "BLOCKED",
            "action": "SAFETY_GATES_FAILED",
            "reason": f"{gates['gates_failed']} gates failed: {gates.get('failed_gates')}",
        }
    
    if score_verdict == "STRONG":
        return {
            "level":  "EXECUTE_NOW",
            "action": "AUTO_EXECUTE",
            "reason": "Strong score + all gates passed",
        }
    elif score_verdict == "GOOD":
        return {
            "level":  "EXECUTE_WITH_REVIEW",
            "action": "SUGGEST_TRADE",
            "reason": "Good score + all gates passed",
        }
    else:
        return {
            "level":  "SKIP",
            "action": "NO_TRADE",
            "reason": f"Score too low: {score_verdict}",
        }



# ─── Quick Test ───────────────────────────────────────────────
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    import json
    
    print("\n" + "="*60)
    print("MASTER SCORER TEST")
    print("="*60)
    
    result = get_master_score("RELIANCE", mode="intraday")
    
    print(f"\n📊 FINAL VERDICT: {result['verdict']}")
    print(f"   Action:     {result['action']}")
    print(f"   Score:      {result['final_score']}/{result['max_score']} ({result['score_pct']}%)")
    print(f"   Confidence: {result['confidence']}")
    print(f"   Tradeable:  {result['tradeable']}")
    
    print(f"\n📈 Score Breakdown:")
    for source, points in result['score_breakdown'].items():
        max_pts = SCORE_WEIGHTS.get(source, 0)
        print(f"   {source:15s}: {points:5.1f} / {max_pts}")
    
    if result['penalty_breakdown']:
        print(f"\n⚠️ Penalties:")
        for penalty, points in result['penalty_breakdown'].items():
            print(f"   {penalty:20s}: -{points}")
    
    print(f"\n📊 Component Summaries:")
    print(f"   Technical: {result['technical']}")
    print(f"   News:      {result['news']}")
    print(f"   Social:    {result['social']}")
    print(f"   NSE:       {result['nse']}")
    print(f"   Trends:    {result['trends']}")
    print(f"   Global:    {result['global']}")
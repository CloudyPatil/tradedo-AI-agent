# E:\tradedo\app\backend\agent\scanner.py

import logging
import time
from typing import List, Dict
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

from ml.engine import predict, get_market_regime
from agent.universe import get_scan_universe

logger = logging.getLogger("tradedo.scanner")

# ─── Scanner Config ───────────────────────────────────────────
MAX_WORKERS         = 5       # Parallel scan threads
MIN_CONFIDENCE      = 65      # Min ML confidence to consider
MIN_COMPOSITE_SCORE = 60      # Min composite for candidate
MAX_CANDIDATES      = 10      # Top N candidates to return


class StockScanner:
    """
    Scans a universe of stocks for trading opportunities.
    Uses parallel processing for speed.
    """
    
    def __init__(self, mode: str = "intraday"):
        self.mode          = mode
        self.market_regime = "NEUTRAL"
        self.results       = []
        self.errors        = []
    
    def _scan_single(self, symbol: str) -> Dict:
        """Scan one stock — used in parallel."""
        try:
            result = predict(symbol, mode=self.mode)
            return {
                "symbol":         symbol,
                "signal":         result["signal"],
                "confidence":     result["confidence_pct"],
                "prob_up":        result["prob_up"],
                "current_price":  result["current_price"],
                "indicators":     result.get("indicators", {}),
                "status":         "success",
            }
        except Exception as e:
            return {
                "symbol": symbol,
                "status": "error",
                "error":  str(e),
            }
    
    def scan(self, tier: str = "tier1") -> Dict:
        """
        Scan the universe and return ranked candidates.
        
        Args:
            tier: "tier1" (50 stocks), "tier2" (100), "full" (150)
        
        Returns:
            Dict with scan results, candidates, stats
        """
        start_time = time.time()
        
        # Get universe
        symbols = get_scan_universe(tier)
        logger.info(f"🔍 Scanning {len(symbols)} stocks ({tier})...")
        
        # Get market regime once
        self.market_regime = get_market_regime()
        logger.info(f"📊 Market Regime: {self.market_regime}")
        
        # Parallel scan
        self.results = []
        self.errors  = []
        
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = {
                executor.submit(self._scan_single, sym): sym 
                for sym in symbols
            }
            
            for future in as_completed(futures):
                res = future.result()
                if res["status"] == "success":
                    self.results.append(res)
                else:
                    self.errors.append(res)
        
        # Filter candidates
        candidates = self._filter_and_rank()
        
        elapsed = round(time.time() - start_time, 1)
        
        stats = {
            "total_scanned":    len(symbols),
            "success":          len(self.results),
            "errors":           len(self.errors),
            "candidates_found": len(candidates),
            "market_regime":    self.market_regime,
            "scan_time_sec":    elapsed,
            "scanned_at":       datetime.now().isoformat(),
        }
        
        logger.info(
            f"✅ Scan complete in {elapsed}s: "
            f"{len(candidates)} candidates from {len(self.results)} successful scans"
        )
        
        return {
            "stats":      stats,
            "candidates": candidates,
            "all_results": self.results,
        }

    # ADD to agent/scanner.py (after existing scan method)

    def deep_scan(self, tier: str = "tier1") -> Dict:
        """
        Deep scan using MASTER SCORER for top candidates.
        
        Process:
        1. Fast scan all stocks (basic ML)
        2. Take top 20 candidates
        3. Run FULL master scorer on those 20 only
        4. Return final ranked list
        
        Way smarter than just ML predictions.
        """
        from agent.master_scorer import get_master_score
        
        start_time = time.time()
        
        # Step 1: Fast scan first
        logger.info("🔍 Deep Scan Step 1: Fast scanning universe...")
        fast_result = self.scan(tier=tier)
        fast_candidates = fast_result["candidates"]
        
        if not fast_candidates:
            return fast_result
        
        # Step 2: Take top 20 for deep analysis
        top_candidates = fast_candidates[:20]
        logger.info(f"🧠 Deep Scan Step 2: Master scoring top {len(top_candidates)}...")
        
        # Step 3: Master scoring in parallel (batch of 3 at a time to avoid overload)
        deep_results = []
        
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = {
                executor.submit(get_master_score, c["symbol"], self.mode): c
                for c in top_candidates
            }
            
            for future in as_completed(futures):
                try:
                    master_result = future.result(timeout=120)
                    if master_result.get("tradeable"):
                        deep_results.append(master_result)
                        logger.info(
                            f"  ✓ {master_result['symbol']}: "
                            f"{master_result['verdict']} ({master_result['final_score']})"
                        )
                except Exception as e:
                    logger.warning(f"Deep score failed: {e}")
        
        # Sort by final score
        deep_results.sort(key=lambda x: x["final_score"], reverse=True)
        
        elapsed = round(time.time() - start_time, 1)
        
        return {
            "stats": {
                "total_scanned":     fast_result["stats"]["total_scanned"],
                "fast_candidates":   len(fast_candidates),
                "deep_analyzed":     len(top_candidates),
                "tradeable":         len(deep_results),
                "market_regime":     self.market_regime,
                "scan_time_sec":     elapsed,
                "scanned_at":        datetime.now().isoformat(),
            },
            "tradeable_candidates":  deep_results[:10],  # Top 10 tradeable
            "all_deep_results":      deep_results,
        }
    
    def _filter_and_rank(self) -> List[Dict]:
        """Apply filters and rank by composite score."""
        from agent.sectors import diversify_candidates, get_sector
        
        candidates = []
        
        for stock in self.results:
            signal     = stock["signal"]
            confidence = stock["confidence"]
        
            if signal == "HOLD":
                continue
            if confidence < MIN_CONFIDENCE:
                continue
        
            regime_aligned = self._check_regime_alignment(signal)
            composite = self._quick_composite_score(
                confidence=confidence,
                regime_aligned=regime_aligned,
                indicators=stock.get("indicators", {}),
                signal=signal,
            )
            
            if composite < MIN_COMPOSITE_SCORE:
                continue
            
            stock["composite_score"] = composite
            stock["regime_aligned"]  = regime_aligned
            stock["sector"]          = get_sector(stock["symbol"])
            candidates.append(stock)
        
        # Sort by composite score (descending)
        candidates.sort(key=lambda x: x["composite_score"], reverse=True)
    
        # ── APPLY SECTOR DIVERSIFICATION ─────────────────────────
        # Keep top 3 per sector for candidates pool
        # (Executor later picks top 1 per sector for actual trades)
        diversified = diversify_candidates(candidates, max_per_sector=3)
    
        return diversified[:MAX_CANDIDATES]
    
    def _check_regime_alignment(self, signal: str) -> bool:
        """Check if signal aligns with market regime."""
        if self.market_regime == "BULLISH":
            return signal == "BUY"
        elif self.market_regime == "BEARISH":
            return signal == "SELL"
        else:
            return True   # Neutral = both allowed
    
    def _quick_composite_score(
        self, confidence: float, regime_aligned: bool,
        indicators: Dict, signal: str
    ) -> float:
        """
        Quick composite score for scanner (0-100).
        No sentiment API call here — that's expensive.
        Full composite happens in final selector.
        """
        # ML score (60 pts max)
        ml_score = (confidence / 100) * 60
        
        # Regime score (25 pts)
        regime_score = 25 if regime_aligned else 5
        
        # Volume/momentum boost (15 pts)
        rsi = indicators.get("rsi", 50)
        momentum_score = 0
        
        if signal == "BUY":
            if 40 <= rsi <= 65:
                momentum_score = 15   # Healthy RSI for buying
            elif rsi < 40:
                momentum_score = 10   # Oversold bounce potential
            else:
                momentum_score = 5    # Overbought risk
        else:  # SELL
            if 35 <= rsi <= 60:
                momentum_score = 15
            elif rsi > 60:
                momentum_score = 10
            else:
                momentum_score = 5
        
        return round(ml_score + regime_score + momentum_score, 1)


# ─── Convenience Function ─────────────────────────────────────
def scan_market(tier: str = "tier1", mode: str = "intraday") -> Dict:
    """Main entry point for market scan."""
    scanner = StockScanner(mode=mode)
    return scanner.scan(tier=tier)


# ─── Quick Test ───────────────────────────────────────────────
if __name__ == "__main__":
    print("Testing scanner...")
    result = scan_market(tier="tier1", mode="intraday")
    
    print(f"\n📊 Stats:")
    for k, v in result["stats"].items():
        print(f"  {k}: {v}")
    
    print(f"\n🏆 Top Candidates:")
    for i, c in enumerate(result["candidates"], 1):
        symbol = c["symbol"].replace(".NS", "")
        print(f"  {i}. {symbol:12s} {c['signal']:5s} "
              f"Conf: {c['confidence']:5.1f}%  Score: {c['composite_score']}")
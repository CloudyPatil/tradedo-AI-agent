# E:\tradedo\app\backend\data_pipeline\global_markets.py

"""
Global markets analyzer.
Fetches key global indicators that affect Indian markets:
- US Futures (Dow, S&P, Nasdaq)
- Crude Oil (affects Reliance, IOC, BPCL, aviation)
- Dollar Index (affects IT stocks)
- Gold (safe haven flow)
- Asian markets (Nikkei, Hang Seng)
- SGX Nifty (India's overnight indicator)
"""

import logging
from typing import Dict, Optional, List
from concurrent.futures import ThreadPoolExecutor
import yfinance as yf

logger = logging.getLogger("tradedo.global")


# ─── Global Symbols on Yahoo Finance ─────────────────────────
GLOBAL_INDICATORS = {
    # US Markets
    "US_DOW":      {"symbol": "YM=F",  "name": "Dow Jones Futures"},
    "US_SP500":    {"symbol": "ES=F",  "name": "S&P 500 Futures"},
    "US_NASDAQ":   {"symbol": "NQ=F",  "name": "Nasdaq Futures"},
    
    # Commodities
    "CRUDE":       {"symbol": "CL=F",  "name": "Crude Oil"},
    "GOLD":        {"symbol": "GC=F",  "name": "Gold"},
    "SILVER":      {"symbol": "SI=F",  "name": "Silver"},
    
    # Currencies
    "DOLLAR_INDEX": {"symbol": "DX-Y.NYB", "name": "US Dollar Index"},
    "USDINR":      {"symbol": "INR=X", "name": "USD/INR"},
    
    # Asian Markets
    "NIKKEI":      {"symbol": "^N225", "name": "Nikkei 225"},
    "HANG_SENG":   {"symbol": "^HSI",  "name": "Hang Seng"},
    "SHANGHAI":    {"symbol": "000001.SS", "name": "Shanghai Composite"},
    
    # India
    "INDIA_VIX":   {"symbol": "^INDIAVIX", "name": "India VIX"},
    "NIFTY":       {"symbol": "^NSEI",     "name": "Nifty 50"},
    "SENSEX":      {"symbol": "^BSESN",    "name": "Sensex"},
    "BANK_NIFTY":  {"symbol": "^NSEBANK",  "name": "Bank Nifty"},
}


def fetch_single_indicator(key: str, info: Dict) -> Optional[Dict]:
    """Fetch data for a single indicator."""
    try:
        ticker = yf.Ticker(info["symbol"])
        
        # Get recent history (2 days for change calc)
        hist = ticker.history(period="5d", interval="1d")
        
        if hist.empty or len(hist) < 2:
            return None
        
        current  = float(hist["Close"].iloc[-1])
        previous = float(hist["Close"].iloc[-2])
        high     = float(hist["High"].iloc[-1])
        low      = float(hist["Low"].iloc[-1])
        
        change     = current - previous
        change_pct = (change / previous * 100) if previous else 0
        
        # Direction
        if change_pct > 0.5:
            direction = "UP"
        elif change_pct < -0.5:
            direction = "DOWN"
        else:
            direction = "FLAT"
        
        return {
            "key":        key,
            "name":       info["name"],
            "symbol":     info["symbol"],
            "value":      round(current, 2),
            "change":     round(change, 2),
            "change_pct": round(change_pct, 2),
            "direction":  direction,
            "high":       round(high, 2),
            "low":        round(low, 2),
        }
    
    except Exception as e:
        logger.debug(f"Failed to fetch {key}: {e}")
        return None


def fetch_all_global_markets() -> Dict:
    """Fetch all global indicators in parallel."""
    logger.info("🌍 Fetching global markets data...")
    
    results = {}
    
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {
            executor.submit(fetch_single_indicator, key, info): key
            for key, info in GLOBAL_INDICATORS.items()
        }
        
        for future in futures:
            try:
                data = future.result(timeout=15)
                if data:
                    results[data["key"]] = data
            except Exception as e:
                logger.debug(f"Global fetch error: {e}")
    
    logger.info(f"  → Fetched {len(results)}/{len(GLOBAL_INDICATORS)} indicators")
    return results


def analyze_global_context() -> Dict:
    """
    Analyze overall global market context.
    Returns comprehensive market bias for Indian markets.
    """
    data = fetch_all_global_markets()
    
    if not data:
        return _empty_global()
    
    # ── US Markets Analysis ──────────────────────────────────
    us_indices = [data.get("US_DOW"), data.get("US_SP500"), data.get("US_NASDAQ")]
    us_indices = [d for d in us_indices if d]
    
    if us_indices:
        us_avg_change = sum(d["change_pct"] for d in us_indices) / len(us_indices)
        if us_avg_change > 0.5:
            us_signal = "BULLISH"
        elif us_avg_change < -0.5:
            us_signal = "BEARISH"
        else:
            us_signal = "NEUTRAL"
    else:
        us_avg_change = 0
        us_signal = "NO_DATA"
    
    # ── Asian Markets Analysis ───────────────────────────────
    asian_indices = [data.get("NIKKEI"), data.get("HANG_SENG"), data.get("SHANGHAI")]
    asian_indices = [d for d in asian_indices if d]
    
    if asian_indices:
        asian_avg_change = sum(d["change_pct"] for d in asian_indices) / len(asian_indices)
        if asian_avg_change > 0.5:
            asian_signal = "BULLISH"
        elif asian_avg_change < -0.5:
            asian_signal = "BEARISH"
        else:
            asian_signal = "NEUTRAL"
    else:
        asian_avg_change = 0
        asian_signal = "NO_DATA"
    
    # ── Crude Oil Analysis (affects energy, aviation) ────────
    crude = data.get("CRUDE")
    if crude:
        if crude["change_pct"] > 2:
            crude_signal = "SPIKE_UP"     # Bad for OMC, aviation
        elif crude["change_pct"] > 0.5:
            crude_signal = "UP"
        elif crude["change_pct"] < -2:
            crude_signal = "SPIKE_DOWN"   # Good for OMC, aviation
        elif crude["change_pct"] < -0.5:
            crude_signal = "DOWN"
        else:
            crude_signal = "STABLE"
    else:
        crude_signal = "NO_DATA"
    
    # ── Dollar Analysis (affects IT stocks) ──────────────────
    dollar = data.get("DOLLAR_INDEX")
    if dollar:
        if dollar["change_pct"] > 0.3:
            dollar_signal = "STRONG"      # Good for IT export
        elif dollar["change_pct"] < -0.3:
            dollar_signal = "WEAK"        # Bad for IT export
        else:
            dollar_signal = "STABLE"
    else:
        dollar_signal = "NO_DATA"
    
    # ── India VIX ────────────────────────────────────────────
    vix = data.get("INDIA_VIX")
    if vix:
        vix_val = vix["value"]
        if vix_val > 20:
            vix_level = "HIGH_FEAR"       # Be cautious
        elif vix_val > 15:
            vix_level = "ELEVATED"
        elif vix_val < 12:
            vix_level = "COMPLACENT"      # Potential reversal
        else:
            vix_level = "NORMAL"
    else:
        vix_val = 0
        vix_level = "NO_DATA"
    
    # ── Overall Bias for Indian Market ───────────────────────
    signals = []
    weights = []
    
    if us_signal == "BULLISH":
        signals.append(1); weights.append(30)
    elif us_signal == "BEARISH":
        signals.append(-1); weights.append(30)
    
    if asian_signal == "BULLISH":
        signals.append(1); weights.append(20)
    elif asian_signal == "BEARISH":
        signals.append(-1); weights.append(20)
    
    if vix_level == "HIGH_FEAR":
        signals.append(-1); weights.append(15)
    elif vix_level == "COMPLACENT":
        signals.append(-0.5); weights.append(10)   # Slight caution
    
    if crude_signal == "SPIKE_UP":
        signals.append(-1); weights.append(10)   # Bad for India
    elif crude_signal == "SPIKE_DOWN":
        signals.append(1); weights.append(10)
    
    if signals:
        total_weight = sum(weights)
        overall_score = sum(s * w for s, w in zip(signals, weights)) / total_weight
    else:
        overall_score = 0
    
    if overall_score > 0.3:
        overall_bias = "BULLISH"
    elif overall_score < -0.3:
        overall_bias = "BEARISH"
    else:
        overall_bias = "NEUTRAL"
    
    logger.info(
        f"🌐 Global: US={us_signal}, Asia={asian_signal}, "
        f"VIX={vix_level}, Overall={overall_bias}"
    )
    
    return {
        "overall_bias":  overall_bias,
        "overall_score": round(overall_score, 3),
        "us_signal":     us_signal,
        "us_change_pct": round(us_avg_change, 2),
        "asian_signal":  asian_signal,
        "asian_change_pct": round(asian_avg_change, 2),
        "crude_signal":  crude_signal,
        "dollar_signal": dollar_signal,
        "vix_level":     vix_level,
        "vix_value":     vix_val,
        "raw_data":      data,
    }


def get_sector_impact_from_global(symbol: str) -> Dict:
    """
    Get sector-specific impact from global markets.
    E.g., IT stocks care about dollar. Energy cares about crude.
    """
    from agent.sectors import get_sector
    
    sector = get_sector(symbol)
    global_data = analyze_global_context()
    
    impact_score = 0
    impact_reasons = []
    
    # IT sector impact
    if sector == "IT":
        dollar_signal = global_data.get("dollar_signal", "STABLE")
        if dollar_signal == "STRONG":
            impact_score += 0.5
            impact_reasons.append("Strong dollar favors IT exports")
        elif dollar_signal == "WEAK":
            impact_score -= 0.5
            impact_reasons.append("Weak dollar hurts IT margins")
        
        # US markets heavily impact IT
        us_signal = global_data.get("us_signal", "NEUTRAL")
        if us_signal == "BULLISH":
            impact_score += 0.3
        elif us_signal == "BEARISH":
            impact_score -= 0.3
    
    # Energy sector impact
    elif sector == "ENERGY":
        crude_signal = global_data.get("crude_signal", "STABLE")
        if crude_signal == "SPIKE_DOWN":
            impact_score += 0.5
            impact_reasons.append("Crude fall benefits OMCs")
        elif crude_signal == "SPIKE_UP":
            impact_score -= 0.5
            impact_reasons.append("Crude spike hurts OMCs")
    
    # Aviation impact
    elif sector == "AVIATION":
        crude_signal = global_data.get("crude_signal", "STABLE")
        if crude_signal == "SPIKE_UP":
            impact_score -= 0.7
            impact_reasons.append("Fuel cost spike hurts airlines")
        elif crude_signal == "SPIKE_DOWN":
            impact_score += 0.5
            impact_reasons.append("Lower fuel cost helps airlines")
    
    # Banking impact from global sentiment
    elif sector in ["BANKING", "NBFC"]:
        us_signal = global_data.get("us_signal", "NEUTRAL")
        vix_level = global_data.get("vix_level", "NORMAL")
        
        if vix_level == "HIGH_FEAR":
            impact_score -= 0.4
            impact_reasons.append("High VIX = risk-off hurts banks")
        if us_signal == "BEARISH":
            impact_score -= 0.3
    
    # Metals from Asian markets (China demand)
    elif sector == "METALS":
        asian_signal = global_data.get("asian_signal", "NEUTRAL")
        if asian_signal == "BULLISH":
            impact_score += 0.4
            impact_reasons.append("Asian strength boosts metals demand")
        elif asian_signal == "BEARISH":
            impact_score -= 0.4
    
    # Determine signal
    if impact_score > 0.3:
        impact_signal = "POSITIVE"
    elif impact_score < -0.3:
        impact_signal = "NEGATIVE"
    else:
        impact_signal = "NEUTRAL"
    
    return {
        "sector":         sector,
        "impact_signal":  impact_signal,
        "impact_score":   round(impact_score, 3),
        "reasons":        impact_reasons,
        "global_bias":    global_data["overall_bias"],
    }


def _empty_global() -> Dict:
    return {
        "overall_bias":  "NEUTRAL",
        "overall_score": 0,
        "us_signal":     "NO_DATA",
        "asian_signal":  "NO_DATA",
        "crude_signal":  "NO_DATA",
        "dollar_signal": "NO_DATA",
        "vix_level":     "NO_DATA",
        "raw_data":      {},
    }


# ─── Quick Test ───────────────────────────────────────────────
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    import json
    
    print("\n" + "="*60)
    print("Global Markets Analysis")
    print("="*60)
    result = analyze_global_context()
    
    print(f"\n📊 Overall Bias:   {result['overall_bias']} ({result['overall_score']})")
    print(f"   US Markets:     {result['us_signal']} ({result['us_change_pct']:+.2f}%)")
    print(f"   Asian Markets:  {result['asian_signal']} ({result['asian_change_pct']:+.2f}%)")
    print(f"   Crude:          {result['crude_signal']}")
    print(f"   Dollar:         {result['dollar_signal']}")
    print(f"   VIX:            {result['vix_level']} ({result['vix_value']})")
    
    print("\n" + "="*60)
    print("Sector-Specific Impact Examples")
    print("="*60)
    for symbol in ["TCS", "RELIANCE", "HDFCBANK", "TATASTEEL"]:
        impact = get_sector_impact_from_global(symbol)
        print(f"\n{symbol} ({impact['sector']}):")
        print(f"  Impact: {impact['impact_signal']} ({impact['impact_score']:+.2f})")
        if impact['reasons']:
            for r in impact['reasons']:
                print(f"  → {r}")
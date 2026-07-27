# E:\tradedo\app\backend\data_pipeline\nse_data.py

"""
NSE Official Data Scraper
Fetches: Announcements, FII/DII, Bulk Deals, F&O Ban, Options Chain
All data from NSE's public endpoints - 100% FREE.
"""

import logging
import requests
import json
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from functools import lru_cache
import time

logger = logging.getLogger("tradedo.nse")


# ─── NSE API Config ───────────────────────────────────────────
NSE_BASE = "https://www.nseindia.com"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept":          "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection":      "keep-alive",
    "Referer":         "https://www.nseindia.com/",
}


class NSEClient:
    """NSE data client with session management."""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        self._initialized = False
    
    def _init_session(self):
        """NSE requires cookie initialization."""
        if self._initialized:
            return
        try:
            # Visit homepage first to get cookies
            self.session.get(NSE_BASE, timeout=10)
            time.sleep(0.5)
            self._initialized = True
            logger.debug("NSE session initialized")
        except Exception as e:
            logger.warning(f"NSE session init failed: {e}")
    
    def get(self, endpoint: str, retries: int = 2) -> Optional[Dict]:
        """Make GET request with retries."""
        self._init_session()
        
        url = f"{NSE_BASE}{endpoint}"
        
        for attempt in range(retries + 1):
            try:
                response = self.session.get(url, timeout=15)
                
                if response.status_code == 200:
                    return response.json()
                
                if response.status_code == 401 or response.status_code == 403:
                    # Reset session
                    self._initialized = False
                    self._init_session()
                    time.sleep(1)
                    continue
                
                logger.warning(f"NSE {endpoint}: HTTP {response.status_code}")
                
            except Exception as e:
                if attempt < retries:
                    logger.debug(f"NSE retry {attempt+1}: {e}")
                    time.sleep(1)
                    continue
                logger.warning(f"NSE {endpoint} failed: {e}")
        
        return None


# ─── Global client ────────────────────────────────────────────
_client: Optional[NSEClient] = None

def get_client() -> NSEClient:
    global _client
    if _client is None:
        _client = NSEClient()
    return _client


# ═══════════════════════════════════════════════════════════════
#   1. CORPORATE ANNOUNCEMENTS
# ═══════════════════════════════════════════════════════════════

def fetch_announcements(symbol: str, days_back: int = 7) -> List[Dict]:
    """
    Get corporate announcements for a stock.
    E.g., board meetings, dividends, results, mergers, splits.
    """
    clean = symbol.replace(".NS", "").replace(".BO", "").upper()
    client = get_client()
    
    endpoint = f"/api/corporate-announcements?index=equities&symbol={clean}"
    data = client.get(endpoint)
    
    if not data:
        return []
    
    cutoff = datetime.now() - timedelta(days=days_back)
    announcements = []
    
    items = data if isinstance(data, list) else data.get("data", [])
    
    for item in items:
        try:
            # Parse date
            date_str = item.get("an_dt") or item.get("attchmntFile", "")
            if not date_str:
                continue
            
            try:
                ann_date = datetime.strptime(date_str[:10], "%d-%b-%Y")
            except:
                try:
                    ann_date = datetime.strptime(date_str[:10], "%Y-%m-%d")
                except:
                    continue
            
            if ann_date < cutoff:
                continue
            
            subject = item.get("desc") or item.get("subject", "")
            details = item.get("attchmntText", "")
            
            announcements.append({
                "symbol":  clean,
                "subject": subject[:200],
                "details": details[:300] if details else "",
                "date":    ann_date.strftime("%Y-%m-%d"),
                "type":    _classify_announcement(subject),
                "impact":  _rate_announcement_impact(subject),
            })
        
        except Exception as e:
            logger.debug(f"Announcement parse error: {e}")
            continue
    
    logger.info(f"NSE Announcements: {clean} → {len(announcements)}")
    return announcements[:10]


def _classify_announcement(subject: str) -> str:
    """Classify announcement type."""
    s = subject.lower()
    if any(w in s for w in ["result", "financial", "earnings", "quarterly"]):
        return "RESULTS"
    if any(w in s for w in ["dividend", "bonus", "split", "buyback"]):
        return "CORPORATE_ACTION"
    if any(w in s for w in ["board meeting", "board of directors"]):
        return "BOARD_MEETING"
    if any(w in s for w in ["merger", "acquisition", "amalgamation"]):
        return "M&A"
    if any(w in s for w in ["order", "contract", "win", "award"]):
        return "BUSINESS_UPDATE"
    if any(w in s for w in ["sebi", "regulatory", "penalty", "notice"]):
        return "REGULATORY"
    if any(w in s for w in ["fraud", "investigation", "raid"]):
        return "NEGATIVE"
    return "OTHER"


def _rate_announcement_impact(subject: str) -> str:
    """Rate potential impact."""
    s = subject.lower()
    if any(w in s for w in ["fraud", "penalty", "raid", "investigation", "sebi order"]):
        return "HIGH_NEGATIVE"
    if any(w in s for w in ["bonus", "buyback", "special dividend", "record"]):
        return "HIGH_POSITIVE"
    if any(w in s for w in ["result", "quarterly", "annual"]):
        return "MEDIUM"
    if any(w in s for w in ["board meeting"]):
        return "LOW"
    return "NEUTRAL"


# ═══════════════════════════════════════════════════════════════
#   2. FII / DII MONEY FLOW
# ═══════════════════════════════════════════════════════════════

@lru_cache(maxsize=1)
def fetch_fii_dii(_ttl_hash: int = None) -> Dict:
    """
    Get latest FII (Foreign) and DII (Domestic) institutional flow.
    Cached for 30 mins because it updates daily only.
    """
    client = get_client()
    data = client.get("/api/fiidiiTradeReact")
    
    if not data or not isinstance(data, list) or len(data) < 2:
        return _empty_fii_dii()
    
    try:
        # Data usually has FII and DII entries
        fii_data = None
        dii_data = None
        
        for entry in data:
            category = entry.get("category", "").upper()
            if "FII" in category or "FPI" in category:
                fii_data = entry
            elif "DII" in category:
                dii_data = entry
        
        if not fii_data or not dii_data:
            return _empty_fii_dii()
        
        fii_net = float(fii_data.get("netValue", 0))
        dii_net = float(dii_data.get("netValue", 0))
        
        # Interpret
        if fii_net > 500 and dii_net > 500:
            signal = "STRONG_BULLISH"
        elif fii_net > 0 and dii_net > 0:
            signal = "BULLISH"
        elif fii_net < -500 and dii_net < -500:
            signal = "STRONG_BEARISH"
        elif fii_net < 0 and dii_net < 0:
            signal = "BEARISH"
        elif fii_net > 0 and dii_net < 0:
            signal = "FII_BUYING"  # FIIs buying, DIIs selling
        elif fii_net < 0 and dii_net > 0:
            signal = "DII_ABSORBING"  # DIIs absorbing FII selling
        else:
            signal = "NEUTRAL"
        
        return {
            "date":       fii_data.get("date", ""),
            "fii_buy":    float(fii_data.get("buyValue", 0)),
            "fii_sell":   float(fii_data.get("sellValue", 0)),
            "fii_net":    fii_net,
            "dii_buy":    float(dii_data.get("buyValue", 0)),
            "dii_sell":   float(dii_data.get("sellValue", 0)),
            "dii_net":    dii_net,
            "total_net":  fii_net + dii_net,
            "signal":     signal,
            "available":  True,
        }
    
    except Exception as e:
        logger.error(f"FII/DII parse error: {e}")
        return _empty_fii_dii()


def _empty_fii_dii() -> Dict:
    return {
        "date":      "",
        "fii_net":   0,
        "dii_net":   0,
        "total_net": 0,
        "signal":    "UNAVAILABLE",
        "available": False,
    }


def get_fii_dii_cached() -> Dict:
    """Get FII/DII with 30-min cache."""
    # Use current 30-min window as cache key
    ttl = int(time.time() // 1800)
    return fetch_fii_dii(ttl)


# ═══════════════════════════════════════════════════════════════
#   3. BULK & BLOCK DEALS
# ═══════════════════════════════════════════════════════════════

def fetch_bulk_deals(symbol: str = None) -> List[Dict]:
    """
    Get today's bulk deals (>0.5% of company shares).
    If symbol provided, filter for that stock.
    """
    client = get_client()
    data = client.get("/api/snapshot-capital-market-largedeal")
    
    if not data:
        return []
    
    bulk = data.get("BULK_DEALS_DATA", []) if isinstance(data, dict) else []
    
    deals = []
    for deal in bulk:
        try:
            symbol_deal = deal.get("symbol", "")
            
            # Filter if symbol specified
            if symbol:
                clean = symbol.replace(".NS", "").replace(".BO", "").upper()
                if symbol_deal.upper() != clean:
                    continue
            
            deals.append({
                "symbol":    symbol_deal,
                "client":    deal.get("clientName", ""),
                "type":      deal.get("buySell", ""),   # BUY or SELL
                "quantity":  int(deal.get("qty", 0)),
                "price":     float(deal.get("watp", 0)),
                "value":     int(deal.get("qty", 0)) * float(deal.get("watp", 0)),
                "date":      deal.get("date", ""),
            })
        except Exception as e:
            logger.debug(f"Bulk deal parse error: {e}")
            continue
    
    logger.info(f"NSE Bulk Deals: {len(deals)} " + (f"for {symbol}" if symbol else "today"))
    return deals


def analyze_bulk_deals_for_stock(symbol: str) -> Dict:
    """Analyze bulk deals for a specific stock."""
    deals = fetch_bulk_deals(symbol)
    
    if not deals:
        return {
            "has_activity": False,
            "signal":       "NEUTRAL",
            "buy_value":    0,
            "sell_value":   0,
            "net_value":    0,
            "deal_count":   0,
            "deals":        [],
        }
    
    buy_value  = sum(d["value"] for d in deals if d["type"] == "BUY")
    sell_value = sum(d["value"] for d in deals if d["type"] == "SELL")
    net_value  = buy_value - sell_value
    
    # Signal based on net activity
    if net_value > 10_00_00_000:  # >₹10 Cr net buying
        signal = "STRONG_BUY_INTEREST"
    elif net_value > 0:
        signal = "BUY_INTEREST"
    elif net_value < -10_00_00_000:
        signal = "STRONG_SELL_PRESSURE"
    elif net_value < 0:
        signal = "SELL_PRESSURE"
    else:
        signal = "MIXED"
    
    return {
        "has_activity": True,
        "signal":       signal,
        "buy_value":    buy_value,
        "sell_value":   sell_value,
        "net_value":    net_value,
        "deal_count":   len(deals),
        "deals":        deals[:5],
    }


# ═══════════════════════════════════════════════════════════════
#   4. F&O BAN LIST
# ═══════════════════════════════════════════════════════════════

@lru_cache(maxsize=1)
def fetch_fno_ban_list(_ttl_hash: int = None) -> List[str]:
    """
    Get today's F&O ban list.
    These stocks CANNOT be traded intraday in F&O segment.
    Cached for 4 hours (updates once daily).
    """
    client = get_client()
    data = client.get("/api/fiiFinicaLimitReport")
    
    if not data:
        return []
    
    try:
        banned = []
        items = data.get("data", []) if isinstance(data, dict) else data
        
        for item in items:
            symbol = item.get("symbol") or item.get("SYMBOL")
            if symbol:
                banned.append(symbol.upper())
        
        return banned
    except Exception as e:
        logger.warning(f"F&O ban list parse error: {e}")
        return []


def get_fno_ban_list_cached() -> List[str]:
    """Get F&O ban list with 4-hour cache."""
    ttl = int(time.time() // 14400)  # 4 hour cache
    return fetch_fno_ban_list(ttl)


def is_fno_banned(symbol: str) -> bool:
    """Check if a stock is in F&O ban list."""
    clean = symbol.replace(".NS", "").replace(".BO", "").upper()
    return clean in get_fno_ban_list_cached()


# ═══════════════════════════════════════════════════════════════
#   5. OPTIONS CHAIN + PCR (Put-Call Ratio)
# ═══════════════════════════════════════════════════════════════

def fetch_option_chain(symbol: str) -> Optional[Dict]:
    """
    Get options chain data for a stock.
    Includes: PCR, Max Pain, OI analysis.
    """
    clean = symbol.replace(".NS", "").replace(".BO", "").upper()
    client = get_client()
    
    endpoint = f"/api/option-chain-equities?symbol={clean}"
    data = client.get(endpoint)
    
    if not data:
        return None
    
    try:
        records = data.get("records", {})
        underlying_value = records.get("underlyingValue", 0)
        expiry_dates     = records.get("expiryDates", [])
        
        if not expiry_dates:
            return None
        
        # Use nearest expiry
        current_expiry = expiry_dates[0]
        
        option_data = records.get("data", [])
        
        total_call_oi = 0
        total_put_oi  = 0
        total_call_vol = 0
        total_put_vol  = 0
        
        # Track OI by strike for max pain calculation
        strike_data = {}
        
        for item in option_data:
            if item.get("expiryDate") != current_expiry:
                continue
            
            strike = item.get("strikePrice", 0)
            
            call_data = item.get("CE", {})
            put_data  = item.get("PE", {})
            
            call_oi = call_data.get("openInterest", 0) if call_data else 0
            put_oi  = put_data.get("openInterest", 0) if put_data else 0
            
            call_vol = call_data.get("totalTradedVolume", 0) if call_data else 0
            put_vol  = put_data.get("totalTradedVolume", 0) if put_data else 0
            
            total_call_oi += call_oi
            total_put_oi  += put_oi
            total_call_vol += call_vol
            total_put_vol  += put_vol
            
            strike_data[strike] = {"call_oi": call_oi, "put_oi": put_oi}
        
        # Calculate PCR
        pcr_oi     = round(total_put_oi / total_call_oi, 3) if total_call_oi > 0 else 0
        pcr_volume = round(total_put_vol / total_call_vol, 3) if total_call_vol > 0 else 0
        
        # Max Pain calculation
        max_pain = _calculate_max_pain(strike_data, underlying_value)
        
        # Interpret PCR
        if pcr_oi > 1.5:
            pcr_signal = "OVERSOLD"       # Too many puts = contrarian bullish
        elif pcr_oi > 1.2:
            pcr_signal = "BULLISH"        # Put writers confident
        elif pcr_oi < 0.5:
            pcr_signal = "OVERBOUGHT"     # Too many calls = contrarian bearish
        elif pcr_oi < 0.8:
            pcr_signal = "BEARISH"        # Call writers confident
        else:
            pcr_signal = "NEUTRAL"
        
        # Max pain analysis
        if max_pain and underlying_value:
            pain_diff_pct = ((underlying_value - max_pain) / underlying_value) * 100
            
            if pain_diff_pct > 3:
                pain_signal = "PRICE_ABOVE_PAIN"    # Might pull down
            elif pain_diff_pct < -3:
                pain_signal = "PRICE_BELOW_PAIN"    # Might pull up
            else:
                pain_signal = "NEAR_MAX_PAIN"
        else:
            pain_signal = "UNKNOWN"
        
        return {
            "underlying_value": underlying_value,
            "expiry":           current_expiry,
            "pcr_oi":           pcr_oi,
            "pcr_volume":       pcr_volume,
            "pcr_signal":       pcr_signal,
            "total_call_oi":    total_call_oi,
            "total_put_oi":     total_put_oi,
            "max_pain":         max_pain,
            "pain_signal":      pain_signal,
            "available":        True,
        }
    
    except Exception as e:
        logger.warning(f"Option chain error for {clean}: {e}")
        return None


def _calculate_max_pain(strike_data: Dict, spot: float) -> Optional[float]:
    """Calculate max pain strike (where option writers profit most)."""
    if not strike_data or not spot:
        return None
    
    try:
        strikes = sorted(strike_data.keys())
        min_pain = float('inf')
        max_pain_strike = None
        
        for target_strike in strikes:
            total_pain = 0
            
            for strike, oi_data in strike_data.items():
                # Call writer pain (if price > strike, call writer loses)
                if target_strike > strike:
                    total_pain += (target_strike - strike) * oi_data["call_oi"]
                # Put writer pain (if price < strike, put writer loses)
                if target_strike < strike:
                    total_pain += (strike - target_strike) * oi_data["put_oi"]
            
            if total_pain < min_pain:
                min_pain = total_pain
                max_pain_strike = target_strike
        
        return max_pain_strike
    
    except Exception:
        return None


# ═══════════════════════════════════════════════════════════════
#   6. DELIVERY PERCENTAGE (Investment Interest)
# ═══════════════════════════════════════════════════════════════

def fetch_delivery_percentage(symbol: str) -> Optional[Dict]:
    """
    Get delivery percentage — indicates investment buying vs speculation.
    High delivery% = investors buying (bullish)
    Low delivery% = intraday chop (bearish)
    """
    clean = symbol.replace(".NS", "").replace(".BO", "").upper()
    client = get_client()
    
    endpoint = f"/api/quote-equity?symbol={clean}"
    data = client.get(endpoint)
    
    if not data:
        return None
    
    try:
        security_info = data.get("securityInfo", {})
        pre_open      = data.get("preOpenMarket", {})
        
        # Delivery data usually in different endpoint
        delivery_endpoint = f"/api/historical/cm/equity/deliverable?symbol={clean}&series=[%22EQ%22]"
        delivery_data = client.get(delivery_endpoint)
        
        if not delivery_data:
            return None
        
        records = delivery_data.get("data", [])
        if not records:
            return None
        
        # Get latest 5 days average
        recent = records[:5]
        
        delivery_pcts = []
        for r in recent:
            try:
                pct = float(r.get("COP_DELIV_PCT", 0))
                if pct > 0:
                    delivery_pcts.append(pct)
            except:
                continue
        
        if not delivery_pcts:
            return None
        
        avg_delivery = round(sum(delivery_pcts) / len(delivery_pcts), 2)
        latest_delivery = delivery_pcts[0]
        
        # Interpret
        if avg_delivery > 60:
            signal = "STRONG_INVESTMENT"    # Investors accumulating
        elif avg_delivery > 45:
            signal = "GOOD_INVESTMENT"
        elif avg_delivery > 30:
            signal = "NORMAL"
        elif avg_delivery > 20:
            signal = "SPECULATIVE"
        else:
            signal = "HEAVY_INTRADAY"       # Very speculative
        
        return {
            "avg_delivery_pct":    avg_delivery,
            "latest_delivery_pct": latest_delivery,
            "signal":              signal,
            "days_analyzed":       len(delivery_pcts),
        }
    
    except Exception as e:
        logger.debug(f"Delivery% error for {clean}: {e}")
        return None


# ═══════════════════════════════════════════════════════════════
#   MASTER FUNCTION: Get All NSE Intel
# ═══════════════════════════════════════════════════════════════

def get_nse_intelligence(symbol: str) -> Dict:
    """
    Get complete NSE intelligence for a stock.
    Returns everything the agent needs from official sources.
    """
    from concurrent.futures import ThreadPoolExecutor
    
    logger.info(f"🏛️ NSE: fetching complete intel for {symbol}...")
    
    # Parallel fetch (with global data cached separately)
    with ThreadPoolExecutor(max_workers=5) as executor:
        announcements_future = executor.submit(fetch_announcements, symbol)
        bulk_deals_future    = executor.submit(analyze_bulk_deals_for_stock, symbol)
        option_chain_future  = executor.submit(fetch_option_chain, symbol)
        delivery_future      = executor.submit(fetch_delivery_percentage, symbol)
        
        announcements = announcements_future.result()
        bulk_deals    = bulk_deals_future.result()
        option_chain  = option_chain_future.result()
        delivery      = delivery_future.result()
    
    # Global data (cached)
    fii_dii  = get_fii_dii_cached()
    is_banned = is_fno_banned(symbol)
    
    # ── Determine overall NSE signal ─────────────────────────
    signals = []
    
    # FII/DII contribution
    if fii_dii.get("available"):
        if "BULLISH" in fii_dii["signal"]:
            signals.append(("FII_DII", 1, 15))
        elif "BEARISH" in fii_dii["signal"]:
            signals.append(("FII_DII", -1, 15))
    
    # Bulk deals
    if bulk_deals.get("has_activity"):
        if "BUY" in bulk_deals["signal"]:
            signals.append(("BULK_DEALS", 1, 20))
        elif "SELL" in bulk_deals["signal"]:
            signals.append(("BULK_DEALS", -1, 20))
    
    # Options PCR
    if option_chain:
        pcr_signal = option_chain["pcr_signal"]
        if pcr_signal in ["BULLISH", "OVERSOLD"]:
            signals.append(("OPTIONS_PCR", 1, 15))
        elif pcr_signal in ["BEARISH", "OVERBOUGHT"]:
            signals.append(("OPTIONS_PCR", -1, 15))
    
    # Delivery% 
    if delivery:
        if "INVESTMENT" in delivery["signal"]:
            signals.append(("DELIVERY", 1, 10))
        elif "SPECULATIVE" in delivery["signal"] or "INTRADAY" in delivery["signal"]:
            signals.append(("DELIVERY", -1, 10))
    
    # Announcements — check for high impact
    negative_ann = [a for a in announcements if a.get("impact") == "HIGH_NEGATIVE"]
    positive_ann = [a for a in announcements if a.get("impact") == "HIGH_POSITIVE"]
    
    if negative_ann:
        signals.append(("ANNOUNCEMENTS", -1, 25))  # Big penalty
    if positive_ann:
        signals.append(("ANNOUNCEMENTS", 1, 20))
    
    # Calculate composite NSE score
    if signals:
        total_weight = sum(w for _, _, w in signals)
        weighted_sum = sum(direction * weight for _, direction, weight in signals)
        nse_score = weighted_sum / total_weight
    else:
        nse_score = 0
    
    # Label
    if nse_score > 0.3:
        nse_label = "STRONG_POSITIVE"
    elif nse_score > 0:
        nse_label = "POSITIVE"
    elif nse_score < -0.3:
        nse_label = "STRONG_NEGATIVE"
    elif nse_score < 0:
        nse_label = "NEGATIVE"
    else:
        nse_label = "NEUTRAL"
    
    # ── Risk Flags ───────────────────────────────────────────
    risk_flags = []
    if is_banned:
        risk_flags.append("FNO_BANNED")
    if negative_ann:
        risk_flags.append("NEGATIVE_ANNOUNCEMENT")
    if bulk_deals.get("signal") == "STRONG_SELL_PRESSURE":
        risk_flags.append("HEAVY_INSTITUTIONAL_SELLING")
    
    should_avoid = len(risk_flags) > 0
    
    logger.info(
        f"  NSE Verdict: {nse_label} (score: {nse_score:.2f}) | "
        f"Risks: {risk_flags if risk_flags else 'None'}"
    )
    
    return {
        "nse_score":         round(nse_score, 3),
        "nse_label":         nse_label,
        "should_avoid":      should_avoid,
        "risk_flags":        risk_flags,
        "signal_contributions": [
            {"source": s[0], "direction": s[1], "weight": s[2]}
            for s in signals
        ],
        "data": {
            "announcements":       announcements,
            "bulk_deals":          bulk_deals,
            "option_chain":        option_chain,
            "delivery":            delivery,
            "fii_dii":             fii_dii,
            "fno_banned":          is_banned,
        },
    }


# ─── Quick Test ───────────────────────────────────────────────
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    import json
    
    # Test individual
    print("\n" + "="*60)
    print("Testing FII/DII (global)")
    print("="*60)
    fii = get_fii_dii_cached()
    print(json.dumps(fii, indent=2))
    
    print("\n" + "="*60)
    print("Testing F&O Ban List")
    print("="*60)
    banned = get_fno_ban_list_cached()
    print(f"Banned stocks: {banned}")
    
    # Test master function
    for symbol in ["RELIANCE", "TCS"]:
        print(f"\n{'='*60}")
        print(f"Full NSE Intel: {symbol}")
        print("="*60)
        result = get_nse_intelligence(symbol)
        
        print(f"\n📊 NSE Score: {result['nse_score']}")
        print(f"   Label:      {result['nse_label']}")
        print(f"   Avoid:      {result['should_avoid']}")
        print(f"   Risks:      {result['risk_flags']}")
        
        if result['data']['bulk_deals']['has_activity']:
            bd = result['data']['bulk_deals']
            print(f"\n   Bulk Deals: {bd['deal_count']} deals, "
                  f"net ₹{bd['net_value']/1e7:.1f} Cr")
        
        if result['data']['option_chain']:
            oc = result['data']['option_chain']
            print(f"\n   Options:    PCR {oc['pcr_oi']} ({oc['pcr_signal']})")
            print(f"   Max Pain:   ₹{oc['max_pain']} vs Spot ₹{oc['underlying_value']}")
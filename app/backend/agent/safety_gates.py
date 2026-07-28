# E:\tradedo\app\backend\agent\safety_gates.py

"""
SAFETY GATES SYSTEM
Every trade candidate must pass ALL applicable gates.
If ANY gate fails → skip trade.

Gates:
1.  Time Window Gate      → Trade only in safe hours
2.  F&O Ban Gate          → Skip banned stocks
3.  Circuit Limit Gate    → Skip stocks near circuits
4.  Liquidity Gate        → Enough volume today
5.  Sector Diversify      → Max 1 trade per sector
6.  Correlation Gate      → Not too similar to existing
7.  Daily Loss Gate       → Stop if daily loss hit
8.  Max Positions Gate    → Not already at max trades
9.  Cooldown Gate         → Wait between similar trades
10. Data Freshness Gate   → Recent data available
11. Beta/VIX Gate         → Volatility appropriate
12. News Blocker Gate     → No major negative news
"""

import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta, time
import yfinance as yf

logger = logging.getLogger("tradedo.gates")


# ═══════════════════════════════════════════════════════════════
#   CONFIGURATION
# ═══════════════════════════════════════════════════════════════

# Market hours (IST)
MARKET_OPEN     = time(9, 15)
MARKET_CLOSE    = time(15, 30)
NO_TRADE_START  = time(15, 0)   # No new trades after 3 PM

# Safe trading windows (avoid high volatility periods)
SAFE_WINDOWS = [
    (time(9, 45),  time(11, 30)),  # Post-opening settle to lunch
    (time(13, 30), time(15, 0)),   # Post-lunch trend to closing
]

# Risk limits
MAX_OPEN_POSITIONS   = 3         # Max simultaneous trades
MAX_DAILY_LOSS_PCT   = 5.0       # Stop trading if down 5%
MAX_PER_SECTOR       = 1         # Max 1 trade per sector

# Cooldown periods (minutes)
COOLDOWN_SAME_STOCK    = 60      # Wait 60 min before re-trading same stock
COOLDOWN_SAME_SECTOR   = 30      # Wait 30 min between same sector

# Liquidity thresholds
MIN_AVG_VOLUME       = 100000    # Min avg daily volume
MIN_TODAYS_VOLUME    = 50000     # Min today's volume

# VIX thresholds
HIGH_VIX             = 20
EXTREME_VIX          = 25

# Circuit safety
CIRCUIT_SAFETY_PCT   = 2.0       # Skip if within 2% of circuit


# ═══════════════════════════════════════════════════════════════
#   GATE RESULT DATA CLASS
# ═══════════════════════════════════════════════════════════════

class GateResult:
    """Result of a single gate check."""
    
    def __init__(self, name: str, passed: bool, reason: str = "", data: Dict = None):
        self.name    = name
        self.passed  = passed
        self.reason  = reason
        self.data    = data or {}
    
    def to_dict(self) -> Dict:
        return {
            "gate":   self.name,
            "passed": self.passed,
            "reason": self.reason,
            "data":   self.data,
        }
    
    def __repr__(self):
        icon = "✅" if self.passed else "❌"
        return f"{icon} {self.name}: {self.reason}"


# ═══════════════════════════════════════════════════════════════
#   INDIVIDUAL GATES
# ═══════════════════════════════════════════════════════════════

def check_time_window_gate(mode: str = "intraday") -> GateResult:
    """Gate 1: Check if current time is in safe trading window."""
    now = datetime.now().time()
    
    # For swing mode, less time restriction
    if mode == "swing":
        if MARKET_OPEN <= now <= NO_TRADE_START:
            return GateResult(
                "TIME_WINDOW", True,
                f"Market open ({now.strftime('%H:%M')})",
                {"current_time": now.strftime("%H:%M")}
            )
        return GateResult(
            "TIME_WINDOW", False,
            f"Outside safe trading hours ({now.strftime('%H:%M')})",
            {"current_time": now.strftime("%H:%M")}
        )
    
    # For intraday: strict safe windows
    for start, end in SAFE_WINDOWS:
        if start <= now <= end:
            return GateResult(
                "TIME_WINDOW", True,
                f"In safe window {start.strftime('%H:%M')}-{end.strftime('%H:%M')}",
                {"current_time": now.strftime("%H:%M")}
            )
    
    # Not in safe window
    if now < MARKET_OPEN:
        reason = "Market not open yet"
    elif now > NO_TRADE_START:
        reason = "Too late for new intraday trades"
    elif time(11, 30) < now < time(13, 30):
        reason = "Lunch hour — weak trends"
    elif time(9, 15) <= now < time(9, 45):
        reason = "Opening volatility — wait for settle"
    else:
        reason = f"Outside safe window ({now.strftime('%H:%M')})"
    
    return GateResult(
        "TIME_WINDOW", False, reason,
        {"current_time": now.strftime("%H:%M")}
    )


def check_fno_ban_gate(symbol: str) -> GateResult:
    """Gate 2: Skip F&O banned stocks."""
    from data_pipeline.nse_data import is_fno_banned
    
    if is_fno_banned(symbol):
        return GateResult(
            "FNO_BAN", False,
            f"{symbol} is in F&O ban list today",
            {"banned": True}
        )
    
    return GateResult("FNO_BAN", True, "Not in ban list")


def check_circuit_limit_gate(symbol: str) -> GateResult:
    """Gate 3: Skip if near circuit limits."""
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.fast_info
        
        current_price = info.get("last_price", 0)
        prev_close    = info.get("regular_market_previous_close", 0)
        
        if not current_price or not prev_close:
            return GateResult(
                "CIRCUIT_LIMIT", True,
                "Cannot verify (skipping check)",
                {}
            )
        
        change_pct = ((current_price - prev_close) / prev_close) * 100
        
        # Upper circuit (usually 10% or 20%)
        # Being safe: skip if within 2% of possible circuit
        if change_pct >= 8:  # Approaching upper circuit
            return GateResult(
                "CIRCUIT_LIMIT", False,
                f"Near upper circuit (+{change_pct:.1f}%)",
                {"change_pct": change_pct}
            )
        
        if change_pct <= -8:  # Approaching lower circuit
            return GateResult(
                "CIRCUIT_LIMIT", False,
                f"Near lower circuit ({change_pct:.1f}%)",
                {"change_pct": change_pct}
            )
        
        return GateResult(
            "CIRCUIT_LIMIT", True,
            f"Safe distance from circuits ({change_pct:+.1f}%)",
            {"change_pct": change_pct}
        )
    
    except Exception as e:
        logger.debug(f"Circuit check failed for {symbol}: {e}")
        return GateResult(
            "CIRCUIT_LIMIT", True,
            "Check skipped due to error",
            {"error": str(e)}
        )


def check_liquidity_gate(symbol: str) -> GateResult:
    """Gate 4: Check liquidity (volume)."""
    try:
        ticker = yf.Ticker(symbol)
        
        # Get last 10 days volume
        hist = ticker.history(period="10d", interval="1d")
        
        if hist.empty:
            return GateResult(
                "LIQUIDITY", False,
                "No volume data available",
                {}
            )
        
        avg_volume = float(hist["Volume"].mean())
        today_volume = float(hist["Volume"].iloc[-1])
        
        if avg_volume < MIN_AVG_VOLUME:
            return GateResult(
                "LIQUIDITY", False,
                f"Low avg volume ({avg_volume:,.0f} < {MIN_AVG_VOLUME:,})",
                {"avg_volume": avg_volume, "today_volume": today_volume}
            )
        
        # Check if today's volume is normal
        volume_ratio = today_volume / avg_volume if avg_volume else 0
        
        if volume_ratio < 0.3:
            return GateResult(
                "LIQUIDITY", False,
                f"Very low today's volume ({volume_ratio:.1%} of avg)",
                {"volume_ratio": volume_ratio}
            )
        
        return GateResult(
            "LIQUIDITY", True,
            f"Volume OK ({volume_ratio:.1f}x avg)",
            {"avg_volume": avg_volume, "today_volume": today_volume, "ratio": volume_ratio}
        )
    
    except Exception as e:
        logger.debug(f"Liquidity check failed for {symbol}: {e}")
        return GateResult(
            "LIQUIDITY", True,
            "Check skipped due to error",
            {"error": str(e)}
        )


def check_sector_diversify_gate(
    symbol: str,
    open_positions: List[Dict]
) -> GateResult:
    """Gate 5: Sector diversification (max 1 per sector)."""
    from agent.sectors import get_sector
    
    new_sector = get_sector(symbol)
    
    if new_sector == "UNKNOWN":
        return GateResult(
            "SECTOR_DIVERSIFY", True,
            "Unknown sector — allowing"
        )
    
    # Count existing positions in this sector
    same_sector_count = sum(
        1 for pos in open_positions
        if get_sector(pos.get("symbol", "")) == new_sector
    )
    
    if same_sector_count >= MAX_PER_SECTOR:
        return GateResult(
            "SECTOR_DIVERSIFY", False,
            f"Already {same_sector_count} trade(s) in {new_sector} sector",
            {"sector": new_sector, "existing_count": same_sector_count}
        )
    
    return GateResult(
        "SECTOR_DIVERSIFY", True,
        f"No conflict in {new_sector} sector",
        {"sector": new_sector}
    )


def check_correlation_gate(
    symbol: str,
    open_positions: List[Dict]
) -> GateResult:
    """
    Gate 6: Correlation check.
    Avoid opening highly correlated trades.
    Simplified: check if same sector + high beta stocks.
    """
    from agent.sectors import get_sector
    
    if not open_positions:
        return GateResult(
            "CORRELATION", True,
            "No open positions to correlate with"
        )
    
    new_sector = get_sector(symbol)
    
    # Highly correlated groups
    correlated_groups = [
        {"BANKING", "NBFC", "INSURANCE"},         # Financial cluster
        {"ENERGY", "POWER", "MINING"},             # Energy cluster
        {"IT", "TECH", "FINANCIAL_TECH"},          # Tech cluster
        {"METALS", "MINING"},                       # Metals cluster
        {"AUTO", "AUTO"},                           # Auto cluster
    ]
    
    for pos in open_positions:
        pos_sector = get_sector(pos.get("symbol", ""))
        
        # Same sector already caught by sector gate
        if pos_sector == new_sector:
            continue
        
        # Check if in same correlated group
        for group in correlated_groups:
            if new_sector in group and pos_sector in group:
                return GateResult(
                    "CORRELATION", False,
                    f"Highly correlated with {pos.get('symbol')} ({pos_sector})",
                    {
                        "new_sector":      new_sector,
                        "conflict_symbol": pos.get("symbol"),
                        "conflict_sector": pos_sector
                    }
                )
    
    return GateResult("CORRELATION", True, "No correlation conflict")


def check_daily_loss_gate(
    current_capital: float,
    starting_capital: float
) -> GateResult:
    """Gate 7: Stop trading if daily loss limit hit."""
    if not starting_capital:
        return GateResult(
            "DAILY_LOSS", True,
            "No baseline capital data"
        )
    
    daily_pnl_pct = ((current_capital - starting_capital) / starting_capital) * 100
    
    if daily_pnl_pct <= -MAX_DAILY_LOSS_PCT:
        return GateResult(
            "DAILY_LOSS", False,
            f"Daily loss limit hit ({daily_pnl_pct:.2f}% <= -{MAX_DAILY_LOSS_PCT}%)",
            {"daily_pnl_pct": daily_pnl_pct}
        )
    
    return GateResult(
        "DAILY_LOSS", True,
        f"Within loss limit ({daily_pnl_pct:+.2f}%)",
        {"daily_pnl_pct": daily_pnl_pct}
    )


def check_max_positions_gate(
    open_positions: List[Dict]
) -> GateResult:
    """Gate 8: Max concurrent positions."""
    count = len(open_positions)
    
    if count >= MAX_OPEN_POSITIONS:
        return GateResult(
            "MAX_POSITIONS", False,
            f"Already at max positions ({count}/{MAX_OPEN_POSITIONS})",
            {"open_count": count, "max": MAX_OPEN_POSITIONS}
        )
    
    return GateResult(
        "MAX_POSITIONS", True,
        f"Room for more ({count}/{MAX_OPEN_POSITIONS})",
        {"open_count": count, "max": MAX_OPEN_POSITIONS}
    )


def check_cooldown_gate(
    symbol: str,
    recent_trades: List[Dict]
) -> GateResult:
    """
    Gate 9: Cooldown between trades on same stock/sector.
    """
    from agent.sectors import get_sector
    
    if not recent_trades:
        return GateResult("COOLDOWN", True, "No recent trades")
    
    now = datetime.now()
    new_sector = get_sector(symbol)
    
    # Check same stock cooldown
    for trade in recent_trades:
        if trade.get("symbol", "").upper() != symbol.upper():
            continue
        
        # Parse trade time
        trade_time_str = trade.get("entry_time") or trade.get("exit_time", "")
        if not trade_time_str:
            continue
        
        try:
            trade_time = datetime.fromisoformat(trade_time_str.replace("Z", "+00:00"))
            if trade_time.tzinfo:
                trade_time = trade_time.replace(tzinfo=None)
            
            mins_ago = (now - trade_time).total_seconds() / 60
            
            if mins_ago < COOLDOWN_SAME_STOCK:
                return GateResult(
                    "COOLDOWN", False,
                    f"Same stock cooldown ({mins_ago:.0f} min < {COOLDOWN_SAME_STOCK} min)",
                    {"mins_ago": mins_ago}
                )
        except Exception:
            continue
    
    # Check same sector cooldown
    for trade in recent_trades:
        trade_sector = get_sector(trade.get("symbol", ""))
        if trade_sector != new_sector or new_sector == "UNKNOWN":
            continue
        
        trade_time_str = trade.get("entry_time", "")
        if not trade_time_str:
            continue
        
        try:
            trade_time = datetime.fromisoformat(trade_time_str.replace("Z", "+00:00"))
            if trade_time.tzinfo:
                trade_time = trade_time.replace(tzinfo=None)
            
            mins_ago = (now - trade_time).total_seconds() / 60
            
            if mins_ago < COOLDOWN_SAME_SECTOR:
                return GateResult(
                    "COOLDOWN", False,
                    f"Same sector cooldown ({new_sector}, {mins_ago:.0f} min)",
                    {"mins_ago": mins_ago, "sector": new_sector}
                )
        except Exception:
            continue
    
    return GateResult("COOLDOWN", True, "Cooldown periods passed")


def check_data_freshness_gate(symbol: str) -> GateResult:
    """Gate 10: Ensure data is fresh."""
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.fast_info
        
        # Check if we have current price
        last_price = info.get("last_price", 0)
        
        if not last_price or last_price <= 0:
            return GateResult(
                "DATA_FRESHNESS", False,
                "No current price data available",
                {}
            )
        
        return GateResult(
            "DATA_FRESHNESS", True,
            "Fresh data available",
            {"last_price": last_price}
        )
    
    except Exception as e:
        return GateResult(
            "DATA_FRESHNESS", False,
            f"Data fetch failed: {str(e)[:50]}",
            {"error": str(e)}
        )


def check_vix_gate(symbol: str) -> GateResult:
    """
    Gate 11: VIX-based volatility check.
    Skip volatile stocks during high VIX periods.
    """
    try:
        from data_pipeline.global_markets import fetch_single_indicator, GLOBAL_INDICATORS
        
        vix_data = fetch_single_indicator("INDIA_VIX", GLOBAL_INDICATORS["INDIA_VIX"])
        
        if not vix_data:
            return GateResult("VIX_CHECK", True, "VIX data unavailable — allowing")
        
        vix_value = vix_data["value"]
        
        if vix_value >= EXTREME_VIX:
            # Extreme fear — only trade very safe (large cap) stocks
            from agent.universe import NIFTY_50
            
            if symbol not in NIFTY_50:
                return GateResult(
                    "VIX_CHECK", False,
                    f"Extreme VIX ({vix_value:.1f}) — only Nifty 50 allowed",
                    {"vix": vix_value}
                )
        
        if vix_value >= HIGH_VIX:
            # High volatility — check stock's own volatility
            try:
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period="20d", interval="1d")
                
                if not hist.empty:
                    daily_returns = hist["Close"].pct_change()
                    stock_volatility = daily_returns.std() * 100
                    
                    # Reject very volatile stocks in high VIX
                    if stock_volatility > 3:
                        return GateResult(
                            "VIX_CHECK", False,
                            f"High VIX ({vix_value:.1f}) + volatile stock ({stock_volatility:.1f}%)",
                            {"vix": vix_value, "stock_vol": stock_volatility}
                        )
            except:
                pass
        
        return GateResult(
            "VIX_CHECK", True,
            f"VIX acceptable ({vix_value:.1f})",
            {"vix": vix_value}
        )
    
    except Exception as e:
        return GateResult("VIX_CHECK", True, "Check skipped", {"error": str(e)})


def check_news_blocker_gate(master_result: Dict) -> GateResult:
    """
    Gate 12: Block trades with major negative news.
    Uses data from master scorer.
    """
    # Check news risk flag
    news = master_result.get("news", {})
    if news.get("risk_flag"):
        return GateResult(
            "NEWS_BLOCKER", False,
            "Risk flag detected in news",
            {"news_label": news.get("label")}
        )
    
    # Check very negative news
    if news.get("score", 0) < -0.5:
        return GateResult(
            "NEWS_BLOCKER", False,
            f"Very negative news sentiment ({news.get('score')})",
            {"news_score": news.get("score")}
        )
    
    # Check NSE risk flags
    nse = master_result.get("nse", {})
    risk_flags = nse.get("risk_flags", [])
    
    if "NEGATIVE_ANNOUNCEMENT" in risk_flags:
        return GateResult(
            "NEWS_BLOCKER", False,
            "Negative NSE announcement detected",
            {"nse_risks": risk_flags}
        )
    
    return GateResult("NEWS_BLOCKER", True, "No blocking news")


# ═══════════════════════════════════════════════════════════════
#   MASTER GATE CHECKER
# ═══════════════════════════════════════════════════════════════

class SafetyGateChecker:
    """Runs ALL safety gates for a trade candidate."""
    
    def __init__(
        self,
        symbol: str,
        mode: str = "intraday",
        open_positions: List[Dict] = None,
        recent_trades: List[Dict] = None,
        current_capital: float = 100000,
        starting_capital: float = 100000,
        master_result: Dict = None,
    ):
        self.symbol           = symbol
        self.mode             = mode
        self.open_positions   = open_positions or []
        self.recent_trades    = recent_trades or []
        self.current_capital  = current_capital
        self.starting_capital = starting_capital
        self.master_result    = master_result or {}
        
        self.results = []
    
    def run_all_gates(self) -> Dict:
        """Run every safety gate and compile results."""
        logger.info(f"🛡️ Running safety gates for {self.symbol}...")
        
        gates = [
            ("time_window",     lambda: check_time_window_gate(self.mode)),
            ("fno_ban",         lambda: check_fno_ban_gate(self.symbol)),
            ("circuit_limit",   lambda: check_circuit_limit_gate(self.symbol)),
            ("liquidity",       lambda: check_liquidity_gate(self.symbol)),
            ("sector_diversify", lambda: check_sector_diversify_gate(
                self.symbol, self.open_positions
            )),
            ("correlation",     lambda: check_correlation_gate(
                self.symbol, self.open_positions
            )),
            ("daily_loss",      lambda: check_daily_loss_gate(
                self.current_capital, self.starting_capital
            )),
            ("max_positions",   lambda: check_max_positions_gate(self.open_positions)),
            ("cooldown",        lambda: check_cooldown_gate(
                self.symbol, self.recent_trades
            )),
            ("data_freshness",  lambda: check_data_freshness_gate(self.symbol)),
            ("vix_check",       lambda: check_vix_gate(self.symbol)),
            ("news_blocker",    lambda: check_news_blocker_gate(self.master_result)),
        ]
        
        passed_count = 0
        failed_count = 0
        failed_gates = []
        
        for gate_name, gate_func in gates:
            try:
                result = gate_func()
                self.results.append(result)
                
                if result.passed:
                    passed_count += 1
                    logger.debug(f"  ✅ {result.name}: {result.reason}")
                else:
                    failed_count += 1
                    failed_gates.append(result.name)
                    logger.info(f"  ❌ {result.name}: {result.reason}")
            
            except Exception as e:
                logger.error(f"Gate {gate_name} crashed: {e}")
                self.results.append(GateResult(
                    gate_name.upper(), False, f"Gate error: {str(e)[:50]}"
                ))
                failed_count += 1
                failed_gates.append(gate_name.upper())
        
        # Overall verdict
        all_passed = failed_count == 0
        
        if all_passed:
            verdict_msg = f"✅ ALL {passed_count} GATES PASSED — Safe to trade"
            logger.info(f"  {verdict_msg}")
        else:
            verdict_msg = f"❌ {failed_count} GATE(S) FAILED — Cannot trade"
            logger.info(f"  {verdict_msg}: {failed_gates}")
        
        return {
            "symbol":         self.symbol,
            "safe_to_trade":  all_passed,
            "gates_passed":   passed_count,
            "gates_failed":   failed_count,
            "total_gates":    len(gates),
            "failed_gates":   failed_gates,
            "gate_results":   [r.to_dict() for r in self.results],
            "verdict":        verdict_msg,
        }


# ═══════════════════════════════════════════════════════════════
#   Main Entry Function
# ═══════════════════════════════════════════════════════════════

def check_all_gates(
    symbol: str,
    mode: str = "intraday",
    open_positions: List[Dict] = None,
    recent_trades: List[Dict] = None,
    current_capital: float = 100000,
    starting_capital: float = 100000,
    master_result: Dict = None,
) -> Dict:
    """
    Main entry point.
    Returns whether it's safe to trade this symbol right now.
    """
    checker = SafetyGateChecker(
        symbol=symbol,
        mode=mode,
        open_positions=open_positions,
        recent_trades=recent_trades,
        current_capital=current_capital,
        starting_capital=starting_capital,
        master_result=master_result,
    )
    return checker.run_all_gates()


# ─── Quick Test ───────────────────────────────────────────────
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    import json
    
    print("\n" + "="*60)
    print("SAFETY GATES TEST")
    print("="*60)
    
    # Mock open positions
    mock_positions = [
        {"symbol": "TCS.NS", "entry_time": (datetime.now() - timedelta(hours=2)).isoformat()},
    ]
    
    # Mock recent trades
    mock_trades = [
        {"symbol": "INFY.NS", "entry_time": (datetime.now() - timedelta(minutes=90)).isoformat()},
    ]
    
    # Test RELIANCE
    result = check_all_gates(
        symbol="RELIANCE.NS",
        mode="intraday",
        open_positions=mock_positions,
        recent_trades=mock_trades,
        current_capital=100000,
        starting_capital=100000,
    )
    
    print(f"\n📊 Result: {result['verdict']}")
    print(f"   Passed: {result['gates_passed']}/{result['total_gates']}")
    
    if result['failed_gates']:
        print(f"   Failed: {result['failed_gates']}")
    
    print("\n📋 All Gate Results:")
    for gate in result['gate_results']:
        icon = "✅" if gate['passed'] else "❌"
        print(f"   {icon} {gate['gate']:20s}: {gate['reason']}")
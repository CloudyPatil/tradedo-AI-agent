# E:\tradedo\app\backend\ml\trade_planner.py

import logging
from typing import Dict, Optional
from datetime import datetime, timedelta

logger = logging.getLogger("tradedo.planner")

# ─── Configuration ────────────────────────────────────────────
VIRTUAL_CAPITAL   = 100000    # ₹1L virtual capital
RISK_PER_TRADE    = 0.02      # 2% risk per trade
MAX_HOLD_SWING    = 7         # Max 7 trading days for swing
MAX_HOLD_INTRADAY = 1         # Same day exit


def generate_trade_plan(prediction: Dict, mode: str = "swing") -> Dict:
    """
    Generate actionable trade plan from prediction.
    
    Uses ATR for volatility-based stops and targets.
    Calculates position size based on risk management.
    
    Returns full trade plan with entry, exit, SL, targets.
    """
    signal    = prediction.get("signal")
    price     = prediction.get("current_price", 0)
    indicators = prediction.get("indicators", {})
    atr       = indicators.get("atr", 0)
    confidence = prediction.get("confidence_pct", 50)
    composite  = prediction.get("composite", {}).get("composite_score", 50)
    
    # ── If HOLD, return simple message ────────────────────────
    if signal == "HOLD" or not atr or atr <= 0:
        return {
            "action":      "WAIT",
            "reason":      "No clear trade setup. Wait for better opportunity.",
            "tradeable":   False,
        }
    
    # ── Direction Multipliers ────────────────────────────────
    is_long = (signal == "BUY")
    direction_sign = 1 if is_long else -1
    
    # ── ATR Multipliers (mode-dependent) ─────────────────────
    if mode == "intraday":
        sl_mult      = 0.75   # Tight SL for intraday
        target1_mult = 1.0    # Quick 1st target
        target2_mult = 1.5    # Extended target
        hold_days    = 0      # Same day
    else:  # swing
        sl_mult      = 1.0    # Standard SL
        target1_mult = 1.5    # 1st target at 1.5x ATR
        target2_mult = 2.5    # 2nd target at 2.5x ATR
        
        # Adjust hold time based on confidence
        if confidence >= 70:
            hold_days = 7
        elif confidence >= 60:
            hold_days = 5
        else:
            hold_days = 3
    
    # ── Calculate Levels ─────────────────────────────────────
    entry     = round(price, 2)
    stop_loss = round(entry - (direction_sign * atr * sl_mult), 2)
    target_1  = round(entry + (direction_sign * atr * target1_mult), 2)
    target_2  = round(entry + (direction_sign * atr * target2_mult), 2)
    
    # ── Calculate Percentages ────────────────────────────────
    sl_pct       = round(((stop_loss - entry) / entry) * 100, 2)
    target1_pct  = round(((target_1 - entry) / entry) * 100, 2)
    target2_pct  = round(((target_2 - entry) / entry) * 100, 2)
    
    # ── Risk-Reward Ratios ──────────────────────────────────
    risk         = abs(entry - stop_loss)
    reward_1     = abs(target_1 - entry)
    reward_2     = abs(target_2 - entry)
    rr_1         = round(reward_1 / risk, 2) if risk > 0 else 0
    rr_2         = round(reward_2 / risk, 2) if risk > 0 else 0
    
    # ── Position Sizing (2% capital risk rule) ──────────────
    risk_amount  = VIRTUAL_CAPITAL * RISK_PER_TRADE   # ₹2000
    shares       = int(risk_amount / risk) if risk > 0 else 0
    investment   = round(shares * entry, 2)
    
    # Cap if investment exceeds 40% of capital
    max_investment = VIRTUAL_CAPITAL * 0.4
    if investment > max_investment:
        shares     = int(max_investment / entry)
        investment = round(shares * entry, 2)
    
    # ── Time Windows ─────────────────────────────────────────
    today = datetime.now()
    
    if mode == "intraday":
        entry_window = "Within next 30 minutes for best liquidity"
        exit_by      = "3:15 PM today (auto square-off)"
        exit_date    = today.strftime("%d %b %Y")
        best_time    = "9:15-10:00 AM (opening momentum) or 2:30-3:00 PM (closing move)"
    else:
        entry_window = f"Today or within next 2 trading days"
        exit_date_dt = _add_trading_days(today, hold_days)
        exit_by      = exit_date_dt.strftime("%d %b %Y")
        exit_date    = exit_by
        best_time    = "First 30 mins of market open (9:15-9:45 AM)"
    
    # ── Timing Confidence ────────────────────────────────────
    # Higher composite score = higher timing confidence
    timing_confidence = min(round(composite * 0.9), 95)
    
    # ── Invalidation Rules ───────────────────────────────────
    rsi = indicators.get("rsi", 50)
    if is_long:
        invalidation = (
            f"Exit early if price closes below ₹{stop_loss} "
            f"OR RSI drops below 30 (currently {rsi:.0f})"
        )
    else:
        invalidation = (
            f"Exit early if price closes above ₹{stop_loss} "
            f"OR RSI rises above 70 (currently {rsi:.0f})"
        )
    
    # ── Trailing Stop Strategy ───────────────────────────────
    trailing_stop = _build_trailing_strategy(
        entry, target_1, target_2, is_long
    )
    
    # ── Final Trade Plan ─────────────────────────────────────
    plan = {
        "action":          signal,   # BUY or SELL
        "direction":       "LONG" if is_long else "SHORT",
        "tradeable":       True,
        
        # Entry
        "entry": {
            "price":       entry,
            "window":      entry_window,
            "best_time":   best_time,
        },
        
        # Targets & Stop Loss
        "target_1": {
            "price":       target_1,
            "profit_pct":  abs(target1_pct),
            "book_pct":    50,      # Book 50% here
            "rr_ratio":    rr_1,
        },
        "target_2": {
            "price":       target_2,
            "profit_pct":  abs(target2_pct),
            "book_pct":    50,      # Book remaining 50%
            "rr_ratio":    rr_2,
        },
        "stop_loss": {
            "price":       stop_loss,
            "loss_pct":    abs(sl_pct),
            "risk_amount": round(risk_amount, 2),
        },
        
        # Time Exit
        "time_exit": {
            "hold_days":   hold_days,
            "exit_by":     exit_by,
        },
        
        # Position Sizing
        "position": {
            "capital":     VIRTUAL_CAPITAL,
            "risk_pct":    RISK_PER_TRADE * 100,
            "shares":      shares,
            "investment":  investment,
            "max_loss":    round(shares * risk, 2),
            "max_profit":  round(shares * reward_2, 2),
        },
        
        # Risk-Reward Summary
        "risk_reward": {
            "target_1":    f"1:{rr_1}",
            "target_2":    f"1:{rr_2}",
            "avg":         f"1:{round((rr_1 + rr_2)/2, 2)}",
        },
        
        # Strategy
        "trailing_stop":   trailing_stop,
        "invalidation":    invalidation,
        
        # Confidence
        "confidence": {
            "direction":   round(confidence, 1),
            "timing":      timing_confidence,
            "overall":     round((confidence + timing_confidence) / 2, 1),
        },
    }
    
    logger.info(
        f"Trade Plan: {signal} @ ₹{entry} | "
        f"SL: ₹{stop_loss} | T1: ₹{target_1} | T2: ₹{target_2} | "
        f"Shares: {shares}"
    )
    
    return plan


def _add_trading_days(start: datetime, days: int) -> datetime:
    """Add trading days (skip weekends)."""
    result = start
    added  = 0
    while added < days:
        result += timedelta(days=1)
        if result.weekday() < 5:  # Mon-Fri
            added += 1
    return result


def _build_trailing_strategy(
    entry: float, target_1: float, target_2: float, is_long: bool
) -> Dict:
    """Build trailing stop rules."""
    if is_long:
        breakeven_trigger = round(entry + (target_1 - entry) * 0.5, 2)
        profit_lock       = round(entry + (target_1 - entry) * 0.8, 2)
    else:
        breakeven_trigger = round(entry - (entry - target_1) * 0.5, 2)
        profit_lock       = round(entry - (entry - target_1) * 0.8, 2)
    
    return {
        "step_1": (
            f"When price reaches ₹{breakeven_trigger}, "
            f"move stop loss to entry (₹{entry}) — breakeven"
        ),
        "step_2": (
            f"When price reaches ₹{target_1}, "
            f"book 50% profit and move SL to ₹{profit_lock}"
        ),
        "step_3": (
            f"For remaining 50%, target ₹{target_2} "
            f"with trailing stop at 1x ATR"
        ),
    }


# ─── Quick Test ───────────────────────────────────────────────
if __name__ == "__main__":
    # Mock prediction for testing
    mock = {
        "signal": "BUY",
        "current_price": 2450,
        "confidence_pct": 78,
        "composite": {"composite_score": 74},
        "indicators": {
            "atr": 42,
            "rsi": 55,
        }
    }
    
    plan = generate_trade_plan(mock, mode="swing")
    
    import json
    print(json.dumps(plan, indent=2))
# E:\tradedo\app\backend\agent\risk_manager.py

"""
ADVANCED RISK MANAGER
Calculates position sizing, stop loss, targets based on:
- Volatility (ATR)
- Confidence level
- Sector characteristics
- Market regime
- Current portfolio exposure
"""

import logging
from typing import Dict, Optional
from datetime import datetime

logger = logging.getLogger("tradedo.risk")


# ═══════════════════════════════════════════════════════════════
#   RISK CONFIGURATION
# ═══════════════════════════════════════════════════════════════

# Capital management
STARTING_CAPITAL     = 100000   # ₹1L virtual capital
RISK_PER_TRADE_PCT   = 2.0      # 2% max risk per trade
MAX_POSITION_PCT     = 25.0     # Max 25% capital per trade
MAX_TOTAL_EXPOSURE   = 75.0     # Max 75% capital deployed

# Confidence-based risk scaling
CONFIDENCE_RISK_SCALE = {
    "VERY_HIGH":  1.5,    # 3% risk for very high confidence
    "HIGH":       1.2,    # 2.4% risk for high confidence
    "MEDIUM":     1.0,    # 2% standard risk
    "LOW":        0.5,    # 1% risk for low confidence
}

# ATR-based stops (mode-specific)
ATR_MULTIPLIERS = {
    "intraday": {
        "sl":        0.75,   # Tight SL for intraday
        "target_1":  1.0,    # Quick 1st target
        "target_2":  1.5,    # Extended target
    },
    "swing": {
        "sl":        1.0,    # Standard SL
        "target_1":  1.5,    # 1st target
        "target_2":  2.5,    # Extended target
    },
}

# Sector-specific volatility adjustments
SECTOR_VOLATILITY = {
    "BANKING":   1.0,    # Standard
    "IT":        1.0,    # Standard
    "FMCG":      0.8,    # Less volatile
    "PHARMA":    1.1,    # Slightly more volatile
    "AUTO":      1.2,    # More volatile
    "METALS":    1.3,    # High volatility
    "ENERGY":    1.2,    # Moderate-high
    "REALTY":    1.4,    # Highest
    "NBFC":      1.1,
    "INSURANCE": 0.9,
    "TELECOM":   1.0,
    "CEMENT":    0.9,
    "CONSUMER":  0.9,
    "TECH":      1.2,
    "AVIATION":  1.5,    # Very volatile
    "MEDIA":     1.3,
    "UNKNOWN":   1.1,    # Conservative default
}


# ═══════════════════════════════════════════════════════════════
#   RISK MANAGER CLASS
# ═══════════════════════════════════════════════════════════════

class RiskManager:
    """
    Calculates optimal position size, stop loss, and targets
    for a trade based on multiple risk factors.
    """
    
    def __init__(
        self,
        capital: float = STARTING_CAPITAL,
        current_exposure: float = 0.0,
        open_positions: int = 0,
    ):
        """
        Args:
            capital: Current available capital
            current_exposure: Money already deployed (₹)
            open_positions: Number of open trades
        """
        self.capital           = capital
        self.current_exposure  = current_exposure
        self.open_positions    = open_positions
    
    def calculate_trade_params(
        self,
        symbol: str,
        entry_price: float,
        atr: float,
        signal: str,
        confidence_pct: float,
        mode: str = "intraday",
        sector: str = "UNKNOWN",
    ) -> Dict:
        """
        Calculate complete trade parameters.
        
        Returns dict with:
        - Position size (shares & value)
        - Stop loss price
        - Target 1 & 2 prices
        - Risk-reward ratio
        - Risk amount
        """
        if entry_price <= 0 or atr <= 0:
            return self._invalid_trade("Invalid price or ATR data")
        
        # 1. Determine confidence level
        confidence_level = self._get_confidence_level(confidence_pct)
        
        # 2. Calculate risk amount (with confidence scaling)
        risk_amount = self._calculate_risk_amount(confidence_level)
        
        # 3. Get ATR multipliers for mode
        multipliers = ATR_MULTIPLIERS.get(mode, ATR_MULTIPLIERS["intraday"]).copy()
        
        # 4. Apply sector volatility adjustment
        sector_mult = SECTOR_VOLATILITY.get(sector, 1.0)
        multipliers["sl"] *= sector_mult
        # Keep targets proportional to SL
        
        # 5. Calculate levels based on signal direction
        is_long = (signal == "BUY")
        direction = 1 if is_long else -1
        
        stop_distance = atr * multipliers["sl"]
        
        stop_loss = round(
            entry_price - (direction * stop_distance), 2
        )
        target_1 = round(
            entry_price + (direction * atr * multipliers["target_1"]), 2
        )
        target_2 = round(
            entry_price + (direction * atr * multipliers["target_2"]), 2
        )
        
        # 6. Calculate position size
        # Formula: shares = risk_amount / stop_distance
        raw_shares = int(risk_amount / stop_distance)
        
        # Cap by max position % of capital
        max_investment = self.capital * (MAX_POSITION_PCT / 100)
        max_shares_by_pct = int(max_investment / entry_price)
        
        # Take smaller of the two
        shares = min(raw_shares, max_shares_by_pct)
        
        # Ensure minimum 1 share
        if shares < 1:
            return self._invalid_trade("Insufficient capital for even 1 share")
        
        # 7. Calculate final values
        investment       = round(shares * entry_price, 2)
        actual_risk      = round(shares * stop_distance, 2)
        potential_profit_1 = round(shares * abs(target_1 - entry_price), 2)
        potential_profit_2 = round(shares * abs(target_2 - entry_price), 2)
        
        # 8. Calculate percentages
        sl_pct      = round(((stop_loss - entry_price) / entry_price) * 100, 2)
        target1_pct = round(((target_1 - entry_price) / entry_price) * 100, 2)
        target2_pct = round(((target_2 - entry_price) / entry_price) * 100, 2)
        
        # 9. Risk-Reward ratios
        rr_1 = round(abs(target_1 - entry_price) / stop_distance, 2)
        rr_2 = round(abs(target_2 - entry_price) / stop_distance, 2)
        
        # 10. Check exposure limits
        new_exposure = self.current_exposure + investment
        exposure_pct = (new_exposure / self.capital) * 100
        
        if exposure_pct > MAX_TOTAL_EXPOSURE:
            return self._invalid_trade(
                f"Would exceed max exposure "
                f"({exposure_pct:.1f}% > {MAX_TOTAL_EXPOSURE}%)"
            )
        
        # 11. Time-based exit
        exit_time = self._calculate_exit_time(mode)
        
        # 12. Build result
        return {
            "valid":            True,
            "symbol":           symbol,
            "signal":           signal,
            "direction":        "LONG" if is_long else "SHORT",
            "mode":             mode,
            "sector":           sector,
            
            # Confidence
            "confidence_pct":   confidence_pct,
            "confidence_level": confidence_level,
            
            # Prices
            "entry_price":      entry_price,
            "stop_loss":        stop_loss,
            "target_1":         target_1,
            "target_2":         target_2,
            
            # Percentages
            "sl_pct":           abs(sl_pct),
            "target_1_pct":     abs(target1_pct),
            "target_2_pct":     abs(target2_pct),
            
            # Position
            "shares":           shares,
            "investment":       investment,
            
            # Risk metrics
            "risk_amount":      actual_risk,
            "risk_pct":         round((actual_risk / self.capital) * 100, 2),
            "potential_profit_1": potential_profit_1,
            "potential_profit_2": potential_profit_2,
            
            # Ratios
            "risk_reward_1":    rr_1,
            "risk_reward_2":    rr_2,
            "avg_rr":           round((rr_1 + rr_2) / 2, 2),
            
            # ATR info
            "atr":              atr,
            "atr_pct":          round((atr / entry_price) * 100, 2),
            "sl_multiplier":    multipliers["sl"],
            "sector_multiplier": sector_mult,
            
            # Exit strategy
            "exit_time":        exit_time,
            "book_at_target_1": 50,   # Book 50% at T1
            "book_at_target_2": 50,   # Book remaining 50% at T2
            
            # Portfolio impact
            "new_exposure":     new_exposure,
            "new_exposure_pct": round(exposure_pct, 2),
            
            # Trailing stop plan
            "trailing_stop":    self._build_trailing_plan(
                entry_price, target_1, target_2, is_long
            ),
            
            # Metadata
            "calculated_at":    datetime.now().isoformat(),
        }
    
    def _get_confidence_level(self, confidence_pct: float) -> str:
        """Classify confidence percentage into levels."""
        if confidence_pct >= 78:
            return "VERY_HIGH"
        elif confidence_pct >= 68:
            return "HIGH"
        elif confidence_pct >= 60:
            return "MEDIUM"
        else:
            return "LOW"
    
    def _calculate_risk_amount(self, confidence_level: str) -> float:
        """Calculate risk amount based on confidence."""
        base_risk_pct = RISK_PER_TRADE_PCT
        scale         = CONFIDENCE_RISK_SCALE.get(confidence_level, 1.0)
        adjusted_pct  = base_risk_pct * scale
        return self.capital * (adjusted_pct / 100)
    
    def _calculate_exit_time(self, mode: str) -> str:
        """When to force close the trade."""
        if mode == "intraday":
            # 3:15 PM force close
            today = datetime.now().replace(
                hour=15, minute=15, second=0, microsecond=0
            )
            return today.strftime("%Y-%m-%d %H:%M")
        else:
            # Swing: hold 5-7 trading days
            from datetime import timedelta
            exit_date = datetime.now()
            days_added = 0
            while days_added < 5:
                exit_date += timedelta(days=1)
                if exit_date.weekday() < 5:  # Mon-Fri
                    days_added += 1
            return exit_date.strftime("%Y-%m-%d 15:15")
    
    def _build_trailing_plan(
        self, entry: float, t1: float, t2: float, is_long: bool
    ) -> Dict:
        """Build trailing stop rules."""
        if is_long:
            breakeven_at = round(entry + (t1 - entry) * 0.5, 2)
            profit_lock  = round(entry + (t1 - entry) * 0.8, 2)
        else:
            breakeven_at = round(entry - (entry - t1) * 0.5, 2)
            profit_lock  = round(entry - (entry - t1) * 0.8, 2)
        
        return {
            "step_1": {
                "trigger_price": breakeven_at,
                "new_sl":        entry,
                "action":        "Move SL to breakeven (entry)",
            },
            "step_2": {
                "trigger_price": t1,
                "new_sl":        profit_lock,
                "action":        f"Book 50% profit + move SL to {profit_lock}",
            },
            "step_3": {
                "trigger_price": t2,
                "new_sl":        "trailing",
                "action":        "Book remaining 50% at T2 or trail with 1x ATR",
            },
        }
    
    def _invalid_trade(self, reason: str) -> Dict:
        """Return invalid trade with reason."""
        return {
            "valid":  False,
            "reason": reason,
        }
    
    def get_risk_summary(self) -> Dict:
        """Get current portfolio risk summary."""
        available = self.capital - self.current_exposure
        exposure_pct = (self.current_exposure / self.capital) * 100 if self.capital else 0
        
        # Determine risk mode
        if exposure_pct >= MAX_TOTAL_EXPOSURE * 0.9:
            risk_mode = "MAXIMUM_EXPOSURE"
        elif exposure_pct >= MAX_TOTAL_EXPOSURE * 0.6:
            risk_mode = "HIGH_EXPOSURE"
        elif exposure_pct >= MAX_TOTAL_EXPOSURE * 0.3:
            risk_mode = "MODERATE_EXPOSURE"
        else:
            risk_mode = "LOW_EXPOSURE"
        
        return {
            "capital":              self.capital,
            "deployed":             self.current_exposure,
            "available":            available,
            "exposure_pct":         round(exposure_pct, 2),
            "max_exposure_pct":     MAX_TOTAL_EXPOSURE,
            "open_positions":       self.open_positions,
            "max_positions":        3,   # From safety_gates
            "risk_mode":            risk_mode,
            "can_take_new_trade":   (
                exposure_pct < MAX_TOTAL_EXPOSURE and
                self.open_positions < 3
            ),
        }


# ═══════════════════════════════════════════════════════════════
#   MAIN ENTRY FUNCTION
# ═══════════════════════════════════════════════════════════════

def calculate_trade_plan(
    symbol: str,
    entry_price: float,
    atr: float,
    signal: str,
    confidence_pct: float,
    mode: str = "intraday",
    sector: str = "UNKNOWN",
    capital: float = STARTING_CAPITAL,
    current_exposure: float = 0.0,
    open_positions: int = 0,
) -> Dict:
    """
    Main entry — calculate complete trade plan.
    """
    manager = RiskManager(
        capital=capital,
        current_exposure=current_exposure,
        open_positions=open_positions,
    )
    return manager.calculate_trade_params(
        symbol=symbol,
        entry_price=entry_price,
        atr=atr,
        signal=signal,
        confidence_pct=confidence_pct,
        mode=mode,
        sector=sector,
    )


# ─── Quick Test ───────────────────────────────────────────────
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    import json
    
    print("\n" + "="*60)
    print("RISK MANAGER TEST")
    print("="*60)
    
    # Test scenario: BUY signal for RELIANCE
    result = calculate_trade_plan(
        symbol="RELIANCE.NS",
        entry_price=1307.80,
        atr=15.50,
        signal="BUY",
        confidence_pct=75.0,
        mode="intraday",
        sector="ENERGY",
        capital=100000,
        current_exposure=25000,
        open_positions=1,
    )
    
    if result["valid"]:
        print(f"\n✅ Trade Plan for {result['symbol']}")
        print(f"   Signal:      {result['signal']} ({result['direction']})")
        print(f"   Confidence:  {result['confidence_level']} ({result['confidence_pct']}%)")
        print(f"\n💰 Position:")
        print(f"   Shares:      {result['shares']}")
        print(f"   Investment:  ₹{result['investment']:,}")
        print(f"\n🎯 Levels:")
        print(f"   Entry:       ₹{result['entry_price']}")
        print(f"   Stop Loss:   ₹{result['stop_loss']} ({result['sl_pct']}%)")
        print(f"   Target 1:    ₹{result['target_1']} (+{result['target_1_pct']}%)")
        print(f"   Target 2:    ₹{result['target_2']} (+{result['target_2_pct']}%)")
        print(f"\n📊 Risk/Reward:")
        print(f"   Risk:        ₹{result['risk_amount']} ({result['risk_pct']}%)")
        print(f"   Max Profit:  ₹{result['potential_profit_2']}")
        print(f"   RR Ratio:    1:{result['risk_reward_1']} (T1) / 1:{result['risk_reward_2']} (T2)")
        print(f"\n📅 Timing:")
        print(f"   Exit by:     {result['exit_time']}")
    else:
        print(f"\n❌ Invalid: {result['reason']}")
    
    print("\n" + "="*60)
    print("Portfolio Risk Summary")
    print("="*60)
    manager = RiskManager(capital=100000, current_exposure=25000, open_positions=1)
    summary = manager.get_risk_summary()
    for k, v in summary.items():
        print(f"   {k:22s}: {v}")
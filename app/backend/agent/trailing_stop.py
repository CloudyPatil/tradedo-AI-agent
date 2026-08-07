# E:\tradedo\app\backend\agent\trailing_stop.py

"""
TRAILING STOP SYSTEM
Automatically adjusts stop losses to lock in profits.

Three-stage strategy:
Stage 1: Breakeven - When 50% to T1, move SL to entry
Stage 2: Profit Lock - When T1 hit, move SL to 80% of T1 gain
Stage 3: ATR Trail - When new high, trail SL by 1x ATR
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import logging
from typing import Dict, Optional, List
from datetime import datetime

from database.db import get_trade_by_id, update_trade

logger = logging.getLogger("tradedo.trailing")


# ═══════════════════════════════════════════════════════════════
#   CONFIG
# ═══════════════════════════════════════════════════════════════

# Trailing stop triggers
BREAKEVEN_TRIGGER_PCT = 0.5    # Move to breakeven at 50% of T1 distance
PROFIT_LOCK_PCT       = 0.8    # Lock 80% of T1 profit after T1 hit
ATR_TRAIL_MULT        = 1.0    # Trail by 1x ATR after new high


# ═══════════════════════════════════════════════════════════════
#   TRAILING STOP MANAGER
# ═══════════════════════════════════════════════════════════════

class TrailingStopManager:
    """Manages trailing stop logic for all open trades."""
    
    def __init__(self):
        self.stats = {
            "trades_evaluated":   0,
            "sl_updates":         0,
            "moved_to_breakeven": 0,
            "moved_to_lock":      0,
            "atr_trails":         0,
        }
    
    def update_all_trailing_stops(self, open_trades: List[Dict], 
                                    current_prices: Dict[str, float]) -> List[Dict]:
        """
        Check and update trailing stops for all open trades.
        Called from live_monitor after price update.
        
        Returns list of SL updates made.
        """
        updates = []
        
        for trade in open_trades:
            try:
                symbol = trade["symbol"]
                if symbol not in current_prices:
                    continue
                
                current_price = current_prices[symbol]
                update = self.evaluate_trailing_stop(trade, current_price)
                
                if update:
                    updates.append(update)
                
                self.stats["trades_evaluated"] += 1
            
            except Exception as e:
                logger.error(f"Trailing stop error for trade {trade.get('id')}: {e}")
        
        return updates
    
    def evaluate_trailing_stop(self, trade: Dict, current_price: float) -> Optional[Dict]:
        """
        Evaluate if this trade's SL should be trailed.
        Returns update dict if SL was moved, None otherwise.
        """
        trade_id      = trade["id"]
        is_long       = trade["direction"] == "LONG"
        entry_price   = trade["entry_price"]
        current_sl    = trade.get("trailing_sl") or trade["stop_loss"]
        target_1      = trade["target_1"]
        target_2      = trade["target_2"]
        atr           = trade.get("atr") or 0
        already_partial = bool(trade.get("partial_exit"))
        highest       = trade.get("highest_price") or entry_price
        lowest        = trade.get("lowest_price") or entry_price
        
        # ── Determine which stage we're in ──────────────────
        
        new_sl = None
        reason = None
        
        # ═══════════════════════════════════════════════════════
        # STAGE 3: ATR Trail (after partial exit at T1)
        # ═══════════════════════════════════════════════════════
        if already_partial and atr > 0:
            new_sl_stage3, reason_stage3 = self._calc_atr_trail(
                is_long, current_price, current_sl, atr, highest, lowest
            )
            if new_sl_stage3:
                new_sl = new_sl_stage3
                reason = reason_stage3
        
        # ═══════════════════════════════════════════════════════
        # STAGE 2: Profit Lock (T1 hit, before ATR trail kicks in)
        # ═══════════════════════════════════════════════════════
        elif already_partial:
            new_sl_stage2, reason_stage2 = self._calc_profit_lock(
                is_long, entry_price, target_1, current_sl
            )
            if new_sl_stage2:
                new_sl = new_sl_stage2
                reason = reason_stage2
        
        # ═══════════════════════════════════════════════════════
        # STAGE 1: Breakeven (50% to T1)
        # ═══════════════════════════════════════════════════════
        else:
            new_sl_stage1, reason_stage1 = self._calc_breakeven(
                is_long, entry_price, target_1, current_price, current_sl
            )
            if new_sl_stage1:
                new_sl = new_sl_stage1
                reason = reason_stage1
        
        # ── Apply update if SL moved favorably ──────────────
        if new_sl and self._is_better_sl(new_sl, current_sl, is_long):
            update_trade(trade_id, trailing_sl=new_sl)
            self.stats["sl_updates"] += 1
            
            logger.info(
                f"📊 Trailing SL updated: Trade {trade_id} | "
                f"{trade['symbol']} | ₹{current_sl:.2f} → ₹{new_sl:.2f} | "
                f"Reason: {reason}"
            )
            
            return {
                "trade_id":    trade_id,
                "symbol":      trade["symbol"],
                "old_sl":      current_sl,
                "new_sl":      new_sl,
                "current_price": current_price,
                "reason":      reason,
            }
        
        return None
    
    # ═══════════════════════════════════════════════════════════
    #   STAGE 1: BREAKEVEN LOGIC
    # ═══════════════════════════════════════════════════════════
    
    def _calc_breakeven(
        self, is_long: bool, entry: float, t1: float,
        current: float, current_sl: float
    ) -> tuple:
        """
        Stage 1: Move SL to breakeven when price moves 50% toward T1.
        
        For LONG:  If price >= entry + 50% * (t1 - entry) → SL = entry
        For SHORT: If price <= entry - 50% * (entry - t1) → SL = entry
        """
        if is_long:
            trigger_price = entry + (t1 - entry) * BREAKEVEN_TRIGGER_PCT
            
            if current >= trigger_price:
                # Only move if new SL is better than current
                if entry > current_sl:
                    self.stats["moved_to_breakeven"] += 1
                    return entry, f"Breakeven trigger (50% to T1)"
        
        else:  # SHORT
            trigger_price = entry - (entry - t1) * BREAKEVEN_TRIGGER_PCT
            
            if current <= trigger_price:
                if entry < current_sl:
                    self.stats["moved_to_breakeven"] += 1
                    return entry, f"Breakeven trigger (50% to T1)"
        
        return None, None
    
    # ═══════════════════════════════════════════════════════════
    #   STAGE 2: PROFIT LOCK LOGIC
    # ═══════════════════════════════════════════════════════════
    
    def _calc_profit_lock(
        self, is_long: bool, entry: float, t1: float, current_sl: float
    ) -> tuple:
        """
        Stage 2: After T1 hit (partial exit), lock 80% of T1 profit.
        
        For LONG:  SL = entry + 80% * (t1 - entry)
        For SHORT: SL = entry - 80% * (entry - t1)
        """
        if is_long:
            profit_lock_price = entry + (t1 - entry) * PROFIT_LOCK_PCT
            
            if profit_lock_price > current_sl:
                self.stats["moved_to_lock"] += 1
                return profit_lock_price, f"T1 hit - Locking 80% profit"
        
        else:  # SHORT
            profit_lock_price = entry - (entry - t1) * PROFIT_LOCK_PCT
            
            if profit_lock_price < current_sl:
                self.stats["moved_to_lock"] += 1
                return profit_lock_price, f"T1 hit - Locking 80% profit"
        
        return None, None
    
    # ═══════════════════════════════════════════════════════════
    #   STAGE 3: ATR TRAILING LOGIC
    # ═══════════════════════════════════════════════════════════
    
    def _calc_atr_trail(
        self, is_long: bool, current: float, current_sl: float,
        atr: float, highest: float, lowest: float
    ) -> tuple:
        """
        Stage 3: Trail SL by ATR based on new highs/lows.
        
        For LONG:  If current > highest → new_sl = current - 1*ATR
        For SHORT: If current < lowest → new_sl = current + 1*ATR
        """
        trail_distance = atr * ATR_TRAIL_MULT
        
        if is_long:
            # Trail based on current price (most recent high)
            new_sl = current - trail_distance
            
            if new_sl > current_sl:
                self.stats["atr_trails"] += 1
                return new_sl, f"ATR trail (1x ATR below current)"
        
        else:  # SHORT
            new_sl = current + trail_distance
            
            if new_sl < current_sl:
                self.stats["atr_trails"] += 1
                return new_sl, f"ATR trail (1x ATR above current)"
        
        return None, None
    
    # ═══════════════════════════════════════════════════════════
    #   HELPERS
    # ═══════════════════════════════════════════════════════════
    
    def _is_better_sl(self, new_sl: float, current_sl: float, is_long: bool) -> bool:
        """Check if new SL is better (higher for long, lower for short)."""
        if is_long:
            return new_sl > current_sl
        else:
            return new_sl < current_sl


# ═══════════════════════════════════════════════════════════════
#   GLOBAL SINGLETON
# ═══════════════════════════════════════════════════════════════

_trailing_manager: Optional[TrailingStopManager] = None

def get_trailing_manager() -> TrailingStopManager:
    global _trailing_manager
    if _trailing_manager is None:
        _trailing_manager = TrailingStopManager()
    return _trailing_manager


# ═══════════════════════════════════════════════════════════════
#   Convenience Function
# ═══════════════════════════════════════════════════════════════

def check_trailing_stops(
    open_trades: List[Dict], current_prices: Dict[str, float]
) -> List[Dict]:
    """Check trailing stops for all open trades."""
    manager = get_trailing_manager()
    return manager.update_all_trailing_stops(open_trades, current_prices)


# ═══════════════════════════════════════════════════════════════
#   Quick Test
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("\n" + "="*60)
    print("TRAILING STOP MANAGER TEST")
    print("="*60)
    
    manager = get_trailing_manager()
    
    # Test scenario 1: Long trade, price up 50% to T1 (breakeven trigger)
    test_trade_1 = {
        "id":              999,
        "symbol":          "TEST.NS",
        "direction":       "LONG",
        "entry_price":     1000,
        "stop_loss":       980,
        "trailing_sl":     None,
        "target_1":        1050,
        "target_2":        1100,
        "atr":             10,
        "partial_exit":    0,
        "highest_price":   1025,
    }
    
    print("\n📊 Test 1: LONG trade at 50% to T1")
    print(f"   Entry: ₹1000, Current SL: ₹980, T1: ₹1050")
    print(f"   Price now: ₹1025 (50% to T1)")
    result = manager.evaluate_trailing_stop(test_trade_1, 1025)
    if result:
        print(f"   ✅ SL moved: ₹{result['old_sl']} → ₹{result['new_sl']}")
        print(f"   Reason: {result['reason']}")
    else:
        print(f"   ⏸️  No SL change")
    
    # Test scenario 2: Long trade, T1 hit (partial done, profit lock)
    test_trade_2 = {
        "id":              998,
        "symbol":          "TEST2.NS",
        "direction":       "LONG",
        "entry_price":     1000,
        "stop_loss":       1000,  # Already at breakeven from stage 1
        "trailing_sl":     1000,
        "target_1":        1050,
        "target_2":        1100,
        "atr":             10,
        "partial_exit":    1,     # T1 was hit
        "highest_price":   1055,
    }
    
    print("\n📊 Test 2: LONG trade after T1 hit (profit lock)")
    print(f"   Entry: ₹1000, Current SL: ₹1000 (breakeven)")
    print(f"   T1 hit at ₹1050, price now ₹1055")
    result = manager.evaluate_trailing_stop(test_trade_2, 1055)
    if result:
        print(f"   ✅ SL moved: ₹{result['old_sl']} → ₹{result['new_sl']}")
        print(f"   Reason: {result['reason']}")
    else:
        print(f"   ⏸️  No SL change")
    
    # Test scenario 3: Long trade, new high (ATR trail)
    test_trade_3 = {
        "id":              997,
        "symbol":          "TEST3.NS",
        "direction":       "LONG",
        "entry_price":     1000,
        "stop_loss":       1040,  # Already at profit lock
        "trailing_sl":     1040,
        "target_1":        1050,
        "target_2":        1100,
        "atr":             10,
        "partial_exit":    1,
        "highest_price":   1080,   # New high
    }
    
    print("\n📊 Test 3: LONG trade with new high (ATR trail)")
    print(f"   Entry: ₹1000, Current SL: ₹1040")
    print(f"   New high: ₹1080, ATR: ₹10")
    result = manager.evaluate_trailing_stop(test_trade_3, 1080)
    if result:
        print(f"   ✅ SL moved: ₹{result['old_sl']} → ₹{result['new_sl']}")
        print(f"   Reason: {result['reason']}")
    else:
        print(f"   ⏸️  No SL change")
    
    # Final stats
    print(f"\n📊 Manager Stats:")
    for k, v in manager.stats.items():
        print(f"   {k}: {v}")
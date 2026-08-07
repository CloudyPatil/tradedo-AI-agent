# E:\tradedo\app\backend\agent\live_monitor.py

"""
LIVE PRICE MONITOR
Watches all open paper trades in real-time.
Auto-triggers exits on SL/target/EOD.

Runs every 1 minute during market hours (9:15 AM - 3:30 PM IST).
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import logging
from typing import Dict, List, Optional
from datetime import datetime, time as dt_time
from concurrent.futures import ThreadPoolExecutor

from database.db import (
    get_open_trades, update_trade, get_agent_state,
    update_agent_state, get_trade_by_id
)
from data_pipeline.price_provider import get_price_provider

logger = logging.getLogger("tradedo.monitor")


# ═══════════════════════════════════════════════════════════════
#   CONFIG
# ═══════════════════════════════════════════════════════════════

MARKET_OPEN    = dt_time(9, 15)
MARKET_CLOSE   = dt_time(15, 30)
EOD_FORCE_TIME = dt_time(15, 15)   # Force close 15 mins before market close


# ═══════════════════════════════════════════════════════════════
#   MONITOR CLASS
# ═══════════════════════════════════════════════════════════════

class LiveMonitor:
    """Real-time trade monitor."""
    
    def __init__(self):
        self.provider = get_price_provider()
        self.stats = {
            "checks_run":      0,
            "trades_updated":  0,
            "sl_hits":         0,
            "target_hits":     0,
            "eod_closes":      0,
            "errors":          0,
        }
    
    # ═══════════════════════════════════════════════════════════
    #   MAIN MONITORING LOOP
    # ═══════════════════════════════════════════════════════════
    
    def check_all_trades(self) -> Dict:
        """
        Main monitoring function.
        Called by scheduler every 1 minute.
        """
        # Check if market is open
        if not self._is_market_open():
            return {
                "status":  "MARKET_CLOSED",
                "message": "Market not open, skipping monitor",
            }
        
        # Get all open trades
        open_trades = get_open_trades()
        
        if not open_trades:
            return {
                "status":  "NO_TRADES",
                "message": "No open trades to monitor",
            }
        
        logger.info(f"🔍 Monitoring {len(open_trades)} open trades...")
        
        # Get unique symbols
        symbols = list(set(t["symbol"] for t in open_trades))
        
        # Fetch all prices in parallel
        prices = self._fetch_prices(symbols)
        
        if not prices:
            logger.warning("No prices fetched, skipping check")
            return {"status": "NO_PRICES"}
        
        # Check each trade
        actions_taken = []
        
        for trade in open_trades:
            try:
                symbol = trade["symbol"]
                if symbol not in prices:
                    logger.debug(f"No price for {symbol}, skipping")
                    continue
                
                current_price = prices[symbol]
                action = self._check_single_trade(trade, current_price)
                
                if action:
                    actions_taken.append(action)
                
                self.stats["checks_run"] += 1
            
            except Exception as e:
                logger.error(f"Error checking trade {trade.get('id')}: {e}")
                self.stats["errors"] += 1
        
        # Check for EOD force close
        eod_closes = self._check_eod_close()
        actions_taken.extend(eod_closes)
        
        return {
            "status":         "OK",
            "trades_checked": len(open_trades),
            "actions_taken":  len(actions_taken),
            "actions":        actions_taken,
            "stats":          self.stats,
        }
    
    # ═══════════════════════════════════════════════════════════
    #   PRICE FETCHING
    # ═══════════════════════════════════════════════════════════
    
    def _fetch_prices(self, symbols: List[str]) -> Dict[str, float]:
        """Fetch current prices for all symbols."""
        # Try batch fetch first
        prices = {}
        
        try:
            batch_results = self.provider.get_multiple_ltp(symbols)
            for sym, data in batch_results.items():
                prices[sym] = data["last_price"]
        except Exception as e:
            logger.warning(f"Batch fetch failed: {e}")
        
        # For any missing, try individual fetch
        missing = [s for s in symbols if s not in prices]
        if missing:
            for sym in missing:
                result = self.provider.get_ltp(sym)
                if result:
                    prices[sym] = result["last_price"]
        
        logger.info(f"📊 Fetched {len(prices)}/{len(symbols)} prices")
        return prices
    
    # ═══════════════════════════════════════════════════════════
    #   SINGLE TRADE CHECK
    # ═══════════════════════════════════════════════════════════
    
    def _check_single_trade(
        self, trade: Dict, current_price: float
    ) -> Optional[Dict]:
        """
        Check one trade for exit conditions.
        Returns action taken (or None if no action).
        """
        trade_id = trade["id"]
        symbol   = trade["symbol"]
        is_long  = trade["direction"] == "LONG"
        
        entry    = trade["entry_price"]
        sl       = trade["stop_loss"]
        target_1 = trade["target_1"]
        target_2 = trade["target_2"]
        
        # Get trailing SL if set (from partial exit)
        trailing_sl = trade.get("trailing_sl") or sl
        active_sl = trailing_sl
        
        # Update current price + running P&L
        self._update_current_price(trade, current_price)
        
        # Check for partial exit (T1 hit)
        already_partial = bool(trade.get("partial_exit"))
        
        # ── LONG POSITION LOGIC ──────────────────────────────
        if is_long:
            # SL hit?
            if current_price <= active_sl:
                return self._close_trade(
                    trade_id, current_price, 
                    "STOP_LOSS" if not already_partial else "TRAILING_SL_HIT"
                )
            
            # Target 2 hit?
            if current_price >= target_2:
                return self._close_trade(trade_id, current_price, "TARGET_2_HIT")
            
            # Target 1 hit (partial exit)?
            if not already_partial and current_price >= target_1:
                return self._partial_close(trade_id, current_price)
        
        # ── SHORT POSITION LOGIC ─────────────────────────────
        else:
            # SL hit?
            if current_price >= active_sl:
                return self._close_trade(
                    trade_id, current_price,
                    "STOP_LOSS" if not already_partial else "TRAILING_SL_HIT"
                )
            
            # Target 2 hit?
            if current_price <= target_2:
                return self._close_trade(trade_id, current_price, "TARGET_2_HIT")
            
            # Target 1 hit (partial exit)?
            if not already_partial and current_price <= target_1:
                return self._partial_close(trade_id, current_price)
        
        return None
    
    # ═══════════════════════════════════════════════════════════
    #   UPDATE CURRENT PRICE + P&L
    # ═══════════════════════════════════════════════════════════
    
    def _update_current_price(self, trade: Dict, current_price: float):
        """Update trade with current price and running P&L."""
        entry = trade["entry_price"]
        qty   = trade["quantity"]
        is_long = trade["direction"] == "LONG"
        
        # Running P&L
        if is_long:
            running_pnl = round((current_price - entry) * qty, 2)
        else:
            running_pnl = round((entry - current_price) * qty, 2)
        
        # Update highest/lowest for trailing stop tracking
        highest = trade.get("highest_price") or entry
        lowest  = trade.get("lowest_price") or entry
        
        updates = {
            "current_price": current_price,
            "pnl":           running_pnl,
        }
        
        if current_price > highest:
            updates["highest_price"] = current_price
        if current_price < lowest:
            updates["lowest_price"] = current_price
        
        update_trade(trade["id"], **updates)
        self.stats["trades_updated"] += 1
    
    # ═══════════════════════════════════════════════════════════
    #   PARTIAL CLOSE (Book 50% at T1)
    # ═══════════════════════════════════════════════════════════
    
    def _partial_close(self, trade_id: int, current_price: float) -> Dict:
        """Book 50% at target 1."""
        from database.db import close_trade
        
        trade = get_trade_by_id(trade_id)
        if not trade:
            return {}
        
        # Book half quantity
        original_qty = trade["quantity"]
        partial_qty  = original_qty // 2
        
        if partial_qty < 1:
            partial_qty = 1
        
        # Close partial in DB
        close_trade(
            trade_id=trade_id,
            exit_price=current_price,
            exit_reason="TARGET_1_HIT",
            is_partial=True,
            partial_qty=partial_qty,
        )
        
        self.stats["target_hits"] += 1
        
        logger.info(
            f"🎯 PARTIAL EXIT: Trade {trade_id} | "
            f"{partial_qty}/{original_qty} @ ₹{current_price} (T1 HIT)"
        )
        
        # Send Telegram alert
        self._send_partial_alert(trade, current_price, partial_qty)
        
        return {
            "action":   "PARTIAL_CLOSE",
            "trade_id": trade_id,
            "symbol":   trade["symbol"],
            "price":    current_price,
            "qty":      partial_qty,
        }
    
    # ═══════════════════════════════════════════════════════════
    #   FULL CLOSE
    # ═══════════════════════════════════════════════════════════
    
    def _close_trade(
        self, trade_id: int, current_price: float, reason: str
    ) -> Dict:
        """Fully close a trade."""
        from database.db import close_trade
        from agent.paper_executor import PaperExecutor
        
        trade = get_trade_by_id(trade_id)
        if not trade:
            return {}
        
        # Close in DB
        close_trade(trade_id, current_price, reason)
        
        # Update stats
        if "STOP" in reason or "SL" in reason:
            self.stats["sl_hits"] += 1
        elif "TARGET" in reason:
            self.stats["target_hits"] += 1
        elif reason == "EOD":
            self.stats["eod_closes"] += 1
        
        # Release capital via executor
        executor = PaperExecutor()
        executor._release_capital(trade["investment"])
        
        # Update daily stats
        updated_trade = get_trade_by_id(trade_id)
        pnl = updated_trade.get("pnl", 0)
        
        state = get_agent_state()
        update_agent_state(
            pnl_today    = state["pnl_today"] + pnl,
            wins_today   = state["wins_today"] + (1 if pnl > 0 else 0),
            losses_today = state["losses_today"] + (1 if pnl < 0 else 0),
            capital      = state["capital"] + pnl,
        )
        
        # Telegram alert
        executor._send_exit_alert(updated_trade, reason)
        
        logger.info(
            f"{'✅' if pnl > 0 else '❌'} CLOSED: Trade {trade_id} | "
            f"{trade['symbol']} @ ₹{current_price} | "
            f"P&L: ₹{pnl} | Reason: {reason}"
        )
        
        return {
            "action":   "CLOSE",
            "trade_id": trade_id,
            "symbol":   trade["symbol"],
            "price":    current_price,
            "pnl":      pnl,
            "reason":   reason,
        }
    
    # ═══════════════════════════════════════════════════════════
    #   EOD FORCE CLOSE
    # ═══════════════════════════════════════════════════════════
    
    def _check_eod_close(self) -> List[Dict]:
        """Force close all intraday trades at EOD."""
        now = datetime.now().time()
        
        if now < EOD_FORCE_TIME:
            return []
        
        # Get all open intraday trades
        open_trades = get_open_trades()
        intraday_trades = [t for t in open_trades if t.get("mode") == "intraday"]
        
        if not intraday_trades:
            return []
        
        logger.info(f"⏰ EOD: Force closing {len(intraday_trades)} intraday trades")
        
        actions = []
        for trade in intraday_trades:
            # Get last known price (could use last update)
            current_price = trade.get("current_price") or trade["entry_price"]
            
            action = self._close_trade(trade["id"], current_price, "EOD")
            if action:
                actions.append(action)
        
        return actions
    
    # ═══════════════════════════════════════════════════════════
    #   HELPERS
    # ═══════════════════════════════════════════════════════════
    
    def _is_market_open(self) -> bool:
        """Check if NSE is open."""
        now = datetime.now()
        
        # Check weekday (Mon=0, Sun=6)
        if now.weekday() >= 5:
            return False
        
        # Check time
        current_time = now.time()
        return MARKET_OPEN <= current_time <= MARKET_CLOSE
    
    def _send_partial_alert(self, trade: Dict, price: float, qty: int):
        """Send Telegram alert for partial exit."""
        try:
            import asyncio
            from utils.telegram_bot import send_message
            
            symbol = trade["symbol"].replace(".NS", "")
            entry  = trade["entry_price"]
            
            if trade["direction"] == "LONG":
                pnl_partial = round((price - entry) * qty, 2)
            else:
                pnl_partial = round((entry - price) * qty, 2)
            
            pnl_pct = round(((price - entry) / entry) * 100, 2)
            
            msg = f"🎯 <b>TARGET 1 HIT #{trade['id']}</b>\n\n"
            msg += f"📌 <b>{symbol}</b>\n"
            msg += f"💰 Booked: {qty} shares @ ₹{price:,.2f}\n"
            msg += f"📈 Partial P&L: ₹{pnl_partial:,.2f} ({pnl_pct:+.2f}%)\n\n"
            msg += f"🔄 Remaining {trade['quantity'] - qty} shares held\n"
            msg += f"🛡️ SL moved to breakeven (₹{entry})\n"
            msg += f"🎯 Targeting T2 for remaining position"
            
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.create_task(send_message(msg))
                else:
                    loop.run_until_complete(send_message(msg))
            except RuntimeError:
                asyncio.run(send_message(msg))
        
        except Exception as e:
            logger.warning(f"Partial alert failed: {e}")


# ═══════════════════════════════════════════════════════════════
#   MAIN ENTRY FUNCTION (Called by Scheduler)
# ═══════════════════════════════════════════════════════════════

_monitor: Optional[LiveMonitor] = None

def get_monitor() -> LiveMonitor:
    """Get global monitor instance."""
    global _monitor
    if _monitor is None:
        _monitor = LiveMonitor()
    return _monitor


async def monitor_open_trades():
    """Async wrapper for scheduler."""
    monitor = get_monitor()
    result = monitor.check_all_trades()
    
    if result.get("actions_taken", 0) > 0:
        logger.info(f"⚡ Monitor took {result['actions_taken']} actions")
    
    return result


def run_monitor_now() -> Dict:
    """Manual trigger for monitoring (for testing/API)."""
    monitor = get_monitor()
    return monitor.check_all_trades()


# ═══════════════════════════════════════════════════════════════
#   Quick Test
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("\n" + "="*60)
    print("LIVE MONITOR TEST")
    print("="*60)
    
    result = run_monitor_now()
    
    print(f"\nStatus: {result.get('status')}")
    print(f"Message: {result.get('message', 'N/A')}")
    
    if result.get("status") == "OK":
        print(f"Trades checked: {result.get('trades_checked')}")
        print(f"Actions taken:  {result.get('actions_taken')}")
        
        if result.get("actions"):
            print("\n🎬 Actions:")
            for action in result["actions"]:
                print(f"   {action}")
        
        stats = result.get("stats", {})
        print(f"\n📊 Session Stats:")
        for k, v in stats.items():
            print(f"   {k}: {v}")
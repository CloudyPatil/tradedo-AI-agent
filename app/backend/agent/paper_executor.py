# E:\tradedo\app\backend\agent\paper_executor.py

"""
PAPER TRADE EXECUTOR
The core execution engine.
Takes trade opportunities → validates → executes → tracks.
"""

# ─── Path Setup (MUST be first) ──────────────────────────────
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import json
import logging
from typing import Dict, Optional, List
from datetime import datetime

from database.db import (
    create_paper_trade, get_agent_state, update_agent_state,
    get_open_trades, get_todays_trades, close_trade,
    update_trade_current_price
)
from agent.risk_manager import calculate_trade_plan, RiskManager
from agent.safety_gates import check_all_gates
from agent.sectors import get_sector
from agent.trade_journal import TradeJournal

logger = logging.getLogger("tradedo.executor")


# ═══════════════════════════════════════════════════════════════
#   PAPER EXECUTOR CLASS
# ═══════════════════════════════════════════════════════════════

class PaperExecutor:
    """
    Executes paper trades based on agent decisions.
    Handles: entry, monitoring, exits, P&L tracking.
    """
    
    def __init__(self, mode: str = "intraday"):
        self.mode = mode
    
    # ═══════════════════════════════════════════════════════════
    #   TRADE ENTRY
    # ═══════════════════════════════════════════════════════════
    
    def execute_trade(
        self,
        symbol: str,
        signal: str,
        current_price: float,
        atr: float,
        confidence_pct: float,
        composite_score: float,
        ai_reasoning: str = "",
        master_result: Dict = None,
    ) -> Dict:
        """
        Main entry point — execute a paper trade.
        
        Full pipeline:
        1. Get agent state
        2. Check safety gates
        3. Calculate risk parameters
        4. Create trade in database
        5. Update agent state
        6. Send notification
        
        Returns dict with execution result.
        """
        logger.info(f"🎯 EXECUTING TRADE: {symbol} {signal}")
        
        # 1. Get current agent state
        agent_state = get_agent_state()
        if not agent_state:
            return self._failed("Agent state not initialized")
        
        # 2. Check if agent is active
        if not agent_state.get("is_active"):
            return self._failed("Agent is not active. Enable via /agent/start")
        
        # 3. Get open positions
        open_trades = get_open_trades()
        recent_trades = get_todays_trades()
        
        # 4. Get sector
        sector = get_sector(symbol)
        
        # 5. Run safety gates
        gate_result = check_all_gates(
            symbol=symbol,
            mode=self.mode,
            open_positions=open_trades,
            recent_trades=recent_trades,
            current_capital=agent_state["capital"],
            starting_capital=agent_state["starting_capital"],
            master_result=master_result or {},
        )
        
        if not gate_result["safe_to_trade"]:
            return self._failed(
                f"Safety gates failed: {gate_result['failed_gates']}",
                gate_result=gate_result
            )
        
        # 6. Calculate risk parameters
        trade_plan = calculate_trade_plan(
            symbol=symbol,
            entry_price=current_price,
            atr=atr,
            signal=signal,
            confidence_pct=confidence_pct,
            mode=self.mode,
            sector=sector,
            capital=agent_state["capital"],
            current_exposure=agent_state["current_exposure"],
            open_positions=agent_state["open_positions"],
        )
        
        if not trade_plan.get("valid"):
            return self._failed(f"Risk manager rejected: {trade_plan.get('reason')}")
        
        # 7. Prepare trade data
        trade_data = {
            "symbol":          symbol,
            "direction":       trade_plan["direction"],
            "signal":          signal,
            "mode":            self.mode,
            "sector":          sector,
            "entry_price":     trade_plan["entry_price"],
            "stop_loss":       trade_plan["stop_loss"],
            "target_1":        trade_plan["target_1"],
            "target_2":        trade_plan["target_2"],
            "quantity":        trade_plan["shares"],
            "investment":      trade_plan["investment"],
            "risk_amount":     trade_plan["risk_amount"],
            "risk_pct":        trade_plan["risk_pct"],
            "atr":             atr,
            "ml_confidence":   confidence_pct,
            "composite_score": composite_score,
            "time_exit_by":    trade_plan["exit_time"],
            "ai_reasoning":    ai_reasoning,
            "metadata":        json.dumps({
                "trailing_stop":     trade_plan.get("trailing_stop"),
                "sector_multiplier": trade_plan.get("sector_multiplier"),
                "confidence_level":  trade_plan.get("confidence_level"),
                "master_result":     self._compact_master(master_result),
            }),
        }
        
        # 8. Create trade in database
        trade_id = create_paper_trade(trade_data)

        # 8.5 ── SAVE JOURNAL SNAPSHOT (NEW!) ────────────────────
        snapshot = TradeJournal.build_entry_snapshot(
            symbol=symbol,
            signal=signal,
            current_price=current_price,
            confidence_pct=confidence_pct,
            composite_score=composite_score,
            master_result=master_result,
            trade_plan=trade_plan,
        )
        TradeJournal.save_full_snapshot(trade_id, snapshot)
        # ── End journal snapshot ─────────────────────────────────
        
        # 9. Update agent state
        update_agent_state(
            current_exposure = agent_state["current_exposure"] + trade_plan["investment"],
            open_positions   = agent_state["open_positions"] + 1,
            trades_today     = agent_state["trades_today"] + 1,
        )

        try:
            from agent.websocket_stream import get_streamer
            streamer = get_streamer()
            if streamer.is_running:
                streamer.subscribe_symbols([symbol])
        except Exception as e:
            logger.debug(f"WebSocket subscribe failed (non-critical): {e}")
        
        # 10. Send Telegram alert
        self._send_entry_alert(trade_id, trade_data, trade_plan)
        
        logger.info(
            f"✅ TRADE EXECUTED: ID {trade_id} | {symbol} {signal} | "
            f"{trade_plan['shares']} shares @ ₹{trade_plan['entry_price']} | "
            f"SL: ₹{trade_plan['stop_loss']} | T2: ₹{trade_plan['target_2']}"
        )
        
        return {
            "success":     True,
            "trade_id":    trade_id,
            "symbol":      symbol,
            "trade_plan":  trade_plan,
            "gate_result": gate_result,
        }
    
    # ═══════════════════════════════════════════════════════════
    #   TRADE EXIT (Manual)
    # ═══════════════════════════════════════════════════════════
    
    def close_trade_manually(
        self,
        trade_id: int,
        current_price: float,
        reason: str = "MANUAL"
    ) -> Dict:
        """Manually close a trade."""
        from database.db import get_trade_by_id
        
        trade = get_trade_by_id(trade_id)
        if not trade:
            return {"success": False, "error": "Trade not found"}
        
        if trade["status"] != "OPEN":
            return {"success": False, "error": f"Trade already {trade['status']}"}
        
        # Close in DB
        close_trade(trade_id, current_price, reason)
        
        # Update agent state
        self._release_capital(trade["investment"])
        
        # Get updated trade for stats
        updated_trade = get_trade_by_id(trade_id)
        pnl = updated_trade.get("pnl", 0)
        
        # Update daily stats
        agent_state = get_agent_state()
        pnl_today = agent_state["pnl_today"] + pnl
        wins_today = agent_state["wins_today"] + (1 if pnl > 0 else 0)
        losses_today = agent_state["losses_today"] + (1 if pnl < 0 else 0)
        
        update_agent_state(
            pnl_today    = pnl_today,
            wins_today   = wins_today,
            losses_today = losses_today,
            capital      = agent_state["capital"] + pnl,
        )
        
        # Send Telegram alert
        self._send_exit_alert(updated_trade, reason)
        
        return {
            "success":   True,
            "trade_id":  trade_id,
            "pnl":       pnl,
            "reason":    reason,
        }
    
    # ═══════════════════════════════════════════════════════════
    #   HELPERS
    # ═══════════════════════════════════════════════════════════
    
    def _release_capital(self, amount: float):
        """Release capital when trade closes."""
        state = get_agent_state()
        update_agent_state(
            current_exposure = max(0, state["current_exposure"] - amount),
            open_positions   = max(0, state["open_positions"] - 1),
        )
    
    def _failed(self, reason: str, **kwargs) -> Dict:
        """Return failed execution result."""
        logger.info(f"❌ Trade skipped: {reason}")
        return {
            "success": False,
            "error":   reason,
            **kwargs,
        }
    
    def _compact_master(self, master: Optional[Dict]) -> Dict:
        """Compact version of master result for storage."""
        if not master:
            return {}
        return {
            "final_score":  master.get("final_score"),
            "verdict":      master.get("verdict"),
            "sentiment":    master.get("news", {}).get("label"),
            "social":       master.get("social", {}).get("label"),
            "market_regime": master.get("technical", {}).get("market_regime"),
        }
    
    def _send_entry_alert(self, trade_id: int, trade_data: Dict, trade_plan: Dict):
        """Send Telegram alert for new trade."""
        try:
            import asyncio
            from utils.telegram_bot import send_message
            
            symbol = trade_data["symbol"].replace(".NS", "")
            emoji  = "🟢" if trade_data["signal"] == "BUY" else "🔴"
            
            msg = f"{emoji} <b>PAPER TRADE #{trade_id}</b>\n\n"
            msg += f"📌 <b>{symbol}</b> — {trade_data['signal']}\n"
            msg += f"🏢 Sector: {trade_data['sector']}\n"
            msg += f"🎯 Confidence: {trade_data['ml_confidence']:.1f}%\n\n"
            
            msg += f"<b>Entry:</b>  ₹{trade_plan['entry_price']:,.2f}\n"
            msg += f"<b>SL:</b>     ₹{trade_plan['stop_loss']:,.2f} "
            msg += f"({trade_plan['sl_pct']:.1f}%)\n"
            msg += f"<b>T1:</b>     ₹{trade_plan['target_1']:,.2f} "
            msg += f"(+{trade_plan['target_1_pct']:.1f}%)\n"
            msg += f"<b>T2:</b>     ₹{trade_plan['target_2']:,.2f} "
            msg += f"(+{trade_plan['target_2_pct']:.1f}%)\n\n"
            
            msg += f"📊 <b>Position:</b>\n"
            msg += f"Shares: {trade_plan['shares']}\n"
            msg += f"Investment: ₹{trade_plan['investment']:,.2f}\n"
            msg += f"Max Risk: ₹{trade_plan['risk_amount']:,.2f} "
            msg += f"({trade_plan['risk_pct']:.2f}%)\n"
            msg += f"R:R: 1:{trade_plan['risk_reward_1']} → 1:{trade_plan['risk_reward_2']}\n\n"
            
            msg += f"⏰ Exit by: {trade_plan['exit_time']}"
            
            # Run async in sync context
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.create_task(send_message(msg))
                else:
                    loop.run_until_complete(send_message(msg))
            except RuntimeError:
                asyncio.run(send_message(msg))
        
        except Exception as e:
            logger.warning(f"Telegram alert failed: {e}")
    
    def _send_exit_alert(self, trade: Dict, reason: str):
        """Send Telegram alert for trade exit."""
        try:
            import asyncio
            from utils.telegram_bot import send_message
            
            symbol = trade["symbol"].replace(".NS", "")
            pnl = trade.get("pnl", 0)
            pnl_pct = trade.get("pnl_pct", 0)
            
            emoji = "✅" if pnl > 0 else "❌"
            reason_emoji = {
                "TARGET_1_HIT": "🎯",
                "TARGET_2_HIT": "🎯🎯",
                "STOP_LOSS":    "🛑",
                "EOD":          "⏰",
                "MANUAL":       "👋",
            }.get(reason, "📊")
            
            msg = f"{emoji} <b>TRADE CLOSED #{trade['id']}</b>\n\n"
            msg += f"📌 <b>{symbol}</b> — {trade['direction']}\n"
            msg += f"{reason_emoji} Reason: {reason}\n\n"
            
            msg += f"Entry: ₹{trade['entry_price']:,.2f}\n"
            msg += f"Exit:  ₹{trade['exit_price']:,.2f}\n"
            msg += f"Qty:   {trade['quantity']}\n\n"
            
            pnl_emoji = "📈" if pnl > 0 else "📉"
            msg += f"<b>{pnl_emoji} P&L: ₹{pnl:,.2f} ({pnl_pct:+.2f}%)</b>\n"
            
            if trade.get("hold_duration_mins"):
                mins = trade["hold_duration_mins"]
                if mins < 60:
                    dur = f"{mins} min"
                else:
                    dur = f"{mins//60}h {mins%60}m"
                msg += f"⏱️ Held: {dur}"
            
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.create_task(send_message(msg))
                else:
                    loop.run_until_complete(send_message(msg))
            except RuntimeError:
                asyncio.run(send_message(msg))
        
        except Exception as e:
            logger.warning(f"Exit alert failed: {e}")


# ═══════════════════════════════════════════════════════════════
#   AGENT CONTROL FUNCTIONS
# ═══════════════════════════════════════════════════════════════

# In agent/paper_executor.py

def start_agent():
    """Enable the agent to execute trades + start WebSocket."""
    update_agent_state(is_active=1)
    logger.info("🚀 AGENT STARTED")
    
    # ── NEW: Start WebSocket streaming ────────────────────────
    try:
        from agent.websocket_stream import start_streaming
        streaming_status = start_streaming()
        logger.info(f"📡 WebSocket streaming initialized: {streaming_status.get('running')}")
    except Exception as e:
        logger.warning(f"WebSocket start failed (non-critical): {e}")
    
    return {"success": True, "message": "Agent activated + WebSocket started"}


def stop_agent():
    """Disable agent + stop WebSocket."""
    update_agent_state(is_active=0)
    logger.info("🛑 AGENT STOPPED")
    
    # ── NEW: Stop WebSocket ──────────────────────────────────
    try:
        from agent.websocket_stream import stop_streaming
        stop_streaming()
    except Exception as e:
        logger.warning(f"WebSocket stop failed: {e}")
    
    return {"success": True, "message": "Agent deactivated"}


def get_agent_status() -> Dict:
    """Get complete agent status."""
    from database.db import get_todays_performance, get_overall_performance
    
    state = get_agent_state()
    today = get_todays_performance()
    overall = get_overall_performance()
    open_trades = get_open_trades()
    
    # Calculate P&L%
    if state.get("starting_capital"):
        total_pnl_pct = round(
            ((state["capital"] - state["starting_capital"]) / state["starting_capital"]) * 100,
            2
        )
    else:
        total_pnl_pct = 0
    
    return {
        "agent": {
            "is_active":       bool(state.get("is_active")),
            "mode":            "intraday",
            "capital":         state.get("capital", 0),
            "starting_capital": state.get("starting_capital", 0),
            "current_exposure": state.get("current_exposure", 0),
            "available":       state.get("capital", 0) - state.get("current_exposure", 0),
            "exposure_pct":    round(
                (state.get("current_exposure", 0) / state.get("capital", 1)) * 100, 2
            ),
            "total_pnl":       state.get("capital", 0) - state.get("starting_capital", 0),
            "total_pnl_pct":   total_pnl_pct,
        },
        "today": today,
        "overall": overall,
        "open_trades": open_trades,
    }


def reset_agent_capital(new_capital: float = 100000):
    """Reset agent capital (for testing)."""
    update_agent_state(
        capital          = new_capital,
        starting_capital = new_capital,
        current_exposure = 0,
        open_positions   = 0,
        trades_today     = 0,
        wins_today       = 0,
        losses_today     = 0,
        pnl_today        = 0,
    )
    logger.info(f"💰 Agent capital reset to ₹{new_capital:,}")
    return {"success": True, "capital": new_capital}


# ─── Quick Test ───────────────────────────────────────────────
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    from database.db import init_db
    init_db()
    
    print("\n" + "="*60)
    print("PAPER EXECUTOR TEST")
    print("="*60)
    
    # Enable agent
    print("\n1. Starting agent...")
    start_agent()
    
    # Show status
    status = get_agent_status()
    print(f"\n2. Agent Status:")
    print(f"   Active:  {status['agent']['is_active']}")
    print(f"   Capital: ₹{status['agent']['capital']:,}")
    print(f"   Open:    {len(status['open_trades'])} trades")
    
    # Try executing a trade
    print(f"\n3. Attempting trade execution...")
    executor = PaperExecutor(mode="intraday")
    
    result = executor.execute_trade(
        symbol="RELIANCE.NS",
        signal="BUY",
        current_price=1307.80,
        atr=15.50,
        confidence_pct=75.0,
        composite_score=145,
        ai_reasoning="Test trade execution",
    )
    
    if result["success"]:
        print(f"   ✅ Trade executed: ID {result['trade_id']}")
    else:
        print(f"   ❌ Trade rejected: {result['error']}")
    
    # Final status
    status = get_agent_status()
    print(f"\n4. Final Status:")
    print(f"   Capital:  ₹{status['agent']['capital']:,}")
    print(f"   Exposure: ₹{status['agent']['current_exposure']:,}")
    print(f"   Open:     {len(status['open_trades'])} trades")
# E:\tradedo\app\backend\agent\brain.py

"""
AGENT BRAIN — Master Orchestrator
Runs the complete autonomous trading pipeline.

Daily Schedule:
  8:30 AM  — Wake up, prepare (fetch cross-asset data)
  8:45 AM  — Morning market scan
  9:15 AM  — Market open, execute top candidates
  9:15 AM to 3:15 PM — Continuous monitoring
  3:15 PM  — EOD force close all trades
  3:30 PM  — Generate daily report
  Weekend — Rest mode
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import logging
import asyncio
from typing import Dict, List, Optional
from datetime import datetime, time as dt_time
from concurrent.futures import ThreadPoolExecutor

from database.db import (
    get_agent_state, update_agent_state, get_open_trades,
    get_todays_performance, get_overall_performance
)

logger = logging.getLogger("tradedo.brain")


# ═══════════════════════════════════════════════════════════════
#   AGENT BRAIN CONFIG
# ═══════════════════════════════════════════════════════════════

MAX_TRADES_PER_DAY  = 5     # Max new trades per day
MIN_SCORE_THRESHOLD = 140    # Only trade candidates with score >= 140
DAILY_LOSS_LIMIT_PCT = 5.0   # Stop trading if lose 5% in a day

# Time thresholds
PREMARKET_TIME = dt_time(8, 30)
SCAN_TIME      = dt_time(8, 45)
MARKET_OPEN    = dt_time(9, 15)
MARKET_CLOSE   = dt_time(15, 30)
EOD_TIME       = dt_time(15, 15)


# ═══════════════════════════════════════════════════════════════
#   AGENT BRAIN CLASS
# ═══════════════════════════════════════════════════════════════

class AgentBrain:
    """The master orchestrator of all agent operations."""
    
    def __init__(self):
        self.stats = {
            "scans_run":         0,
            "candidates_found":  0,
            "trades_executed":   0,
            "trades_rejected":   0,
            "gates_failed":      0,
            "monitoring_cycles": 0,
        }
        
        # Store today's candidates
        self.todays_candidates: List[Dict] = []
    
    # ═══════════════════════════════════════════════════════════
    #   PREMARKET PREPARATION (8:30 AM)
    # ═══════════════════════════════════════════════════════════
    
    async def premarket_prep(self):
        """
        Pre-market preparation.
        Runs at 8:30 AM (before scan).
        """
        logger.info("=" * 60)
        logger.info("🌅 PREMARKET PREPARATION STARTING")
        logger.info("=" * 60)
        
        try:
            # 1. Reset daily agent state
            from database.db import reset_daily_agent_state
            reset_daily_agent_state()
            logger.info("✅ Daily counters reset")
            
            # 2. Refresh cross-asset data
            from data_pipeline.cross_asset import refresh_cross_asset_data
            refresh_cross_asset_data()
            logger.info("✅ Cross-asset data refreshed")
            
            # 3. Verify Upstox connection
            from data_pipeline.upstox_api import get_upstox_client
            client = get_upstox_client()
            conn_test = client.test_connection()
            
            if conn_test.get("success"):
                logger.info(f"✅ Upstox connected: {conn_test['user_name']}")
            else:
                logger.warning(f"⚠️ Upstox issue: {conn_test.get('error')}")
                # Send alert
                await self._send_message(
                    "⚠️ <b>Premarket Alert</b>\n\n"
                    f"Upstox connection issue: {conn_test.get('error')}\n"
                    "Please regenerate access token."
                )
            
            # 4. Check agent state
            state = get_agent_state()
            
            if not state.get("is_active"):
                logger.warning("⚠️ Agent not active - won't trade today")
                await self._send_message(
                    "⚠️ <b>Agent Not Active</b>\n\n"
                    "Start agent via /agent/start to enable auto-trading."
                )
                return
            
            # 5. Send morning alert
            await self._send_message(
                "🌅 <b>Good Morning!</b>\n\n"
                "TRADEDO Agent is ready for today's session.\n"
                f"💰 Capital: ₹{state['capital']:,.0f}\n"
                f"📊 P&L: ₹{state.get('capital', 0) - state.get('starting_capital', 100000):,.0f}\n\n"
                "Morning scan will run at 8:45 AM.\n"
                "Auto-execution starts at 9:15 AM."
            )
            
            logger.info("✅ Premarket preparation complete")
        
        except Exception as e:
            logger.error(f"Premarket prep failed: {e}", exc_info=True)
    
    # ═══════════════════════════════════════════════════════════
    #   MORNING SCAN (8:45 AM)
    # ═══════════════════════════════════════════════════════════
    
    async def morning_scan(self):
        """
        Comprehensive morning scan.
        Finds top trading candidates for the day.
        Runs at 8:45 AM.
        """
        logger.info("=" * 60)
        logger.info("🔍 MORNING SCAN STARTING")
        logger.info("=" * 60)
        
        try:
            # Check if agent is active
            state = get_agent_state()
            if not state.get("is_active"):
                logger.info("Agent not active, skipping scan")
                return
            
            # Run deep scan
            from agent.scanner import StockScanner
            scanner = StockScanner(mode="intraday")
            
            logger.info("Running deep scan on Tier 1 (Nifty 50)...")
            result = scanner.deep_scan(tier="tier1")
            
            self.stats["scans_run"] += 1
            
            candidates = result.get("tradeable_candidates", [])
            self.stats["candidates_found"] += len(candidates)
            
            # Filter by score threshold
            top_candidates = [
                c for c in candidates 
                if c.get("final_score", 0) >= MIN_SCORE_THRESHOLD
            ]
            
            # Store for market open execution
            self.todays_candidates = top_candidates[:MAX_TRADES_PER_DAY]
            
            # Send scan report
            await self._send_scan_report(result, self.todays_candidates)
            
            logger.info(
                f"✅ Scan complete: {len(candidates)} tradeable, "
                f"{len(self.todays_candidates)} selected for execution"
            )
        
        except Exception as e:
            logger.error(f"Morning scan failed: {e}", exc_info=True)
    
    async def _send_scan_report(self, scan_result: Dict, selected: List[Dict]):
        """Send morning scan report via Telegram."""
        stats = scan_result.get("stats", {})
        
        msg = "🔍 <b>Morning Scan Complete</b>\n\n"
        msg += f"📊 Scanned: {stats.get('total_scanned', 0)} stocks\n"
        msg += f"⏱️ Time: {stats.get('scan_time_sec', 0)}s\n"
        msg += f"🎯 Regime: <b>{stats.get('market_regime', 'N/A')}</b>\n"
        msg += f"🏆 Tradeable: {stats.get('tradeable', 0)}\n\n"
        
        if selected:
            msg += f"<b>Selected for Execution ({len(selected)}):</b>\n"
            for i, c in enumerate(selected, 1):
                symbol = c["symbol"].replace(".NS", "")
                signal = c.get("signal", "N/A")
                score  = c.get("final_score", 0)
                
                emoji = "🟢" if signal == "BUY" else "🔴"
                msg += (
                    f"{i}. {emoji} <b>{symbol}</b>  "
                    f"{signal}  "
                    f"Score: <b>{score}</b>\n"
                )
            msg += "\n⏰ Auto-execution at 9:15 AM"
        else:
            msg += "🟡 No candidates meeting quality threshold.\n"
            msg += "Agent will not trade today."
        
        await self._send_message(msg)
    
    # ═══════════════════════════════════════════════════════════
    #   MARKET OPEN EXECUTION (9:15 AM)
    # ═══════════════════════════════════════════════════════════
    
    async def market_open_execution(self):
        """
        Execute selected candidates at market open.
        Runs at 9:15 AM.
        """
        logger.info("=" * 60)
        logger.info("🚀 MARKET OPEN - EXECUTING TRADES")
        logger.info("=" * 60)
        
        try:
            state = get_agent_state()
            if not state.get("is_active"):
                logger.info("Agent not active, skipping execution")
                return
            
            if not self.todays_candidates:
                logger.info("No candidates to execute today")
                return
            
            # Execute each candidate
            from agent.paper_executor import PaperExecutor
            executor = PaperExecutor(mode="intraday")
            
            executed = []
            rejected = []
            
            for candidate in self.todays_candidates:
                try:
                    symbol   = candidate["symbol"]
                    signal   = candidate.get("signal", "BUY")
                    
                    # Get fresh master result
                    from agent.master_scorer import get_master_score_with_gates
                    master = get_master_score_with_gates(symbol, mode="intraday")
                    
                    if not master.get("can_execute"):
                        logger.info(f"❌ {symbol}: Gates failed at execution time")
                        rejected.append({
                            "symbol": symbol,
                            "reason": "Gates failed at execution time",
                        })
                        self.stats["gates_failed"] += 1
                        continue
                    
                    # Extract required data
                    technical  = master.get("technical", {})
                    indicators = master.get("technical", {})
                    
                    # Get ATR from full master data (need to fetch)
                    from ml.engine import fetch_intraday_data, compute_intraday_features_v3
                    from data_pipeline.cross_asset import get_cross_asset_data
                    
                    try:
                        df_stock = fetch_intraday_data(symbol)
                        cross_asset = get_cross_asset_data()
                        feat = compute_intraday_features_v3(df_stock, cross_asset)
                        
                        if not feat.empty:
                            atr_pct = feat["atr_pct"].iloc[-1]
                            current_price = technical.get("current_price", 0)
                            atr = (atr_pct / 100) * current_price
                        else:
                            logger.warning(f"No ATR data for {symbol}, using estimate")
                            atr = technical.get("current_price", 100) * 0.015
                    except Exception as e:
                        logger.warning(f"ATR calc failed for {symbol}: {e}")
                        atr = technical.get("current_price", 100) * 0.015
                    
                    # Execute trade
                    result = executor.execute_trade(
                        symbol          = symbol,
                        signal          = signal,
                        current_price   = technical.get("current_price", 0),
                        atr             = atr,
                        confidence_pct  = technical.get("confidence", 0),
                        composite_score = master.get("final_score", 0),
                        ai_reasoning    = master.get("ai_reasoning", ""),
                        master_result   = master,
                    )
                    
                    if result.get("success"):
                        executed.append({
                            "symbol":   symbol,
                            "trade_id": result.get("trade_id"),
                        })
                        self.stats["trades_executed"] += 1
                        logger.info(f"✅ Executed: {symbol} (Trade #{result.get('trade_id')})")
                    else:
                        rejected.append({
                            "symbol": symbol,
                            "reason": result.get("error", "Unknown"),
                        })
                        self.stats["trades_rejected"] += 1
                        logger.info(f"❌ Rejected: {symbol} - {result.get('error')}")
                
                except Exception as e:
                    logger.error(f"Execution failed for {candidate.get('symbol')}: {e}")
                    rejected.append({
                        "symbol": candidate.get("symbol"),
                        "reason": str(e)[:100],
                    })
            
            # Send execution report
            await self._send_execution_report(executed, rejected)
        
        except Exception as e:
            logger.error(f"Market open execution failed: {e}", exc_info=True)
    
    async def _send_execution_report(self, executed: List[Dict], rejected: List[Dict]):
        """Send execution report via Telegram."""
        msg = "🚀 <b>Market Open - Execution Report</b>\n\n"
        
        if executed:
            msg += f"✅ <b>Executed ({len(executed)}):</b>\n"
            for e in executed:
                symbol = e["symbol"].replace(".NS", "")
                msg += f"  🟢 {symbol} (Trade #{e['trade_id']})\n"
            msg += "\n"
        
        if rejected:
            msg += f"❌ <b>Rejected ({len(rejected)}):</b>\n"
            for r in rejected:
                symbol = r["symbol"].replace(".NS", "")
                msg += f"  ⚠️ {symbol}: {r['reason'][:60]}\n"
            msg += "\n"
        
        if not executed and not rejected:
            msg += "🟡 No trades taken today.\n"
        
        msg += "⏰ Live monitoring active until 3:15 PM"
        
        await self._send_message(msg)
    
    # ═══════════════════════════════════════════════════════════
    #   EOD SUMMARY (3:30 PM)
    # ═══════════════════════════════════════════════════════════
    
    async def eod_summary(self):
        """
        End of day summary.
        Runs at 3:30 PM (after market close).
        """
        logger.info("=" * 60)
        logger.info("🌆 EOD SUMMARY")
        logger.info("=" * 60)
        
        try:
            # Get today's stats
            today = get_todays_performance()
            overall = get_overall_performance()
            state = get_agent_state()
            
            # Build report
            msg = "🌆 <b>End of Day Summary</b>\n\n"
            
            # Today's performance
            pnl_today = today.get("total_pnl", 0)
            pnl_emoji = "📈" if pnl_today > 0 else "📉"
            
            msg += f"<b>📅 Today's Performance:</b>\n"
            msg += f"Trades: {today.get('total_trades', 0)} "
            msg += f"({today.get('closed_trades', 0)} closed)\n"
            msg += f"Wins: {today.get('winning_trades', 0)} | "
            msg += f"Losses: {today.get('losing_trades', 0)}\n"
            msg += f"Win Rate: <b>{today.get('win_rate', 0):.1f}%</b>\n"
            msg += f"{pnl_emoji} P&L: <b>₹{pnl_today:,.2f}</b>\n\n"
            
            # Overall performance
            msg += f"<b>📊 Overall (All-Time):</b>\n"
            msg += f"Total Trades: {overall.get('total_trades', 0)}\n"
            msg += f"Win Rate: {overall.get('win_rate', 0):.1f}%\n"
            msg += f"Total P&L: ₹{overall.get('total_pnl', 0):,.2f}\n"
            msg += f"Capital: ₹{state.get('capital', 100000):,.2f}\n\n"
            
            # Best/worst trades
            if today.get("largest_win", 0) > 0:
                msg += f"🎯 Best Trade: ₹{today['largest_win']:,.2f}\n"
            if today.get("largest_loss", 0) < 0:
                msg += f"💔 Worst Trade: ₹{today['largest_loss']:,.2f}\n"
            
            msg += "\n🌙 Agent going to rest. See you tomorrow at 8:30 AM!"
            
            await self._send_message(msg)
            
            # Reset for tomorrow
            self.todays_candidates = []
        
        except Exception as e:
            logger.error(f"EOD summary failed: {e}", exc_info=True)
    
    # ═══════════════════════════════════════════════════════════
    #   HELPERS
    # ═══════════════════════════════════════════════════════════
    
    async def _send_message(self, msg: str):
        """Send Telegram message."""
        try:
            from utils.telegram_bot import send_message
            await send_message(msg)
        except Exception as e:
            logger.warning(f"Telegram send failed: {e}")
    
    def _is_weekday(self) -> bool:
        """Check if today is a weekday."""
        return datetime.now().weekday() < 5
    
    def get_status(self) -> Dict:
        """Get brain status."""
        return {
            "todays_candidates": len(self.todays_candidates),
            "stats":             self.stats,
        }


# ═══════════════════════════════════════════════════════════════
#   GLOBAL SINGLETON
# ═══════════════════════════════════════════════════════════════

_brain: Optional[AgentBrain] = None

def get_brain() -> AgentBrain:
    global _brain
    if _brain is None:
        _brain = AgentBrain()
    return _brain


# ═══════════════════════════════════════════════════════════════
#   SCHEDULER JOBS (async wrappers)
# ═══════════════════════════════════════════════════════════════

async def job_premarket_prep():
    """Scheduler wrapper for premarket prep."""
    brain = get_brain()
    await brain.premarket_prep()


async def job_morning_scan():
    """Scheduler wrapper for morning scan."""
    brain = get_brain()
    await brain.morning_scan()


async def job_market_open_execution():
    """Scheduler wrapper for market open execution."""
    brain = get_brain()
    await brain.market_open_execution()


async def job_eod_summary():
    """Scheduler wrapper for EOD summary."""
    brain = get_brain()
    await brain.eod_summary()


# ═══════════════════════════════════════════════════════════════
#   Quick Test
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("\n" + "="*60)
    print("AGENT BRAIN TEST")
    print("="*60)
    
    brain = get_brain()
    status = brain.get_status()
    
    print(f"\n📊 Brain Status:")
    for k, v in status.items():
        print(f"   {k}: {v}")
    
    print("\n⚠️ Note: Actual brain jobs run via scheduler")
    print("   Test individual functions by triggering via API")
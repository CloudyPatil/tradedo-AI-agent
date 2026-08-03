# E:\tradedo\app\backend\agent\trade_journal.py

"""
TRADE JOURNAL
Rich logging system that captures EVERY data point about a trade.
This becomes the training data for Reinforcement Learning in Phase 5.5.

Every trade stores:
- Full market context at entry
- All feature values
- All data source scores
- Time context
- Complete outcome

Query patterns:
- "Which setups win most?"
- "Which sectors fail in bearish regimes?"
- "What time of day is most profitable?"
- "Which composite score range has best win rate?"
"""

# ─── Path Setup (MUST be first) ──────────────────────────────
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from database.db import get_connection, get_trade_by_id, update_trade

logger = logging.getLogger("tradedo.journal")


# ═══════════════════════════════════════════════════════════════
#   JOURNAL ENTRY BUILDER
# ═══════════════════════════════════════════════════════════════

class TradeJournal:
    """Rich trade logging for RL training data."""
    
    @staticmethod
    def build_entry_snapshot(
        symbol: str,
        signal: str,
        current_price: float,
        confidence_pct: float,
        composite_score: float,
        master_result: Dict = None,
        trade_plan: Dict = None,
    ) -> Dict:
        """
        Build a comprehensive snapshot at trade entry.
        This is the "state" in reinforcement learning terms.
        """
        now = datetime.now()
        
        # ── Basic context ────────────────────────────────────
        snapshot = {
            "entry_timestamp":   now.isoformat(),
            "symbol":            symbol,
            "signal":            signal,
            "current_price":     current_price,
            "confidence_pct":    confidence_pct,
            "composite_score":   composite_score,
            
            # Time features (RL states)
            "hour":              now.hour,
            "minute":            now.minute,
            "day_of_week":       now.weekday(),  # 0=Mon, 6=Sun
            "day_of_month":      now.day,
            "month":             now.month,
            "quarter":           (now.month - 1) // 3 + 1,
            "is_monday":         now.weekday() == 0,
            "is_friday":         now.weekday() == 4,
            "is_month_start":    now.day <= 5,
            "is_month_end":      now.day >= 25,
            "is_quarter_end":    now.month in [3, 6, 9, 12] and now.day >= 25,
        }
        
        # ── Extract from master_result ───────────────────────
        if master_result:
            snapshot["master_verdict"] = master_result.get("verdict")
            snapshot["master_action"]  = master_result.get("action")
            
            # Score breakdown
            breakdown = master_result.get("score_breakdown", {})
            snapshot["score_technical"] = breakdown.get("technical", 0)
            snapshot["score_news"]      = breakdown.get("news", 0)
            snapshot["score_reddit"]    = breakdown.get("reddit_st", 0)
            snapshot["score_youtube"]   = breakdown.get("youtube", 0)
            snapshot["score_twitter"]   = breakdown.get("twitter", 0)
            snapshot["score_nse_money"] = breakdown.get("nse_money", 0)
            snapshot["score_nse_bulk"]  = breakdown.get("nse_bulk", 0)
            snapshot["score_options"]   = breakdown.get("options", 0)
            snapshot["score_delivery"]  = breakdown.get("delivery", 0)
            snapshot["score_trends"]    = breakdown.get("trends", 0)
            snapshot["score_global"]    = breakdown.get("global", 0)
            
            # Penalties
            penalties = master_result.get("penalty_breakdown", {})
            snapshot["penalty_total"]   = sum(penalties.values()) if penalties else 0
            
            # Technical summary
            tech = master_result.get("technical", {})
            snapshot["ml_prob_up"]      = tech.get("prob_up")
            snapshot["ml_signal"]       = tech.get("signal")
            snapshot["indicator_rsi"]   = tech.get("rsi")
            
            # News
            news = master_result.get("news", {})
            snapshot["news_label"]      = news.get("label")
            snapshot["news_score"]      = news.get("score")
            snapshot["news_risk_flag"]  = news.get("risk_flag")
            
            # Social
            social = master_result.get("social", {})
            snapshot["social_label"]    = social.get("label")
            snapshot["social_score"]    = social.get("score")
            snapshot["social_confidence"] = social.get("confidence")
            snapshot["social_buzz"]     = social.get("buzz_score")
            
            # NSE
            nse = master_result.get("nse", {})
            snapshot["nse_label"]       = nse.get("label")
            snapshot["nse_score"]       = nse.get("score")
            snapshot["nse_risk_flags"]  = ",".join(nse.get("risk_flags", []))
            
            # Trends
            trends = master_result.get("trends", {})
            snapshot["trends_signal"]   = trends.get("signal")
            snapshot["trends_spike"]    = trends.get("spike_ratio")
            
            # Global
            global_ctx = master_result.get("global", {})
            snapshot["global_impact"]   = global_ctx.get("impact_signal")
            snapshot["global_score"]    = global_ctx.get("impact_score")
            snapshot["sector"]          = global_ctx.get("sector")
        
        # ── Extract from trade_plan ──────────────────────────
        if trade_plan:
            snapshot["confidence_level"]  = trade_plan.get("confidence_level")
            snapshot["risk_amount"]       = trade_plan.get("risk_amount")
            snapshot["risk_pct"]          = trade_plan.get("risk_pct")
            snapshot["atr"]               = trade_plan.get("atr")
            snapshot["atr_pct"]           = trade_plan.get("atr_pct")
            snapshot["sl_pct"]            = trade_plan.get("sl_pct")
            snapshot["target_1_pct"]      = trade_plan.get("target_1_pct")
            snapshot["target_2_pct"]      = trade_plan.get("target_2_pct")
            snapshot["risk_reward_1"]     = trade_plan.get("risk_reward_1")
            snapshot["risk_reward_2"]     = trade_plan.get("risk_reward_2")
            snapshot["sector_multiplier"] = trade_plan.get("sector_multiplier")
            snapshot["shares"]            = trade_plan.get("shares")
            snapshot["investment"]        = trade_plan.get("investment")
        
        return snapshot
    
    @staticmethod
    def build_exit_analysis(trade: Dict) -> Dict:
        """Build exit analysis for RL reward calculation."""
        if not trade or trade["status"] == "OPEN":
            return {}
        
        entry_price = trade["entry_price"]
        exit_price  = trade.get("exit_price", entry_price)
        pnl         = trade.get("pnl", 0)
        pnl_pct     = trade.get("pnl_pct", 0)
        
        # ── Reward calculation (for RL) ──────────────────────
        # Base reward from P&L
        reward = pnl_pct  # Percentage return
        
        # Bonus for hitting targets
        if trade["status"] == "T2_HIT":
            reward += 20     # Bonus for hitting T2
        elif trade["status"] == "T1_HIT":
            reward += 10     # Bonus for T1
        elif trade["status"] == "SL_HIT":
            reward -= 5      # Small penalty for SL
        elif trade["status"] == "EOD":
            if pnl < 0:
                reward -= 3  # Penalty for EOD loss
        
        # Time efficiency bonus
        hold_mins = trade.get("hold_duration_mins", 0)
        if hold_mins > 0:
            if pnl > 0 and hold_mins < 60:
                reward += 5   # Fast win bonus
            elif pnl < 0 and hold_mins > 240:
                reward -= 5   # Slow loss penalty
        
        # ── Trade quality metrics ────────────────────────────
        is_winner = pnl > 0
        
        # Move efficiency (how much of favorable move did we capture)
        if is_winner:
            highest = trade.get("highest_price", exit_price)
            max_possible_gain = highest - entry_price if trade["direction"] == "LONG" else entry_price - trade.get("lowest_price", exit_price)
            captured_gain = exit_price - entry_price if trade["direction"] == "LONG" else entry_price - exit_price
            move_efficiency = round((captured_gain / max_possible_gain) * 100, 1) if max_possible_gain > 0 else 100
        else:
            move_efficiency = None
        
        return {
            "exit_timestamp":  trade.get("exit_time"),
            "exit_price":      exit_price,
            "pnl":             pnl,
            "pnl_pct":         pnl_pct,
            "status":          trade["status"],
            "exit_reason":     trade.get("exit_reason"),
            "hold_duration_mins": hold_mins,
            "is_winner":       is_winner,
            
            # RL Reward
            "rl_reward":       round(reward, 2),
            
            # Trade quality
            "move_efficiency_pct": move_efficiency,
            "highest_price":   trade.get("highest_price"),
            "lowest_price":    trade.get("lowest_price"),
        }
    
    @staticmethod
    def save_full_snapshot(trade_id: int, snapshot: Dict):
        """Save the full snapshot to trade metadata."""
        try:
            snapshot_json = json.dumps(snapshot, default=str)
            update_trade(trade_id, metadata=snapshot_json)
            logger.info(f"📓 Journal snapshot saved for trade {trade_id}")
        except Exception as e:
            logger.error(f"Journal save failed: {e}")


# ═══════════════════════════════════════════════════════════════
#   ANALYTICS QUERIES (RL Data Extraction)
# ═══════════════════════════════════════════════════════════════

def get_all_closed_trades_with_journal() -> List[Dict]:
    """Get all closed trades with parsed journal data."""
    conn = get_connection()
    rows = conn.execute("""
        SELECT * FROM paper_trades 
        WHERE status != 'OPEN' AND metadata IS NOT NULL
        ORDER BY entry_time DESC
    """).fetchall()
    conn.close()
    
    trades = []
    for row in rows:
        trade = dict(row)
        # Parse metadata
        try:
            trade["journal"] = json.loads(trade["metadata"]) if trade["metadata"] else {}
        except:
            trade["journal"] = {}
        
        # Add exit analysis
        trade["exit_analysis"] = TradeJournal.build_exit_analysis(trade)
        trades.append(trade)
    
    return trades


def analyze_win_rate_by_confidence() -> Dict:
    """Analyze win rate by confidence level."""
    trades = get_all_closed_trades_with_journal()
    
    if not trades:
        return {"message": "No trades to analyze yet"}
    
    buckets = {
        "VERY_HIGH": {"wins": 0, "total": 0, "pnl": 0},
        "HIGH":      {"wins": 0, "total": 0, "pnl": 0},
        "MEDIUM":    {"wins": 0, "total": 0, "pnl": 0},
        "LOW":       {"wins": 0, "total": 0, "pnl": 0},
    }
    
    for trade in trades:
        level = trade.get("journal", {}).get("confidence_level", "MEDIUM")
        if level not in buckets:
            continue
        
        buckets[level]["total"] += 1
        buckets[level]["pnl"]   += trade.get("pnl", 0)
        if (trade.get("pnl") or 0) > 0:
            buckets[level]["wins"] += 1
    
    result = {}
    for level, data in buckets.items():
        if data["total"] > 0:
            result[level] = {
                "total_trades":  data["total"],
                "wins":          data["wins"],
                "win_rate":      round(data["wins"] / data["total"] * 100, 1),
                "total_pnl":     round(data["pnl"], 2),
                "avg_pnl":       round(data["pnl"] / data["total"], 2),
            }
    
    return result


def analyze_win_rate_by_sector() -> Dict:
    """Analyze win rate by sector."""
    trades = get_all_closed_trades_with_journal()
    
    if not trades:
        return {"message": "No trades to analyze yet"}
    
    sectors = {}
    for trade in trades:
        sector = trade.get("sector", "UNKNOWN")
        if sector not in sectors:
            sectors[sector] = {"wins": 0, "total": 0, "pnl": 0}
        
        sectors[sector]["total"] += 1
        sectors[sector]["pnl"]   += trade.get("pnl", 0)
        if (trade.get("pnl") or 0) > 0:
            sectors[sector]["wins"] += 1
    
    result = {}
    for sector, data in sectors.items():
        if data["total"] > 0:
            result[sector] = {
                "trades":    data["total"],
                "wins":      data["wins"],
                "win_rate":  round(data["wins"] / data["total"] * 100, 1),
                "total_pnl": round(data["pnl"], 2),
                "avg_pnl":   round(data["pnl"] / data["total"], 2),
            }
    
    # Sort by win rate
    return dict(sorted(result.items(), key=lambda x: x[1]["win_rate"], reverse=True))


def analyze_win_rate_by_time() -> Dict:
    """Analyze win rate by hour of day."""
    trades = get_all_closed_trades_with_journal()
    
    if not trades:
        return {"message": "No trades to analyze yet"}
    
    hours = {}
    for trade in trades:
        hour = trade.get("journal", {}).get("hour")
        if hour is None:
            continue
        
        if hour not in hours:
            hours[hour] = {"wins": 0, "total": 0, "pnl": 0}
        
        hours[hour]["total"] += 1
        hours[hour]["pnl"]   += trade.get("pnl", 0)
        if (trade.get("pnl") or 0) > 0:
            hours[hour]["wins"] += 1
    
    result = {}
    for hour in sorted(hours.keys()):
        data = hours[hour]
        if data["total"] > 0:
            result[f"{hour}:00"] = {
                "trades":    data["total"],
                "win_rate":  round(data["wins"] / data["total"] * 100, 1),
                "avg_pnl":   round(data["pnl"] / data["total"], 2),
            }
    
    return result


def analyze_win_rate_by_composite_score() -> Dict:
    """Analyze win rate by composite score buckets."""
    trades = get_all_closed_trades_with_journal()
    
    if not trades:
        return {"message": "No trades to analyze yet"}
    
    buckets = {
        "150+":    {"wins": 0, "total": 0, "pnl": 0},
        "130-150": {"wins": 0, "total": 0, "pnl": 0},
        "110-130": {"wins": 0, "total": 0, "pnl": 0},
        "90-110":  {"wins": 0, "total": 0, "pnl": 0},
        "<90":     {"wins": 0, "total": 0, "pnl": 0},
    }
    
    for trade in trades:
        score = trade.get("composite_score", 0) or 0
        
        if score >= 150:
            key = "150+"
        elif score >= 130:
            key = "130-150"
        elif score >= 110:
            key = "110-130"
        elif score >= 90:
            key = "90-110"
        else:
            key = "<90"
        
        buckets[key]["total"] += 1
        buckets[key]["pnl"]   += trade.get("pnl", 0)
        if (trade.get("pnl") or 0) > 0:
            buckets[key]["wins"] += 1
    
    result = {}
    for bucket, data in buckets.items():
        if data["total"] > 0:
            result[bucket] = {
                "trades":    data["total"],
                "wins":      data["wins"],
                "win_rate":  round(data["wins"] / data["total"] * 100, 1),
                "avg_pnl":   round(data["pnl"] / data["total"], 2),
            }
    
    return result


def analyze_exit_reasons() -> Dict:
    """Analyze what causes trade exits."""
    trades = get_all_closed_trades_with_journal()
    
    if not trades:
        return {"message": "No trades to analyze yet"}
    
    reasons = {}
    for trade in trades:
        reason = trade.get("exit_reason", "UNKNOWN")
        if reason not in reasons:
            reasons[reason] = {"count": 0, "total_pnl": 0}
        
        reasons[reason]["count"]     += 1
        reasons[reason]["total_pnl"] += trade.get("pnl", 0)
    
    result = {}
    for reason, data in reasons.items():
        result[reason] = {
            "count":     data["count"],
            "total_pnl": round(data["total_pnl"], 2),
            "avg_pnl":   round(data["total_pnl"] / data["count"], 2),
        }
    
    return result


def get_learning_insights() -> Dict:
    """
    Comprehensive analysis for insights.
    This becomes the base for RL system.
    """
    trades = get_all_closed_trades_with_journal()
    
    return {
        "total_closed_trades": len(trades),
        "insights": {
            "by_confidence":       analyze_win_rate_by_confidence(),
            "by_sector":           analyze_win_rate_by_sector(),
            "by_hour":             analyze_win_rate_by_time(),
            "by_composite_score":  analyze_win_rate_by_composite_score(),
            "by_exit_reason":      analyze_exit_reasons(),
        },
        "data_ready_for_rl": len(trades) >= 20,
    }


# ═══════════════════════════════════════════════════════════════
#   PATTERN DISCOVERY (Preview of RL)
# ═══════════════════════════════════════════════════════════════

def find_best_patterns(min_trades: int = 5) -> List[Dict]:
    """Find winning patterns in trade history."""
    trades = get_all_closed_trades_with_journal()
    
    if len(trades) < min_trades:
        return [{"message": f"Need at least {min_trades} trades to find patterns"}]
    
    patterns = []
    
    # Pattern 1: High confidence + specific sector
    sector_conf = {}
    for trade in trades:
        sector = trade.get("sector", "UNKNOWN")
        conf_level = trade.get("journal", {}).get("confidence_level", "MEDIUM")
        key = f"{sector}_{conf_level}"
        
        if key not in sector_conf:
            sector_conf[key] = {"trades": [], "wins": 0}
        
        sector_conf[key]["trades"].append(trade)
        if (trade.get("pnl") or 0) > 0:
            sector_conf[key]["wins"] += 1
    
    for key, data in sector_conf.items():
        if len(data["trades"]) >= 3:
            win_rate = data["wins"] / len(data["trades"]) * 100
            if win_rate >= 70:
                patterns.append({
                    "pattern": key,
                    "type":    "SECTOR_CONFIDENCE",
                    "trades":  len(data["trades"]),
                    "wins":    data["wins"],
                    "win_rate": round(win_rate, 1),
                    "recommendation": "STRONG - keep taking these setups",
                })
            elif win_rate <= 30:
                patterns.append({
                    "pattern": key,
                    "type":    "SECTOR_CONFIDENCE",
                    "trades":  len(data["trades"]),
                    "wins":    data["wins"],
                    "win_rate": round(win_rate, 1),
                    "recommendation": "AVOID - these setups fail",
                })
    
    return sorted(patterns, key=lambda x: x.get("win_rate", 0), reverse=True)


def find_worst_patterns(min_trades: int = 5) -> List[Dict]:
    """Find losing patterns to avoid."""
    all_patterns = find_best_patterns(min_trades)
    return [p for p in all_patterns if p.get("win_rate", 100) < 40]


# ─── Quick Test ───────────────────────────────────────────────
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    import json
    
    print("\n" + "="*60)
    print("TRADE JOURNAL ANALYTICS")
    print("="*60)
    
    insights = get_learning_insights()
    
    print(f"\n📊 Total Closed Trades: {insights['total_closed_trades']}")
    print(f"📊 Ready for RL: {insights['data_ready_for_rl']}")
    
    print("\n📈 By Confidence Level:")
    for level, data in insights["insights"]["by_confidence"].items():
        if isinstance(data, dict):
            print(f"   {level}: {data.get('win_rate', 0)}% win rate ({data.get('total_trades', 0)} trades)")
    
    print("\n📈 By Sector:")
    for sector, data in list(insights["insights"]["by_sector"].items())[:5]:
        if isinstance(data, dict):
            print(f"   {sector}: {data.get('win_rate', 0)}% ({data.get('trades', 0)} trades)")
    
    print("\n📈 By Composite Score:")
    for bucket, data in insights["insights"]["by_composite_score"].items():
        if isinstance(data, dict):
            print(f"   {bucket}: {data.get('win_rate', 0)}% ({data.get('trades', 0)} trades)")
# E:\tradedo\app\backend\agent\analytics.py

"""
ENHANCED PERFORMANCE ANALYTICS
Professional-grade trading metrics.

Metrics calculated:
- Sharpe Ratio, Sortino Ratio, Calmar Ratio
- Maximum Drawdown, Recovery Factor
- Profit Factor, Expectancy, Kelly Criterion
- Win/Loss streaks
- Time-based analytics
- Rolling performance
- Trade distribution
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import logging
import math
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict
import statistics

from database.db import get_connection

logger = logging.getLogger("tradedo.analytics")


# ═══════════════════════════════════════════════════════════════
#   CONFIG
# ═══════════════════════════════════════════════════════════════

RISK_FREE_RATE = 0.065        # 6.5% annual (Indian govt bonds)
TRADING_DAYS_YEAR = 252
MIN_TRADES_FOR_STATS = 5      # Need this many for meaningful stats


# ═══════════════════════════════════════════════════════════════
#   PERFORMANCE ANALYTICS CLASS
# ═══════════════════════════════════════════════════════════════

class PerformanceAnalytics:
    """Advanced performance analytics engine."""
    
    def __init__(self):
        self.trades = []
        self._load_trades()
    
    def _load_trades(self):
        """Load all closed trades from DB."""
        conn = get_connection()
        rows = conn.execute("""
            SELECT * FROM paper_trades 
            WHERE status != 'OPEN' 
            AND pnl IS NOT NULL
            ORDER BY entry_time ASC
        """).fetchall()
        conn.close()
        
        self.trades = [dict(r) for r in rows]
        logger.info(f"Loaded {len(self.trades)} closed trades for analytics")
    
    def refresh(self):
        """Reload trades from DB."""
        self._load_trades()
    
    def has_enough_data(self) -> bool:
        """Check if we have enough trades for meaningful stats."""
        return len(self.trades) >= MIN_TRADES_FOR_STATS
    
    # ═══════════════════════════════════════════════════════════
    #   CORE METRICS
    # ═══════════════════════════════════════════════════════════
    
    def basic_metrics(self) -> Dict:
        """Basic performance metrics."""
        if not self.trades:
            return self._empty_metrics()
        
        pnls = [t.get("pnl", 0) for t in self.trades]
        winners = [t for t in self.trades if t.get("pnl", 0) > 0]
        losers = [t for t in self.trades if t.get("pnl", 0) < 0]
        
        total_pnl = sum(pnls)
        gross_profit = sum(t["pnl"] for t in winners) if winners else 0
        gross_loss = abs(sum(t["pnl"] for t in losers)) if losers else 0
        
        win_rate = (len(winners) / len(self.trades)) * 100 if self.trades else 0
        
        return {
            "total_trades":   len(self.trades),
            "winning_trades": len(winners),
            "losing_trades":  len(losers),
            "win_rate":       round(win_rate, 2),
            "total_pnl":      round(total_pnl, 2),
            "gross_profit":   round(gross_profit, 2),
            "gross_loss":     round(gross_loss, 2),
            "avg_win":        round(gross_profit / len(winners), 2) if winners else 0,
            "avg_loss":       round(gross_loss / len(losers), 2) if losers else 0,
            "largest_win":    round(max(pnls), 2) if pnls else 0,
            "largest_loss":   round(min(pnls), 2) if pnls else 0,
        }
    
    # ═══════════════════════════════════════════════════════════
    #   SHARPE RATIO
    # ═══════════════════════════════════════════════════════════
    
    def sharpe_ratio(self) -> float:
        """
        Sharpe Ratio: Return per unit of risk (volatility).
        Higher is better. > 1 is good, > 2 is very good, > 3 is excellent.
        """
        if not self.has_enough_data():
            return 0.0
        
        returns = self._get_daily_returns_pct()
        if not returns or len(returns) < 2:
            return 0.0
        
        avg_return = statistics.mean(returns)
        std_dev = statistics.stdev(returns)
        
        if std_dev == 0:
            return 0.0
        
        # Annualize
        daily_risk_free = RISK_FREE_RATE / TRADING_DAYS_YEAR
        excess_return = avg_return - daily_risk_free
        
        sharpe = (excess_return / std_dev) * math.sqrt(TRADING_DAYS_YEAR)
        return round(sharpe, 3)
    
    # ═══════════════════════════════════════════════════════════
    #   SORTINO RATIO
    # ═══════════════════════════════════════════════════════════
    
    def sortino_ratio(self) -> float:
        """
        Sortino Ratio: Similar to Sharpe but only considers DOWNSIDE volatility.
        Better metric because upside volatility is good.
        """
        if not self.has_enough_data():
            return 0.0
        
        returns = self._get_daily_returns_pct()
        if not returns or len(returns) < 2:
            return 0.0
        
        avg_return = statistics.mean(returns)
        
        # Only consider negative returns for downside deviation
        negative_returns = [r for r in returns if r < 0]
        if not negative_returns:
            return 999.0  # No losses = infinite ratio
        
        downside_std = math.sqrt(sum(r ** 2 for r in negative_returns) / len(negative_returns))
        
        if downside_std == 0:
            return 0.0
        
        daily_risk_free = RISK_FREE_RATE / TRADING_DAYS_YEAR
        excess_return = avg_return - daily_risk_free
        
        sortino = (excess_return / downside_std) * math.sqrt(TRADING_DAYS_YEAR)
        return round(sortino, 3)
    
    # ═══════════════════════════════════════════════════════════
    #   MAXIMUM DRAWDOWN
    # ═══════════════════════════════════════════════════════════
    
    def max_drawdown(self) -> Dict:
        """
        Maximum Drawdown: Largest peak-to-trough decline.
        Critical risk metric — how much you could lose from a peak.
        """
        if not self.trades:
            return {"max_dd_pct": 0, "max_dd_amount": 0, "duration_days": 0}
        
        # Calculate cumulative equity curve
        starting_capital = 100000  # From agent state
        equity_curve = [starting_capital]
        
        for trade in self.trades:
            equity_curve.append(equity_curve[-1] + trade.get("pnl", 0))
        
        # Find max drawdown
        peak = equity_curve[0]
        max_dd_amount = 0
        max_dd_pct = 0
        peak_idx = 0
        trough_idx = 0
        
        for i, value in enumerate(equity_curve):
            if value > peak:
                peak = value
                peak_idx = i
            
            drawdown_amount = peak - value
            drawdown_pct = (drawdown_amount / peak) * 100 if peak > 0 else 0
            
            if drawdown_pct > max_dd_pct:
                max_dd_pct = drawdown_pct
                max_dd_amount = drawdown_amount
                trough_idx = i
        
        # Calculate duration
        duration_days = 0
        if peak_idx < len(self.trades) and trough_idx < len(self.trades):
            try:
                peak_time = datetime.fromisoformat(
                    self.trades[peak_idx - 1]["entry_time"].replace("Z", "+00:00")
                ) if peak_idx > 0 else datetime.now()
                
                trough_time = datetime.fromisoformat(
                    self.trades[trough_idx - 1]["entry_time"].replace("Z", "+00:00")
                ) if trough_idx > 0 else datetime.now()
                
                if peak_time.tzinfo:
                    peak_time = peak_time.replace(tzinfo=None)
                if trough_time.tzinfo:
                    trough_time = trough_time.replace(tzinfo=None)
                
                duration_days = (trough_time - peak_time).days
            except:
                duration_days = 0
        
        return {
            "max_dd_pct":     round(max_dd_pct, 2),
            "max_dd_amount":  round(max_dd_amount, 2),
            "duration_days":  duration_days,
            "peak_value":     round(peak, 2),
            "trough_value":   round(equity_curve[trough_idx] if trough_idx < len(equity_curve) else 0, 2),
        }
    
    # ═══════════════════════════════════════════════════════════
    #   CALMAR RATIO
    # ═══════════════════════════════════════════════════════════
    
    def calmar_ratio(self) -> float:
        """
        Calmar Ratio: Annualized return / Max Drawdown.
        Measures return per unit of drawdown risk.
        Higher is better. > 1 is good.
        """
        if not self.has_enough_data():
            return 0.0
        
        # Calculate annualized return
        if not self.trades:
            return 0.0
        
        total_pnl = sum(t.get("pnl", 0) for t in self.trades)
        starting_capital = 100000
        
        # Get time period
        try:
            first_trade = datetime.fromisoformat(
                self.trades[0]["entry_time"].replace("Z", "+00:00")
            )
            last_trade = datetime.fromisoformat(
                self.trades[-1]["entry_time"].replace("Z", "+00:00")
            )
            
            if first_trade.tzinfo:
                first_trade = first_trade.replace(tzinfo=None)
            if last_trade.tzinfo:
                last_trade = last_trade.replace(tzinfo=None)
            
            days = max((last_trade - first_trade).days, 1)
        except:
            days = 1
        
        # Annualize return
        total_return_pct = (total_pnl / starting_capital) * 100
        annualized_return = total_return_pct * (365 / days)
        
        # Get max drawdown
        max_dd = self.max_drawdown()["max_dd_pct"]
        
        if max_dd == 0:
            return 999.0 if annualized_return > 0 else 0.0
        
        return round(annualized_return / max_dd, 3)
    
    # ═══════════════════════════════════════════════════════════
    #   PROFIT FACTOR
    # ═══════════════════════════════════════════════════════════
    
    def profit_factor(self) -> float:
        """
        Profit Factor: Gross Profit / Gross Loss.
        > 1.0 = profitable system
        > 1.5 = good system
        > 2.0 = excellent system
        """
        winners = [t for t in self.trades if t.get("pnl", 0) > 0]
        losers = [t for t in self.trades if t.get("pnl", 0) < 0]
        
        gross_profit = sum(t["pnl"] for t in winners) if winners else 0
        gross_loss = abs(sum(t["pnl"] for t in losers)) if losers else 0
        
        if gross_loss == 0:
            return 999.0 if gross_profit > 0 else 0.0
        
        return round(gross_profit / gross_loss, 3)
    
    # ═══════════════════════════════════════════════════════════
    #   EXPECTANCY
    # ═══════════════════════════════════════════════════════════
    
    def expectancy(self) -> Dict:
        """
        Expectancy: Average profit/loss per trade.
        This is what you can EXPECT to make per trade over time.
        """
        if not self.trades:
            return {"expectancy": 0, "expectancy_pct": 0}
        
        winners = [t for t in self.trades if t.get("pnl", 0) > 0]
        losers = [t for t in self.trades if t.get("pnl", 0) < 0]
        
        win_rate = len(winners) / len(self.trades)
        loss_rate = len(losers) / len(self.trades)
        
        avg_win = sum(t["pnl"] for t in winners) / len(winners) if winners else 0
        avg_loss = abs(sum(t["pnl"] for t in losers) / len(losers)) if losers else 0
        
        expectancy_amount = (win_rate * avg_win) - (loss_rate * avg_loss)
        
        # As percentage of avg loss
        expectancy_pct = (expectancy_amount / avg_loss * 100) if avg_loss > 0 else 0
        
        return {
            "expectancy":     round(expectancy_amount, 2),
            "expectancy_pct": round(expectancy_pct, 2),
            "interpretation": self._interpret_expectancy(expectancy_amount),
        }
    
    def _interpret_expectancy(self, exp: float) -> str:
        if exp > 100:
            return "EXCELLENT - Highly profitable system"
        elif exp > 50:
            return "GOOD - Consistent profitability"
        elif exp > 0:
            return "PROFITABLE - Positive edge"
        elif exp == 0:
            return "BREAKEVEN - No edge"
        else:
            return "UNPROFITABLE - System losing money"
    
    # ═══════════════════════════════════════════════════════════
    #   KELLY CRITERION
    # ═══════════════════════════════════════════════════════════
    
    def kelly_criterion(self) -> Dict:
        """
        Kelly Criterion: Optimal position size for long-term growth.
        Formula: f = (bp - q) / b
          b = win/loss ratio
          p = win rate
          q = loss rate (1 - p)
        """
        if not self.has_enough_data():
            return {"kelly_pct": 0, "recommended_size_pct": 0}
        
        winners = [t for t in self.trades if t.get("pnl", 0) > 0]
        losers = [t for t in self.trades if t.get("pnl", 0) < 0]
        
        if not winners or not losers:
            return {"kelly_pct": 0, "recommended_size_pct": 0}
        
        win_rate = len(winners) / len(self.trades)
        loss_rate = 1 - win_rate
        
        avg_win = sum(t["pnl"] for t in winners) / len(winners)
        avg_loss = abs(sum(t["pnl"] for t in losers) / len(losers))
        
        if avg_loss == 0:
            return {"kelly_pct": 0, "recommended_size_pct": 0}
        
        b = avg_win / avg_loss  # win/loss ratio
        kelly = (b * win_rate - loss_rate) / b
        kelly_pct = kelly * 100
        
        # Recommend 25% of Kelly (safer, less volatile)
        recommended = max(0, kelly_pct * 0.25)
        
        return {
            "kelly_pct":            round(kelly_pct, 2),
            "recommended_size_pct": round(recommended, 2),
            "interpretation":       self._interpret_kelly(kelly_pct),
        }
    
    def _interpret_kelly(self, kelly: float) -> str:
        if kelly < 0:
            return "NEGATIVE - Don't trade this system"
        elif kelly < 5:
            return "SMALL EDGE - Trade small size"
        elif kelly < 15:
            return "MODERATE EDGE - Normal sizing OK"
        elif kelly < 30:
            return "STRONG EDGE - Can size up"
        else:
            return "EXCEPTIONAL EDGE - But use fractional Kelly for safety"
    
    # ═══════════════════════════════════════════════════════════
    #   WIN/LOSS STREAKS
    # ═══════════════════════════════════════════════════════════
    
    def streaks(self) -> Dict:
        """Analyze winning and losing streaks."""
        if not self.trades:
            return {
                "current_streak":      0,
                "current_streak_type": "NONE",
                "longest_win_streak":  0,
                "longest_loss_streak": 0,
                "avg_win_streak":      0,
                "avg_loss_streak":     0,
            }
        
        # Build streak sequence
        streaks = []
        current_type = None
        current_count = 0
        
        for trade in self.trades:
            pnl = trade.get("pnl", 0)
            trade_type = "WIN" if pnl > 0 else "LOSS" if pnl < 0 else None
            
            if trade_type is None:
                continue
            
            if trade_type == current_type:
                current_count += 1
            else:
                if current_type:
                    streaks.append((current_type, current_count))
                current_type = trade_type
                current_count = 1
        
        # Add final streak
        if current_type:
            streaks.append((current_type, current_count))
        
        # Analyze
        win_streaks = [count for type_, count in streaks if type_ == "WIN"]
        loss_streaks = [count for type_, count in streaks if type_ == "LOSS"]
        
        # Current streak (last one)
        current_streak = 0
        current_streak_type = "NONE"
        if streaks:
            current_streak_type, current_streak = streaks[-1]
        
        return {
            "current_streak":      current_streak,
            "current_streak_type": current_streak_type,
            "longest_win_streak":  max(win_streaks) if win_streaks else 0,
            "longest_loss_streak": max(loss_streaks) if loss_streaks else 0,
            "avg_win_streak":      round(sum(win_streaks) / len(win_streaks), 1) if win_streaks else 0,
            "avg_loss_streak":     round(sum(loss_streaks) / len(loss_streaks), 1) if loss_streaks else 0,
            "total_streaks":       len(streaks),
        }
    
    # ═══════════════════════════════════════════════════════════
    #   RECOVERY FACTOR
    # ═══════════════════════════════════════════════════════════
    
    def recovery_factor(self) -> float:
        """
        Recovery Factor: Total Return / Max Drawdown
        Measures how efficiently system recovers from drawdowns.
        Higher is better.
        """
        total_pnl = sum(t.get("pnl", 0) for t in self.trades)
        max_dd = self.max_drawdown()["max_dd_amount"]
        
        if max_dd == 0:
            return 999.0 if total_pnl > 0 else 0.0
        
        return round(total_pnl / max_dd, 3)
    
    # ═══════════════════════════════════════════════════════════
    #   TIME-BASED ANALYTICS
    # ═══════════════════════════════════════════════════════════
    
    def performance_by_hour(self) -> Dict:
        """Win rate and P&L by hour of day."""
        by_hour = defaultdict(lambda: {"trades": 0, "wins": 0, "pnl": 0})
        
        for trade in self.trades:
            try:
                entry = datetime.fromisoformat(
                    trade["entry_time"].replace("Z", "+00:00")
                )
                if entry.tzinfo:
                    entry = entry.replace(tzinfo=None)
                
                hour = entry.hour
                pnl = trade.get("pnl", 0)
                
                by_hour[hour]["trades"] += 1
                by_hour[hour]["pnl"] += pnl
                if pnl > 0:
                    by_hour[hour]["wins"] += 1
            except:
                continue
        
        result = {}
        for hour, data in sorted(by_hour.items()):
            result[f"{hour:02d}:00"] = {
                "trades":   data["trades"],
                "wins":     data["wins"],
                "win_rate": round((data["wins"] / data["trades"]) * 100, 1),
                "total_pnl": round(data["pnl"], 2),
                "avg_pnl":   round(data["pnl"] / data["trades"], 2),
            }
        
        return result
    
    def performance_by_day_of_week(self) -> Dict:
        """Win rate and P&L by day of week."""
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
        by_day = defaultdict(lambda: {"trades": 0, "wins": 0, "pnl": 0})
        
        for trade in self.trades:
            try:
                entry = datetime.fromisoformat(
                    trade["entry_time"].replace("Z", "+00:00")
                )
                if entry.tzinfo:
                    entry = entry.replace(tzinfo=None)
                
                day_idx = entry.weekday()
                if day_idx >= 5:
                    continue
                
                day_name = days[day_idx]
                pnl = trade.get("pnl", 0)
                
                by_day[day_name]["trades"] += 1
                by_day[day_name]["pnl"] += pnl
                if pnl > 0:
                    by_day[day_name]["wins"] += 1
            except:
                continue
        
        result = {}
        for day in days:
            data = by_day[day]
            if data["trades"] > 0:
                result[day] = {
                    "trades":   data["trades"],
                    "win_rate": round((data["wins"] / data["trades"]) * 100, 1),
                    "total_pnl": round(data["pnl"], 2),
                    "avg_pnl":   round(data["pnl"] / data["trades"], 2),
                }
        
        return result
    
    # ═══════════════════════════════════════════════════════════
    #   TRADE DISTRIBUTION
    # ═══════════════════════════════════════════════════════════
    
    def trade_distribution(self) -> Dict:
        """Distribution of trade outcomes."""
        if not self.trades:
            return {}
        
        pnls = [t.get("pnl", 0) for t in self.trades]
        
        # Buckets by P&L
        buckets = {
            "big_wins":    len([p for p in pnls if p > 500]),
            "medium_wins": len([p for p in pnls if 100 < p <= 500]),
            "small_wins":  len([p for p in pnls if 0 < p <= 100]),
            "breakeven":   len([p for p in pnls if p == 0]),
            "small_losses":  len([p for p in pnls if -100 <= p < 0]),
            "medium_losses": len([p for p in pnls if -500 <= p < -100]),
            "big_losses":    len([p for p in pnls if p < -500]),
        }
        
        return {
            "distribution": buckets,
            "total":        len(pnls),
            "median_pnl":   round(statistics.median(pnls), 2),
            "std_dev":      round(statistics.stdev(pnls), 2) if len(pnls) > 1 else 0,
        }
    
    # ═══════════════════════════════════════════════════════════
    #   EQUITY CURVE
    # ═══════════════════════════════════════════════════════════
    
    def equity_curve(self) -> List[Dict]:
        """Generate equity curve data points."""
        if not self.trades:
            return []
        
        starting_capital = 100000
        equity = starting_capital
        curve = []
        
        for trade in self.trades:
            equity += trade.get("pnl", 0)
            
            try:
                exit_time = trade.get("exit_time") or trade.get("entry_time")
                dt = datetime.fromisoformat(exit_time.replace("Z", "+00:00"))
                if dt.tzinfo:
                    dt = dt.replace(tzinfo=None)
                timestamp = dt.isoformat()
            except:
                timestamp = datetime.now().isoformat()
            
            curve.append({
                "timestamp": timestamp,
                "trade_id":  trade["id"],
                "symbol":    trade["symbol"],
                "pnl":       round(trade.get("pnl", 0), 2),
                "equity":    round(equity, 2),
                "return_pct": round(((equity - starting_capital) / starting_capital) * 100, 2),
            })
        
        return curve
    
    # ═══════════════════════════════════════════════════════════
    #   HELPER: Daily Returns
    # ═══════════════════════════════════════════════════════════
    
    def _get_daily_returns_pct(self) -> List[float]:
        """Get list of daily return percentages."""
        # Group trades by day
        daily_pnl = defaultdict(float)
        
        for trade in self.trades:
            try:
                exit_time = trade.get("exit_time") or trade.get("entry_time")
                dt = datetime.fromisoformat(exit_time.replace("Z", "+00:00"))
                if dt.tzinfo:
                    dt = dt.replace(tzinfo=None)
                
                day_key = dt.date().isoformat()
                daily_pnl[day_key] += trade.get("pnl", 0)
            except:
                continue
        
        if not daily_pnl:
            return []
        
        # Convert to returns %
        starting_capital = 100000
        returns = []
        current_capital = starting_capital
        
        for day in sorted(daily_pnl.keys()):
            pnl = daily_pnl[day]
            return_pct = (pnl / current_capital) * 100 if current_capital > 0 else 0
            returns.append(return_pct)
            current_capital += pnl
        
        return returns
    
    def _empty_metrics(self) -> Dict:
        return {
            "total_trades":   0,
            "winning_trades": 0,
            "losing_trades":  0,
            "win_rate":       0,
            "total_pnl":      0,
            "gross_profit":   0,
            "gross_loss":     0,
        }
    
    # ═══════════════════════════════════════════════════════════
    #   COMPREHENSIVE REPORT
    # ═══════════════════════════════════════════════════════════
    
    def full_report(self) -> Dict:
        """Complete performance report — all metrics."""
        return {
            "generated_at":     datetime.now().isoformat(),
            "has_enough_data":  self.has_enough_data(),
            
            # Core
            "basic":            self.basic_metrics(),
            
            # Risk-adjusted
            "sharpe_ratio":     self.sharpe_ratio(),
            "sortino_ratio":    self.sortino_ratio(),
            "calmar_ratio":     self.calmar_ratio(),
            
            # Risk
            "max_drawdown":     self.max_drawdown(),
            "recovery_factor":  self.recovery_factor(),
            
            # Profitability
            "profit_factor":    self.profit_factor(),
            "expectancy":       self.expectancy(),
            "kelly_criterion":  self.kelly_criterion(),
            
            # Streaks
            "streaks":          self.streaks(),
            
            # Time-based
            "by_hour":          self.performance_by_hour(),
            "by_day_of_week":   self.performance_by_day_of_week(),
            
            # Distribution
            "distribution":     self.trade_distribution(),
        }


# ═══════════════════════════════════════════════════════════════
#   GLOBAL INSTANCE
# ═══════════════════════════════════════════════════════════════

def get_analytics() -> PerformanceAnalytics:
    """Get fresh analytics instance."""
    return PerformanceAnalytics()


# ═══════════════════════════════════════════════════════════════
#   Convenience Functions
# ═══════════════════════════════════════════════════════════════

def get_performance_report() -> Dict:
    """Get complete performance report."""
    return get_analytics().full_report()


def get_equity_curve() -> List[Dict]:
    """Get equity curve data."""
    return get_analytics().equity_curve()


# ═══════════════════════════════════════════════════════════════
#   Quick Test
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("\n" + "="*60)
    print("PERFORMANCE ANALYTICS TEST")
    print("="*60)
    
    analytics = get_analytics()
    
    if not analytics.has_enough_data():
        print(f"\n⚠️  Only {len(analytics.trades)} trades in DB")
        print(f"   Need {MIN_TRADES_FOR_STATS}+ for meaningful stats")
        print("\n📊 Basic metrics:")
        for k, v in analytics.basic_metrics().items():
            print(f"   {k}: {v}")
    else:
        report = analytics.full_report()
        
        print(f"\n📊 Basic Metrics:")
        for k, v in report["basic"].items():
            print(f"   {k}: {v}")
        
        print(f"\n📈 Risk-Adjusted Metrics:")
        print(f"   Sharpe Ratio:  {report['sharpe_ratio']}")
        print(f"   Sortino Ratio: {report['sortino_ratio']}")
        print(f"   Calmar Ratio:  {report['calmar_ratio']}")
        
        print(f"\n⚠️  Risk:")
        dd = report["max_drawdown"]
        print(f"   Max Drawdown: {dd['max_dd_pct']}% (₹{dd['max_dd_amount']})")
        print(f"   Recovery Factor: {report['recovery_factor']}")
        
        print(f"\n💰 Profitability:")
        print(f"   Profit Factor: {report['profit_factor']}")
        exp = report["expectancy"]
        print(f"   Expectancy: ₹{exp['expectancy']}")
        print(f"   → {exp['interpretation']}")
        
        kelly = report["kelly_criterion"]
        print(f"   Kelly: {kelly['kelly_pct']}%")
        print(f"   → {kelly['interpretation']}")
        
        print(f"\n🔥 Streaks:")
        s = report["streaks"]
        print(f"   Current: {s['current_streak']} {s['current_streak_type']}")
        print(f"   Longest Win Streak:  {s['longest_win_streak']}")
        print(f"   Longest Loss Streak: {s['longest_loss_streak']}")
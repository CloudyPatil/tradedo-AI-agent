# E:\tradedo\app\backend\agent\risk_analytics.py

"""
RISK ANALYTICS DASHBOARD
Professional-grade portfolio risk metrics.

Metrics:
- Value at Risk (VaR)
- Expected Shortfall (CVaR)
- Portfolio Beta
- Sector Concentration
- Correlation Analysis
- Diversification Score
- Position Risk Breakdown
- Stress Test Scenarios
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import logging
import math
import statistics
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict

from database.db import get_connection, get_open_trades, get_agent_state
from agent.sectors import get_sector

logger = logging.getLogger("tradedo.risk")


# ═══════════════════════════════════════════════════════════════
#   CONFIG
# ═══════════════════════════════════════════════════════════════

VAR_CONFIDENCE_95 = 1.645     # Z-score for 95% VaR
VAR_CONFIDENCE_99 = 2.326     # Z-score for 99% VaR

# Sector concentration limits (max % of capital per sector)
MAX_SECTOR_PCT = 30

# Correlation thresholds
HIGH_CORRELATION = 0.7
LOW_CORRELATION  = 0.3


# ═══════════════════════════════════════════════════════════════
#   RISK ANALYTICS CLASS
# ═══════════════════════════════════════════════════════════════

class RiskAnalytics:
    """Portfolio risk analysis engine."""
    
    def __init__(self):
        self.open_trades = []
        self.closed_trades = []
        self.agent_state = {}
        self._load_data()
    
    def _load_data(self):
        """Load all data needed for risk analysis."""
        self.open_trades = get_open_trades()
        self.agent_state = get_agent_state()
        
        # Load closed trades for historical risk calculation
        conn = get_connection()
        rows = conn.execute("""
            SELECT * FROM paper_trades 
            WHERE status != 'OPEN' 
            AND pnl IS NOT NULL
            ORDER BY entry_time DESC
            LIMIT 100
        """).fetchall()
        conn.close()
        
        self.closed_trades = [dict(r) for r in rows]
    
    def refresh(self):
        """Reload data from DB."""
        self._load_data()
    
    # ═══════════════════════════════════════════════════════════
    #   VALUE AT RISK (VaR)
    # ═══════════════════════════════════════════════════════════
    
    def value_at_risk(self) -> Dict:
        """
        VaR: Maximum expected loss over a given period at given confidence.
        95% VaR = You won't lose more than X in 95% of days
        99% VaR = You won't lose more than Y in 99% of days
        """
        if len(self.closed_trades) < 10:
            return {
                "has_data": False,
                "message": "Need at least 10 trades for VaR calculation",
            }
        
        # Get daily returns
        daily_returns = self._get_daily_returns_pct()
        
        if not daily_returns:
            return {"has_data": False}
        
        # Calculate statistics
        mean_return = statistics.mean(daily_returns)
        std_dev = statistics.stdev(daily_returns) if len(daily_returns) > 1 else 0
        
        capital = self.agent_state.get("capital", 100000)
        
        # Parametric VaR (assumes normal distribution)
        var_95_pct = -(mean_return - VAR_CONFIDENCE_95 * std_dev)
        var_99_pct = -(mean_return - VAR_CONFIDENCE_99 * std_dev)
        
        # Historical VaR (empirical)
        sorted_returns = sorted(daily_returns)
        idx_95 = int(len(sorted_returns) * 0.05)
        idx_99 = int(len(sorted_returns) * 0.01)
        
        hist_var_95 = -sorted_returns[idx_95] if idx_95 < len(sorted_returns) else 0
        hist_var_99 = -sorted_returns[idx_99] if idx_99 < len(sorted_returns) else 0
        
        return {
            "has_data": True,
            "parametric": {
                "var_95_pct":  round(var_95_pct, 3),
                "var_99_pct":  round(var_99_pct, 3),
                "var_95_amount": round(capital * var_95_pct / 100, 2),
                "var_99_amount": round(capital * var_99_pct / 100, 2),
            },
            "historical": {
                "var_95_pct":  round(hist_var_95, 3),
                "var_99_pct":  round(hist_var_99, 3),
                "var_95_amount": round(capital * hist_var_95 / 100, 2),
                "var_99_amount": round(capital * hist_var_99 / 100, 2),
            },
            "interpretation": self._interpret_var(var_95_pct),
        }
    
    def _interpret_var(self, var_pct: float) -> str:
        if var_pct < 1:
            return "LOW RISK - Very conservative"
        elif var_pct < 2:
            return "MODERATE RISK - Balanced"
        elif var_pct < 4:
            return "ELEVATED RISK - Aggressive"
        else:
            return "HIGH RISK - Very aggressive, consider reducing size"
    
    # ═══════════════════════════════════════════════════════════
    #   EXPECTED SHORTFALL (CVaR)
    # ═══════════════════════════════════════════════════════════
    
    def expected_shortfall(self) -> Dict:
        """
        Expected Shortfall (CVaR): Average loss in worst-case scenarios.
        Better than VaR because it tells you HOW BAD the tail is.
        """
        if len(self.closed_trades) < 10:
            return {"has_data": False}
        
        daily_returns = self._get_daily_returns_pct()
        if not daily_returns:
            return {"has_data": False}
        
        sorted_returns = sorted(daily_returns)
        
        # 5% worst case
        cutoff_5 = int(len(sorted_returns) * 0.05) + 1
        worst_5 = sorted_returns[:cutoff_5]
        es_95 = -sum(worst_5) / len(worst_5) if worst_5 else 0
        
        # 1% worst case
        cutoff_1 = int(len(sorted_returns) * 0.01) + 1
        worst_1 = sorted_returns[:cutoff_1]
        es_99 = -sum(worst_1) / len(worst_1) if worst_1 else 0
        
        capital = self.agent_state.get("capital", 100000)
        
        return {
            "has_data": True,
            "es_95_pct":    round(es_95, 3),
            "es_99_pct":    round(es_99, 3),
            "es_95_amount": round(capital * es_95 / 100, 2),
            "es_99_amount": round(capital * es_99 / 100, 2),
        }
    
    # ═══════════════════════════════════════════════════════════
    #   SECTOR CONCENTRATION
    # ═══════════════════════════════════════════════════════════
    
    def sector_concentration(self) -> Dict:
        """Analyze exposure by sector."""
        if not self.open_trades:
            return {
                "has_positions": False,
                "sectors": {},
                "concentration_risk": "NONE",
            }
        
        # Group by sector
        sector_exposure = defaultdict(lambda: {
            "trades":     0,
            "investment": 0,
            "symbols":    [],
        })
        
        total_investment = 0
        
        for trade in self.open_trades:
            sector = get_sector(trade["symbol"])
            investment = trade.get("investment", 0)
            
            sector_exposure[sector]["trades"] += 1
            sector_exposure[sector]["investment"] += investment
            sector_exposure[sector]["symbols"].append(
                trade["symbol"].replace(".NS", "")
            )
            
            total_investment += investment
        
        # Calculate percentages
        result = {}
        max_sector_pct = 0
        highest_sector = None
        
        capital = self.agent_state.get("capital", 100000)
        
        for sector, data in sector_exposure.items():
            pct_of_portfolio = (data["investment"] / total_investment * 100) if total_investment > 0 else 0
            pct_of_capital = (data["investment"] / capital * 100) if capital > 0 else 0
            
            if pct_of_capital > max_sector_pct:
                max_sector_pct = pct_of_capital
                highest_sector = sector
            
            result[sector] = {
                "trades":         data["trades"],
                "symbols":        data["symbols"],
                "investment":     round(data["investment"], 2),
                "portfolio_pct":  round(pct_of_portfolio, 2),
                "capital_pct":    round(pct_of_capital, 2),
                "risk_level":     self._sector_risk_level(pct_of_capital),
            }
        
        # Overall concentration risk
        if max_sector_pct >= MAX_SECTOR_PCT:
            concentration_risk = "HIGH"
        elif max_sector_pct >= MAX_SECTOR_PCT * 0.7:
            concentration_risk = "MEDIUM"
        else:
            concentration_risk = "LOW"
        
        return {
            "has_positions":       True,
            "sectors":             result,
            "total_investment":    round(total_investment, 2),
            "highest_sector":      highest_sector,
            "highest_sector_pct":  round(max_sector_pct, 2),
            "concentration_risk":  concentration_risk,
            "sector_count":        len(sector_exposure),
        }
    
    def _sector_risk_level(self, pct: float) -> str:
        if pct >= 30:
            return "HIGH"
        elif pct >= 20:
            return "MEDIUM"
        elif pct >= 10:
            return "LOW"
        else:
            return "MINIMAL"
    
    # ═══════════════════════════════════════════════════════════
    #   PORTFOLIO HEAT (Capital at Risk)
    # ═══════════════════════════════════════════════════════════
    
    def portfolio_heat(self) -> Dict:
        """
        Portfolio Heat: How much of capital is at risk right now.
        Sum of (position risk) across all open trades.
        """
        if not self.open_trades:
            return {
                "has_positions": False,
                "total_at_risk": 0,
                "heat_pct":      0,
            }
        
        capital = self.agent_state.get("capital", 100000)
        total_at_risk = 0
        position_risks = []
        
        for trade in self.open_trades:
            is_long = trade["direction"] == "LONG"
            entry = trade["entry_price"]
            sl = trade.get("trailing_sl") or trade["stop_loss"]
            qty = trade["quantity"]
            
            # Risk = distance to SL × quantity
            if is_long:
                risk_per_share = max(entry - sl, 0)
            else:
                risk_per_share = max(sl - entry, 0)
            
            position_risk = risk_per_share * qty
            total_at_risk += position_risk
            
            position_risks.append({
                "symbol":       trade["symbol"].replace(".NS", ""),
                "trade_id":     trade["id"],
                "direction":    trade["direction"],
                "entry":        entry,
                "current_sl":   sl,
                "quantity":     qty,
                "risk_amount":  round(position_risk, 2),
                "risk_pct":     round((position_risk / capital) * 100, 3),
            })
        
        # Sort by risk
        position_risks.sort(key=lambda x: x["risk_amount"], reverse=True)
        
        heat_pct = (total_at_risk / capital) * 100 if capital > 0 else 0
        
        return {
            "has_positions":   True,
            "total_at_risk":   round(total_at_risk, 2),
            "heat_pct":        round(heat_pct, 3),
            "capital":         capital,
            "positions":       position_risks,
            "heat_level":      self._heat_level(heat_pct),
            "num_positions":   len(self.open_trades),
        }
    
    def _heat_level(self, pct: float) -> str:
        if pct < 3:
            return "COOL - Low risk exposure"
        elif pct < 6:
            return "WARM - Moderate risk"
        elif pct < 10:
            return "HOT - High risk exposure"
        else:
            return "OVERHEATED - Consider reducing positions"
    
    # ═══════════════════════════════════════════════════════════
    #   DIVERSIFICATION SCORE
    # ═══════════════════════════════════════════════════════════
    
    def diversification_score(self) -> Dict:
        """
        Diversification Score (0-100).
        Higher = more diversified.
        """
        if not self.open_trades:
            return {
                "score":         0,
                "level":         "NO_POSITIONS",
                "recommendation": "Add positions to calculate diversification",
            }
        
        # Factor 1: Number of positions (max 30 pts)
        num_positions = len(self.open_trades)
        position_score = min(30, num_positions * 10)
        
        # Factor 2: Sector diversity (max 40 pts)
        sectors = set(get_sector(t["symbol"]) for t in self.open_trades)
        sector_score = min(40, len(sectors) * 15)
        
        # Factor 3: Position size distribution (max 30 pts)
        # Better if positions are similar in size
        investments = [t.get("investment", 0) for t in self.open_trades]
        if len(investments) > 1:
            avg_inv = statistics.mean(investments)
            std_inv = statistics.stdev(investments) if len(investments) > 1 else 0
            cv = (std_inv / avg_inv) if avg_inv > 0 else 0
            # Lower CV = more even distribution
            distribution_score = max(0, 30 * (1 - cv))
        else:
            distribution_score = 0
        
        total_score = position_score + sector_score + distribution_score
        
        # Determine level
        if total_score >= 80:
            level = "EXCELLENT"
        elif total_score >= 60:
            level = "GOOD"
        elif total_score >= 40:
            level = "MODERATE"
        elif total_score >= 20:
            level = "POOR"
        else:
            level = "VERY_POOR"
        
        return {
            "score":            round(total_score, 1),
            "max_score":        100,
            "level":            level,
            "breakdown": {
                "position_count":  round(position_score, 1),
                "sector_diversity": round(sector_score, 1),
                "size_distribution": round(distribution_score, 1),
            },
            "num_positions":    num_positions,
            "num_sectors":      len(sectors),
            "recommendation":   self._diversification_recommendation(total_score),
        }
    
    def _diversification_recommendation(self, score: float) -> str:
        if score < 40:
            return "Add more positions across different sectors to reduce concentration risk"
        elif score < 60:
            return "Diversification improving, consider adding 1-2 more sectors"
        elif score < 80:
            return "Well diversified, maintain current mix"
        else:
            return "Excellent diversification, portfolio is well protected"
    
    # ═══════════════════════════════════════════════════════════
    #   POSITION-LEVEL RISK
    # ═══════════════════════════════════════════════════════════
    
    def position_risk_breakdown(self) -> List[Dict]:
        """Detailed risk analysis per open position."""
        if not self.open_trades:
            return []
        
        capital = self.agent_state.get("capital", 100000)
        breakdown = []
        
        for trade in self.open_trades:
            is_long = trade["direction"] == "LONG"
            entry = trade["entry_price"]
            current = trade.get("current_price") or entry
            sl = trade.get("trailing_sl") or trade["stop_loss"]
            target = trade.get("target_2", entry)
            qty = trade["quantity"]
            
            # Risk metrics
            if is_long:
                risk_per_share = max(entry - sl, 0)
                reward_per_share = max(target - entry, 0)
                current_pnl_per_share = current - entry
            else:
                risk_per_share = max(sl - entry, 0)
                reward_per_share = max(entry - target, 0)
                current_pnl_per_share = entry - current
            
            total_risk = risk_per_share * qty
            total_reward = reward_per_share * qty
            current_pnl = current_pnl_per_share * qty
            
            rr_ratio = (reward_per_share / risk_per_share) if risk_per_share > 0 else 0
            
            # Risk metrics
            risk_pct_of_capital = (total_risk / capital) * 100
            
            # Distance to SL/Target
            if is_long:
                pct_to_sl = ((sl - current) / current) * 100
                pct_to_target = ((target - current) / current) * 100
            else:
                pct_to_sl = ((current - sl) / current) * 100
                pct_to_target = ((current - target) / current) * 100
            
            breakdown.append({
                "trade_id":         trade["id"],
                "symbol":           trade["symbol"].replace(".NS", ""),
                "sector":           get_sector(trade["symbol"]),
                "direction":        trade["direction"],
                "entry":            entry,
                "current":          current,
                "stop_loss":        sl,
                "target":           target,
                "quantity":         qty,
                "investment":       trade.get("investment", 0),
                
                # Risk
                "risk_amount":      round(total_risk, 2),
                "risk_pct":         round(risk_pct_of_capital, 3),
                "reward_amount":    round(total_reward, 2),
                "risk_reward":      round(rr_ratio, 2),
                
                # Current status
                "current_pnl":      round(current_pnl, 2),
                "pct_to_sl":        round(pct_to_sl, 2),
                "pct_to_target":    round(pct_to_target, 2),
                
                # Alerts
                "warnings":         self._position_warnings(trade, current),
            })
        
        # Sort by risk (highest first)
        breakdown.sort(key=lambda x: x["risk_amount"], reverse=True)
        
        return breakdown
    
    def _position_warnings(self, trade: Dict, current: float) -> List[str]:
        """Get warnings for a position."""
        warnings = []
        entry = trade["entry_price"]
        sl = trade.get("trailing_sl") or trade["stop_loss"]
        is_long = trade["direction"] == "LONG"
        
        # Close to SL warning
        if is_long:
            distance_to_sl = ((current - sl) / current) * 100
        else:
            distance_to_sl = ((sl - current) / current) * 100
        
        if distance_to_sl < 1:
            warnings.append("VERY CLOSE TO STOP LOSS")
        elif distance_to_sl < 2:
            warnings.append("Close to stop loss")
        
        # Losing position
        if is_long and current < entry:
            loss_pct = ((entry - current) / entry) * 100
            if loss_pct > 3:
                warnings.append(f"Down {loss_pct:.1f}%")
        elif not is_long and current > entry:
            loss_pct = ((current - entry) / entry) * 100
            if loss_pct > 3:
                warnings.append(f"Down {loss_pct:.1f}%")
        
        return warnings
    
    # ═══════════════════════════════════════════════════════════
    #   STRESS TEST
    # ═══════════════════════════════════════════════════════════
    
    def stress_test(self) -> Dict:
        """
        Stress test scenarios:
        - Market crash (-5%, -10%)
        - Sector shock (-15%)
        - Individual stock crash (-20%)
        """
        if not self.open_trades:
            return {"has_positions": False}
        
        capital = self.agent_state.get("capital", 100000)
        
        scenarios = {}
        
        # Scenario 1: Market crash -5%
        crash_5_loss = 0
        for trade in self.open_trades:
            entry = trade["entry_price"]
            new_price = entry * 0.95  # Down 5%
            
            if trade["direction"] == "LONG":
                loss = (new_price - entry) * trade["quantity"]
            else:
                loss = (entry - new_price) * trade["quantity"]
            
            crash_5_loss += loss
        
        scenarios["market_crash_5pct"] = {
            "loss":     round(crash_5_loss, 2),
            "loss_pct": round((crash_5_loss / capital) * 100, 2),
            "impact":   "MODERATE",
        }
        
        # Scenario 2: Market crash -10%
        crash_10_loss = crash_5_loss * 2
        scenarios["market_crash_10pct"] = {
            "loss":     round(crash_10_loss, 2),
            "loss_pct": round((crash_10_loss / capital) * 100, 2),
            "impact":   "SEVERE",
        }
        
        # Scenario 3: All SLs hit simultaneously
        all_sl_loss = 0
        for trade in self.open_trades:
            entry = trade["entry_price"]
            sl = trade.get("trailing_sl") or trade["stop_loss"]
            
            if trade["direction"] == "LONG":
                loss = (sl - entry) * trade["quantity"]
            else:
                loss = (entry - sl) * trade["quantity"]
            
            all_sl_loss += loss
        
        scenarios["all_sl_hit"] = {
            "loss":     round(all_sl_loss, 2),
            "loss_pct": round((all_sl_loss / capital) * 100, 2),
            "impact":   "PLANNED_MAX",
            "note":     "Maximum planned loss if all SLs hit",
        }
        
        # Scenario 4: Sector crash (-15%)
        # Find largest sector
        sector_exposure = defaultdict(float)
        for trade in self.open_trades:
            sector = get_sector(trade["symbol"])
            sector_exposure[sector] += trade.get("investment", 0)
        
        largest_sector = max(sector_exposure.items(), key=lambda x: x[1]) if sector_exposure else (None, 0)
        
        if largest_sector[0]:
            sector_crash_loss = 0
            for trade in self.open_trades:
                if get_sector(trade["symbol"]) == largest_sector[0]:
                    entry = trade["entry_price"]
                    new_price = entry * 0.85  # Down 15%
                    
                    if trade["direction"] == "LONG":
                        loss = (new_price - entry) * trade["quantity"]
                    else:
                        loss = (entry - new_price) * trade["quantity"]
                    
                    sector_crash_loss += loss
            
            scenarios["sector_crash"] = {
                "sector":   largest_sector[0],
                "loss":     round(sector_crash_loss, 2),
                "loss_pct": round((sector_crash_loss / capital) * 100, 2),
                "impact":   "HIGH",
            }
        
        return {
            "has_positions": True,
            "capital":       capital,
            "scenarios":     scenarios,
        }
    
    # ═══════════════════════════════════════════════════════════
    #   RISK SCORE (OVERALL)
    # ═══════════════════════════════════════════════════════════
    
    def overall_risk_score(self) -> Dict:
        """
        Overall portfolio risk score (0-100).
        Lower is safer.
        """
        score = 0
        factors = {}
        
        # Factor 1: Portfolio heat (max 30 pts)
        heat = self.portfolio_heat()
        if heat.get("has_positions"):
            heat_pct = heat["heat_pct"]
            heat_score = min(30, heat_pct * 3)  # 10% heat = 30 pts
            score += heat_score
            factors["portfolio_heat"] = round(heat_score, 1)
        
        # Factor 2: Sector concentration (max 25 pts)
        concentration = self.sector_concentration()
        if concentration.get("has_positions"):
            conc_pct = concentration["highest_sector_pct"]
            conc_score = min(25, (conc_pct / 40) * 25)
            score += conc_score
            factors["sector_concentration"] = round(conc_score, 1)
        
        # Factor 3: Diversification inverse (max 20 pts)
        div = self.diversification_score()
        div_score = max(0, 20 - (div["score"] / 5))
        score += div_score
        factors["diversification_inverse"] = round(div_score, 1)
        
        # Factor 4: Number of positions vs limit (max 15 pts)
        num_pos = len(self.open_trades)
        # More positions = more risk (up to max 3)
        pos_score = min(15, num_pos * 5)
        score += pos_score
        factors["position_count"] = round(pos_score, 1)
        
        # Factor 5: Recent drawdown (max 10 pts)
        # Check if we're in a drawdown
        capital = self.agent_state.get("capital", 100000)
        starting = self.agent_state.get("starting_capital", 100000)
        if capital < starting:
            dd_pct = ((starting - capital) / starting) * 100
            dd_score = min(10, dd_pct * 2)
            score += dd_score
            factors["current_drawdown"] = round(dd_score, 1)
        
        # Determine level
        if score < 20:
            level = "LOW"
            color = "green"
        elif score < 40:
            level = "MODERATE"
            color = "yellow"
        elif score < 60:
            level = "HIGH"
            color = "orange"
        else:
            level = "CRITICAL"
            color = "red"
        
        return {
            "score":     round(score, 1),
            "max_score": 100,
            "level":     level,
            "color":     color,
            "factors":   factors,
            "recommendation": self._risk_recommendation(score),
        }
    
    def _risk_recommendation(self, score: float) -> str:
        if score < 20:
            return "Portfolio is well-protected. Continue normal trading."
        elif score < 40:
            return "Moderate risk. Monitor positions, avoid adding correlated trades."
        elif score < 60:
            return "High risk. Consider reducing position sizes or exposure."
        else:
            return "CRITICAL risk. Close some positions immediately."
    
    # ═══════════════════════════════════════════════════════════
    #   HELPER
    # ═══════════════════════════════════════════════════════════
    
    def _get_daily_returns_pct(self) -> List[float]:
        """Get daily returns for VaR calculation."""
        daily_pnl = defaultdict(float)
        
        for trade in self.closed_trades:
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
        
        starting_capital = 100000
        returns = []
        current_capital = starting_capital
        
        for day in sorted(daily_pnl.keys()):
            pnl = daily_pnl[day]
            return_pct = (pnl / current_capital) * 100 if current_capital > 0 else 0
            returns.append(return_pct)
            current_capital += pnl
        
        return returns
    
    # ═══════════════════════════════════════════════════════════
    #   COMPREHENSIVE REPORT
    # ═══════════════════════════════════════════════════════════
    
    def full_report(self) -> Dict:
        """Complete risk report."""
        return {
            "generated_at":       datetime.now().isoformat(),
            "overall_risk_score": self.overall_risk_score(),
            "portfolio_heat":     self.portfolio_heat(),
            "value_at_risk":      self.value_at_risk(),
            "expected_shortfall": self.expected_shortfall(),
            "sector_concentration": self.sector_concentration(),
            "diversification":    self.diversification_score(),
            "position_risks":     self.position_risk_breakdown(),
            "stress_test":        self.stress_test(),
        }


# ═══════════════════════════════════════════════════════════════
#   GLOBAL INSTANCE
# ═══════════════════════════════════════════════════════════════

def get_risk_analytics() -> RiskAnalytics:
    """Get fresh risk analytics instance."""
    return RiskAnalytics()


# ═══════════════════════════════════════════════════════════════
#   Convenience Functions
# ═══════════════════════════════════════════════════════════════

def get_risk_report() -> Dict:
    """Get complete risk report."""
    return get_risk_analytics().full_report()


# ═══════════════════════════════════════════════════════════════
#   Quick Test
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("\n" + "="*60)
    print("RISK ANALYTICS TEST")
    print("="*60)
    
    analytics = get_risk_analytics()
    
    print(f"\n📊 Open Trades:  {len(analytics.open_trades)}")
    print(f"📊 Closed Trades: {len(analytics.closed_trades)}")
    print(f"💰 Capital: ₹{analytics.agent_state.get('capital', 0):,.2f}")
    
    # Overall risk
    print(f"\n🎯 Overall Risk Score:")
    risk = analytics.overall_risk_score()
    print(f"   Score: {risk['score']}/100 [{risk['level']}]")
    print(f"   → {risk['recommendation']}")
    
    # Portfolio heat
    print(f"\n🔥 Portfolio Heat:")
    heat = analytics.portfolio_heat()
    if heat.get("has_positions"):
        print(f"   Total at Risk: ₹{heat['total_at_risk']:,.2f}")
        print(f"   Heat Level: {heat['heat_pct']}%")
        print(f"   Status: {heat['heat_level']}")
    else:
        print(f"   No open positions")
    
    # Sector concentration
    print(f"\n🏢 Sector Concentration:")
    conc = analytics.sector_concentration()
    if conc.get("has_positions"):
        print(f"   Total Sectors: {conc['sector_count']}")
        print(f"   Highest: {conc['highest_sector']} ({conc['highest_sector_pct']}%)")
        print(f"   Risk: {conc['concentration_risk']}")
    else:
        print(f"   No positions")
    
    # Diversification
    print(f"\n🎨 Diversification:")
    div = analytics.diversification_score()
    print(f"   Score: {div['score']}/100 [{div['level']}]")
    print(f"   → {div['recommendation']}")
    
    # VaR
    print(f"\n⚠️  Value at Risk (VaR):")
    var = analytics.value_at_risk()
    if var.get("has_data"):
        p = var["parametric"]
        print(f"   95% VaR: ₹{p['var_95_amount']:,.2f} ({p['var_95_pct']}%)")
        print(f"   99% VaR: ₹{p['var_99_amount']:,.2f} ({p['var_99_pct']}%)")
        print(f"   → {var['interpretation']}")
    else:
        print(f"   {var.get('message', 'Not enough data')}")
    
    # Stress test
    print(f"\n💥 Stress Test:")
    stress = analytics.stress_test()
    if stress.get("has_positions"):
        for name, data in stress["scenarios"].items():
            print(f"   {name}: ₹{data['loss']:,.2f} ({data['loss_pct']}%)")
    else:
        print(f"   No positions to test")
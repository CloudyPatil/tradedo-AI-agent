# E:\tradedo\app\backend\agent\news_exit.py

"""
NEWS-BASED EXIT TRIGGER
Monitors breaking news for open trades.
Auto-exits on major negative news.

Runs every 5 minutes during market hours.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import logging
import json
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor

from database.db import get_open_trades, get_trade_by_id
from data_pipeline.news_data import fetch_rss_news
from data_pipeline.sentiment import analyze_sentiment
from data_pipeline.nse_data import fetch_announcements

logger = logging.getLogger("tradedo.news_exit")


# ═══════════════════════════════════════════════════════════════
#   CONFIG
# ═══════════════════════════════════════════════════════════════

# Sentiment thresholds for emergency exit
CRITICAL_NEGATIVE_SCORE = -0.6    # Very negative sentiment
MODERATE_NEGATIVE_SCORE = -0.4    # Moderately negative

# High-impact keywords (auto-trigger exit regardless of sentiment)
CRITICAL_KEYWORDS = [
    # Regulatory
    "sebi investigation", "sebi order", "sebi penalty",
    "sebi probe", "regulatory action",
    
    # Legal
    "court case", "lawsuit filed", "class action",
    "supreme court verdict", "ruling against",
    
    # Financial issues
    "fraud detected", "accounting fraud", "financial fraud",
    "insider trading", "money laundering", "raid",
    "search operation", "arrest", "arrested",
    
    # Corporate crisis
    "ceo resigned", "cfo resigned", "board resignation",
    "auditor resigned", "chairman quits",
    "major layoffs", "plant shutdown", "operations halted",
    
    # Downgrades
    "credit rating downgrade", "rating downgraded",
    "outlook negative", "junk status",
    
    # Business failure
    "bankruptcy filed", "insolvency", "liquidation",
    "delisting", "trading suspended",
    
    # Governance
    "governance concerns", "misappropriation",
    "profit warning", "guidance cut",
]

# Keywords that suggest positive news (don't exit on these)
POSITIVE_OVERRIDE_KEYWORDS = [
    "acquires", "acquired", "merger approved",
    "record profit", "best quarter", "beats estimates",
    "upgrade", "buy rating", "target raised",
    "special dividend", "bonus issue", "buyback",
]


# ═══════════════════════════════════════════════════════════════
#   NEWS EXIT ANALYZER
# ═══════════════════════════════════════════════════════════════

class NewsExitAnalyzer:
    """Analyzes news for emergency exit signals."""
    
    def __init__(self):
        self.stats = {
            "trades_analyzed":   0,
            "news_checked":      0,
            "exits_triggered":   0,
            "critical_alerts":   0,
            "false_alarms":      0,
        }
    
    def check_all_open_trades(self) -> Dict:
        """
        Main entry point - check news for all open trades.
        Returns actions taken.
        """
        open_trades = get_open_trades()
        
        if not open_trades:
            return {
                "status":  "NO_TRADES",
                "message": "No open trades to monitor",
            }
        
        logger.info(f"📰 News check for {len(open_trades)} open trades...")
        
        # Check each trade in parallel
        exits_needed = []
        
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = {
                executor.submit(self._check_single_trade, trade): trade 
                for trade in open_trades
            }
            
            for future in futures:
                try:
                    result = future.result(timeout=60)
                    if result and result.get("should_exit"):
                        exits_needed.append(result)
                except Exception as e:
                    logger.error(f"News check failed: {e}")
        
        # Execute exits
        actions_taken = []
        for exit_info in exits_needed:
            action = self._execute_emergency_exit(exit_info)
            if action:
                actions_taken.append(action)
        
        return {
            "status":         "OK",
            "trades_checked": len(open_trades),
            "exits_needed":   len(exits_needed),
            "exits_executed": len(actions_taken),
            "actions":        actions_taken,
            "stats":          self.stats,
        }
    
    # ═══════════════════════════════════════════════════════════
    #   ANALYZE SINGLE TRADE
    # ═══════════════════════════════════════════════════════════
    
    def _check_single_trade(self, trade: Dict) -> Optional[Dict]:
        """
        Check news for one trade. Determine if exit needed.
        """
        symbol = trade["symbol"]
        clean_symbol = symbol.replace(".NS", "").replace(".BO", "")
        
        # Get entry time - only care about news AFTER entry
        entry_time_str = trade.get("entry_time", "")
        try:
            entry_time = datetime.fromisoformat(
                entry_time_str.replace("Z", "+00:00")
            )
            if entry_time.tzinfo:
                entry_time = entry_time.replace(tzinfo=None)
        except:
            entry_time = datetime.now() - timedelta(hours=1)
        
        self.stats["trades_analyzed"] += 1
        
        # ── Fetch recent news ────────────────────────────────
        articles = fetch_rss_news(clean_symbol, max_articles=8)
        
        # Filter to only news after entry
        recent_articles = []
        for article in articles:
            pub_str = article.get("published", "")
            try:
                # Try to parse various date formats
                pub_time = datetime.strptime(
                    pub_str[:25], "%a, %d %b %Y %H:%M:%S"
                )
                if pub_time > entry_time - timedelta(minutes=30):
                    recent_articles.append(article)
            except:
                # If can't parse, include it to be safe
                recent_articles.append(article)
        
        self.stats["news_checked"] += len(recent_articles)
        
        if not recent_articles:
            return None
        
        # ── Check for critical keywords first (fast) ─────────
        critical_alert = self._check_critical_keywords(recent_articles)
        
        if critical_alert:
            self.stats["critical_alerts"] += 1
            return {
                "should_exit":  True,
                "trade":        trade,
                "reason":       "CRITICAL_NEWS",
                "trigger":      critical_alert["keyword"],
                "article":      critical_alert["article"],
                "urgency":      "IMMEDIATE",
            }
        
        # ── Full sentiment analysis (slower, LLM) ────────────
        sentiment = analyze_sentiment(recent_articles)
        
        # ── Also check NSE announcements ─────────────────────
        announcements = fetch_announcements(symbol, days_back=1)
        negative_announcements = [
            a for a in announcements 
            if a.get("impact") == "HIGH_NEGATIVE"
        ]
        
        # ── Determine action ─────────────────────────────────
        return self._determine_exit_action(
            trade, sentiment, recent_articles, negative_announcements
        )
    
    # ═══════════════════════════════════════════════════════════
    #   CRITICAL KEYWORD CHECKER
    # ═══════════════════════════════════════════════════════════
    
    def _check_critical_keywords(self, articles: List[Dict]) -> Optional[Dict]:
        """
        Fast keyword scan for critical news.
        Returns dict if critical keyword found.
        """
        for article in articles:
            title = article.get("title", "").lower()
            summary = article.get("summary", "").lower()
            full_text = f"{title} {summary}"
            
            # Check for positive override first
            has_positive = any(pos in full_text for pos in POSITIVE_OVERRIDE_KEYWORDS)
            if has_positive:
                continue
            
            # Check for critical keywords
            for keyword in CRITICAL_KEYWORDS:
                if keyword in full_text:
                    return {
                        "keyword":  keyword,
                        "article":  article,
                    }
        
        return None
    
    # ═══════════════════════════════════════════════════════════
    #   DETERMINE EXIT ACTION
    # ═══════════════════════════════════════════════════════════
    
    def _determine_exit_action(
        self, trade: Dict, sentiment: Dict,
        articles: List[Dict], announcements: List[Dict]
    ) -> Optional[Dict]:
        """Decide if trade should be exited based on all signals."""
        
        sentiment_score = sentiment.get("score", 0)
        sentiment_label = sentiment.get("label", "NEUTRAL")
        risk_flag = sentiment.get("risk_flag", False)
        
        is_long = trade["direction"] == "LONG"
        
        # For LONG positions - exit on negative news
        # For SHORT positions - exit on positive news
        
        if is_long:
            # ── CRITICAL: Very negative sentiment ────────────
            if sentiment_score <= CRITICAL_NEGATIVE_SCORE:
                return {
                    "should_exit": True,
                    "trade":       trade,
                    "reason":      "VERY_NEGATIVE_SENTIMENT",
                    "score":       sentiment_score,
                    "label":       sentiment_label,
                    "urgency":     "HIGH",
                    "sentiment":   sentiment,
                }
            
            # ── NEGATIVE ANNOUNCEMENT from NSE ───────────────
            if announcements:
                return {
                    "should_exit": True,
                    "trade":       trade,
                    "reason":      "NEGATIVE_NSE_ANNOUNCEMENT",
                    "announcement": announcements[0],
                    "urgency":     "HIGH",
                }
            
            # ── Moderate negative + risk flag ────────────────
            if sentiment_score <= MODERATE_NEGATIVE_SCORE and risk_flag:
                return {
                    "should_exit": True,
                    "trade":       trade,
                    "reason":      "MODERATE_NEGATIVE_WITH_RISK",
                    "score":       sentiment_score,
                    "urgency":     "MEDIUM",
                    "sentiment":   sentiment,
                }
        
        else:  # SHORT position
            # ── CRITICAL: Very positive sentiment (for shorts) ─
            if sentiment_score >= abs(CRITICAL_NEGATIVE_SCORE):
                return {
                    "should_exit": True,
                    "trade":       trade,
                    "reason":      "VERY_POSITIVE_SENTIMENT_FOR_SHORT",
                    "score":       sentiment_score,
                    "urgency":     "HIGH",
                    "sentiment":   sentiment,
                }
        
        # No exit needed
        return None
    
    # ═══════════════════════════════════════════════════════════
    #   EXECUTE EMERGENCY EXIT
    # ═══════════════════════════════════════════════════════════
    
    def _execute_emergency_exit(self, exit_info: Dict) -> Optional[Dict]:
        """Execute the emergency exit."""
        trade = exit_info["trade"]
        reason = exit_info["reason"]
        urgency = exit_info.get("urgency", "MEDIUM")
        
        # Get current price
        from data_pipeline.price_provider import get_price_provider
        provider = get_price_provider()
        price_data = provider.get_ltp(trade["symbol"])
        
        if not price_data:
            logger.error(f"Could not fetch price for emergency exit: {trade['symbol']}")
            return None
        
        current_price = price_data["last_price"]
        
        # Execute close via live_monitor's close function
        from database.db import close_trade
        from agent.paper_executor import PaperExecutor
        
        close_reason = f"NEWS_EXIT_{reason}"
        
        try:
            close_trade(trade["id"], current_price, close_reason)
            
            # Release capital
            executor = PaperExecutor()
            executor._release_capital(trade["investment"])
            
            # Update stats
            self.stats["exits_triggered"] += 1
            
            # Get updated trade for alert
            updated_trade = get_trade_by_id(trade["id"])
            pnl = updated_trade.get("pnl", 0)
            
            # Send urgent alert
            self._send_urgent_alert(updated_trade, exit_info, current_price)
            
            logger.warning(
                f"🚨 EMERGENCY EXIT: Trade {trade['id']} | "
                f"{trade['symbol']} @ ₹{current_price} | "
                f"Reason: {reason} | P&L: ₹{pnl}"
            )
            
            return {
                "action":     "EMERGENCY_EXIT",
                "trade_id":   trade["id"],
                "symbol":     trade["symbol"],
                "price":      current_price,
                "pnl":        pnl,
                "reason":     close_reason,
                "urgency":    urgency,
                "trigger":    exit_info.get("trigger") or exit_info.get("reason"),
            }
        
        except Exception as e:
            logger.error(f"Emergency exit failed: {e}")
            return None
    
    # ═══════════════════════════════════════════════════════════
    #   TELEGRAM ALERT
    # ═══════════════════════════════════════════════════════════
    
    def _send_urgent_alert(
        self, trade: Dict, exit_info: Dict, exit_price: float
    ):
        """Send urgent Telegram alert for emergency exit."""
        try:
            import asyncio
            from utils.telegram_bot import send_message
            
            symbol = trade["symbol"].replace(".NS", "")
            pnl = trade.get("pnl", 0)
            pnl_emoji = "📈" if pnl > 0 else "📉"
            urgency = exit_info.get("urgency", "MEDIUM")
            
            urgency_emoji = {
                "IMMEDIATE": "🚨🚨🚨",
                "HIGH":      "🚨🚨",
                "MEDIUM":    "🚨",
            }.get(urgency, "⚠️")
            
            msg = f"{urgency_emoji} <b>EMERGENCY NEWS EXIT #{trade['id']}</b>\n\n"
            msg += f"📌 <b>{symbol}</b>\n"
            msg += f"💰 Exit: ₹{exit_price:,.2f}\n"
            msg += f"{pnl_emoji} P&L: ₹{pnl:,.2f}\n\n"
            
            msg += f"⚠️ <b>Reason:</b> {exit_info['reason']}\n"
            
            # Add specific trigger info
            if exit_info.get("trigger"):
                msg += f"🎯 Trigger: {exit_info['trigger']}\n"
            
            if exit_info.get("article"):
                title = exit_info["article"].get("title", "")[:120]
                msg += f"\n📰 <i>{title}</i>\n"
            
            if exit_info.get("announcement"):
                subject = exit_info["announcement"].get("subject", "")[:120]
                msg += f"\n📢 NSE: <i>{subject}</i>\n"
            
            if exit_info.get("sentiment"):
                sent = exit_info["sentiment"]
                msg += f"\n📊 Sentiment: {sent.get('label')} ({sent.get('score')})\n"
                if sent.get("reasoning"):
                    msg += f"💭 {sent.get('reasoning')[:150]}"
            
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.create_task(send_message(msg))
                else:
                    loop.run_until_complete(send_message(msg))
            except RuntimeError:
                asyncio.run(send_message(msg))
        
        except Exception as e:
            logger.warning(f"Urgent alert failed: {e}")


# ═══════════════════════════════════════════════════════════════
#   GLOBAL SINGLETON
# ═══════════════════════════════════════════════════════════════

_analyzer: Optional[NewsExitAnalyzer] = None

def get_news_analyzer() -> NewsExitAnalyzer:
    global _analyzer
    if _analyzer is None:
        _analyzer = NewsExitAnalyzer()
    return _analyzer


# ═══════════════════════════════════════════════════════════════
#   Convenience Functions
# ═══════════════════════════════════════════════════════════════

def check_news_for_exits() -> Dict:
    """Main entry - check all open trades for news-based exits."""
    analyzer = get_news_analyzer()
    return analyzer.check_all_open_trades()


async def news_exit_job():
    """Async wrapper for scheduler."""
    result = check_news_for_exits()
    
    if result.get("exits_executed", 0) > 0:
        logger.warning(
            f"🚨 News exit triggered for {result['exits_executed']} trades"
        )
    
    return result


# ═══════════════════════════════════════════════════════════════
#   Quick Test
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("\n" + "="*60)
    print("NEWS EXIT TRIGGER TEST")
    print("="*60)
    
    result = check_news_for_exits()
    
    print(f"\nStatus: {result.get('status')}")
    print(f"Message: {result.get('message', 'N/A')}")
    
    if result.get("status") == "OK":
        print(f"Trades checked: {result.get('trades_checked')}")
        print(f"Exits needed:   {result.get('exits_needed')}")
        print(f"Exits executed: {result.get('exits_executed')}")
        
        if result.get("actions"):
            print("\n🚨 Emergency Exits:")
            for action in result["actions"]:
                print(f"   {action}")
        
        print(f"\n📊 Stats:")
        for k, v in result.get("stats", {}).items():
            print(f"   {k}: {v}")
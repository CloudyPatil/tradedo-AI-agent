# E:\tradedo\app\backend\utils\scheduler.py

import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

logger = logging.getLogger("tradedo.scheduler")

scheduler = AsyncIOScheduler(timezone="Asia/Kolkata")


# ─── Confidence Threshold for Auto-Alerts ─────────────────────
STRONG_SIGNAL_THRESHOLD = 70   # Only alert if confidence >= 70%
COMPOSITE_THRESHOLD     = 65   # AND composite score >= 65


# ─── Job Functions ────────────────────────────────────────────

async def auto_refresh_watchlist():
    """Refresh predictions and send alerts for strong signals."""
    from database.db import get_watchlist, save_prediction
    from ml.engine import predict_full
    from utils.telegram_bot import send_signal_alert

    logger.info("⏰ Auto-refresh + alert check...")

    symbols = get_watchlist()
    updated = 0
    alerted = 0

    for symbol in symbols:
        try:
            # Get FULL prediction with sentiment + trade plan
            result = predict_full(symbol, mode="swing")
            save_prediction(result)
            updated += 1

            # Check if it's a STRONG signal → send alert
            confidence = result.get("confidence_pct", 0)
            composite  = result.get("composite", {}).get("composite_score", 0)
            signal     = result.get("signal")

            if (signal in ("BUY", "SELL") and 
                confidence >= STRONG_SIGNAL_THRESHOLD and
                composite >= COMPOSITE_THRESHOLD):
                
                # Check if we already alerted this symbol today
                if not _was_alerted_recently(symbol):
                    await send_signal_alert(result)
                    _mark_alerted(symbol)
                    alerted += 1
                    logger.info(f"  📱 Alert sent for {symbol}")

        except Exception as e:
            logger.warning(f"Refresh failed for {symbol}: {e}")

    logger.info(f"✅ Refresh done: {updated}/{len(symbols)} updated, {alerted} alerts sent")


async def morning_summary():
    """
    Runs at 9:00 AM IST.
    Scan watchlist and send morning summary.
    """
    from database.db import get_watchlist
    from ml.engine import predict
    from utils.telegram_bot import send_daily_summary

    logger.info("🌅 Morning summary starting...")

    symbols = get_watchlist()
    predictions = []

    for symbol in symbols:
        try:
            p = predict(symbol, mode="swing")
            predictions.append(p)
        except Exception as e:
            logger.warning(f"Failed for {symbol}: {e}")

    if predictions:
        await send_daily_summary(predictions)
        logger.info(f"✅ Morning summary sent ({len(predictions)} stocks)")

    # Clear alert history for new day
    _clear_alert_history()


async def eod_summary():
    """Runs at 3:45 PM IST — end of day."""
    from utils.telegram_bot import send_message
    logger.info("🌆 EOD summary...")
    
    await send_message(
        "🌆 <b>Market Closed</b>\n\n"
        "Check dashboard for today's performance.\n"
        "See you tomorrow! 👋",
        silent=True
    )


async def live_monitor_job():
    """Monitor open paper trades every minute."""
    from agent.live_monitor import monitor_open_trades
    try:
        result = await monitor_open_trades()
        # Only log if actions taken (avoid spam)
        if result.get("actions_taken", 0) > 0:
            logger.info(f"⚡ Live monitor: {result['actions_taken']} actions")
    except Exception as e:
        logger.error(f"Live monitor failed: {e}", exc_info=True)


async def news_exit_check():
    """Check news for emergency exits every 5 mins."""
    from agent.news_exit import news_exit_job
    try:
        result = await news_exit_job()
        if result.get("exits_executed", 0) > 0:
            logger.warning(
                f"🚨 News-based exits: {result['exits_executed']} trades closed"
            )
    except Exception as e:
        logger.error(f"News exit check failed: {e}", exc_info=True)


async def websocket_sync_job():
    """Sync WebSocket subscriptions periodically."""
    try:
        from agent.websocket_stream import sync_subscriptions, get_streamer
        
        streamer = get_streamer()
        if streamer.is_running:
            result = sync_subscriptions()
            if result.get("added") or result.get("removed"):
                logger.info(
                    f"📡 WebSocket sync: +{len(result.get('added',[]))} "
                    f"-{len(result.get('removed',[]))}"
                )
    except Exception as e:
        logger.debug(f"WebSocket sync failed: {e}")


# ─── Alert Deduplication (in-memory) ──────────────────────────
_alerted_today: set = set()

def _was_alerted_recently(symbol: str) -> bool:
    return symbol in _alerted_today

def _mark_alerted(symbol: str):
    _alerted_today.add(symbol)

def _clear_alert_history():
    global _alerted_today
    _alerted_today = set()


# ─── Scheduler Setup ──────────────────────────────────────────

def setup_scheduler():
    """Register all scheduled jobs."""

    async def refresh_cross_asset():
        """Refresh cross-asset data (Nifty, VIX, etc.) once per day."""
        from data_pipeline.cross_asset import refresh_cross_asset_data
        logger.info("🔄 Daily cross-asset refresh...")
        refresh_cross_asset_data()

    async def morning_agent_scan():
        """
        Runs at 8:45 AM IST (before market opens).
        Scans full universe and sends top picks via Telegram.
        """
        from agent.scanner import scan_market
        from database.db import save_scan_result, clear_todays_scans
        from utils.telegram_bot import send_message
        
        logger.info("🌅 Morning agent scan starting...")
        
        try:
            clear_todays_scans()
            result = scan_market(tier="tier1", mode="intraday")
            
            # Save to DB
            for candidate in result["candidates"]:
                save_scan_result(candidate, is_selected=True)
            
            # Format Telegram message
            stats = result["stats"]
            candidates = result["candidates"]
            
            msg = "🌅 <b>Morning Market Scan Complete</b>\n\n"
            msg += f"📊 Scanned: {stats['total_scanned']} stocks in {stats['scan_time_sec']}s\n"
            msg += f"🎯 Regime: <b>{stats['market_regime']}</b>\n"
            msg += f"🏆 Found: <b>{stats['candidates_found']}</b> candidates\n\n"
        
            if candidates:
                msg += "<b>Top Intraday Picks:</b>\n"
                for i, c in enumerate(candidates[:5], 1):
                    symbol = c["symbol"].replace(".NS", "")
                    emoji = "🟢" if c["signal"] == "BUY" else "🔴"
                    msg += (
                        f"{i}. {emoji} <b>{symbol}</b>  "
                        f"{c['signal']}  "
                        f"Score: <b>{c['composite_score']}</b>  "
                        f"₹{c['current_price']:,.0f}\n"
                    )
            else:
                msg += "🟡 No strong candidates today.\n"
            
            msg += f"\n📱 <a href='http://localhost:3000/agent'>View Agent Dashboard</a>"
            
            await send_message(msg)
            logger.info(f"✅ Morning scan sent — {len(candidates)} candidates")
        
        except Exception as e:
            logger.error(f"Morning scan failed: {e}", exc_info=True)


    # 1. Cross-Asset Refresh at 8:30 AM (Mon-Fri)
    scheduler.add_job(
        refresh_cross_asset,
        CronTrigger(
            hour=8, minute=30,     # Before market opens
            day_of_week="mon-fri",
            timezone="Asia/Kolkata"
        ),
        id="cross_asset_refresh",
        name="Daily Cross-Asset Data Refresh",
        replace_existing=True,
    )

    # 2. Morning Agent Scan at 8:45 AM (Mon-Fri)
    scheduler.add_job(
        morning_agent_scan,
        CronTrigger(
            hour=8, minute=45,   # 8:45 AM (30 mins before market)
            day_of_week="mon-fri",
            timezone="Asia/Kolkata"
        ),
        id="morning_agent_scan",
        name="Morning Agent Scan",
        replace_existing=True,
    )
    
    # 3. Morning summary at 9:00 AM (Mon-Fri)
    scheduler.add_job(
        morning_summary,
        CronTrigger(
            hour=9, minute=0,
            day_of_week="mon-fri",
            timezone="Asia/Kolkata"
        ),
        id="morning_summary",
        name="Morning Summary",
        replace_existing=True,
    )

    # 4. Auto refresh every 15 mins during market (Mon-Fri)
    scheduler.add_job(
        auto_refresh_watchlist,
        CronTrigger(
            hour="9-15",
            minute="*/15",
            day_of_week="mon-fri",
            timezone="Asia/Kolkata"
        ),
        id="watchlist_refresh",
        name="Watchlist Refresh + Alerts",
        replace_existing=True,
    )

    # 5. EOD at 3:45 PM
    scheduler.add_job(
        eod_summary,
        CronTrigger(
            hour=15, minute=45,
            day_of_week="mon-fri",
            timezone="Asia/Kolkata"
        ),
        id="eod_summary",
        name="EOD Summary",
        replace_existing=True,
    )

    scheduler.add_job(
        live_monitor_job,
        CronTrigger(
            hour="9-15",
            minute="*",           # Every minute
            day_of_week="mon-fri",
            timezone="Asia/Kolkata"
        ),
        id="live_monitor",
        name="Live Trade Monitor",
        replace_existing=True,
    )

    scheduler.add_job(
    news_exit_check,
    CronTrigger(
        hour="9-15",
        minute="*/5",           # Every 5 minutes
        day_of_week="mon-fri",
        timezone="Asia/Kolkata"
    ),
    id="news_exit_check",
    name="News-Based Exit Trigger",
    replace_existing=True,
    )

    scheduler.add_job(
    websocket_sync_job,
    CronTrigger(
        hour="9-15",
        minute="*/2",       # Every 2 minutes
        day_of_week="mon-fri",
        timezone="Asia/Kolkata"
    ),
    id="websocket_sync",
    name="WebSocket Subscription Sync",
    replace_existing=True,
    )


    logger.info("✅ Scheduler configured with 7 jobs")
    return scheduler


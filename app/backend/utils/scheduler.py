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
    
    # Morning summary at 9:00 AM (Mon-Fri)
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

    # Auto refresh every 15 mins during market (Mon-Fri)
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

    # EOD at 3:45 PM
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

    logger.info("✅ Scheduler configured with 3 jobs")
    return scheduler
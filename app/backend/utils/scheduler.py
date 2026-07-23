# E:\tradedo\app\backend\utils\scheduler.py

import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

logger = logging.getLogger("tradedo.scheduler")

scheduler = AsyncIOScheduler(timezone="Asia/Kolkata")


# ─── Scheduled Jobs ───────────────────────────────────────────

async def auto_refresh_watchlist():
    """
    Runs every 15 minutes during market hours.
    Refreshes predictions for all watchlist stocks.
    Saves to database automatically.
    """
    from database.db import get_watchlist, save_prediction
    from ml.engine import predict

    logger.info("⏰ Auto-refresh: Updating watchlist predictions...")

    symbols = get_watchlist()
    updated = 0

    for symbol in symbols:
        try:
            result = predict(symbol, mode="swing")
            save_prediction(result)
            updated += 1
        except Exception as e:
            logger.warning(f"Auto-refresh failed for {symbol}: {e}")

    logger.info(f"✅ Auto-refresh complete: {updated}/{len(symbols)} updated")


async def morning_market_check():
    """
    Runs at 9:00 AM IST.
    Pre-market check — fetches fresh data + predictions.
    """
    logger.info("🌅 Morning market check starting...")
    await auto_refresh_watchlist()
    logger.info("✅ Morning check complete — market opens in 15 mins")


async def eod_summary():
    """
    Runs at 3:45 PM IST.
    End of day summary + cleanup.
    """
    logger.info("🌆 EOD summary running...")
    # TODO: Generate daily report (Phase 3)
    logger.info("✅ EOD summary complete")


# ─── Scheduler Setup ──────────────────────────────────────────

def setup_scheduler():
    """
    Register all scheduled jobs.
    Called from main.py on startup.
    """
    # Morning check at 9:00 AM IST (Mon-Fri)
    scheduler.add_job(
        morning_market_check,
        CronTrigger(
            hour=9, minute=0,
            day_of_week="mon-fri",
            timezone="Asia/Kolkata"
        ),
        id="morning_check",
        name="Morning Market Check",
        replace_existing=True,
    )

    # Auto refresh every 15 mins (9:15 AM to 3:30 PM, Mon-Fri)
    scheduler.add_job(
        auto_refresh_watchlist,
        CronTrigger(
            hour="9-15",
            minute="*/15",
            day_of_week="mon-fri",
            timezone="Asia/Kolkata"
        ),
        id="watchlist_refresh",
        name="Watchlist Auto Refresh",
        replace_existing=True,
    )

    # EOD summary at 3:45 PM IST
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
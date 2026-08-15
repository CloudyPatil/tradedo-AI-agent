# E:\tradedo\app\backend\utils\scheduler.py

import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

logger = logging.getLogger("tradedo.scheduler")

scheduler = AsyncIOScheduler(timezone="Asia/Kolkata")


# ═══════════════════════════════════════════════════════════════
#   AGENT BRAIN JOBS
# ═══════════════════════════════════════════════════════════════

async def scheduled_premarket_prep():
    """8:30 AM - Premarket preparation."""
    from agent.brain import job_premarket_prep
    try:
        await job_premarket_prep()
    except Exception as e:
        logger.error(f"Premarket prep failed: {e}", exc_info=True)


async def scheduled_morning_scan():
    """8:45 AM - Morning market scan."""
    from agent.brain import job_morning_scan
    try:
        await job_morning_scan()
    except Exception as e:
        logger.error(f"Morning scan failed: {e}", exc_info=True)


async def scheduled_market_open_execution():
    """9:15 AM - Execute trades at market open."""
    from agent.brain import job_market_open_execution
    try:
        await job_market_open_execution()
    except Exception as e:
        logger.error(f"Market execution failed: {e}", exc_info=True)


async def scheduled_eod_summary():
    """3:30 PM - End of day summary."""
    from agent.brain import job_eod_summary
    try:
        await job_eod_summary()
    except Exception as e:
        logger.error(f"EOD summary failed: {e}", exc_info=True)


# ═══════════════════════════════════════════════════════════════
#   MONITORING JOBS (from earlier phases)
# ═══════════════════════════════════════════════════════════════

async def live_monitor_job():
    """Monitor open trades every minute."""
    from agent.live_monitor import monitor_open_trades
    try:
        result = await monitor_open_trades()
        if result.get("actions_taken", 0) > 0:
            logger.info(f"⚡ Monitor: {result['actions_taken']} actions")
    except Exception as e:
        logger.error(f"Monitor failed: {e}", exc_info=True)


async def news_exit_check():
    """Check news for emergency exits every 5 mins."""
    from agent.news_exit import news_exit_job
    try:
        result = await news_exit_job()
        if result.get("exits_executed", 0) > 0:
            logger.warning(f"🚨 News exits: {result['exits_executed']}")
    except Exception as e:
        logger.error(f"News exit failed: {e}", exc_info=True)


async def websocket_sync_job():
    """Sync WebSocket subscriptions."""
    try:
        from agent.websocket_stream import sync_subscriptions, get_streamer
        streamer = get_streamer()
        if streamer.is_running:
            result = sync_subscriptions()
            if result.get("added") or result.get("removed"):
                logger.info(f"📡 WS sync: +{len(result.get('added',[]))}")
    except Exception as e:
        logger.debug(f"WS sync failed: {e}")


async def cross_asset_refresh():
    """Refresh cross-asset data."""
    from data_pipeline.cross_asset import refresh_cross_asset_data
    try:
        refresh_cross_asset_data()
    except Exception as e:
        logger.error(f"Cross-asset refresh failed: {e}")


async def youtube_sync_job():
    """Sync YouTube channels every 4 hours."""
    from data_pipeline.youtube_monitor import sync_all_channels
    try:
        logger.info("🎥 Starting YouTube sync...")
        result = sync_all_channels()
        logger.info(f"✅ YouTube sync: {result['videos_added']} videos, {result['transcripts_fetched']} transcripts")
    except Exception as e:
        logger.error(f"YouTube sync failed: {e}", exc_info=True)


async def manual_position_update_job():
    """Update manual position prices every minute."""
    from agent.manual_executor import update_position_prices, check_pending_orders
    try:
        # Update position prices
        update_position_prices()
        # Check pending orders
        check_pending_orders()
    except Exception as e:
        logger.error(f"Manual position update failed: {e}")


# ═══════════════════════════════════════════════════════════════
#   SETUP ALL JOBS
# ═══════════════════════════════════════════════════════════════

def setup_scheduler():
    """Register all scheduled jobs."""
    
    # ─── AGENT BRAIN JOBS ────────────────────────────────────
    
    # 8:30 AM - Premarket prep
    scheduler.add_job(
        scheduled_premarket_prep,
        CronTrigger(
            hour=8, minute=30,
            day_of_week="mon-fri",
            timezone="Asia/Kolkata"
        ),
        id="brain_premarket",
        name="Agent Brain: Premarket Prep",
        replace_existing=True,
    )
    
    # 8:45 AM - Morning scan
    scheduler.add_job(
        scheduled_morning_scan,
        CronTrigger(
            hour=8, minute=45,
            day_of_week="mon-fri",
            timezone="Asia/Kolkata"
        ),
        id="brain_scan",
        name="Agent Brain: Morning Scan",
        replace_existing=True,
    )
    
    # 9:15 AM - Market open execution
    scheduler.add_job(
        scheduled_market_open_execution,
        CronTrigger(
            hour=9, minute=15,
            day_of_week="mon-fri",
            timezone="Asia/Kolkata"
        ),
        id="brain_execution",
        name="Agent Brain: Market Open Execution",
        replace_existing=True,
    )
    
    # 3:30 PM - EOD summary
    scheduler.add_job(
        scheduled_eod_summary,
        CronTrigger(
            hour=15, minute=30,
            day_of_week="mon-fri",
            timezone="Asia/Kolkata"
        ),
        id="brain_eod",
        name="Agent Brain: EOD Summary",
        replace_existing=True,
    )
    
    # ─── MONITORING JOBS ─────────────────────────────────────
    
    # Live monitor - every minute during market
    scheduler.add_job(
        live_monitor_job,
        CronTrigger(
            hour="9-15", minute="*",
            day_of_week="mon-fri",
            timezone="Asia/Kolkata"
        ),
        id="live_monitor",
        name="Live Trade Monitor",
        replace_existing=True,
    )
    
    # News exit - every 5 minutes
    scheduler.add_job(
        news_exit_check,
        CronTrigger(
            hour="9-15", minute="*/5",
            day_of_week="mon-fri",
            timezone="Asia/Kolkata"
        ),
        id="news_exit",
        name="News-Based Exit Checker",
        replace_existing=True,
    )
    
    # WebSocket sync - every 2 minutes
    scheduler.add_job(
        websocket_sync_job,
        CronTrigger(
            hour="9-15", minute="*/2",
            day_of_week="mon-fri",
            timezone="Asia/Kolkata"
        ),
        id="ws_sync",
        name="WebSocket Sync",
        replace_existing=True,
    )
    
    # Cross-asset refresh - once per day
    scheduler.add_job(
        cross_asset_refresh,
        CronTrigger(
            hour=8, minute=15,
            day_of_week="mon-fri",
            timezone="Asia/Kolkata"
        ),
        id="cross_asset_refresh",
        name="Daily Cross-Asset Refresh",
        replace_existing=True,
    )

    scheduler.add_job(
    youtube_sync_job,
    CronTrigger(
        hour="*/4",             # Every 4 hours
        minute=0,
        timezone="Asia/Kolkata"
    ),
    id="youtube_sync",
    name="YouTube Channel Sync",
    replace_existing=True,
    )

    scheduler.add_job(
    manual_position_update_job,
    CronTrigger(
        hour="9-15", minute="*",
        day_of_week="mon-fri",
        timezone="Asia/Kolkata"
    ),
    id="manual_positions_update",
    name="Manual Positions & Orders Update",
    replace_existing=True,
    )

    
    logger.info("✅ Scheduler configured with all agent jobs")
    return scheduler
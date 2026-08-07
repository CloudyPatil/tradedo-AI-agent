# E:\tradedo\app\backend\api\routes.py

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse
from typing import Optional, List
import logging
from ml.engine import predict, ModelStore

logger = logging.getLogger("tradedo.routes")
router = APIRouter()

# ─── Default Watchlist ────────────────────────────────────────
DEFAULT_WATCHLIST = [
    "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS",
    "INFY.NS",     "TATAMOTORS.NS", "ADANIENT.NS",
    "WIPRO.NS",    "ICICIBANK.NS",  "SBIN.NS",
    "BAJFINANCE.NS"
]

# ─── Routes ───────────────────────────────────────────────────

@router.get("/health")
async def health_check():
    """Simple health check."""
    return {"status": "ok", "service": "TRADEDO API"}


@router.get("/predict/{symbol}")
async def predict_stock(
    symbol: str,
    mode: str = Query(
        default="swing",
        description="'swing' for daily | 'intraday' for 5-min"
    )
):
    """
    Predict stock direction for any NSE stock.

    Examples:
    - /predict/RELIANCE?mode=swing
    - /predict/TCS?mode=intraday
    - /predict/TATAMOTORS.NS?mode=swing
    """
    if mode not in ("swing", "intraday"):
        raise HTTPException(
            status_code=400,
            detail="mode must be 'swing' or 'intraday'"
        )

    try:
        result = predict(symbol, mode=mode)
        return JSONResponse(content=result)

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Prediction error for {symbol}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")


@router.get("/watchlist")
async def get_watchlist(
    mode: str = Query(default="swing")
):
    """
    Get predictions for entire default watchlist.
    Returns all stocks with their signals.
    """
    results  = []
    errors   = []

    for symbol in DEFAULT_WATCHLIST:
        try:
            r = predict(symbol, mode=mode)
            results.append(r)
            logger.info(f"  ✅ {symbol}: {r['signal']}")
        except Exception as e:
            errors.append({"symbol": symbol, "error": str(e)})
            logger.warning(f"  ❌ {symbol}: {e}")

    # Sort: BUY first, then HOLD, then SELL
    order = {"BUY": 0, "HOLD": 1, "SELL": 2}
    results.sort(key=lambda x: (order.get(x["signal"], 9), -x["confidence_pct"]))

    return {
        "mode":    mode,
        "count":   len(results),
        "results": results,
        "errors":  errors,
    }


@router.get("/watchlist/custom")
async def get_custom_watchlist(
    symbols: str = Query(
        description="Comma-separated symbols e.g. RELIANCE,TCS,INFY"
    ),
    mode: str = Query(default="swing")
):
    """
    Predict for a custom list of symbols.
    ?symbols=RELIANCE,TCS,INFY&mode=swing
    """
    symbol_list = [s.strip() for s in symbols.split(",") if s.strip()]

    if not symbol_list:
        raise HTTPException(status_code=400, detail="No symbols provided")

    if len(symbol_list) > 20:
        raise HTTPException(
            status_code=400,
            detail="Max 20 symbols per request"
        )

    results = []
    errors  = []

    for symbol in symbol_list:
        try:
            r = predict(symbol, mode=mode)
            results.append(r)
        except Exception as e:
            errors.append({"symbol": symbol, "error": str(e)})

    order = {"BUY": 0, "HOLD": 1, "SELL": 2}
    results.sort(key=lambda x: (order.get(x["signal"], 9), -x["confidence_pct"]))

    return {
        "mode":    mode,
        "count":   len(results),
        "results": results,
        "errors":  errors,
    }


@router.get("/models/status")
async def model_status():
    """Check if models are loaded and ready."""
    swing_loaded    = ModelStore._swing_model is not None
    intraday_loaded = ModelStore._intraday_model is not None

    return {
        "swing_model":    {
            "loaded":   swing_loaded,
            "features": len(ModelStore._swing_features) if swing_loaded else 0,
        },
        "intraday_model": {
            "loaded":   intraday_loaded,
            "features": len(ModelStore._intraday_features) if intraday_loaded else 0,
        },
        "all_ready": swing_loaded and intraday_loaded
    }

# ADD THESE NEW ROUTES to existing routes.py
# (Keep all existing routes, just add these below)

from database.db import (
    save_prediction, get_watchlist as db_get_watchlist,
    add_to_watchlist, remove_from_watchlist,
    get_recent_predictions, init_db
)
from ml.engine import predict_full


@router.get("/predict/full/{symbol}")
async def predict_stock_full(
    symbol: str,
    mode: str = Query(default="swing")
):
    """
    FULL prediction with:
    - ML signal
    - News sentiment
    - Composite score
    - AI reasoning
    - Market regime

    Slower than /predict/ but much more complete.
    Use this for detailed stock analysis.
    """
    if mode not in ("swing", "intraday"):
        raise HTTPException(status_code=400, detail="Invalid mode")

    try:
        result = predict_full(symbol, mode=mode)

        # Save to database (background, don't block response)
        try:
            save_prediction(result)
        except Exception as e:
            logger.warning(f"DB save failed (non-critical): {e}")

        import json

        def make_serializable(obj):
            if isinstance(obj, dict):
                return {k: make_serializable(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [make_serializable(i) for i in obj]
            elif isinstance(obj, (bool,)):
                return bool(obj)
            elif hasattr(obj, 'item'):  # numpy types
                return obj.item()
            return obj
        
        result = make_serializable(result)
        return JSONResponse(content=result)

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Full prediction error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/watchlist/{symbol}")
async def add_stock_to_watchlist(symbol: str):
    """Add a stock to watchlist."""
    try:
        add_to_watchlist(symbol.upper())
        return {"message": f"{symbol} added to watchlist"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/watchlist/{symbol}")
async def remove_stock_from_watchlist(symbol: str):
    """Remove a stock from watchlist."""
    try:
        remove_from_watchlist(symbol.upper())
        return {"message": f"{symbol} removed from watchlist"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history/{symbol}")
async def get_prediction_history(
    symbol: str,
    limit: int = Query(default=20, le=100)
):
    """Get recent prediction history for a symbol."""
    try:
        history = get_recent_predictions(
            symbol=symbol.upper(),
            limit=limit
        )
        return {"symbol": symbol, "history": history}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ADD to routes.py

@router.post("/telegram/test")
async def test_telegram():
    """Test telegram bot connection."""
    from utils.telegram_bot import send_message
    from datetime import datetime
    
    msg = (
        "🧪 <b>Test Message from TRADEDO</b>\n\n"
        f"🕒 {datetime.now().strftime('%H:%M:%S')}\n"
        "✅ Bot is working perfectly!"
    )
    success = await send_message(msg)
    return {"success": success}


@router.post("/telegram/send-summary")
async def send_summary_now():
    """Manually trigger morning summary."""
    from utils.scheduler import morning_summary
    await morning_summary()
    return {"message": "Summary sent"}

# ADD to api/routes.py

@router.post("/agent/scan")
async def trigger_scan(
    tier: str = Query(default="tier1", description="tier1 (50), tier2 (100), full (150)"),
    mode: str = Query(default="intraday")
):
    """
    Trigger a market scan.
    Returns top candidates sorted by composite score.
    """
    from agent.scanner import scan_market
    from database.db import save_scan_result, clear_todays_scans
    
    try:
        # Clear old scans for today
        clear_todays_scans()
        
        # Run scan
        result = scan_market(tier=tier, mode=mode)
        
        # Save candidates to DB
        for candidate in result["candidates"]:
            save_scan_result(candidate, is_selected=True)
        
        return result
    
    except Exception as e:
        logger.error(f"Scan failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/agent/scan/latest")
async def get_latest_scan():
    """Get today's latest scan candidates from DB."""
    from database.db import get_todays_scan_candidates
    
    candidates = get_todays_scan_candidates(limit=20)
    return {
        "count": len(candidates),
        "candidates": candidates
    }

# ADD to routes.py

@router.get("/agent/llm-status")
async def llm_pool_status():
    """Check LLM pool health."""
    from utils.llm_manager import get_pool
    return get_pool().get_stats()

# ADD to routes.py

@router.get("/social/{symbol}")
async def get_social_data(symbol: str):
    """
    Get combined social intelligence for a stock.
    Aggregates Reddit + StockTwits sentiment.
    """
    from data_pipeline.social_intel import get_social_intelligence
    
    try:
        return get_social_intelligence(symbol)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/social/{symbol}/reddit")
async def get_reddit_only(symbol: str):
    """Get only Reddit sentiment."""
    from data_pipeline.reddit_data import fetch_reddit_sentiment
    return fetch_reddit_sentiment(symbol)


@router.get("/social/{symbol}/stocktwits")
async def get_stocktwits_only(symbol: str):
    """Get only StockTwits sentiment."""
    from data_pipeline.stocktwits_data import fetch_stocktwits_data
    return fetch_stocktwits_data(symbol)

# ADD to routes.py

@router.get("/social/{symbol}/youtube")
async def get_youtube_only(symbol: str):
    """Get only YouTube intelligence."""
    from data_pipeline.youtube_data import fetch_youtube_intel
    return fetch_youtube_intel(symbol)

# ADD to routes.py

@router.get("/social/{symbol}/twitter")
async def get_twitter_only(symbol: str):
    """Get only Twitter/X intelligence."""
    from data_pipeline.twitter_data import fetch_twitter_intel
    return fetch_twitter_intel(symbol)

# ADD to routes.py

# ═══════════════════════════════════════════════════════════════
#   NSE Official Data Endpoints
# ═══════════════════════════════════════════════════════════════

@router.get("/nse/{symbol}")
async def get_nse_intel(symbol: str):
    """Get complete NSE intelligence for a stock."""
    from data_pipeline.nse_data import get_nse_intelligence
    return get_nse_intelligence(symbol)


@router.get("/nse/{symbol}/announcements")
async def get_nse_announcements(symbol: str, days: int = 7):
    """Get corporate announcements."""
    from data_pipeline.nse_data import fetch_announcements
    return {"announcements": fetch_announcements(symbol, days)}


@router.get("/nse/{symbol}/options")
async def get_nse_options(symbol: str):
    """Get options chain analysis."""
    from data_pipeline.nse_data import fetch_option_chain
    return fetch_option_chain(symbol) or {"error": "No data"}


@router.get("/nse/{symbol}/bulk-deals")
async def get_stock_bulk_deals(symbol: str):
    """Get bulk deals for a stock."""
    from data_pipeline.nse_data import analyze_bulk_deals_for_stock
    return analyze_bulk_deals_for_stock(symbol)


@router.get("/nse/market/fii-dii")
async def get_fii_dii():
    """Get today's FII/DII flow."""
    from data_pipeline.nse_data import get_fii_dii_cached
    return get_fii_dii_cached()


@router.get("/nse/market/fno-ban")
async def get_fno_ban():
    """Get today's F&O ban list."""
    from data_pipeline.nse_data import get_fno_ban_list_cached
    return {"banned_stocks": get_fno_ban_list_cached()}


@router.get("/nse/market/bulk-deals")
async def get_all_bulk_deals():
    """Get all bulk deals today."""
    from data_pipeline.nse_data import fetch_bulk_deals
    return {"deals": fetch_bulk_deals()}

# ADD to routes.py

# ═══════════════════════════════════════════════════════════════
#   Google Trends + Global Markets Endpoints
# ═══════════════════════════════════════════════════════════════

@router.get("/trends/{symbol}")
async def get_google_trends(symbol: str):
    """Get Google Trends search interest for a stock."""
    from data_pipeline.trends_data import fetch_google_trends
    return fetch_google_trends(symbol)


@router.get("/global/markets")
async def get_global_markets():
    """Get all global market indicators."""
    from data_pipeline.global_markets import analyze_global_context
    return analyze_global_context()


@router.get("/global/impact/{symbol}")
async def get_global_impact(symbol: str):
    """Get sector-specific global market impact for a stock."""
    from data_pipeline.global_markets import get_sector_impact_from_global
    return get_sector_impact_from_global(symbol)


@router.get("/global/raw")
async def get_global_raw():
    """Get raw data for all global indicators."""
    from data_pipeline.global_markets import fetch_all_global_markets
    return fetch_all_global_markets()

# ADD to routes.py

# ═══════════════════════════════════════════════════════════════
#   Master Scorer Endpoints
# ═══════════════════════════════════════════════════════════════

@router.get("/master/{symbol}")
async def get_master_score_endpoint(
    symbol: str,
    mode: str = Query(default="intraday")
):
    """
    Get complete master score for a stock.
    Combines all 10+ data sources into one verdict.
    Takes ~30-60 seconds due to comprehensive analysis.
    """
    from agent.master_scorer import get_master_score
    
    try:
        return get_master_score(symbol, mode=mode)
    except Exception as e:
        logger.error(f"Master score failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/master/{symbol}/lite")
async def get_master_score_lite_endpoint(
    symbol: str,
    mode: str = Query(default="intraday")
):
    """
    Fast version — technical + news + NSE only.
    Takes ~10-15 seconds.
    """
    from agent.master_scorer import get_master_score_lite
    
    try:
        return get_master_score_lite(symbol, mode=mode)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/agent/deep-scan")
async def deep_scan(
    tier: str = Query(default="tier1")
):
    """
    Deep scan using MASTER SCORER.
    Way smarter than basic scan.
    Takes 5-10 minutes.
    """
    from agent.scanner import StockScanner
    
    try:
        scanner = StockScanner(mode="intraday")
        return scanner.deep_scan(tier=tier)
    except Exception as e:
        logger.error(f"Deep scan failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ADD to routes.py

@router.get("/gates/{symbol}")
async def check_safety_gates_endpoint(
    symbol: str,
    mode: str = Query(default="intraday")
):
    """
    Check ALL safety gates for a stock.
    Shows why a trade would be blocked (if any).
    """
    from agent.safety_gates import check_all_gates
    from agent.master_scorer import get_master_score
    
    try:
        # Get master result for news blocker gate
        master_result = get_master_score(symbol, mode=mode)
        
        # Run gates
        return check_all_gates(
            symbol=symbol,
            mode=mode,
            master_result=master_result,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/master-full/{symbol}")
async def get_full_master_with_gates(
    symbol: str,
    mode: str = Query(default="intraday")
):
    """
    Get master score + safety gates combined.
    THE ULTIMATE ANALYSIS ENDPOINT.
    """
    from agent.master_scorer import get_master_score_with_gates
    
    try:
        return get_master_score_with_gates(symbol, mode=mode)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ADD to routes.py

# ═══════════════════════════════════════════════════════════════
#   Paper Executor Endpoints
# ═══════════════════════════════════════════════════════════════

@router.post("/agent/start")
async def start_agent_endpoint():
    """Enable the agent to execute trades."""
    from agent.paper_executor import start_agent
    return start_agent()


@router.post("/agent/stop")
async def stop_agent_endpoint():
    """Disable the agent."""
    from agent.paper_executor import stop_agent
    return stop_agent()


@router.get("/agent/status")
async def agent_status_endpoint():
    """Get complete agent status."""
    from agent.paper_executor import get_agent_status
    return get_agent_status()


@router.post("/agent/reset-capital")
async def reset_capital_endpoint(new_capital: float = Query(default=100000)):
    """Reset virtual capital (for testing)."""
    from agent.paper_executor import reset_agent_capital
    return reset_agent_capital(new_capital)


@router.post("/agent/execute-trade/{symbol}")
async def execute_trade_endpoint(
    symbol: str,
    mode: str = Query(default="intraday")
):
    """
    Manually trigger a trade for a specific symbol.
    Full pipeline: master score → gates → risk → execute.
    """
    from agent.master_scorer import get_master_score_with_gates
    from agent.paper_executor import PaperExecutor
    
    try:
        # Get master analysis
        master = get_master_score_with_gates(symbol, mode=mode)
        
        if not master.get("can_execute"):
            return {
                "success": False,
                "reason": "Master analysis says no",
                "master": master,
            }
        
        # Execute
        executor = PaperExecutor(mode=mode)
        
        technical = master.get("technical", {})
        indicators = master.get("technical", {})
        
        result = executor.execute_trade(
            symbol=symbol,
            signal=technical.get("signal"),
            current_price=technical.get("current_price"),
            atr=indicators.get("rsi"),  # We need ATR — get from raw data
            confidence_pct=technical.get("confidence"),
            composite_score=master.get("final_score"),
            ai_reasoning=master.get("ai_reasoning", ""),
            master_result=master,
        )
        
        return result
    
    except Exception as e:
        logger.error(f"Trade execution failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/agent/close-trade/{trade_id}")
async def close_trade_endpoint(
    trade_id: int,
    current_price: float = Query(...),
    reason: str = Query(default="MANUAL"),
):
    """Manually close a paper trade."""
    from agent.paper_executor import PaperExecutor
    executor = PaperExecutor()
    return executor.close_trade_manually(trade_id, current_price, reason)


@router.get("/agent/trades")
async def get_trades(
    status: str = Query(default="all", regex="^(all|open|closed)$"),
    limit: int = Query(default=20, le=100)
):
    """Get paper trades."""
    from database.db import get_open_trades, get_recent_trades
    
    if status == "open":
        return {"trades": get_open_trades()}
    elif status == "closed":
        all_trades = get_recent_trades(limit=100)
        closed = [t for t in all_trades if t["status"] != "OPEN"][:limit]
        return {"trades": closed}
    else:
        return {"trades": get_recent_trades(limit=limit)}


@router.get("/agent/performance/today")
async def todays_performance():
    """Get today's performance."""
    from database.db import get_todays_performance
    return get_todays_performance()


@router.get("/agent/performance/overall")
async def overall_performance():
    """Get all-time performance."""
    from database.db import get_overall_performance
    return get_overall_performance()

# ADD to routes.py

# ═══════════════════════════════════════════════════════════════
#   Trade Journal / Analytics Endpoints
# ═══════════════════════════════════════════════════════════════

@router.get("/journal/insights")
async def get_journal_insights():
    """Get comprehensive learning insights from trade history."""
    from agent.trade_journal import get_learning_insights
    return get_learning_insights()


@router.get("/journal/patterns/best")
async def get_best_patterns():
    """Find winning patterns in trade history."""
    from agent.trade_journal import find_best_patterns
    return {"patterns": find_best_patterns()}


@router.get("/journal/patterns/worst")
async def get_worst_patterns():
    """Find losing patterns to avoid."""
    from agent.trade_journal import find_worst_patterns
    return {"patterns": find_worst_patterns()}


@router.get("/journal/analytics/confidence")
async def analytics_by_confidence():
    """Win rate breakdown by confidence level."""
    from agent.trade_journal import analyze_win_rate_by_confidence
    return analyze_win_rate_by_confidence()


@router.get("/journal/analytics/sector")
async def analytics_by_sector():
    """Win rate breakdown by sector."""
    from agent.trade_journal import analyze_win_rate_by_sector
    return analyze_win_rate_by_sector()


@router.get("/journal/analytics/time")
async def analytics_by_time():
    """Win rate breakdown by hour."""
    from agent.trade_journal import analyze_win_rate_by_time
    return analyze_win_rate_by_time()


@router.get("/journal/analytics/score")
async def analytics_by_score():
    """Win rate breakdown by composite score."""
    from agent.trade_journal import analyze_win_rate_by_composite_score
    return analyze_win_rate_by_composite_score()


@router.get("/journal/analytics/exits")
async def analytics_by_exit():
    """Analyze what causes trade exits."""
    from agent.trade_journal import analyze_exit_reasons
    return analyze_exit_reasons()


@router.get("/journal/trades/full")
async def get_journal_full():
    """Get all closed trades with rich journal data."""
    from agent.trade_journal import get_all_closed_trades_with_journal
    return {"trades": get_all_closed_trades_with_journal()}

# ADD to routes.py

@router.post("/agent/monitor/run")
async def run_monitor_manually():
    """Manually trigger the live monitor (for testing)."""
    from agent.live_monitor import run_monitor_now
    return run_monitor_now()


@router.get("/agent/monitor/status")
async def monitor_status():
    """Get current monitor status."""
    from agent.live_monitor import get_monitor
    monitor = get_monitor()
    
    return {
        "is_market_open": monitor._is_market_open(),
        "stats":          monitor.stats,
    }

# ADD to routes.py

@router.get("/agent/trailing/status")
async def trailing_stop_status():
    """Get trailing stop manager statistics."""
    from agent.trailing_stop import get_trailing_manager
    manager = get_trailing_manager()
    return {
        "stats": manager.stats,
        "config": {
            "breakeven_trigger": "50% to T1",
            "profit_lock":       "80% of T1 gain",
            "atr_trail":         "1x ATR below/above high/low",
        }
    }


@router.post("/agent/trailing/test/{trade_id}")
async def test_trailing_for_trade(trade_id: int):
    """Manually check trailing stop for a specific trade."""
    from agent.trailing_stop import get_trailing_manager
    from data_pipeline.price_provider import get_price_provider
    from database.db import get_trade_by_id
    
    trade = get_trade_by_id(trade_id)
    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found")
    
    provider = get_price_provider()
    price_data = provider.get_ltp(trade["symbol"])
    
    if not price_data:
        raise HTTPException(status_code=500, detail="Could not fetch price")
    
    manager = get_trailing_manager()
    result = manager.evaluate_trailing_stop(trade, price_data["last_price"])
    
    return {
        "trade_id": trade_id,
        "symbol":   trade["symbol"],
        "current_price": price_data["last_price"],
        "current_sl":    trade.get("trailing_sl") or trade["stop_loss"],
        "action":   result or "No SL change needed",
    }

# ADD to routes.py

@router.post("/agent/news-exit/check")
async def manual_news_exit_check():
    """Manually trigger news-based exit check for all open trades."""
    from agent.news_exit import check_news_for_exits
    return check_news_for_exits()


@router.get("/agent/news-exit/stats")
async def news_exit_stats():
    """Get news exit analyzer statistics."""
    from agent.news_exit import get_news_analyzer
    analyzer = get_news_analyzer()
    return {
        "stats": analyzer.stats,
        "config": {
            "critical_negative_threshold": -0.6,
            "moderate_negative_threshold": -0.4,
            "check_frequency":             "Every 5 minutes",
            "critical_keywords_count":     len([
                # imported from module
            ]),
        }
    }


@router.post("/agent/news-exit/test/{trade_id}")
async def test_news_exit_for_trade(trade_id: int):
    """Test news exit analysis for a specific trade (no actual exit)."""
    from agent.news_exit import get_news_analyzer
    from database.db import get_trade_by_id
    
    trade = get_trade_by_id(trade_id)
    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found")
    
    if trade["status"] != "OPEN":
        return {"message": f"Trade is not open (status: {trade['status']})"}
    
    analyzer = get_news_analyzer()
    result = analyzer._check_single_trade(trade)
    
    if result:
        return {
            "would_exit": True,
            "trade_id":   trade_id,
            "reason":     result.get("reason"),
            "urgency":    result.get("urgency"),
            "details":    result,
        }
    else:
        return {
            "would_exit": False,
            "trade_id":   trade_id,
            "message":    "No news-based exit needed",
        }
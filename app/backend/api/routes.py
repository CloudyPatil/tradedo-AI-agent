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
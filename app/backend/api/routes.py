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
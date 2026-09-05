# E:\tradedo\app\backend\main.py

import sys
import logging
import asyncio
import os
from pathlib import Path
from contextlib import asynccontextmanager
from datetime import datetime
from database.db import get_connection

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

sys.path.insert(0, str(Path(__file__).parent))

from api.routes         import router
from api.chart_routes   import router as chart_router
from ml.engine          import ModelStore
from database.db        import init_db
from utils.scheduler    import setup_scheduler, scheduler
from utils.telegram_bot import create_bot_app, send_message

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("tradedo.main")

# Store bot app globally for shutdown
bot_app = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global bot_app

    logger.info("=" * 50)
    logger.info("  TRADEDO Backend Starting...")
    logger.info("=" * 50)

    # 1. Database
    init_db()

    # 2. Models
    ModelStore.load_all()

    # 3. Scheduler
    setup_scheduler()
    scheduler.start()

    # 4. Telegram Bot (polling for commands)
    bot_app = create_bot_app()
    if bot_app:
        await bot_app.initialize()
        await bot_app.start()
        await bot_app.updater.start_polling(drop_pending_updates=True)
        logger.info("✅ Telegram bot polling started")

        # Send startup notification
        await send_message(
            "🚀 <b>TRADEDO Backend Online</b>\n\n"
            "All systems operational.\n"
            "Type /help for commands.",
            silent=True
        )

    logger.info("=" * 50)
    logger.info("✅ TRADEDO is LIVE!")
    logger.info("   API: http://localhost:8000/docs")
    logger.info("=" * 50)

    yield

    # ── Shutdown ──────────────────────────────────────────────
    logger.info("Shutting down...")
    
    if bot_app:
        await bot_app.updater.stop()
        await bot_app.stop()
        await bot_app.shutdown()

    scheduler.shutdown()
    logger.info("Shutdown complete")


app = FastAPI(
    title    = "TRADEDO API",
    version  = "1.0.0",
    lifespan = lifespan,
)

CORS_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "TRADEDO_CORS_ORIGINS",
        "http://localhost:3000,http://127.0.0.1:3000",
    ).split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    # These endpoints can place and close paper trades. Do not permit an
    # arbitrary website to issue browser requests to a running terminal.
    allow_origins     = CORS_ORIGINS,
    allow_credentials = False,
    allow_methods     = ["*"],
    allow_headers     = ["*"],
)

app.include_router(router,       prefix="/api/v1")
app.include_router(chart_router, prefix="/api/v1")


@app.get("/")
async def root():
    return {
        "app":    "TRADEDO",
        "docs":   "http://localhost:8000/docs",
        "status": "running"
    }

# ADD to main.py

@app.get("/health")
async def health_check():
    """Comprehensive system health check."""
    from data_pipeline.upstox_api import get_upstox_client
    from data_pipeline.price_provider import get_price_provider
    from ml.engine import ModelStore
    from database.db import get_agent_state
    from agent.websocket_stream import get_streamer
    
    health = {
        "status":    "healthy",
        "timestamp": datetime.now().isoformat(),
        "services":  {},
    }
    
    # Check models
    try:
        ModelStore.load_all()
        health["services"]["ml_models"] = {
            "status": "healthy",
            "swing":    "v2 loaded",
            "intraday": "v3 loaded",
        }
    except Exception as e:
        health["services"]["ml_models"] = {"status": "unhealthy", "error": str(e)}
        health["status"] = "degraded"
    
    # Check Upstox
    try:
        client = get_upstox_client()
        health["services"]["upstox"] = {
            "status": "healthy" if client.is_ready else "unhealthy",
            "ready":  client.is_ready,
        }
        if not client.is_ready:
            health["status"] = "degraded"
    except Exception as e:
        health["services"]["upstox"] = {"status": "error", "error": str(e)}
    
    # Check price provider
    try:
        provider = get_price_provider()
        health["services"]["price_provider"] = provider.get_status()
    except Exception as e:
        health["services"]["price_provider"] = {"status": "error", "error": str(e)}
    
    # Check WebSocket
    try:
        streamer = get_streamer()
        health["services"]["websocket"] = streamer.get_status()
    except Exception as e:
        health["services"]["websocket"] = {"status": "error", "error": str(e)}
    
    # Check agent
    try:
        state = get_agent_state()
        health["services"]["agent"] = {
            "status":         "healthy",
            "is_active":      bool(state.get("is_active")),
            "open_positions": state.get("open_positions", 0),
            "capital":        state.get("capital", 0),
        }
    except Exception as e:
        health["services"]["agent"] = {"status": "error", "error": str(e)}
    
    # Check database
    try:
        conn = get_connection()
        conn.execute("SELECT 1").fetchone()
        conn.close()
        health["services"]["database"] = {"status": "healthy"}
    except Exception as e:
        health["services"]["database"] = {"status": "error", "error": str(e)}
        health["status"] = "unhealthy"
    
    return health


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False, workers=1)

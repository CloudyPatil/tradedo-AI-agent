# E:\tradedo\app\backend\main.py

import sys
import logging
import asyncio
from pathlib import Path
from contextlib import asynccontextmanager

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

app.add_middleware(
    CORSMiddleware,
    allow_origins     = ["*"],
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


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False, workers=1)
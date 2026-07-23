# E:\tradedo\app\backend\main.py
# COMPLETE FINAL VERSION

import sys
import logging
from pathlib import Path
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

sys.path.insert(0, str(Path(__file__).parent))

from api.routes      import router
from ml.engine       import ModelStore
from database.db     import init_db
from utils.scheduler import setup_scheduler, scheduler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("tradedo.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── STARTUP ───────────────────────────────────────────────
    logger.info("=" * 50)
    logger.info("  TRADEDO Backend Starting...")
    logger.info("=" * 50)

    # 1. Initialize database
    logger.info("Initializing database...")
    init_db()

    # 2. Load ML models
    logger.info("Loading ML models...")
    ModelStore.load_all()

    # 3. Start scheduler
    logger.info("Starting scheduler...")
    setup_scheduler()
    scheduler.start()

    logger.info("=" * 50)
    logger.info("✅ TRADEDO is LIVE!")
    logger.info("   API Docs: http://localhost:8000/docs")
    logger.info("=" * 50)

    yield

    # ── SHUTDOWN ──────────────────────────────────────────────
    logger.info("Shutting down scheduler...")
    scheduler.shutdown()
    logger.info("TRADEDO shutdown complete")


app = FastAPI(
    title       = "TRADEDO API",
    description = "AI-powered stock prediction for NSE",
    version     = "1.0.0",
    lifespan    = lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins     = ["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials = True,
    allow_methods     = ["*"],
    allow_headers     = ["*"],
)

app.include_router(router, prefix="/api/v1")


@app.get("/")
async def root():
    return {
        "app":     "TRADEDO",
        "version": "1.0.0",
        "docs":    "http://localhost:8000/docs",
        "status":  "running"
    }


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host    = "0.0.0.0",
        port    = 8000,
        reload  = False,
        workers = 1
    )
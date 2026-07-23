# E:\tradedo\app\backend\database\db.py

import sqlite3
import logging
from pathlib import Path
from datetime import datetime

logger = logging.getLogger("tradedo.db")

# ─── Database Path ────────────────────────────────────────────
DB_PATH = Path(__file__).resolve().parent.parent.parent.parent / "data" / "tradedo.db"


def get_connection():
    """Get SQLite connection. Creates DB if not exists."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row  # Returns dicts instead of tuples
    return conn


def init_db():
    """
    Create all tables if they don't exist.
    Safe to run multiple times.
    """
    conn = get_connection()
    cursor = conn.cursor()

    # ── Predictions Log ───────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS predictions (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol          TEXT NOT NULL,
            mode            TEXT NOT NULL,
            signal          TEXT NOT NULL,
            confidence_pct  REAL,
            composite_score REAL,
            prob_up         REAL,
            current_price   REAL,
            sentiment_label TEXT,
            sentiment_score REAL,
            market_regime   TEXT,
            ai_reasoning    TEXT,
            created_at      DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # ── Watchlist ─────────────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS watchlist (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol     TEXT UNIQUE NOT NULL,
            added_at   DATETIME DEFAULT CURRENT_TIMESTAMP,
            is_active  BOOLEAN DEFAULT 1
        )
    """)

    # ── Paper Trades ──────────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS paper_trades (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol       TEXT NOT NULL,
            direction    TEXT NOT NULL,
            entry_price  REAL NOT NULL,
            exit_price   REAL,
            quantity     INTEGER NOT NULL,
            stop_loss    REAL NOT NULL,
            target       REAL NOT NULL,
            confidence   REAL,
            composite_score REAL,
            status       TEXT DEFAULT 'OPEN',
            pnl          REAL DEFAULT 0,
            entry_time   DATETIME DEFAULT CURRENT_TIMESTAMP,
            exit_time    DATETIME,
            exit_reason  TEXT,
            ai_reasoning TEXT
        )
    """)

    # ── Agent Performance ─────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS agent_performance (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            date            DATE UNIQUE,
            total_trades    INTEGER DEFAULT 0,
            winning_trades  INTEGER DEFAULT 0,
            losing_trades   INTEGER DEFAULT 0,
            gross_pnl       REAL DEFAULT 0,
            win_rate        REAL DEFAULT 0,
            virtual_capital REAL DEFAULT 100000
        )
    """)

    # ── Daily Scan Results ────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS daily_scan (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            scan_time   DATETIME DEFAULT CURRENT_TIMESTAMP,
            symbol      TEXT NOT NULL,
            confidence  REAL,
            signal      TEXT,
            composite   REAL,
            selected    BOOLEAN DEFAULT 0,
            reason      TEXT
        )
    """)

    # ── Insert default watchlist ───────────────────────────────
    default_stocks = [
        "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS",
        "TATAMOTORS.NS", "WIPRO.NS", "ICICIBANK.NS",
        "SBIN.NS", "ADANIENT.NS", "BAJFINANCE.NS"
    ]

    for symbol in default_stocks:
        cursor.execute("""
            INSERT OR IGNORE INTO watchlist (symbol) VALUES (?)
        """, (symbol,))

    conn.commit()
    conn.close()
    logger.info(f"✅ Database initialized at {DB_PATH}")


def save_prediction(prediction: dict):
    """Save a prediction result to database."""
    conn = get_connection()
    try:
        conn.execute("""
            INSERT INTO predictions
            (symbol, mode, signal, confidence_pct, composite_score,
             prob_up, current_price, sentiment_label, sentiment_score,
             market_regime, ai_reasoning)
            VALUES (?,?,?,?,?,?,?,?,?,?,?)
        """, (
            prediction.get("symbol"),
            prediction.get("mode"),
            prediction.get("signal"),
            prediction.get("confidence_pct"),
            prediction.get("composite", {}).get("composite_score"),
            prediction.get("prob_up"),
            prediction.get("current_price"),
            prediction.get("sentiment", {}).get("label"),
            prediction.get("sentiment", {}).get("score"),
            prediction.get("market_regime"),
            prediction.get("ai_reasoning"),
        ))
        conn.commit()
    except Exception as e:
        logger.error(f"Save prediction failed: {e}")
    finally:
        conn.close()


def get_watchlist() -> list:
    """Get all active watchlist symbols."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT symbol FROM watchlist WHERE is_active=1 ORDER BY id"
    ).fetchall()
    conn.close()
    return [row["symbol"] for row in rows]


def add_to_watchlist(symbol: str):
    """Add stock to watchlist."""
    conn = get_connection()
    try:
        conn.execute(
            "INSERT OR IGNORE INTO watchlist (symbol) VALUES (?)",
            (symbol,)
        )
        conn.commit()
    finally:
        conn.close()


def remove_from_watchlist(symbol: str):
    """Remove stock from watchlist."""
    conn = get_connection()
    conn.execute(
        "UPDATE watchlist SET is_active=0 WHERE symbol=?",
        (symbol,)
    )
    conn.commit()
    conn.close()


def get_recent_predictions(symbol: str = None, limit: int = 20) -> list:
    """Get recent predictions, optionally filtered by symbol."""
    conn = get_connection()
    if symbol:
        rows = conn.execute("""
            SELECT * FROM predictions
            WHERE symbol=?
            ORDER BY created_at DESC LIMIT ?
        """, (symbol, limit)).fetchall()
    else:
        rows = conn.execute("""
            SELECT * FROM predictions
            ORDER BY created_at DESC LIMIT ?
        """, (limit,)).fetchall()
    conn.close()
    return [dict(row) for row in rows]


# ─── Init on import ───────────────────────────────────────────
if __name__ == "__main__":
    init_db()
    print("Database created successfully!")
    print(f"Location: {DB_PATH}")
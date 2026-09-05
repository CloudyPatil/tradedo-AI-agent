# E:\tradedo\app\backend\database\db.py

import sqlite3
import logging
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo

logger = logging.getLogger("tradedo.db")

# ─── Database Path ────────────────────────────────────────────
DB_PATH = Path(__file__).resolve().parent.parent.parent.parent / "data" / "tradedo.db"


def get_connection():
    """Get a SQLite connection configured for concurrent API/scheduler access."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    # The scheduler and request handlers can write at the same time. WAL plus
    # a busy timeout prevents transient "database is locked" failures while
    # retaining this lightweight local database.
    conn = sqlite3.connect(str(DB_PATH), timeout=10)
    conn.row_factory = sqlite3.Row  # Returns dicts instead of tuples
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=10000")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    """Create all tables — updated for Phase 5.3."""
    conn = get_connection()
    cursor = conn.cursor()

    # ── Predictions Log (existing) ────────────────────────────
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

    # ── Watchlist (existing) ──────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS watchlist (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol     TEXT UNIQUE NOT NULL,
            added_at   DATETIME DEFAULT CURRENT_TIMESTAMP,
            is_active  BOOLEAN DEFAULT 1
        )
    """)

    # ── Paper Trades (ENHANCED) ───────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS paper_trades (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol          TEXT NOT NULL,
            direction       TEXT NOT NULL,          -- LONG/SHORT
            signal          TEXT NOT NULL,          -- BUY/SELL
            mode            TEXT NOT NULL,          -- intraday/swing
            sector          TEXT,
            
            -- Prices
            entry_price     REAL NOT NULL,
            current_price   REAL,
            exit_price      REAL,
            stop_loss       REAL NOT NULL,
            target_1        REAL NOT NULL,
            target_2        REAL NOT NULL,
            
            -- Position
            quantity        INTEGER NOT NULL,
            investment      REAL NOT NULL,
            
            -- Risk metrics
            risk_amount     REAL,
            risk_pct        REAL,
            atr             REAL,
            
            -- Confidence & scoring
            ml_confidence   REAL,
            composite_score REAL,
            
            -- Status tracking
            status          TEXT DEFAULT 'OPEN',    -- OPEN/T1_HIT/T2_HIT/SL_HIT/EOD/MANUAL
            partial_exit    BOOLEAN DEFAULT 0,      -- If 50% booked at T1
            partial_qty     INTEGER DEFAULT 0,      -- Quantity booked at T1
            
            -- P&L
            pnl             REAL DEFAULT 0,
            pnl_pct         REAL DEFAULT 0,
            partial_pnl     REAL DEFAULT 0,
            
            -- Trailing stop tracking
            trailing_sl     REAL,
            highest_price   REAL,
            lowest_price    REAL,
            
            -- Times
            entry_time      DATETIME DEFAULT CURRENT_TIMESTAMP,
            exit_time       DATETIME,
            time_exit_by    DATETIME,               -- Force exit time
            
            -- Exit info
            exit_reason     TEXT,
            hold_duration_mins INTEGER,
            
            -- AI/Reasoning
            ai_reasoning    TEXT,
            
            -- Metadata (JSON blob for RL features)
            metadata        TEXT
        )
    """)

    # ── Agent Performance (ENHANCED) ──────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS agent_performance (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            date            DATE UNIQUE,
            starting_capital REAL,
            ending_capital  REAL,
            total_trades    INTEGER DEFAULT 0,
            winning_trades  INTEGER DEFAULT 0,
            losing_trades   INTEGER DEFAULT 0,
            eod_trades      INTEGER DEFAULT 0,
            gross_pnl       REAL DEFAULT 0,
            gross_profit    REAL DEFAULT 0,
            gross_loss      REAL DEFAULT 0,
            win_rate        REAL DEFAULT 0,
            avg_win         REAL DEFAULT 0,
            avg_loss        REAL DEFAULT 0,
            largest_win     REAL DEFAULT 0,
            largest_loss    REAL DEFAULT 0,
            avg_hold_mins   INTEGER DEFAULT 0
        )
    """)

    # ── Daily Scan Results (existing) ─────────────────────────
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

    # ── Agent Capital State (NEW) ─────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS agent_state (
            id                  INTEGER PRIMARY KEY,
            capital             REAL DEFAULT 100000,
            starting_capital    REAL DEFAULT 100000,
            current_exposure    REAL DEFAULT 0,
            open_positions      INTEGER DEFAULT 0,
            trades_today        INTEGER DEFAULT 0,
            wins_today          INTEGER DEFAULT 0,
            losses_today        INTEGER DEFAULT 0,
            pnl_today           REAL DEFAULT 0,
            is_active           BOOLEAN DEFAULT 0,
            last_reset          DATE,
            updated_at          DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Initialize agent state (single row)
    cursor.execute("""
        INSERT OR IGNORE INTO agent_state (id, capital, starting_capital, last_reset)
        VALUES (1, 100000, 100000, date('now'))
    """)

    # ═══════════════════════════════════════════════════════════
    #   MANUAL TRADING TABLES (NEW)
    # ═══════════════════════════════════════════════════════════
    
    # Manual account state
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS manual_state (
            id                  INTEGER PRIMARY KEY,
            capital             REAL DEFAULT 100000,
            starting_capital    REAL DEFAULT 100000,
            current_exposure    REAL DEFAULT 0,
            open_positions      INTEGER DEFAULT 0,
            total_realized_pnl  REAL DEFAULT 0,
            total_unrealized_pnl REAL DEFAULT 0,
            trades_today        INTEGER DEFAULT 0,
            wins_today          INTEGER DEFAULT 0,
            losses_today        INTEGER DEFAULT 0,
            pnl_today           REAL DEFAULT 0,
            last_reset          DATE,
            updated_at          DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Initialize manual state
    cursor.execute("""
        INSERT OR IGNORE INTO manual_state (id, capital, starting_capital, last_reset)
        VALUES (1, 100000, 100000, date('now'))
    """)
    
    # Manual orders (order book - includes pending, filled, cancelled)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS manual_orders (
            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol              TEXT NOT NULL,
            order_type          TEXT NOT NULL,      -- MARKET, LIMIT, SL, SL_MARKET
            side                TEXT NOT NULL,      -- BUY, SELL
            product_type        TEXT DEFAULT 'INTRADAY',  -- INTRADAY, DELIVERY
            
            -- Order details
            quantity            INTEGER NOT NULL,
            price               REAL,               -- Limit price
            trigger_price       REAL,               -- SL trigger price
            
            -- Filled details
            filled_quantity     INTEGER DEFAULT 0,
            avg_fill_price      REAL,
            
            -- Status
            status              TEXT DEFAULT 'PENDING',   -- PENDING, FILLED, PARTIAL, CANCELLED, REJECTED
            reason              TEXT,               -- Cancellation/rejection reason
            
            -- Optional bracket order details
            is_bracket          BOOLEAN DEFAULT 0,
            stop_loss           REAL,
            target              REAL,
            
            -- Times
            created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
            filled_at           DATETIME,
            cancelled_at        DATETIME,
            
            -- Notes
            notes               TEXT
        )
    """)
    
    # Manual trades (executed positions)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS manual_trades (
            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol              TEXT NOT NULL,
            direction           TEXT NOT NULL,      -- LONG, SHORT
            sector              TEXT,
            
            -- Order reference
            entry_order_id      INTEGER,
            exit_order_id       INTEGER,
            
            -- Prices
            entry_price         REAL NOT NULL,
            current_price       REAL,
            exit_price          REAL,
            stop_loss           REAL,
            target              REAL,
            
            -- Position
            quantity            INTEGER NOT NULL,
            investment          REAL NOT NULL,
            product_type        TEXT DEFAULT 'INTRADAY',
            margin_used         REAL DEFAULT 0,
            entry_charges       REAL DEFAULT 0,
            price_source        TEXT,
            price_updated_at    DATETIME,
            
            -- P&L
            unrealized_pnl      REAL DEFAULT 0,
            realized_pnl        REAL,
            pnl_pct             REAL,
            
            -- Status
            status              TEXT DEFAULT 'OPEN',  -- OPEN, CLOSED, PARTIAL
            
            -- Tracking
            highest_price       REAL,
            lowest_price        REAL,
            
            -- Times
            entry_time          DATETIME DEFAULT CURRENT_TIMESTAMP,
            exit_time           DATETIME,
            hold_duration_mins  INTEGER,
            
            -- Meta
            exit_reason         TEXT,
            notes               TEXT
        )
    """)
    
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_manual_orders_status ON manual_orders(status)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_manual_trades_status ON manual_trades(status)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_manual_trades_symbol ON manual_trades(symbol)")

    # These columns were added after manual trading was introduced.  SQLite's
    # CREATE TABLE IF NOT EXISTS does not upgrade existing installations.
    existing_manual_trade_columns = {
        row["name"] for row in cursor.execute("PRAGMA table_info(manual_trades)")
    }
    for column, definition in (
        ("product_type", "TEXT DEFAULT 'INTRADAY'"),
        ("margin_used", "REAL DEFAULT 0"),
        ("entry_charges", "REAL DEFAULT 0"),
        ("price_source", "TEXT"),
        ("price_updated_at", "DATETIME"),
    ):
        if column not in existing_manual_trade_columns:
            cursor.execute(f"ALTER TABLE manual_trades ADD COLUMN {column} {definition}")
    
    # Insert default watchlist
    default_stocks = [
        "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS",
        "TATAMOTORS.NS", "WIPRO.NS", "ICICIBANK.NS",
        "SBIN.NS", "ADANIENT.NS", "BAJFINANCE.NS"
    ]

    for symbol in default_stocks:
        cursor.execute(
            "INSERT OR IGNORE INTO watchlist (symbol) VALUES (?)",
            (symbol,)
        )

    conn.commit()
    conn.close()
    logger.info(f"✅ Database initialized at {DB_PATH}")


# ═══════════════════════════════════════════════════════════════
#   AGENT STATE FUNCTIONS
# ═══════════════════════════════════════════════════════════════

def get_agent_state() -> dict:
    """Get current agent state."""
    conn = get_connection()
    row = conn.execute("SELECT * FROM agent_state WHERE id=1").fetchone()
    conn.close()
    return dict(row) if row else {}

def update_agent_state(**kwargs):
    """Update agent state fields."""
    if not kwargs:
        return
        
    conn = get_connection()
    updates = ", ".join(f"{k}=?" for k in kwargs.keys())
    values = list(kwargs.values())
    
    conn.execute(
        f"UPDATE agent_state SET {updates}, updated_at=CURRENT_TIMESTAMP WHERE id=1",
        values
    )
    conn.commit()
    conn.close()

def reset_daily_agent_state():
    """Reset daily counters (call at start of new day)."""
    conn = get_connection()
    conn.execute("""
        UPDATE agent_state 
        SET trades_today=0, wins_today=0, losses_today=0, pnl_today=0,
            last_reset=date('now'), updated_at=CURRENT_TIMESTAMP
        WHERE id=1
    """)
    conn.commit()
    conn.close()


# ═══════════════════════════════════════════════════════════════
#   PAPER TRADE FUNCTIONS
# ═══════════════════════════════════════════════════════════════

def create_paper_trade(trade_data: dict) -> int:
    """Create a new paper trade. Returns trade ID."""
    conn = get_connection()
    
    cursor = conn.execute("""
        INSERT INTO paper_trades (
            symbol, direction, signal, mode, sector,
            entry_price, current_price, stop_loss, target_1, target_2,
            quantity, investment,
            risk_amount, risk_pct, atr,
            ml_confidence, composite_score,
            time_exit_by, ai_reasoning, metadata
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        trade_data.get("symbol"),
        trade_data.get("direction"),
        trade_data.get("signal"),
        trade_data.get("mode"),
        trade_data.get("sector"),
        trade_data.get("entry_price"),
        trade_data.get("entry_price"),  # current = entry initially
        trade_data.get("stop_loss"),
        trade_data.get("target_1"),
        trade_data.get("target_2"),
        trade_data.get("quantity"),
        trade_data.get("investment"),
        trade_data.get("risk_amount"),
        trade_data.get("risk_pct"),
        trade_data.get("atr"),
        trade_data.get("ml_confidence"),
        trade_data.get("composite_score"),
        trade_data.get("time_exit_by"),
        trade_data.get("ai_reasoning"),
        trade_data.get("metadata"),
    ))
    
    trade_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    logger.info(f"📝 Paper trade created: ID {trade_id}")
    return trade_id

def get_open_trades() -> list:
    """Get all open paper trades."""
    conn = get_connection()
    rows = conn.execute("""
        SELECT * FROM paper_trades 
        WHERE status = 'OPEN' 
        ORDER BY entry_time DESC
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_todays_trades() -> list:
    """Get all trades opened today."""
    conn = get_connection()
    rows = conn.execute("""
        SELECT * FROM paper_trades 
        WHERE date(entry_time) = date('now')
        ORDER BY entry_time DESC
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_recent_trades(limit: int = 20) -> list:
    """Get recent trades."""
    conn = get_connection()
    rows = conn.execute("""
        SELECT * FROM paper_trades 
        ORDER BY entry_time DESC 
        LIMIT ?
    """, (limit,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_trade_by_id(trade_id: int) -> dict:
    """Get a specific trade."""
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM paper_trades WHERE id = ?",
        (trade_id,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None

def update_trade(trade_id: int, **kwargs):
    """Update trade fields."""
    if not kwargs:
        return
        
    conn = get_connection()
    updates = ", ".join(f"{k}=?" for k in kwargs.keys())
    values = list(kwargs.values()) + [trade_id]
    
    conn.execute(
        f"UPDATE paper_trades SET {updates} WHERE id=?",
        values
    )
    conn.commit()
    conn.close()

def close_trade(
    trade_id: int,
    exit_price: float,
    exit_reason: str,
    is_partial: bool = False,
    partial_qty: int = 0,
):
    """Close a paper trade (full or partial)."""
    trade = get_trade_by_id(trade_id)
    if not trade:
        logger.error(f"Trade {trade_id} not found")
        return
        
    is_long = trade["direction"] == "LONG"
    entry_price = trade["entry_price"]
    
    if is_partial:
        # Partial exit at T1 (usually 50%)
        qty_exiting = partial_qty
        remaining_qty = trade["quantity"] - qty_exiting
        
        # Calculate partial P&L
        if is_long:
            partial_pnl = round((exit_price - entry_price) * qty_exiting, 2)
        else:
            partial_pnl = round((entry_price - exit_price) * qty_exiting, 2)
            
        update_trade(
            trade_id,
            partial_exit=1,
            partial_qty=qty_exiting,
            partial_pnl=partial_pnl,
            quantity=remaining_qty,
            trailing_sl=entry_price,  # Move SL to breakeven
        )
        
        logger.info(
            f"💰 Partial exit: Trade {trade_id} | "
            f"{qty_exiting} shares @ ₹{exit_price} | P&L: ₹{partial_pnl}"
        )
    else:
        # Full exit
        remaining_qty = trade["quantity"]
        
        if is_long:
            pnl = round((exit_price - entry_price) * remaining_qty, 2)
        else:
            pnl = round((entry_price - exit_price) * remaining_qty, 2)
            
        # Add partial P&L if any
        total_pnl = pnl + (trade.get("partial_pnl", 0) or 0)
        
        # Total investment (including partial)
        total_invested = (
            trade["investment"]  # Original investment
        )
        pnl_pct = round((total_pnl / total_invested) * 100, 2) if total_invested else 0
        
        # Calculate hold duration
        from datetime import datetime
        entry_time = datetime.fromisoformat(trade["entry_time"].replace("Z", "+00:00"))
        if entry_time.tzinfo:
            entry_time = entry_time.replace(tzinfo=None)
            
        exit_time = datetime.now()
        hold_mins = int((exit_time - entry_time).total_seconds() / 60)
        
        # Determine status
        if exit_reason == "TARGET_1_HIT":
            status = "T1_HIT"
        elif exit_reason == "TARGET_2_HIT":
            status = "T2_HIT"
        elif exit_reason == "STOP_LOSS":
            status = "SL_HIT"
        elif exit_reason == "EOD":
            status = "EOD"
        else:
            status = "MANUAL"
            
        update_trade(
            trade_id,
            exit_price=exit_price,
            exit_time=exit_time.isoformat(),
            exit_reason=exit_reason,
            status=status,
            pnl=total_pnl,
            pnl_pct=pnl_pct,
            hold_duration_mins=hold_mins,
        )
        
        emoji = "✅" if total_pnl > 0 else "❌"
        logger.info(
            f"{emoji} Trade closed: ID {trade_id} | "
            f"{trade['symbol']} | P&L: ₹{total_pnl} ({pnl_pct}%) | "
            f"Reason: {exit_reason}"
        )

def update_trade_current_price(trade_id: int, current_price: float):
    """Update the current market price for a trade."""
    trade = get_trade_by_id(trade_id)
    if not trade:
        return
        
    is_long = trade["direction"] == "LONG"
    entry_price = trade["entry_price"]
    qty = trade["quantity"]
    
    # Calculate running P&L
    if is_long:
        running_pnl = round((current_price - entry_price) * qty, 2)
    else:
        running_pnl = round((entry_price - current_price) * qty, 2)
        
    # Track highest/lowest
    updates = {
        "current_price": current_price,
        "pnl": running_pnl,
    }
    
    highest = trade.get("highest_price") or entry_price
    lowest = trade.get("lowest_price") or entry_price
    
    if current_price > highest:
        updates["highest_price"] = current_price
    if current_price < lowest:
        updates["lowest_price"] = current_price
        
    update_trade(trade_id, **updates)


# ═══════════════════════════════════════════════════════════════
#   PERFORMANCE FUNCTIONS
# ═══════════════════════════════════════════════════════════════

def get_todays_performance() -> dict:
    """Calculate today's performance stats."""
    trades = get_todays_trades()
    closed = [t for t in trades if t["status"] != "OPEN"]
    open_trades = [t for t in trades if t["status"] == "OPEN"]
    
    winning = [t for t in closed if (t.get("pnl") or 0) > 0]
    losing = [t for t in closed if (t.get("pnl") or 0) < 0]
    
    total_pnl = sum(t.get("pnl", 0) for t in closed)
    total_profit = sum(t["pnl"] for t in winning) if winning else 0
    total_loss = sum(t["pnl"] for t in losing) if losing else 0
    
    win_rate = round((len(winning) / len(closed)) * 100, 2) if closed else 0
    avg_win = round(total_profit / len(winning), 2) if winning else 0
    avg_loss = round(total_loss / len(losing), 2) if losing else 0
    
    return {
        "date":           str(datetime.now().date()),
        "total_trades":   len(trades),
        "closed_trades":  len(closed),
        "open_trades":    len(open_trades),
        "winning_trades": len(winning),
        "losing_trades":  len(losing),
        "win_rate":       win_rate,
        "total_pnl":      round(total_pnl, 2),
        "avg_win":        avg_win,
        "avg_loss":       avg_loss,
        "largest_win":    round(max((t["pnl"] for t in winning), default=0), 2),
        "largest_loss":   round(min((t["pnl"] for t in losing), default=0), 2),
    }

def get_overall_performance() -> dict:
    """Get all-time performance stats."""
    conn = get_connection()
    
    total_rows = conn.execute("""
        SELECT COUNT(*) as total,
               SUM(pnl) as total_pnl,
               SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) as wins,
               SUM(CASE WHEN pnl < 0 THEN 1 ELSE 0 END) as losses,
               AVG(hold_duration_mins) as avg_hold
        FROM paper_trades WHERE status != 'OPEN'
    """).fetchone()
    
    conn.close()
    
    if not total_rows or total_rows["total"] == 0:
        return {
            "total_trades": 0,
            "total_pnl":    0,
            "win_rate":     0,
        }
        
    total = total_rows["total"]
    wins  = total_rows["wins"] or 0
    losses = total_rows["losses"] or 0
    
    return {
        "total_trades":   total,
        "total_pnl":      round(total_rows["total_pnl"] or 0, 2),
        "winning_trades": wins,
        "losing_trades":  losses,
        "win_rate":       round((wins / total) * 100, 2) if total else 0,
        "avg_hold_mins":  round(total_rows["avg_hold"] or 0),
    }


# ─── Keep existing functions ──────────────────────────────────
# save_prediction, get_watchlist, add_to_watchlist, remove_from_watchlist,
# get_recent_predictions, save_scan_result, get_todays_scan_candidates, clear_todays_scans

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


def save_scan_result(scan_data: dict, is_selected: bool = False):
    """Save a single scan result."""
    conn = get_connection()
    try:
        conn.execute("""
            INSERT INTO daily_scan
            (symbol, confidence, signal, composite, selected, reason)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            scan_data.get("symbol"),
            scan_data.get("confidence"),
            scan_data.get("signal"),
            scan_data.get("composite_score"),
            is_selected,
            scan_data.get("reason", ""),
        ))
        conn.commit()
    finally:
        conn.close()


def get_todays_scan_candidates(limit: int = 10) -> list:
    """Get today's scan candidates."""
    conn = get_connection()
    rows = conn.execute("""
        SELECT * FROM daily_scan 
        WHERE date(scan_time) = date('now')
        ORDER BY composite DESC 
        LIMIT ?
    """, (limit,)).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def clear_todays_scans():
    """Clear today's scan results before new scan."""
    conn = get_connection()
    conn.execute("DELETE FROM daily_scan WHERE date(scan_time) = date('now')")
    conn.commit()
    conn.close()



# ═══════════════════════════════════════════════════════════════
#   MANUAL ACCOUNT FUNCTIONS
# ═══════════════════════════════════════════════════════════════

def get_manual_state() -> dict:
    """Get manual account state."""
    ensure_manual_daily_state()
    conn = get_connection()
    row = conn.execute("SELECT * FROM manual_state WHERE id=1").fetchone()
    conn.close()
    return dict(row) if row else {}


def update_manual_state(**kwargs):
    """Update manual state."""
    if not kwargs:
        return
    conn = get_connection()
    updates = ", ".join(f"{k}=?" for k in kwargs.keys())
    values = list(kwargs.values())
    conn.execute(
        f"UPDATE manual_state SET {updates}, updated_at=CURRENT_TIMESTAMP WHERE id=1",
        values
    )
    conn.commit()
    conn.close()


def reset_manual_daily_state():
    """Reset daily counters."""
    today = datetime.now(ZoneInfo("Asia/Kolkata")).date().isoformat()
    conn = get_connection()
    conn.execute("""
        UPDATE manual_state 
        SET trades_today=0, wins_today=0, losses_today=0, pnl_today=0,
            last_reset=?, updated_at=CURRENT_TIMESTAMP
        WHERE id=1
    """, (today,))
    conn.commit()
    conn.close()


def ensure_manual_daily_state():
    """Reset manual daily counters once per India trading day, including after restarts."""
    today = datetime.now(ZoneInfo("Asia/Kolkata")).date().isoformat()
    conn = get_connection()
    row = conn.execute("SELECT last_reset FROM manual_state WHERE id=1").fetchone()
    if row and row["last_reset"] != today:
        conn.execute("""
            UPDATE manual_state
            SET trades_today=0, wins_today=0, losses_today=0, pnl_today=0,
                last_reset=?, updated_at=CURRENT_TIMESTAMP
            WHERE id=1
        """, (today,))
        conn.commit()
    conn.close()


# ─── Manual Orders ────────────────────────────────────────────

def create_manual_order(order_data: dict) -> int:
    """Create new manual order."""
    conn = get_connection()
    cursor = conn.execute("""
        INSERT INTO manual_orders (
            symbol, order_type, side, product_type,
            quantity, price, trigger_price,
            is_bracket, stop_loss, target, notes
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        order_data.get("symbol"),
        order_data.get("order_type"),
        order_data.get("side"),
        order_data.get("product_type", "INTRADAY"),
        order_data.get("quantity"),
        order_data.get("price"),
        order_data.get("trigger_price"),
        order_data.get("is_bracket", False),
        order_data.get("stop_loss"),
        order_data.get("target"),
        order_data.get("notes", ""),
    ))
    order_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return order_id


def get_manual_orders(status: str = None, limit: int = 100) -> list:
    """Get manual orders."""
    conn = get_connection()
    if status:
        rows = conn.execute("""
            SELECT * FROM manual_orders 
            WHERE status = ? 
            ORDER BY created_at DESC 
            LIMIT ?
        """, (status, limit)).fetchall()
    else:
        rows = conn.execute("""
            SELECT * FROM manual_orders 
            ORDER BY created_at DESC 
            LIMIT ?
        """, (limit,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_manual_order(order_id: int) -> dict:
    """Get specific order."""
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM manual_orders WHERE id = ?",
        (order_id,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def update_manual_order(order_id: int, **kwargs):
    """Update order fields."""
    if not kwargs:
        return
    conn = get_connection()
    updates = ", ".join(f"{k}=?" for k in kwargs.keys())
    values = list(kwargs.values()) + [order_id]
    conn.execute(
        f"UPDATE manual_orders SET {updates} WHERE id=?",
        values
    )
    conn.commit()
    conn.close()


def cancel_manual_order(order_id: int, reason: str = "Manual cancellation"):
    """Cancel pending order."""
    update_manual_order(
        order_id,
        status="CANCELLED",
        reason=reason,
        cancelled_at=datetime.now().isoformat(),
    )


# ─── Manual Trades ────────────────────────────────────────────

def create_manual_trade(trade_data: dict) -> int:
    """Create manual trade."""
    conn = get_connection()
    cursor = conn.execute("""
        INSERT INTO manual_trades (
            symbol, direction, sector, entry_order_id,
        entry_price, current_price, stop_loss, target,
            quantity, investment, product_type, margin_used, entry_charges, notes
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        trade_data.get("symbol"),
        trade_data.get("direction"),
        trade_data.get("sector"),
        trade_data.get("entry_order_id"),
        trade_data.get("entry_price"),
        trade_data.get("entry_price"),
        trade_data.get("stop_loss"),
        trade_data.get("target"),
        trade_data.get("quantity"),
        trade_data.get("investment"),
        trade_data.get("product_type", "INTRADAY"),
        trade_data.get("margin_used", 0),
        trade_data.get("entry_charges", 0),
        trade_data.get("notes", ""),
    ))
    trade_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return trade_id


def get_manual_trades(status: str = None, limit: int = 100) -> list:
    """Get manual trades."""
    conn = get_connection()
    if status:
        rows = conn.execute("""
            SELECT * FROM manual_trades 
            WHERE status = ? 
            ORDER BY entry_time DESC 
            LIMIT ?
        """, (status, limit)).fetchall()
    else:
        rows = conn.execute("""
            SELECT * FROM manual_trades 
            ORDER BY entry_time DESC 
            LIMIT ?
        """, (limit,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_manual_trade(trade_id: int) -> dict:
    """Get specific trade."""
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM manual_trades WHERE id = ?",
        (trade_id,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def update_manual_trade(trade_id: int, **kwargs):
    """Update trade fields."""
    if not kwargs:
        return
    conn = get_connection()
    updates = ", ".join(f"{k}=?" for k in kwargs.keys())
    values = list(kwargs.values()) + [trade_id]
    conn.execute(
        f"UPDATE manual_trades SET {updates} WHERE id=?",
        values
    )
    conn.commit()
    conn.close()


def close_manual_trade(trade_id: int, exit_price: float, reason: str = "MANUAL"):
    """Close a manual trade."""
    trade = get_manual_trade(trade_id)
    if not trade:
        return
    
    is_long = trade["direction"] == "LONG"
    entry = trade["entry_price"]
    qty = trade["quantity"]
    
    # Calculate P&L
    if is_long:
        pnl = round((exit_price - entry) * qty, 2)
    else:
        pnl = round((entry - exit_price) * qty, 2)
    
    pnl_pct = round((pnl / trade["investment"]) * 100, 2) if trade["investment"] else 0
    
    # Calculate hold duration
    entry_time = datetime.fromisoformat(trade["entry_time"].replace("Z", "+00:00"))
    if entry_time.tzinfo:
        entry_time = entry_time.replace(tzinfo=None)
    
    exit_time = datetime.now()
    hold_mins = int((exit_time - entry_time).total_seconds() / 60)
    
    update_manual_trade(
        trade_id,
        exit_price=exit_price,
        exit_time=exit_time.isoformat(),
        exit_reason=reason,
        status="CLOSED",
        realized_pnl=pnl,
        pnl_pct=pnl_pct,
        hold_duration_mins=hold_mins,
    )
    
    return pnl

# ─── Init on import ───────────────────────────────────────────
if __name__ == "__main__":
    init_db()
    print("Database created successfully!")
    print(f"Location: {DB_PATH}")

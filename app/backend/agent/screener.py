# E:\tradedo\app\backend\agent\screener.py

"""
UNIVERSAL STOCK SCREENER
Analyzes and ranks stocks from Nifty 500 universe.
Caches results in database for fast frontend queries.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import logging
import sqlite3
import time
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

from database.db import get_connection
from ml.engine import predict
from agent.universe import get_scan_universe, NIFTY_500
from agent.sectors import get_sector

logger = logging.getLogger("tradedo.screener")


# ═══════════════════════════════════════════════════════════════
#   CONFIG
# ═══════════════════════════════════════════════════════════════

MAX_WORKERS = 5
SCAN_TIMEOUT = 30


# ═══════════════════════════════════════════════════════════════
#   DATABASE SCHEMA
# ═══════════════════════════════════════════════════════════════

def init_screener_tables():
    """Create screener cache tables."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Stock analysis cache
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS stock_analysis (
            symbol          TEXT PRIMARY KEY,
            sector          TEXT,
            
            -- Latest analysis
            signal          TEXT,
            confidence_pct  REAL,
            prob_up         REAL,
            current_price   REAL,
            
            -- Technical
            rsi             REAL,
            macd            REAL,
            
            -- Returns
            returns_5d      REAL,
            returns_20d     REAL,
            
            -- Volume
            volume_change   REAL,
            
            -- Meta
            mode            TEXT,        -- 'swing' or 'intraday'
            analyzed_at     DATETIME DEFAULT CURRENT_TIMESTAMP,
            
            -- JSON dump of full analysis
            full_data       TEXT
        )
    """)
    
    # Screener runs log
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS screener_runs (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            run_time        DATETIME DEFAULT CURRENT_TIMESTAMP,
            tier            TEXT,
            mode            TEXT,
            stocks_scanned  INTEGER,
            successful      INTEGER,
            failed          INTEGER,
            duration_seconds REAL
        )
    """)
    
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_signal ON stock_analysis(signal)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_sector ON stock_analysis(sector)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_confidence ON stock_analysis(confidence_pct)")
    
    conn.commit()
    conn.close()
    logger.info("✅ Screener tables initialized")


# ═══════════════════════════════════════════════════════════════
#   ANALYSIS FUNCTIONS
# ═══════════════════════════════════════════════════════════════

def analyze_single_stock(symbol: str, mode: str = "swing") -> Optional[Dict]:
    """Analyze one stock and return result."""
    try:
        result = predict(symbol, mode=mode)
        return {
            "symbol":          symbol,
            "sector":          get_sector(symbol),
            "signal":          result.get("signal"),
            "confidence_pct":  result.get("confidence_pct"),
            "prob_up":         result.get("prob_up"),
            "current_price":   result.get("current_price"),
            "mode":            mode,
            "indicators":      result.get("indicators", {}),
            "status":          "success",
        }
    except Exception as e:
        return {
            "symbol": symbol,
            "status": "error",
            "error":  str(e)[:200],
        }


def save_analysis(analysis: Dict):
    """Save stock analysis to cache."""
    if analysis.get("status") != "success":
        return
    
    import json
    conn = get_connection()
    
    indicators = analysis.get("indicators", {})
    
    conn.execute("""
        INSERT OR REPLACE INTO stock_analysis
        (symbol, sector, signal, confidence_pct, prob_up, current_price,
         rsi, macd, returns_5d, returns_20d, volume_change,
         mode, analyzed_at, full_data)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, ?)
    """, (
        analysis["symbol"],
        analysis["sector"],
        analysis["signal"],
        analysis["confidence_pct"],
        analysis["prob_up"],
        analysis["current_price"],
        indicators.get("rsi"),
        indicators.get("macd"),
        indicators.get("returns_5d") or indicators.get("returns_5"),
        indicators.get("returns_20d"),
        indicators.get("volume_change"),
        analysis["mode"],
        json.dumps(analysis),
    ))
    
    conn.commit()
    conn.close()


# ═══════════════════════════════════════════════════════════════
#   BATCH SCANNING
# ═══════════════════════════════════════════════════════════════

def scan_universe(tier: str = "tier2", mode: str = "swing") -> Dict:
    """
    Scan entire universe and cache results.
    
    Args:
        tier: 'tier1', 'tier2', 'tier3', 'full'
        mode: 'swing' or 'intraday'
    """
    init_screener_tables()
    
    symbols = get_scan_universe(tier)
    start_time = time.time()
    
    logger.info(f"🔍 Screener: scanning {len(symbols)} stocks ({tier}, {mode})...")
    
    successful = 0
    failed = 0
    errors = []
    
    # Parallel scanning
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {
            executor.submit(analyze_single_stock, symbol, mode): symbol
            for symbol in symbols
        }
        
        for i, future in enumerate(as_completed(futures)):
            symbol = futures[future]
            try:
                result = future.result(timeout=SCAN_TIMEOUT)
                
                if result.get("status") == "success":
                    save_analysis(result)
                    successful += 1
                    
                    if (i + 1) % 25 == 0:
                        logger.info(f"   Progress: {i+1}/{len(symbols)} ({successful} success)")
                else:
                    failed += 1
                    errors.append({
                        "symbol": symbol,
                        "error": result.get("error", "Unknown"),
                    })
            except Exception as e:
                failed += 1
                errors.append({"symbol": symbol, "error": str(e)[:100]})
    
    elapsed = round(time.time() - start_time, 1)
    
    # Log run
    conn = get_connection()
    conn.execute("""
        INSERT INTO screener_runs 
        (tier, mode, stocks_scanned, successful, failed, duration_seconds)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (tier, mode, len(symbols), successful, failed, elapsed))
    conn.commit()
    conn.close()
    
    logger.info(
        f"✅ Screener complete in {elapsed}s: "
        f"{successful} success, {failed} failed"
    )
    
    return {
        "tier": tier,
        "mode": mode,
        "total_scanned": len(symbols),
        "successful": successful,
        "failed": failed,
        "duration_seconds": elapsed,
        "errors": errors[:10],  # Only return first 10 errors
    }


# ═══════════════════════════════════════════════════════════════
#   QUERY FUNCTIONS (For Frontend)
# ═══════════════════════════════════════════════════════════════

def get_all_analyzed_stocks(
    signal: Optional[str] = None,
    sector: Optional[str] = None,
    min_confidence: float = 0,
    sort_by: str = "confidence",
    order: str = "desc",
    limit: int = 500,
) -> List[Dict]:
    """
    Get analyzed stocks with filters.
    
    Args:
        signal: 'BUY', 'SELL', 'HOLD' or None for all
        sector: sector name or None
        min_confidence: minimum confidence %
        sort_by: 'confidence', 'price', 'symbol', 'returns_5d'
        order: 'asc' or 'desc'
    """
    conn = get_connection()
    
    # Build query
    query = "SELECT * FROM stock_analysis WHERE 1=1"
    params = []
    
    if signal and signal != "ALL":
        query += " AND signal = ?"
        params.append(signal)
    
    if sector and sector != "ALL":
        query += " AND sector = ?"
        params.append(sector)
    
    if min_confidence > 0:
        query += " AND confidence_pct >= ?"
        params.append(min_confidence)
    
    # Sort
    sort_column = {
        "confidence": "confidence_pct",
        "price": "current_price",
        "symbol": "symbol",
        "returns_5d": "returns_5d",
        "rsi": "rsi",
    }.get(sort_by, "confidence_pct")
    
    query += f" ORDER BY {sort_column} {'DESC' if order == 'desc' else 'ASC'}"
    query += f" LIMIT ?"
    params.append(limit)
    
    rows = conn.execute(query, params).fetchall()
    conn.close()
    
    return [dict(r) for r in rows]


def get_stock_analysis(symbol: str) -> Optional[Dict]:
    """Get analysis for a specific stock."""
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM stock_analysis WHERE symbol = ?",
        (symbol,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def get_screener_stats() -> Dict:
    """Get screener statistics."""
    conn = get_connection()
    
    # Total analyzed
    total = conn.execute("SELECT COUNT(*) as c FROM stock_analysis").fetchone()["c"]
    
    # By signal
    signals = conn.execute("""
        SELECT signal, COUNT(*) as count 
        FROM stock_analysis 
        GROUP BY signal
    """).fetchall()
    
    signal_counts = {row["signal"]: row["count"] for row in signals}
    
    # By sector
    sectors = conn.execute("""
        SELECT sector, COUNT(*) as count 
        FROM stock_analysis 
        GROUP BY sector 
        ORDER BY count DESC
    """).fetchall()
    
    # Latest run
    latest_run = conn.execute("""
        SELECT * FROM screener_runs 
        ORDER BY run_time DESC 
        LIMIT 1
    """).fetchone()
    
    # High confidence stocks
    high_conf = conn.execute("""
        SELECT COUNT(*) as c 
        FROM stock_analysis 
        WHERE confidence_pct >= 70
    """).fetchone()["c"]
    
    conn.close()
    
    return {
        "total_analyzed": total,
        "high_confidence": high_conf,
        "by_signal": signal_counts,
        "by_sector": [{"sector": s["sector"], "count": s["count"]} for s in sectors],
        "last_run": dict(latest_run) if latest_run else None,
    }


def get_top_picks(mode: str = "swing", limit: int = 10) -> Dict:
    """Get top BUY/SELL picks."""
    conn = get_connection()
    
    top_buys = conn.execute("""
        SELECT * FROM stock_analysis
        WHERE signal = 'BUY' AND confidence_pct >= 60
        ORDER BY confidence_pct DESC
        LIMIT ?
    """, (limit,)).fetchall()
    
    top_sells = conn.execute("""
        SELECT * FROM stock_analysis
        WHERE signal = 'SELL' AND confidence_pct >= 60
        ORDER BY confidence_pct DESC
        LIMIT ?
    """, (limit,)).fetchall()
    
    conn.close()
    
    return {
        "top_buys": [dict(r) for r in top_buys],
        "top_sells": [dict(r) for r in top_sells],
    }


# ═══════════════════════════════════════════════════════════════
#   Quick Test
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("\n" + "="*60)
    print("SCREENER TEST")
    print("="*60)
    
    # Initialize
    init_screener_tables()
    
    print("\n🔍 Running scan on Nifty 50 (tier1)...")
    result = scan_universe(tier="tier1", mode="swing")
    
    print(f"\n✅ Result:")
    for k, v in result.items():
        if k != "errors":
            print(f"   {k}: {v}")
    
    print(f"\n📊 Stats:")
    stats = get_screener_stats()
    print(f"   Total analyzed: {stats['total_analyzed']}")
    print(f"   High confidence: {stats['high_confidence']}")
    print(f"   By signal: {stats['by_signal']}")
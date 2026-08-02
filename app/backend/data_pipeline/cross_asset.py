# E:\tradedo\app\backend\data_pipeline\cross_asset.py

"""
Cross-asset data fetcher for v3 intraday model.
Fetches Nifty, VIX, USD/INR, Crude, and 8 sector indices.
Cached daily — updates once per day at market open.
"""

import logging
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
from typing import Optional
from pathlib import Path
import pickle
import threading

logger = logging.getLogger("tradedo.cross_asset")


# ─── Configuration ────────────────────────────────────────────
CACHE_DIR = Path(__file__).resolve().parent.parent.parent.parent / "data" / "cache"
CACHE_FILE = CACHE_DIR / "cross_asset_daily.pkl"
CACHE_TTL_HOURS = 6   # Refresh every 6 hours

# All required tickers
TICKERS = {
    "nifty":   "^NSEI",
    "vix":     "^INDIAVIX",
    "usdinr": "INR=X",
    "crude":  "CL=F",
}

SECTORS = {
    "it":     "^CNXIT",
    "bank":   "^NSEBANK",
    "auto":   "^CNXAUTO",
    "pharma": "^CNXPHARMA",
    "fmcg":   "^CNXFMCG",
    "metal":  "^CNXMETAL",
    "energy": "^CNXENERGY",
    "realty": "^CNXREALTY",
}


# ─── Thread-safe cache ────────────────────────────────────────
_cache_lock = threading.Lock()
_cross_asset_cache: Optional[pd.DataFrame] = None
_cache_timestamp: Optional[datetime] = None


def _ensure_cache_dir():
    """Ensure cache directory exists."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)


def _download_ticker(symbol: str, start: str, end: str) -> Optional[pd.DataFrame]:
    """Safely download data for one ticker."""
    try:
        df = yf.download(
            symbol,
            start=start,
            end=end,
            interval="1d",
            progress=False,
            auto_adjust=True,
        )
        
        if df.empty:
            return None
        
        # Flatten multi-index columns
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        
        df.index = pd.to_datetime(df.index).normalize()
        return df
    
    except Exception as e:
        logger.warning(f"Failed to download {symbol}: {e}")
        return None


def build_cross_asset_data() -> pd.DataFrame:
    """
    Build complete cross-asset dataframe.
    Fetches all required tickers and computes features.
    """
    logger.info("🌐 Building cross-asset data (this takes 30-60 seconds)...")
    
    # 400 days for 252-day rolling percentile + buffer
    end_date   = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=400)).strftime("%Y-%m-%d")
    
    result = pd.DataFrame()
    
    # ── Nifty features ────────────────────────────────────────
    nifty = _download_ticker(TICKERS["nifty"], start_date, end_date)
    if nifty is not None and not nifty.empty:
        result["nifty_close"] = nifty["Close"]
        result["nifty_return"] = nifty["Close"].pct_change()
        
        nifty_ema200 = nifty["Close"].ewm(span=200).mean()
        result["nifty_dist_ema200"] = (
            (nifty["Close"] - nifty_ema200) / nifty_ema200 * 100
        )
        
        # Market regime: -1 bear, 0 sideways, 1 bull
        result["market_regime"] = result["nifty_dist_ema200"].apply(
            lambda x: 1 if x > 5 else (-1 if x < -5 else 0)
        )
        logger.info("  ✓ Nifty data")
    else:
        # Fallback values
        result["nifty_return"] = 0.0
        result["nifty_dist_ema200"] = 0.0
        result["market_regime"] = 0
        logger.warning("  ✗ Nifty fetch failed - using defaults")
    
    # ── VIX percentile ────────────────────────────────────────
    vix = _download_ticker(TICKERS["vix"], start_date, end_date)
    if vix is not None and not vix.empty:
        result["vix_close"] = vix["Close"]
        result["vix_percentile"] = (
            vix["Close"].rolling(252, min_periods=30).rank(pct=True) * 100
        )
        logger.info("  ✓ VIX data")
    else:
        result["vix_percentile"] = 50.0  # Neutral default
        logger.warning("  ✗ VIX fetch failed - using defaults")
    
    # ── USD/INR ───────────────────────────────────────────────
    usdinr = _download_ticker(TICKERS["usdinr"], start_date, end_date)
    if usdinr is not None and not usdinr.empty:
        result["usdinr_change"] = usdinr["Close"].pct_change()
        logger.info("  ✓ USD/INR data")
    else:
        result["usdinr_change"] = 0.0
        logger.warning("  ✗ USD/INR fetch failed - using defaults")
    
    # ── Crude Oil ─────────────────────────────────────────────
    crude = _download_ticker(TICKERS["crude"], start_date, end_date)
    if crude is not None and not crude.empty:
        result["crude_change"] = crude["Close"].pct_change()
        logger.info("  ✓ Crude data")
    else:
        result["crude_change"] = 0.0
        logger.warning("  ✗ Crude fetch failed - using defaults")
    
    # ── Sector Returns ────────────────────────────────────────
    for sec_name, sec_ticker in SECTORS.items():
        col_name = f"sector_{sec_name}_return"
        
        sec_df = _download_ticker(sec_ticker, start_date, end_date)
        if sec_df is not None and not sec_df.empty:
            result[col_name] = sec_df["Close"].pct_change()
            logger.info(f"  ✓ Sector {sec_name}: {len(sec_df)} days")
        else:
            result[col_name] = 0.0
            logger.warning(f"  ✗ {sec_name} sector fetch failed - using defaults")
            
    # ── Fill remaining NaN with 0 (safe default) ──────────────
    sector_cols = [f"sector_{s}_return" for s in SECTORS.keys()]
    result[sector_cols] = result[sector_cols].fillna(0)
    
    # Forward fill for holidays (max 3 days)
    result = result.ffill(limit=3)
    
    # Drop rows before we have enough data
    result = result.dropna(subset=["nifty_return"], how="all")
    
    logger.info(f"✅ Cross-asset data built: {len(result)} days")
    return result


def _save_cache(data: pd.DataFrame):
    """Save cross-asset data to disk cache."""
    _ensure_cache_dir()
    try:
        with open(CACHE_FILE, "wb") as f:
            pickle.dump({
                "data": data,
                "timestamp": datetime.now(),
            }, f)
        logger.info(f"💾 Cross-asset cache saved to {CACHE_FILE}")
    except Exception as e:
        logger.error(f"Cache save failed: {e}")


def _load_cache() -> Optional[dict]:
    """Load cross-asset data from disk cache."""
    if not CACHE_FILE.exists():
        return None
    
    try:
        with open(CACHE_FILE, "rb") as f:
            return pickle.load(f)
    except Exception as e:
        logger.warning(f"Cache load failed: {e}")
        return None


def _is_cache_valid(cached_time: datetime) -> bool:
    """Check if cache is still fresh."""
    age = datetime.now() - cached_time
    return age.total_seconds() < (CACHE_TTL_HOURS * 3600)


def get_cross_asset_data(force_refresh: bool = False) -> pd.DataFrame:
    """
    Get cross-asset data (cached).
    
    Args:
        force_refresh: If True, ignores cache and fetches fresh
    
    Returns:
        DataFrame with cross-asset features
    """
    global _cross_asset_cache, _cache_timestamp
    
    with _cache_lock:
        # Check in-memory cache first
        if not force_refresh and _cross_asset_cache is not None:
            if _cache_timestamp and _is_cache_valid(_cache_timestamp):
                return _cross_asset_cache.copy()
        
        # Try disk cache
        if not force_refresh:
            cached = _load_cache()
            if cached and _is_cache_valid(cached["timestamp"]):
                _cross_asset_cache = cached["data"]
                _cache_timestamp = cached["timestamp"]
                logger.info(f"📂 Cross-asset loaded from disk cache")
                return _cross_asset_cache.copy()
        
        # Build fresh
        logger.info("🔄 Building fresh cross-asset data...")
        data = build_cross_asset_data()
        
        # Cache it
        _cross_asset_cache = data
        _cache_timestamp = datetime.now()
        _save_cache(data)
        
        return data.copy()


def refresh_cross_asset_data():
    """Force refresh — call from scheduler once per day."""
    logger.info("🔄 Force refreshing cross-asset data...")
    get_cross_asset_data(force_refresh=True)


# ─── Quick Test ───────────────────────────────────────────────
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("\nFetching cross-asset data...")
    data = get_cross_asset_data(force_refresh=True)
    
    print(f"\n✅ Rows: {len(data)}")
    print(f"✅ Columns: {list(data.columns)}")
    print(f"\nLatest values:")
    print(data.tail(3))
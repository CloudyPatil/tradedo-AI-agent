# E:\tradedo\app\backend\ml\engine.py

# ─── Path Setup (must be first) ──────────────────────────────
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import joblib
import numpy as np
import pandas as pd
import yfinance as yf
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import ta
from ta.momentum   import RSIIndicator, StochasticOscillator
from ta.trend      import MACD, EMAIndicator, SMAIndicator
from ta.volatility import BollingerBands, AverageTrueRange
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("tradedo.engine")

# ─── Paths ────────────────────────────────────────────────────
BASE_DIR   = Path(__file__).resolve().parent.parent.parent.parent
MODELS_DIR = BASE_DIR / "models"


# ═══════════════════════════════════════════════════════════════
#   MODEL LOADER (Updated for v3)
# ═══════════════════════════════════════════════════════════════

class ModelStore:
    """Load and cache all models."""
    _swing_model      = None
    _swing_features   = None
    _intraday_model   = None
    _intraday_features = None

    @classmethod
    def load_all(cls):
        logger.info(f"Loading models from: {MODELS_DIR}")

        # Swing v2 (unchanged)
        swing_path  = MODELS_DIR / "lgbm_v2.pkl"
        s_feat_path = MODELS_DIR / "features_v2.pkl"
        
        # Intraday v3 (NEW!)
        intra_path  = MODELS_DIR / "lgbm_intraday_v3.pkl"
        i_feat_path = MODELS_DIR / "features_intraday_v3.pkl"

        for p in [swing_path, s_feat_path, intra_path, i_feat_path]:
            if not p.exists():
                raise FileNotFoundError(f"❌ Missing: {p}")

        cls._swing_model       = joblib.load(swing_path)
        cls._swing_features    = joblib.load(s_feat_path)
        cls._intraday_model    = joblib.load(intra_path)
        cls._intraday_features = joblib.load(i_feat_path)

        logger.info(f"✅ Models loaded")
        logger.info(f"   Swing v2:    {len(cls._swing_features)} features")
        logger.info(f"   Intraday v3: {len(cls._intraday_features)} features")

    @classmethod
    def get_swing(cls):
        if cls._swing_model is None:
            cls.load_all()
        return cls._swing_model, cls._swing_features

    @classmethod
    def get_intraday(cls):
        if cls._intraday_model is None:
            cls.load_all()
        return cls._intraday_model, cls._intraday_features


# ═══════════════════════════════════════════════════════════════
#   DATA FETCHERS
# ═══════════════════════════════════════════════════════════════

def fetch_swing_data(symbol: str) -> pd.DataFrame:
    """Fetch 1yr daily + update with live price."""
    logger.info(f"Fetching swing data for {symbol}")
    
    df = yf.download(
        symbol, period="1y", interval="1d",
        auto_adjust=True, progress=False
    )

    if df.empty:
        raise ValueError(f"No data for {symbol}")

    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.droplevel(1)

    df.dropna(inplace=True)
    
    # Update last candle with live price
    try:
        ticker = yf.Ticker(symbol)
        live_price = ticker.fast_info.get("last_price")
        if live_price and live_price > 0:
            df.loc[df.index[-1], "Close"] = float(live_price)
    except Exception as e:
        logger.warning(f"Live price fetch failed: {e}")
    
    return df


def fetch_intraday_data(symbol: str) -> pd.DataFrame:
    """
    Fetch 7 days of 5-min data for v3 intraday model.
    Need enough for 200-period rolling ATR percentile.
    """
    logger.info(f"Fetching intraday data for {symbol}")
    
    df = yf.download(
        symbol,
        period="7d",       # 7 days = ~525 candles (enough for 200-period rolling)
        interval="5m",
        auto_adjust=True,
        progress=False
    )

    if df.empty:
        raise ValueError(f"No intraday data for {symbol}")

    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.droplevel(1)

    df.dropna(inplace=True)
    
    logger.info(f"  → {len(df)} 5-min candles")
    return df


# ═══════════════════════════════════════════════════════════════
#   SWING FEATURES (v2 - unchanged)
# ═══════════════════════════════════════════════════════════════

def compute_swing_features(df: pd.DataFrame) -> pd.DataFrame:
    """Compute 20 swing features for v2 model (unchanged)."""
    df = df.copy()
    
    close, high, low, volume = df["Close"], df["High"], df["Low"], df["Volume"]

    df["rsi"]      = RSIIndicator(close, window=14).rsi()
    df["rsi_lag1"] = df["rsi"].shift(1)
    df["rsi_lag2"] = df["rsi"].shift(2)

    stoch = StochasticOscillator(high, low, close, window=14)
    df["stoch"] = stoch.stoch()

    macd_obj = MACD(close)
    df["macd"]        = macd_obj.macd()
    df["macd_signal"] = macd_obj.macd_signal()
    df["macd_diff"]   = macd_obj.macd_diff()

    df["ema20"]  = EMAIndicator(close, window=20).ema_indicator()
    df["sma50"]  = SMAIndicator(close, window=50).sma_indicator()
    df["sma200"] = SMAIndicator(close, window=200).sma_indicator()

    df["atr"] = AverageTrueRange(high, low, close, window=14).average_true_range()

    bb = BollingerBands(close, window=20)
    df["bb_width"] = bb.bollinger_wband()

    df["volume_change"] = volume.pct_change()
    df["obv"] = ta.volume.OnBalanceVolumeIndicator(close, volume).on_balance_volume()

    df["returns"]     = close.pct_change()
    df["returns_5d"]  = close.pct_change(5)
    df["returns_10d"] = close.pct_change(10)
    df["returns_20d"] = close.pct_change(20)

    df["close_ema20_ratio"] = close / df["ema20"]
    df["close_sma50_ratio"] = close / df["sma50"]

    df.dropna(inplace=True)
    return df


# ═══════════════════════════════════════════════════════════════
#   INTRADAY v3 FEATURES (NEW - 49 features!)
# ═══════════════════════════════════════════════════════════════

def compute_intraday_features_v3(
    df_stock: pd.DataFrame,
    cross_asset: pd.DataFrame,
) -> pd.DataFrame:
    """
    Compute all 49 intraday v3 features.
    EXACT replication of training code.
    """
    df = df_stock.copy()
    
    # Ensure clean index
    df.index = pd.to_datetime(df.index)
    if df.index.tz is not None:
        df.index = df.index.tz_localize(None)
    df = df.sort_index()
    
    df = df[df["Close"] > 0].dropna(
        subset=["Close", "High", "Low", "Open", "Volume"]
    )
    
    if len(df) < 100:
        return pd.DataFrame()
    
    close  = df["Close"]
    high   = df["High"]
    low    = df["Low"]
    volume = df["Volume"]
    open_  = df["Open"]
    
    feat = pd.DataFrame(index=df.index)
    
    # ── MOMENTUM ──────────────────────────────────────────────
    rsi_ind = RSIIndicator(close=close, window=14)
    feat["rsi"]          = rsi_ind.rsi()
    feat["rsi_lag1"]     = feat["rsi"].shift(1)
    feat["rsi_lag2"]     = feat["rsi"].shift(2)
    feat["rsi_momentum"] = feat["rsi"] - feat["rsi"].shift(3)
    feat["rsi_regime"]   = pd.cut(
        feat["rsi"].fillna(50),
        bins=[0, 30, 45, 55, 70, 100],
        labels=[0, 1, 2, 3, 4]
    ).astype(float)
    
    stoch = StochasticOscillator(high=high, low=low, close=close, window=14)
    feat["stoch"] = stoch.stoch()
    
    # ── MACD ──────────────────────────────────────────────────
    macd_ind = MACD(close=close)
    feat["macd"]        = macd_ind.macd()
    feat["macd_signal"] = macd_ind.macd_signal()
    feat["macd_diff"]   = macd_ind.macd_diff()
    
    # ── PRICE RATIOS ──────────────────────────────────────────
    ema9  = EMAIndicator(close=close, window=9).ema_indicator()
    ema20 = EMAIndicator(close=close, window=20).ema_indicator()
    sma50 = SMAIndicator(close=close, window=50).sma_indicator()
    
    feat["close_ema9_ratio"]  = close / ema9.replace(0, np.nan)
    feat["close_ema20_ratio"] = close / ema20.replace(0, np.nan)
    feat["close_sma50_ratio"] = close / sma50.replace(0, np.nan)
    
    # ── VOLATILITY ────────────────────────────────────────────
    atr_ind = AverageTrueRange(high=high, low=low, close=close, window=14)
    atr = atr_ind.average_true_range()
    feat["atr_pct"] = atr / close.replace(0, np.nan) * 100
    feat["atr_percentile"] = (
        atr.rolling(200, min_periods=50).rank(pct=True) * 100
    )
    
    bb = BollingerBands(close=close, window=20)
    feat["bb_width"] = bb.bollinger_wband()
    feat["bb_pct"]   = bb.bollinger_pband()
    
    # ── VOLUME ────────────────────────────────────────────────
    vol_mean = volume.rolling(20, min_periods=5).mean()
    vol_std  = volume.rolling(20, min_periods=5).std()
    
    feat["volume_change"] = volume.pct_change()
    feat["volume_zscore"] = (
        (volume - vol_mean) / vol_std.replace(0, np.nan)
    )
    feat["volume_trend"] = (
        volume.rolling(5, min_periods=2).mean() / vol_mean.replace(0, np.nan)
    )
    
    # ── RETURNS ───────────────────────────────────────────────
    feat["returns"]      = close.pct_change()
    feat["returns_5"]    = close.pct_change(5)
    feat["returns_10"]   = close.pct_change(10)
    feat["returns_20"]   = close.pct_change(20)
    feat["return_accel"] = feat["returns"] - feat["returns"].shift(1)
    
    # ── TIME FEATURES ─────────────────────────────────────────
    hours   = np.array(feat.index.hour, dtype=float)
    minutes = np.array(feat.index.minute, dtype=float)
    dow     = np.array(feat.index.dayofweek, dtype=float)
    
    feat["hour"]        = hours
    feat["minute"]      = minutes
    feat["day_of_week"] = dow
    
    # Session progress (UTC: NSE opens 3:45, closes 10:00)
    mins_since_open = np.clip(
        (hours - 3) * 60 + (minutes - 45),
        0, 375
    )
    feat["session_progress"] = np.clip(mins_since_open / 375, 0.0, 1.0)
    feat["is_opening"] = (mins_since_open <= 30).astype(int)
    feat["is_closing"] = (mins_since_open >= 345).astype(int)
    
    # ── INTRADAY POSITION ─────────────────────────────────────
    date_key = feat.index.normalize()
    
    s_high = pd.Series(high.values, index=date_key)
    s_low  = pd.Series(low.values, index=date_key)
    
    d_high = s_high.groupby(level=0).transform("max")
    d_low  = s_low.groupby(level=0).transform("min")
    d_high.index = feat.index
    d_low.index  = feat.index
    
    d_range = (d_high - d_low).replace(0, np.nan)
    feat["intraday_position"] = (close - d_low) / d_range
    
    # ── GAP % ─────────────────────────────────────────────────
    s_close = pd.Series(close.values, index=date_key)
    first_c = s_close.groupby(level=0).transform("first")
    first_c.index = feat.index
    prev_fc = first_c.shift(1)
    feat["gap_pct"] = (
        (first_c - prev_fc) / prev_fc.replace(0, np.nan) * 100
    )
    
    # ── VWAP RATIO ────────────────────────────────────────────
    typical = (high + low + close) / 3
    tp_vol  = typical * volume
    
    s_tpvol   = pd.Series(tp_vol.values, index=date_key)
    s_vol     = pd.Series(volume.values, index=date_key)
    cum_tpvol = s_tpvol.groupby(level=0).cumsum()
    cum_vol   = s_vol.groupby(level=0).cumsum()
    cum_tpvol.index = feat.index
    cum_vol.index   = feat.index
    
    vwap = cum_tpvol / cum_vol.replace(0, np.nan)
    feat["vwap_ratio"] = close / vwap.replace(0, np.nan)
    
    # ── CONSECUTIVE CANDLES ───────────────────────────────────
    is_green = (close > open_).values
    consec_g, consec_r = [], []
    g_count = r_count = 0
    for green in is_green:
        if green:
            g_count += 1
            r_count  = 0
        else:
            r_count += 1
            g_count  = 0
        consec_g.append(g_count)
        consec_r.append(r_count)
    feat["consec_green"] = consec_g
    feat["consec_red"]   = consec_r
    
    # ── CROSS-ASSET (daily merged to intraday) ────────────────
    cross_cols = [
        "market_regime", "vix_percentile",
        "nifty_dist_ema200", "nifty_return",
        "usdinr_change", "crude_change",
        "sector_it_return", "sector_bank_return",
        "sector_auto_return", "sector_pharma_return",
        "sector_fmcg_return", "sector_metal_return",
        "sector_energy_return", "sector_realty_return",
    ]
    for col in cross_cols:
        if col in cross_asset.columns:
            merged = cross_asset[col].reindex(date_key, method="ffill")
            merged.index = feat.index
            feat[col] = merged.values
        else:
            feat[col] = 0.0
    
    # ── CLIP OUTLIERS (production version - fixed bounds) ─────
    clip_map = {
        "volume_change": (-0.99, 10.0),
        "volume_zscore": (-4.0, 4.0),
        "returns":       (-0.15, 0.15),
        "returns_5":     (-0.30, 0.30),
        "returns_10":    (-0.40, 0.40),
        "returns_20":    (-0.50, 0.50),
        "return_accel":  (-0.15, 0.15),
        "gap_pct":       (-10.0, 10.0),
        "macd":          (-5.0, 5.0),
        "macd_signal":   (-5.0, 5.0),
        "macd_diff":     (-5.0, 5.0),
    }
    for col, (lo, hi) in clip_map.items():
        if col in feat.columns:
            feat[col] = feat[col].clip(lo, hi)
    
    return feat


# ═══════════════════════════════════════════════════════════════
#   SIGNAL INTERPRETER
# ═══════════════════════════════════════════════════════════════

def interpret_signal(prob_up: float, mode: str = "swing") -> Dict:
    """Convert probability to signal."""
    # v3 intraday uses stricter thresholds
    if mode == "intraday":
        threshold_buy  = 0.65   # Or 0.70 for higher accuracy
        threshold_sell = 0.35
    else:
        threshold_buy  = 0.60
        threshold_sell = 0.40

    if prob_up >= threshold_buy:
        signal    = "BUY"
        strength  = "STRONG" if prob_up >= (threshold_buy + 0.08) else "MODERATE"
        emoji     = "🟢"
    elif prob_up <= threshold_sell:
        signal    = "SELL"
        strength  = "STRONG" if prob_up <= (threshold_sell - 0.08) else "MODERATE"
        emoji     = "🔴"
    else:
        signal   = "HOLD"
        strength = "NEUTRAL"
        emoji    = "🟡"

    confidence_pct = round(max(prob_up, 1 - prob_up) * 100, 2)

    return {
        "signal":         signal,
        "strength":       strength,
        "emoji":          emoji,
        "prob_up":        round(float(prob_up), 4),
        "prob_down":      round(float(1 - prob_up), 4),
        "confidence_pct": confidence_pct,
    }


# ═══════════════════════════════════════════════════════════════
#   PREDICTION FUNCTIONS
# ═══════════════════════════════════════════════════════════════

def predict_swing(symbol: str) -> Dict:
    """Swing prediction using v2 model."""
    model, features = ModelStore.get_swing()

    df = fetch_swing_data(symbol)
    df = compute_swing_features(df)

    if len(df) < 5:
        raise ValueError(f"Not enough data for {symbol}")

    latest = df.iloc[-1]
    X = pd.DataFrame([latest[features]])
    
    prob_up = model.predict_proba(X)[0][1]
    result = interpret_signal(prob_up, mode="swing")

    result.update({
        "symbol":        symbol,
        "mode":          "swing",
        "current_price": round(float(latest["Close"]), 2),
        "last_updated":  str(df.index[-1].date()),
        "model_version": "v2",
        "indicators": {
            "rsi":               round(float(latest["rsi"]), 2),
            "macd":              round(float(latest["macd"]), 4),
            "macd_signal":       round(float(latest["macd_signal"]), 4),
            "ema20":             round(float(latest["ema20"]), 2),
            "sma50":             round(float(latest["sma50"]), 2),
            "sma200":            round(float(latest["sma200"]), 2),
            "atr":               round(float(latest["atr"]), 4),
            "bb_width":          round(float(latest["bb_width"]), 4),
            "returns_5d":        round(float(latest["returns_5d"]) * 100, 2),
            "returns_20d":       round(float(latest["returns_20d"]) * 100, 2),
            "close_ema20_ratio": round(float(latest["close_ema20_ratio"]), 4),
        }
    })

    logger.info(f"[SWING v2] {symbol} → {result['emoji']} {result['signal']} ({result['confidence_pct']}%)")
    return result


def predict_intraday(symbol: str) -> Dict:
    """Intraday prediction using v3 model (49 features)."""
    from data_pipeline.cross_asset import get_cross_asset_data
    
    model, features = ModelStore.get_intraday()

    # 1. Fetch 5-min data
    df_stock = fetch_intraday_data(symbol)
    
    # 2. Get cross-asset data (cached)
    cross_asset = get_cross_asset_data()
    
    # 3. Compute all 49 features
    feat = compute_intraday_features_v3(df_stock, cross_asset)
    
    if feat.empty:
        raise ValueError(f"Feature computation failed for {symbol}")
    
    # 4. Get latest complete row (all features non-NaN)
    feat_clean = feat[features].dropna()
    
    if len(feat_clean) == 0:
        raise ValueError(f"No complete feature rows for {symbol}")
    
    latest_row = feat_clean.iloc[[-1]]
    
    # 5. Predict
    X = latest_row.astype(np.float32)
    prob_up = model.predict_proba(X)[0][1]
    
    # 6. Interpret with v3 thresholds
    result = interpret_signal(prob_up, mode="intraday")
    
    # 7. Add context
    latest_idx = feat_clean.index[-1]
    current_price = float(df_stock.loc[latest_idx, "Close"]) if latest_idx in df_stock.index else float(df_stock["Close"].iloc[-1])
    
    result.update({
        "symbol":        symbol,
        "mode":          "intraday",
        "current_price": round(current_price, 2),
        "last_updated":  str(latest_idx),
        "model_version": "v3",
        "features_count": len(features),
        "indicators": {
            "rsi":               round(float(latest_row["rsi"].iloc[0]), 2),
            "macd_diff":         round(float(latest_row["macd_diff"].iloc[0]), 4),
            "atr_pct":           round(float(latest_row["atr_pct"].iloc[0]), 4),
            "session_progress":  round(float(latest_row["session_progress"].iloc[0]), 3),
            "intraday_position": round(float(latest_row["intraday_position"].iloc[0]), 3),
            "vwap_ratio":        round(float(latest_row["vwap_ratio"].iloc[0]), 4),
            "market_regime":     int(latest_row["market_regime"].iloc[0]),
            "vix_percentile":    round(float(latest_row["vix_percentile"].iloc[0]), 1),
            "nifty_return":      round(float(latest_row["nifty_return"].iloc[0]) * 100, 2),
        }
    })
    
    logger.info(f"[INTRADAY v3] {symbol} → {result['emoji']} {result['signal']} ({result['confidence_pct']}%)")
    return result


def predict(symbol: str, mode: str = "swing") -> Dict:
    """Unified prediction entry point."""
    symbol = symbol.upper().strip()
    if not symbol.endswith(".NS") and not symbol.endswith(".BO"):
        symbol = symbol + ".NS"

    if mode == "intraday":
        return predict_intraday(symbol)
    else:
        return predict_swing(symbol)


# ═══════════════════════════════════════════════════════════════
#   COMPOSITE SCORING (keep existing)
# ═══════════════════════════════════════════════════════════════

def get_market_regime() -> str:
    """Detect Nifty 50 market regime."""
    try:
        nifty = yf.Ticker("^NSEI")
        df = nifty.history(period="3mo", interval="1d")

        if df.empty or len(df) < 20:
            return "NEUTRAL"

        price = float(df["Close"].iloc[-1])
        sma20 = float(df["Close"].rolling(20).mean().iloc[-1])
        sma50 = float(df["Close"].rolling(50).mean().iloc[-1])

        if price > sma20 and sma20 > sma50:
            return "BULLISH"
        elif price < sma20 and sma20 < sma50:
            return "BEARISH"
        else:
            return "NEUTRAL"
    except Exception as e:
        logger.warning(f"Market regime check failed: {e}")
        return "NEUTRAL"


def calculate_composite_score(
    ml_confidence: float,
    sentiment_score: float,
    volume_ratio: float,
    regime: str,
    signal: str
) -> Dict:
    """Composite scoring (0-90)."""
    ml_score = round(ml_confidence * 40, 1)

    if regime == "BULLISH" and signal == "BUY":
        regime_score = 20
    elif regime == "BEARISH" and signal == "SELL":
        regime_score = 20
    elif regime == "NEUTRAL":
        regime_score = 10
    else:
        regime_score = 0

    if volume_ratio >= 1.5:
        volume_score = 15
    elif volume_ratio >= 1.2:
        volume_score = 10
    elif volume_ratio >= 0.8:
        volume_score = 5
    else:
        volume_score = 0

    if signal == "BUY":
        raw = (sentiment_score + 1) / 2
    else:
        raw = (1 - sentiment_score) / 2
    sentiment_pts = round(raw * 15, 1)

    total = ml_score + regime_score + volume_score + sentiment_pts

    return {
        "composite_score": round(total, 1),
        "max_score":       90,
        "breakdown": {
            "ml_score":        ml_score,
            "regime_score":    regime_score,
            "volume_score":    volume_score,
            "sentiment_score": sentiment_pts,
        },
        "tradeable": total >= 65,
    }


def predict_full(symbol: str, mode: str = "swing") -> Dict:
    """Full prediction with news + sentiment + composite + trade plan."""
    from data_pipeline.news_data import fetch_rss_news
    from data_pipeline.sentiment import analyze_sentiment, generate_trade_reasoning
    from ml.trade_planner import generate_trade_plan

    ml_result = predict(symbol, mode=mode)

    regime = get_market_regime()
    ml_result["market_regime"] = regime

    clean_symbol = symbol.replace(".NS", "").replace(".BO", "")
    articles = fetch_rss_news(clean_symbol, max_articles=8)

    sentiment = analyze_sentiment(articles)
    ml_result["sentiment"] = sentiment
    ml_result["news"] = articles[:5]

    indicators = ml_result.get("indicators", {})
    volume_ratio = 1.0  # Simplified for v3

    composite = calculate_composite_score(
        ml_confidence   = ml_result["confidence_pct"] / 100,
        sentiment_score = sentiment.get("score", 0),
        volume_ratio    = volume_ratio,
        regime          = regime,
        signal          = ml_result["signal"]
    )
    ml_result["composite"] = composite

    if ml_result["signal"] != "HOLD":
        reasoning = generate_trade_reasoning(ml_result, sentiment)
        ml_result["ai_reasoning"] = reasoning
    else:
        ml_result["ai_reasoning"] = (
            f"Model uncertain about {clean_symbol}. "
            f"Confidence {ml_result['confidence_pct']}% below threshold."
        )
    
    ml_result["trade_plan"] = generate_trade_plan(ml_result, mode=mode)

    logger.info(
        f"[FULL] {symbol} → {ml_result['emoji']} {ml_result['signal']} "
        f"| Composite: {composite['composite_score']}/90 "
        f"| Sentiment: {sentiment.get('label')}"
    )

    return ml_result


# ─── Quick Test ───────────────────────────────────────────────
if __name__ == "__main__":
    print("\n" + "="*55)
    print("  TRADEDO Engine Test (v3 Intraday)")
    print("="*55)

    print("\n📊 SWING prediction (RELIANCE)...")
    try:
        r = predict("RELIANCE", mode="swing")
        print(f"  {r['emoji']} {r['signal']} ({r['strength']})")
        print(f"  Price: ₹{r['current_price']}")
        print(f"  Confidence: {r['confidence_pct']}%")
    except Exception as e:
        print(f"  ❌ Failed: {e}")

    print("\n⚡ INTRADAY v3 prediction (RELIANCE)...")
    try:
        r = predict("RELIANCE", mode="intraday")
        print(f"  {r['emoji']} {r['signal']} ({r['strength']})")
        print(f"  Price: ₹{r['current_price']}")
        print(f"  Confidence: {r['confidence_pct']}%")
        print(f"  Model: {r.get('model_version')}")
        print(f"  Features used: {r.get('features_count')}")
    except Exception as e:
        print(f"  ❌ Failed: {e}")
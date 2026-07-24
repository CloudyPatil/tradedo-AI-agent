# E:\tradedo\app\backend\ml\engine.py

import joblib
import numpy as np
import pandas as pd
import yfinance as yf
from pathlib import Path
from datetime import datetime, timedelta
import ta
import logging
from typing import Dict, List, Optional

# ─── Logger Setup ─────────────────────────────────────────────
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("tradedo.engine")

# ─── Paths ────────────────────────────────────────────────────
BASE_DIR   = Path(__file__).resolve().parent.parent.parent.parent
MODELS_DIR = BASE_DIR / "models"

# ─── Load Models Once at Startup ──────────────────────────────
class ModelStore:
    """
    Singleton-style model loader.
    Models are loaded once into memory — no repeated disk I/O.
    """
    _swing_model      = None
    _swing_features   = None
    _intraday_model   = None
    _intraday_features = None

    @classmethod
    def load_all(cls):
        logger.info(f"Loading models from: {MODELS_DIR}")

        swing_path    = MODELS_DIR / "lgbm_v2.pkl"
        s_feat_path   = MODELS_DIR / "features_v2.pkl"
        intra_path    = MODELS_DIR / "lgbm_intraday.pkl"
        i_feat_path   = MODELS_DIR / "features_intraday.pkl"

        # Validate files exist
        for p in [swing_path, s_feat_path, intra_path, i_feat_path]:
            if not p.exists():
                raise FileNotFoundError(
                    f"❌ Model file missing: {p}\n"
                    f"   Download from Google Drive → E:\\tradedo\\models\\"
                )

        cls._swing_model       = joblib.load(swing_path)
        cls._swing_features    = joblib.load(s_feat_path)
        cls._intraday_model    = joblib.load(intra_path)
        cls._intraday_features = joblib.load(i_feat_path)

        logger.info("✅ All models loaded successfully")
        logger.info(f"   Swing features:    {len(cls._swing_features)}")
        logger.info(f"   Intraday features: {len(cls._intraday_features)}")

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


# ─── Data Fetcher ─────────────────────────────────────────────
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
    
    # ── Update last candle with LIVE price ────────────────
    try:
        ticker = yf.Ticker(symbol)
        live_price = ticker.fast_info.get("last_price")
        
        if live_price and live_price > 0:
            df.loc[df.index[-1], "Close"] = float(live_price)
            logger.info(f"  → Live price applied: ₹{live_price:.2f}")
    except Exception as e:
        logger.warning(f"Live price fetch failed: {e}")
    
    logger.info(f"  → {len(df)} candles")
    return df


def fetch_intraday_data(symbol: str) -> pd.DataFrame:
    """
    Fetch 60 days of 5-minute intraday data.
    yfinance limit: 60 days for 5min interval.
    """
    logger.info(f"Fetching intraday data for {symbol}")
    df = yf.download(
        symbol,
        period="60d",
        interval="5m",
        auto_adjust=True,
        progress=False
    )

    if df.empty:
        raise ValueError(f"No intraday data for {symbol}")

    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.droplevel(1)

    df.dropna(inplace=True)
    logger.info(f"  → {len(df)} intraday candles (5min) fetched")
    return df


# ─── Feature Engineering ──────────────────────────────────────
def compute_swing_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Reproduce EXACT same features used during Colab training.
    Order matters — must match features_v2.pkl list.
    """
    df = df.copy()

    close  = df["Close"]
    high   = df["High"]
    low    = df["Low"]
    volume = df["Volume"]

    # ── RSI ──────────────────────────────────────────────────
    df["rsi"]      = ta.momentum.RSIIndicator(close, window=14).rsi()
    df["rsi_lag1"] = df["rsi"].shift(1)
    df["rsi_lag2"] = df["rsi"].shift(2)

    # ── Stochastic ───────────────────────────────────────────
    stoch          = ta.momentum.StochasticOscillator(high, low, close, window=14)
    df["stoch"]    = stoch.stoch()

    # ── MACD ─────────────────────────────────────────────────
    macd_obj         = ta.trend.MACD(close)
    df["macd"]       = macd_obj.macd()
    df["macd_signal"] = macd_obj.macd_signal()
    df["macd_diff"]  = macd_obj.macd_diff()

    # ── Moving Averages ───────────────────────────────────────
    df["ema20"]  = ta.trend.EMAIndicator(close, window=20).ema_indicator()
    df["sma50"]  = ta.trend.SMAIndicator(close, window=50).sma_indicator()
    df["sma200"] = ta.trend.SMAIndicator(close, window=200).sma_indicator()

    # ── ATR ───────────────────────────────────────────────────
    df["atr"] = ta.volatility.AverageTrueRange(high, low, close, window=14).average_true_range()

    # ── Bollinger Band Width ───────────────────────────────────
    bb          = ta.volatility.BollingerBands(close, window=20)
    df["bb_width"] = bb.bollinger_wband()

    # ── Volume ────────────────────────────────────────────────
    df["volume_change"] = volume.pct_change()
    df["obv"]           = ta.volume.OnBalanceVolumeIndicator(close, volume).on_balance_volume()

    # ── Returns ───────────────────────────────────────────────
    df["returns"]    = close.pct_change()
    df["returns_5d"] = close.pct_change(5)
    df["returns_10d"] = close.pct_change(10)
    df["returns_20d"] = close.pct_change(20)

    # ── Price Ratios ──────────────────────────────────────────
    df["close_ema20_ratio"] = close / df["ema20"]
    df["close_sma50_ratio"] = close / df["sma50"]

    df.dropna(inplace=True)
    return df


def compute_intraday_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Intraday feature set — matches features_intraday.pkl exactly.
    """
    df = df.copy()

    close  = df["Close"]
    high   = df["High"]
    low    = df["Low"]
    volume = df["Volume"]

    # ── RSI ──────────────────────────────────────────────────
    df["rsi"]      = ta.momentum.RSIIndicator(close, window=14).rsi()
    df["rsi_lag1"] = df["rsi"].shift(1)

    # ── Stochastic ───────────────────────────────────────────
    stoch       = ta.momentum.StochasticOscillator(high, low, close, window=14)
    df["stoch"] = stoch.stoch()

    # ── MACD ─────────────────────────────────────────────────
    macd_obj          = ta.trend.MACD(close)
    df["macd"]        = macd_obj.macd()
    df["macd_signal"] = macd_obj.macd_signal()
    df["macd_diff"]   = macd_obj.macd_diff()

    # ── Moving Averages ───────────────────────────────────────
    df["ema20"] = ta.trend.EMAIndicator(close, window=20).ema_indicator()
    df["sma50"] = ta.trend.SMAIndicator(close, window=50).sma_indicator()

    # ── ATR ───────────────────────────────────────────────────
    df["atr"] = ta.volatility.AverageTrueRange(
        high, low, close, window=14
    ).average_true_range()

    # ── Bollinger Band Width ───────────────────────────────────
    bb             = ta.volatility.BollingerBands(close, window=20)
    df["bb_width"] = bb.bollinger_wband()

    # ── Volume ────────────────────────────────────────────────
    df["volume_change"] = volume.pct_change()

    # ── Returns ───────────────────────────────────────────────
    df["returns"]   = close.pct_change()
    df["returns_5"]  = close.pct_change(5)
    df["returns_10"] = close.pct_change(10)

    # ── Price Ratio ───────────────────────────────────────────
    df["close_ema_ratio"] = close / df["ema20"]

    df.dropna(inplace=True)
    return df


# ─── Signal Interpreter ───────────────────────────────────────
def interpret_signal(
    prob_up: float,
    mode: str = "swing"
) -> dict:
    """
    Convert raw probability to human-readable signal.

    Thresholds (from training analysis):
    - Swing:    BUY > 0.60, SELL < 0.40
    - Intraday: BUY > 0.65, SELL < 0.35
    """
    threshold_buy  = 0.60 if mode == "swing" else 0.65
    threshold_sell = 0.40 if mode == "swing" else 0.35

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

    confidence_pct = round(
        max(prob_up, 1 - prob_up) * 100, 2
    )

    return {
        "signal":         signal,
        "strength":       strength,
        "emoji":          emoji,
        "prob_up":        round(float(prob_up), 4),
        "prob_down":      round(float(1 - prob_up), 4),
        "confidence_pct": confidence_pct,
    }


# ─── Main Prediction Functions ────────────────────────────────
def predict_swing(symbol: str) -> dict:
    """
    Full swing (daily) prediction pipeline for any NSE stock.

    Returns:
        {
          symbol, mode, signal, strength, confidence_pct,
          prob_up, prob_down, current_price, last_updated,
          indicators: {rsi, macd, sma50, ...}
        }
    """
    model, features = ModelStore.get_swing()

    # 1. Fetch data
    df = fetch_swing_data(symbol)

    # 2. Compute indicators
    df = compute_swing_features(df)

    if len(df) < 5:
        raise ValueError(f"Not enough data after feature calc for {symbol}")

    # 3. Get LATEST row for prediction
    latest = df.iloc[-1]

    # 4. Build feature vector — EXACT order from training
    try:
        X = pd.DataFrame([latest[features]])
    except KeyError as e:
        missing = [f for f in features if f not in latest.index]
        raise ValueError(f"Missing features: {missing}") from e

    # 5. Predict
    prob_up = model.predict_proba(X)[0][1]   # class 1 = price goes up

    # 6. Interpret
    result = interpret_signal(prob_up, mode="swing")

    # 7. Add context
    result.update({
        "symbol":        symbol,
        "mode":          "swing",
        "current_price": round(float(latest["Close"]), 2),
        "last_updated":  str(df.index[-1].date()),
        "indicators": {
            "rsi":              round(float(latest["rsi"]), 2),
            "macd":             round(float(latest["macd"]), 4),
            "macd_signal":      round(float(latest["macd_signal"]), 4),
            "ema20":            round(float(latest["ema20"]), 2),
            "sma50":            round(float(latest["sma50"]), 2),
            "sma200":           round(float(latest["sma200"]), 2),
            "atr":              round(float(latest["atr"]), 4),
            "bb_width":         round(float(latest["bb_width"]), 4),
            "returns_5d":       round(float(latest["returns_5d"]) * 100, 2),
            "returns_20d":      round(float(latest["returns_20d"]) * 100, 2),
            "close_ema20_ratio": round(float(latest["close_ema20_ratio"]), 4),
        }
    })

    logger.info(
        f"[SWING] {symbol} → {result['emoji']} {result['signal']} "
        f"({result['confidence_pct']}% confidence)"
    )
    return result


def predict_intraday(symbol: str) -> dict:
    """
    Full intraday (5-min) prediction pipeline for any NSE stock.
    """
    model, features = ModelStore.get_intraday()

    # 1. Fetch intraday data
    df = fetch_intraday_data(symbol)

    # 2. Compute indicators
    df = compute_intraday_features(df)

    if len(df) < 5:
        raise ValueError(f"Not enough intraday data for {symbol}")

    # 3. Get latest candle
    latest = df.iloc[-1]

    # 4. Build feature vector
    try:
        X = pd.DataFrame([latest[features]])
    except KeyError as e:
        missing = [f for f in features if f not in latest.index]
        raise ValueError(f"Missing intraday features: {missing}") from e

    # 5. Predict
    prob_up = model.predict_proba(X)[0][1]

    # 6. Interpret
    result = interpret_signal(prob_up, mode="intraday")

    # 7. Add context
    result.update({
        "symbol":        symbol,
        "mode":          "intraday",
        "current_price": round(float(latest["Close"]), 2),
        "last_updated":  str(df.index[-1]),
        "indicators": {
            "rsi":            round(float(latest["rsi"]), 2),
            "macd":           round(float(latest["macd"]), 4),
            "macd_signal":    round(float(latest["macd_signal"]), 4),
            "ema20":          round(float(latest["ema20"]), 2),
            "sma50":          round(float(latest["sma50"]), 2),
            "atr":            round(float(latest["atr"]), 4),
            "bb_width":       round(float(latest["bb_width"]), 4),
            "returns_5":      round(float(latest["returns_5"]) * 100, 2),
            "close_ema_ratio": round(float(latest["close_ema_ratio"]), 4),
        }
    })

    logger.info(
        f"[INTRADAY] {symbol} → {result['emoji']} {result['signal']} "
        f"({result['confidence_pct']}% confidence)"
    )
    return result


# ─── Unified Predict (Auto-Route) ─────────────────────────────
def predict(symbol: str, mode: str = "swing") -> dict:
    """
    Single entry point for all predictions.
    
    Args:
        symbol: e.g. "TATAMOTORS.NS", "RELIANCE.NS", "TCS.NS"
        mode:   "swing" | "intraday"
    
    Returns:
        Full prediction dict
    """
    symbol = symbol.upper().strip()

    # Auto-add .NS suffix for Indian stocks if missing
    if not symbol.endswith(".NS") and not symbol.endswith(".BO"):
        symbol = symbol + ".NS"
        logger.info(f"Auto-appended .NS → {symbol}")

    if mode == "intraday":
        return predict_intraday(symbol)
    else:
        return predict_swing(symbol)


# ─── Quick Test ───────────────────────────────────────────────
if __name__ == "__main__":
    print("\n" + "="*55)
    print("  TRADEDO — Engine Test")
    print("="*55)

    # Test 1: Swing prediction
    print("\n📊 Testing SWING prediction (RELIANCE.NS)...")
    try:
        r = predict("RELIANCE", mode="swing")
        print(f"\n  {r['emoji']} Signal:     {r['signal']} ({r['strength']})")
        print(f"  💰 Price:      ₹{r['current_price']}")
        print(f"  📈 Confidence: {r['confidence_pct']}%")
        print(f"  🔼 Prob Up:    {r['prob_up']}")
        print(f"  🔽 Prob Down:  {r['prob_down']}")
        print(f"  📅 Updated:    {r['last_updated']}")
        print(f"\n  Indicators:")
        for k, v in r['indicators'].items():
            print(f"    {k:22s}: {v}")
    except Exception as e:
        print(f"  ❌ Swing test failed: {e}")

    # Test 2: Intraday prediction
    print("\n⚡ Testing INTRADAY prediction (TCS.NS)...")
    try:
        r2 = predict("TCS", mode="intraday")
        print(f"\n  {r2['emoji']} Signal:     {r2['signal']} ({r2['strength']})")
        print(f"  💰 Price:      ₹{r2['current_price']}")
        print(f"  📈 Confidence: {r2['confidence_pct']}%")
        print(f"  ⏱️  Updated:    {r2['last_updated']}")
    except Exception as e:
        print(f"  ❌ Intraday test failed: {e}")

    print("\n" + "="*55 + "\n")


# ─── ADD THIS TO BOTTOM OF engine.py ─────────────────────────

def calculate_composite_score(
    ml_confidence: float,
    sentiment_score: float,
    volume_ratio: float,
    regime: str,
    signal: str
) -> Dict:
    """
    Composite scoring system (0-100).
    Combines ML + Market Regime + Volume + Sentiment.

    Weights:
        ML Model:      40 pts
        Market Regime: 20 pts
        Volume:        15 pts
        Sentiment:     15 pts
        (Sector):      10 pts — simplified for now

    Returns dict with score + breakdown
    """
    # ── ML Score (0-40) ───────────────────────────────────────
    # prob_up or prob_down depending on signal
    ml_score = round(ml_confidence * 40, 1)

    # ── Regime Score (0-20) ───────────────────────────────────
    # Full points if signal aligns with regime
    # Zero if signal fights regime
    if regime == "BULLISH" and signal == "BUY":
        regime_score = 20
    elif regime == "BEARISH" and signal == "SELL":
        regime_score = 20
    elif regime == "NEUTRAL":
        regime_score = 10      # Neutral = half points
    else:
        regime_score = 0       # Fighting the market trend

    # ── Volume Score (0-15) ───────────────────────────────────
    # volume_ratio = current_vol / avg_vol
    if volume_ratio >= 1.5:
        volume_score = 15      # Strong volume confirmation
    elif volume_ratio >= 1.2:
        volume_score = 10
    elif volume_ratio >= 0.8:
        volume_score = 5       # Average volume
    else:
        volume_score = 0       # Low volume = weak signal

    # ── Sentiment Score (0-15) ────────────────────────────────
    # sentiment_score: -1.0 to 1.0
    if signal == "BUY":
        # For BUY signals, positive news = full score
        raw = (sentiment_score + 1) / 2  # Convert to 0-1
    else:
        # For SELL signals, negative news = full score
        raw = (1 - sentiment_score) / 2

    sentiment_pts = round(raw * 15, 1)

    # ── Total ─────────────────────────────────────────────────
    total = ml_score + regime_score + volume_score + sentiment_pts

    return {
        "composite_score":  round(total, 1),
        "max_score":        90,    # Sector not implemented yet
        "breakdown": {
            "ml_score":        ml_score,
            "regime_score":    regime_score,
            "volume_score":    volume_score,
            "sentiment_score": sentiment_pts,
        },
        "tradeable": total >= 65,   # Only trade if ≥ 65
    }


def get_market_regime() -> str:
    """
    Detect current Nifty 50 market regime.
    Returns: BULLISH | BEARISH | NEUTRAL
    """
    try:
        import yfinance as yf
        nifty = yf.Ticker("^NSEI")
        df    = nifty.history(period="3mo", interval="1d")

        if df.empty or len(df) < 20:
            return "NEUTRAL"

        price  = float(df["Close"].iloc[-1])
        sma20  = float(df["Close"].rolling(20).mean().iloc[-1])
        sma50  = float(df["Close"].rolling(50).mean().iloc[-1])

        if price > sma20 and sma20 > sma50:
            return "BULLISH"
        elif price < sma20 and sma20 < sma50:
            return "BEARISH"
        else:
            return "NEUTRAL"

    except Exception as e:
        logger.warning(f"Market regime check failed: {e}")
        return "NEUTRAL"


def predict_full(symbol: str, mode: str = "swing") -> Dict:
    """
    FULL prediction pipeline:
    ML Signal + News Sentiment + Composite Score + AI Reasoning

    This is the MAIN function for the API.
    predict() is kept for quick/raw predictions.
    """
    from data_pipeline.news_data import fetch_rss_news
    from data_pipeline.sentiment import analyze_sentiment, generate_trade_reasoning

    # 1. Get ML prediction
    ml_result = predict(symbol, mode=mode)

    # 2. Get market regime
    regime = get_market_regime()
    ml_result["market_regime"] = regime

    # 3. Fetch news
    clean_symbol = symbol.replace(".NS", "").replace(".BO", "")
    articles     = fetch_rss_news(clean_symbol, max_articles=8)

    # 4. Analyze sentiment
    sentiment = analyze_sentiment(articles)
    ml_result["sentiment"] = sentiment
    ml_result["news"]      = articles[:5]  # Return top 5 to frontend

    # 5. Calculate composite score
    indicators   = ml_result.get("indicators", {})
    volume_ratio = indicators.get("volume_change", 0) + 1.0

    composite = calculate_composite_score(
        ml_confidence  = ml_result["confidence_pct"] / 100,
        sentiment_score = sentiment.get("score", 0),
        volume_ratio   = volume_ratio,
        regime         = regime,
        signal         = ml_result["signal"]
    )
    ml_result["composite"] = composite

    # 6. Generate AI reasoning (only for BUY/SELL signals)
    if ml_result["signal"] != "HOLD":
        reasoning = generate_trade_reasoning(ml_result, sentiment)
        ml_result["ai_reasoning"] = reasoning
    else:
        ml_result["ai_reasoning"] = (
            f"Model is uncertain about {clean_symbol}. "
            f"Confidence {ml_result['confidence_pct']}% is below threshold. "
            f"Consider waiting for clearer signal."
        )

    # ── 7. ADD THIS: Generate Trade Plan ─────────────────────
    from ml.trade_planner import generate_trade_plan
    ml_result["trade_plan"] = generate_trade_plan(ml_result, mode=mode)

    logger.info(
        f"[FULL] {symbol} → {ml_result['emoji']} {ml_result['signal']} "
        f"| Composite: {composite['composite_score']}/90 "
        f"| Sentiment: {sentiment.get('label')}"
    )

    return ml_result
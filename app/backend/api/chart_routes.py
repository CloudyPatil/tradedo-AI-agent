# E:\tradedo\app\backend\api\chart_routes.py

from fastapi import APIRouter, HTTPException, Query
import yfinance as yf
import pandas as pd
import logging

logger = logging.getLogger("tradedo.chart")
router = APIRouter()


@router.get("/chart/{symbol}")
async def get_chart_data(
    symbol: str,
    mode: str = Query(default="swing", description="'swing' or 'intraday'"),
    period: str = Query(default="3mo", description="1mo, 3mo, 6mo, 1y")
):
    """
    Fetch OHLCV data formatted for Lightweight Charts.
    
    Returns:
        candles: [{time, open, high, low, close}]
        volume:  [{time, value, color}]
        overlays: {ema20, sma50, sma200}
    """
    # Auto-add .NS
    symbol = symbol.upper().strip()
    if not symbol.endswith(".NS") and not symbol.endswith(".BO"):
        symbol = symbol + ".NS"

    # Determine interval based on mode
    if mode == "intraday":
        interval = "5m"
        period   = "5d"       # Last 5 days of 5-min candles
    else:
        interval = "1d"
        # period stays as-is (default 3mo)

    try:
        df = yf.download(
            symbol,
            period=period,
            interval=interval,
            auto_adjust=True,
            progress=False,
        )

        if df.empty:
            raise HTTPException(status_code=404, detail=f"No data for {symbol}")

        # Flatten MultiIndex columns
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.droplevel(1)

        df.dropna(inplace=True)

        # ── Format candles for Lightweight Charts ────────────
        candles = []
        volume  = []

        for idx, row in df.iterrows():
            # Time format depends on interval
            if interval == "1d":
                time_val = idx.strftime("%Y-%m-%d")
            else:
                # For intraday, use UNIX timestamp
                time_val = int(idx.timestamp())

            open_p  = float(row["Open"])
            high_p  = float(row["High"])
            low_p   = float(row["Low"])
            close_p = float(row["Close"])
            vol     = int(row["Volume"])

            candles.append({
                "time":  time_val,
                "open":  round(open_p, 2),
                "high":  round(high_p, 2),
                "low":   round(low_p, 2),
                "close": round(close_p, 2),
            })

            # Volume with color (green if up, red if down)
            color = "#26A69A" if close_p >= open_p else "#EF5350"
            volume.append({
                "time":  time_val,
                "value": vol,
                "color": color,
            })

        # ── Calculate Moving Averages ────────────────────────
        df["ema20"]  = df["Close"].ewm(span=20, adjust=False).mean()
        df["sma50"]  = df["Close"].rolling(50).mean()
        df["sma200"] = df["Close"].rolling(200).mean()

        def to_line_data(series):
            data = []
            for idx, val in series.items():
                if pd.isna(val):
                    continue
                time_val = (
                    idx.strftime("%Y-%m-%d") if interval == "1d"
                    else int(idx.timestamp())
                )
                data.append({"time": time_val, "value": round(float(val), 2)})
            return data

        overlays = {
            "ema20":  to_line_data(df["ema20"]),
            "sma50":  to_line_data(df["sma50"]),
            "sma200": to_line_data(df["sma200"]),
        }

        logger.info(f"Chart data: {symbol} → {len(candles)} candles")

        return {
            "symbol":    symbol,
            "interval":  interval,
            "period":    period,
            "candles":   candles,
            "volume":    volume,
            "overlays":  overlays,
        }

    except Exception as e:
        logger.error(f"Chart fetch error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
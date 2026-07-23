import yfinance as yf
import pandas as pd
import os
from datetime import datetime
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.config import DATA_PATH
from data_pipeline.nifty500 import get_nifty500_symbols


STOCKS = get_nifty500_symbols()

STOCKS += ["^NSEI", "^BSESN", "^GSPC", "^IXIC"]

def fetch_historical(symbol, period="5y", interval="1d"):
    try:
        df = yf.download(symbol, period=period, interval=interval)
        if df.empty:
            print(f"No data: {symbol}")
            return None
        # Save to CSV
        path = os.path.join(DATA_PATH, "historical")
        os.makedirs(path, exist_ok=True)
        filename = symbol.replace("^","IDX_").replace(".","_")
        df.to_csv(f"{path}/{filename}.csv")
        print(f"✅ Saved: {symbol}")
        return df
    except Exception as e:
        print(f"❌ Error {symbol}: {e}")
        return None

def fetch_realtime(symbol):
    try:
        ticker = yf.Ticker(symbol)
        data = ticker.fast_info
        return {
            "symbol": symbol,
            "price": data.last_price,
            "volume": data.three_month_average_volume,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        print(f"❌ Realtime error {symbol}: {e}")
        return None

def fetch_all_historical():
    print("📥 Fetching historical data...")
    for stock in STOCKS:
        fetch_historical(stock)
    print("✅ Historical data complete!")

def fetch_all_realtime():
    results = []
    for stock in STOCKS:
        data = fetch_realtime(stock)
        if data:
            results.append(data)
    return results

if __name__ == "__main__":
    fetch_all_historical()
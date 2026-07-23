import requests
import pandas as pd

NSE_URL = "https://archives.nseindia.com/content/indices/ind_nifty500list.csv"

def get_nifty500_symbols():
    df = pd.read_csv(NSE_URL)
    symbols = df["Symbol"].tolist()
    # Add .NS suffix for yfinance
    symbols = [s + ".NS" for s in symbols]
    return symbols

if __name__ == "__main__":
    stocks = get_nifty500_symbols()
    print(f"Total Stocks: {len(stocks)}")
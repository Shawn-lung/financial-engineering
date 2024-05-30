
import yfinance as yf
import pandas as pd

tickers = ["4763.TW", "8069.TWO", "2881.TW", "2882.TW", "2330.TW", "TWN", "TLT", "GLD", "00632R.TW"]

def get_data(tickers, start_date="2019-05-26", end_date="2023-12-31"):
    data = {}
    for ticker in tickers:
        data[ticker] = yf.download(ticker, start=start_date, end=end_date)
    return data

if __name__ == "__main__":
    data = get_data(tickers)
    for ticker, df in data.items():
        df.to_csv(f"data/{ticker}.csv")

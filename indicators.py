
import pandas as pd

def calculate_indicators(df):
    df['EMA20'] = df['Close'].ewm(span=20, adjust=False).mean()
    df['EMA60'] = df['Close'].ewm(span=60, adjust=False).mean()
    df['MACD'] = df['Close'].ewm(span=12, adjust=False).mean() - df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD_signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
    df['ATR'] = df['High'].rolling(window=14).max() - df['Low'].rolling(window=14).min()
    return df

if __name__ == "__main__":
    tickers = ["4763.TW", "8069.TWO", "2881.TW", "2882.TW", "2330.TW", "TWN", "TLT", "GLD", "00632R.TW"]
    for ticker in tickers:
        df = pd.read_csv(f"data/{ticker}.csv", index_col="Date", parse_dates=True)
        df = calculate_indicators(df)
        print(df)
        df.to_csv(f"data/{ticker}_indicators.csv")

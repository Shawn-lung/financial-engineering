# indicators.py

import pandas as pd

def calculate_indicators(df):
    df['EMA20'] = df['Close'].ewm(span=20, adjust=False).mean()
    df['EMA60'] = df['Close'].ewm(span=60, adjust=False).mean()
    df['MACD'] = df['Close'].ewm(span=12, adjust=False).mean() - df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD_signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
    
    # 计算ATR
    df['High-Low'] = df['High'] - df['Low']
    df['High-Close'] = (df['High'] - df['Close'].shift()).abs()
    df['Low-Close'] = (df['Low'] - df['Close'].shift()).abs()
    df['TrueRange'] = df[['High-Low', 'High-Close', 'Low-Close']].max(axis=1)
    df['ATR'] = df['TrueRange'].rolling(window=14).mean()
    
    # 计算布林带
    df['MiddleBand'] = df['Close'].rolling(window=20).mean()
    df['UpperBand'] = df['MiddleBand'] + 2 * df['Close'].rolling(window=20).std()
    df['LowerBand'] = df['MiddleBand'] - 2 * df['Close'].rolling(window=20).std()
    
    # 计算KD指标
    low_list = df['Low'].rolling(window=9).min()
    high_list = df['High'].rolling(window=9).max()
    df['K'] = 100 * (df['Close'] - low_list) / (high_list - low_list)
    df['D'] = df['K'].rolling(window=3).mean()

    return df

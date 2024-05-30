# backtest.py

from data_fetcher import get_data
from indicators import calculate_indicators
from portfolio import Portfolio, trade_logic
import os
import pandas as pd
import matplotlib.pyplot as plt

# 確保數據目錄存在
os.makedirs("data", exist_ok=True)

tickers = ["4763.TW", "8069.TWO", "2881.TW", "2882.TW", "2330.TW", "TWN", "TLT", "GLD", "00632R.TW"]
data = get_data(tickers)

for ticker in data:
    data[ticker] = calculate_indicators(data[ticker])
    data[ticker].to_csv(f"data/{ticker}_indicators.csv")

allocation = {
    "4763.TW": 0.10,
    "8069.TW": 0.10,
    "2881.TW": 0.05,
    "2882.TW": 0.05,
    "2330.TW": 0.30,
    "TWN": 0.10,
    "TLT": 0.15,
    "GLD": 0.05,
    "00632R.TW": 0.10
}

portfolio = Portfolio(allocation=allocation)
trade_logic(data, portfolio)

# 保存交易歷史
history_df = pd.DataFrame(portfolio.history, columns=['Date', 'Ticker', 'Action', 'Amount', 'Price'])
history_df.to_csv("data/trade_history.csv", index=False)

# 保存每日資產總值
daily_values_df = pd.DataFrame(portfolio.daily_values, columns=['Date', 'Total Value'])
daily_values_df.to_csv("data/daily_values.csv", index=False)

# 保存每日各資產價值
daily_holdings_df = pd.DataFrame(portfolio.daily_holdings, columns=['Date', 'Holdings'])
daily_holdings_df.to_csv("data/daily_holdings.csv", index=False)

# 打印最終資產值
final_prices = {ticker: data[ticker].iloc[-1]['Close'] for ticker in data}
print(f"Final Portfolio Value: {portfolio.get_value(final_prices)}")

# 繪製每日資產總值隨時間的變化
daily_values_df['Date'] = pd.to_datetime(daily_values_df['Date'])

# 繪製資產績效和各資產佔比變化
fig, axs = plt.subplots(2, 1, figsize=(14, 14))

# 繪製總資產隨時間變化圖
axs[0].plot(daily_values_df['Date'], daily_values_df['Total Value'], label='Total Value')
axs[0].set_xlabel('Date')
axs[0].set_ylabel('Total Value')
axs[0].set_title('Portfolio Total Value Over Time')
axs[0].legend()
axs[0].grid(True)

# 繪製各資產比例隨時間變化圖
daily_holdings_df['Date'] = pd.to_datetime(daily_holdings_df['Date'])
holdings_dict = daily_holdings_df.set_index('Date')['Holdings'].to_dict()
holdings_df = pd.DataFrame.from_dict(holdings_dict, orient='index').fillna(0)
proportion_df = holdings_df.div(daily_values_df.set_index('Date')['Total Value'], axis=0)

proportion_df.plot(ax=axs[1], kind='area', stacked=True)
axs[1].set_xlabel('Date')
axs[1].set_ylabel('Proportion of Total Value')
axs[1].set_title('Proportion of Each Asset Over Time')
axs[1].legend(loc='upper left')
axs[1].grid(True)

plt.tight_layout()
plt.show()

# 計算收益率
initial_value = daily_values_df.iloc[0]['Total Value']
final_value = daily_values_df.iloc[-1]['Total Value']
return_rate = (final_value - initial_value) / initial_value * 100
print(f"Return Rate: {return_rate:.2f}%")

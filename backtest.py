# backtest.py

from data_fetcher import get_data
from indicators import calculate_indicators
from portfolio import Portfolio
import os
import pandas as pd
import matplotlib.pyplot as plt

# 确保数据目录存在
os.makedirs("data", exist_ok=True)

tickers = ["4763.TW", "8069.TWO", "2881.TW", "2882.TW", "2330.TW", "TWN", "TLT", "GLD", "00632R.TW"]
data = get_data(tickers)

for ticker in data:
    data[ticker] = calculate_indicators(data[ticker])
    data[ticker].to_csv(f"data/{ticker}_indicators.csv")

allocation = {
    "4763.TW": 0.10,
    "8069.TWO": 0.10,
    "2881.TW": 0.05,
    "2882.TW": 0.05,
    "2330.TW": 0.30,
    "TWN": 0.10,
    "TLT": 0.15,
    "GLD": 0.05,
    "00632R.TW": 0.10
}

def trade_logic(data, portfolio):
    initial_invested = False
    last_prices = {}

    for date in data['2330.TW'].index:
        prices = {}
        for ticker in data:
            if date in data[ticker].index:
                prices[ticker] = data[ticker].loc[date, 'Close']
                last_prices[ticker] = data[ticker].loc[date, 'Close']
            else:
                prices[ticker] = last_prices.get(ticker, None)
                if prices[ticker] is None:
                    print(f"Missing data for {ticker} on {date} and no previous value available")
                else:
                    print(f"Missing data for {ticker} on {date}, using previous value {prices[ticker]}")

        portfolio.update_daily_value(date, prices)

        # 初始进场逻辑
        if not initial_invested:
            initial_investment = portfolio.cash  # 初始投资总金额
            for ticker, alloc in portfolio.allocation.items():
                if prices.get(ticker) is not None:
                    amount_to_buy = (initial_investment * alloc) / prices[ticker]
                    portfolio.buy(date, ticker, prices[ticker], amount_to_buy)
                    print(f"Initial Buy: {amount_to_buy} of {ticker} at {prices[ticker]} on {date}")
            initial_invested = True

        # 交易逻辑
        for ticker in data:
            df = data[ticker]
            try:
                if ticker in ["2330.TW", "4763.TW", "8069.TWO", "2881.TW", "2882.TW"]:
                    if (df.loc[date, 'EMA20'] > df.loc[date, 'EMA60'] and 
                        df.loc[date, 'Close'] > df.loc[date, 'EMA20'] and 
                        df.loc[date, 'MACD'] > df.loc[date, 'MACD_signal']):
                        if ticker not in portfolio.entry_prices:  # 初始进场
                            amount_to_buy = (portfolio.cash * portfolio.allocation[ticker]) / df.loc[date, 'Close']
                            portfolio.buy(date, ticker, df.loc[date, 'Close'], amount_to_buy)
                            portfolio.entry_prices[ticker] = df.loc[date, 'Close']
                            print(f"Initial Buy: {amount_to_buy} of {ticker} at {df.loc[date, 'Close']} on {date}")
                        elif ticker in portfolio.holdings:  # 加仓逻辑
                            entry_price = portfolio.entry_prices[ticker]
                            current_price = df.loc[date, 'Close']
                            ATR = df['ATR'].loc[date]
                            if current_price <= entry_price - ATR * 2:  # 退场策略
                                amount_to_sell = portfolio.holdings[ticker]
                                portfolio.sell(date, ticker, current_price, amount_to_sell)
                                portfolio.entry_prices.pop(ticker, None)  # 清除entry_price
                                print(f"Sold {amount_to_sell} of {ticker} at {current_price} on {date} due to ATR stop-loss")
                            elif portfolio.count[ticker] < 4:
                                if current_price >= entry_price * 1.05:  # 上涨5%加仓
                                    amount_to_buy = (portfolio.cash * portfolio.allocation[ticker] * 0.25) / current_price
                                    portfolio.buy(date, ticker, current_price, amount_to_buy)
                                    portfolio.entry_prices[ticker] = current_price  # 重置entry_price
                                    portfolio.count[ticker] += 1
                                    print(f"Add Buy: {amount_to_buy} of {ticker} at {current_price} on {date} due to 5% rise")
                                elif current_price <= entry_price * 0.90:  # 下跌10%加仓
                                    amount_to_buy = (portfolio.cash * portfolio.allocation[ticker] * 0.25) / current_price
                                    portfolio.buy(date, ticker, current_price, amount_to_buy)
                                    portfolio.entry_prices[ticker] = current_price  # 重置entry_price
                                    portfolio.count[ticker] += 1
                                    print(f"Add Buy: {amount_to_buy} of {ticker} at {current_price} on {date} due to 10% fall")
                elif ticker == "00632R.TW":  # 反向ETF
                    if df.loc[date, 'Close'] > df['UpperBand'].loc[date]:  # 布林带上轨
                        if df['K'].loc[date] > 80 and df['K'].loc[date] < df['D'].loc[date]:  # KD指标
                            amount_to_sell = portfolio.holdings.get(ticker, 0) * 0.25
                            portfolio.sell(date, ticker, df.loc[date, 'Close'], amount_to_sell)
                            print(f"Sold {amount_to_sell} of {ticker} at {df.loc[date, 'Close']} on {date} due to UpperBand")
                    elif df.loc[date, 'Close'] < df['LowerBand'].loc[date]:  # 布林带下轨
                        if df['K'].loc[date] < 20 and df['K'].loc[date] > df['D'].loc[date]:  # KD指标
                            amount_to_buy = (portfolio.cash * portfolio.allocation[ticker] * 0.25) / df.loc[date, 'Close']
                            portfolio.buy(date, ticker, df.loc[date, 'Close'], amount_to_buy)
                            portfolio.entry_prices[ticker] = df.loc[date, 'Close']  # 重置entry_price
                            print(f"Bought {amount_to_buy} of {ticker} at {df.loc[date, 'Close']} on {date} due to LowerBand")
                elif ticker == "TWN":  # 台指期
                    if df.loc[date, 'Close'] > df['UpperBand'].loc[date]:  # 布林带上轨
                        if df['K'].loc[date] > 80 and df['K'].loc[date] < df['D'].loc[date]:  # KD指标
                            amount_to_sell = portfolio.holdings.get(ticker, 0)
                            portfolio.sell(date, ticker, df.loc[date, 'Close'], amount_to_sell)
                            print(f"Sold {amount_to_sell} of {ticker} at {df.loc[date, 'Close']} on {date} due to UpperBand")
                    elif df.loc[date, 'Close'] < df['LowerBand'].loc[date]:  # 布林带下轨
                        if df['K'].loc[date] < 20 and df['K'].loc[date] > df['D'].loc[date]:  # KD指标
                            amount_to_buy = (portfolio.cash * portfolio.allocation[ticker]) / df.loc[date, 'Close']
                            portfolio.buy(date, ticker, df.loc[date, 'Close'], amount_to_buy)
                            portfolio.entry_prices[ticker] = df.loc[date, 'Close']  # 重置entry_price
                            print(f"Bought {amount_to_buy} of {ticker} at {df.loc[date, 'Close']} on {date} due to LowerBand")
            except KeyError:
                # 忽略缺失的日期
                continue

portfolio = Portfolio(allocation=allocation)
trade_logic(data, portfolio)

# 保存交易历史
history_df = pd.DataFrame(portfolio.history, columns=['Date', 'Ticker', 'Action', 'Amount', 'Price', 'Transaction Tax', 'Profit Tax'])
history_df.to_csv("data/trade_history.csv", index=False)

# 保存每日资产总值
daily_values_df = pd.DataFrame(portfolio.daily_values, columns=['Date', 'Total Value'])
daily_values_df.to_csv("data/daily_values.csv", index=False)

# 保存每日各资产价值
daily_holdings_df = pd.DataFrame(portfolio.daily_holdings, columns=['Date', 'Holdings'])
daily_holdings_df.to_csv("data/daily_holdings.csv", index=False)

# 打印最终资产值
final_prices = {ticker: data[ticker].iloc[-1]['Close'] for ticker in data}
print(f"Final Portfolio Value: {portfolio.get_value(final_prices)}")

# 绘制每日资产总值随时间的变化
daily_values_df['Date'] = pd.to_datetime(daily_values_df['Date'])

# 绘制资产绩效和各资产占比变化
fig, axs = plt.subplots(2, 1, figsize=(14, 14))

# 绘制总资产随时间变化图
axs[0].plot(daily_values_df['Date'], daily_values_df['Total Value'], label='Total Value')
axs[0].set_xlabel('Date')
axs[0].set_ylabel('Total Value')
axs[0].set_title('Portfolio Total Value Over Time')
axs[0].legend()
axs[0].grid(True)

# 绘制各资产比例随时间变化图
daily_holdings_df['Date'] = pd.to_datetime(daily_holdings_df['Date'])
holdings_dict = daily_holdings_df.set_index('Date')['Holdings'].to_dict()
holdings_df = pd.DataFrame.from_dict(holdings_dict, orient='index').fillna(0)
proportion_df = holdings_df.div(daily_values_df.set_index('Date')['Total Value'], axis=0)

# 将 cash 列加到 proportion_df 中
proportion_df['cash'] = portfolio.cash / daily_values_df.set_index('Date')['Total Value']

# 归一化每一行使得比例总和为1
proportion_df = proportion_df.div(proportion_df.sum(axis=1), axis=0)

proportion_df.plot(ax=axs[1], kind='area', stacked=True)
axs[1].set_xlabel('Date')
axs[1].set_ylabel('Proportion of Total Value')
axs[1].set_title('Proportion of Each Asset Over Time')
axs[1].legend(loc='upper left')
axs[1].grid(True)

plt.tight_layout()
plt.show()

# 计算收益率
initial_value = daily_values_df.iloc[0]['Total Value']
final_value = daily_values_df.iloc[-1]['Total Value']
return_rate = (final_value - initial_value) / initial_value * 100
print(f"Return Rate: {return_rate:.2f}%")

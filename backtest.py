# backtest.py

from data_fetcher import get_data
from indicators import calculate_indicators
from portfolio import Portfolio
import os
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression
import numpy as np

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

        if not initial_invested and date == pd.Timestamp('2019-05-28'):
            available_tickers = [ticker for ticker in tickers if prices.get(ticker) is not None]
            if len(available_tickers) == len(tickers):
                initial_investment = portfolio.cash  # Use the entire initial cash for allocation
                for ticker, alloc in portfolio.allocation.items():
                    if prices.get(ticker) is not None:
                        amount_to_buy = (initial_investment * alloc) / prices[ticker]
                        portfolio.buy(date, ticker, prices[ticker], amount_to_buy)
                        print(f"Initial Buy: {amount_to_buy} of {ticker} at {prices[ticker]} on {date}")
                initial_invested = True

        for ticker in data:
            df = data[ticker]
            try:
                if ticker in ["2330.TW", "4763.TW", "8069.TWO", "2881.TW", "2882.TW"]:
                    if (df.loc[date, 'EMA20'] > df.loc[date, 'EMA60'] and 
                        df.loc[date, 'Close'] > df.loc[date, 'EMA20'] and 
                        df.loc[date, 'MACD'] > df.loc[date, 'MACD_signal']):
                        if ticker not in portfolio.entry_prices:  
                            amount_to_buy = (portfolio.cash * portfolio.allocation[ticker]) / df.loc[date, 'Close']
                            portfolio.buy(date, ticker, df.loc[date, 'Close'], amount_to_buy)
                            portfolio.entry_prices[ticker] = df.loc[date, 'Close']
                            print(f"Initial Buy: {amount_to_buy} of {ticker} at {df.loc[date, 'Close']} on {date}")
                        elif ticker in portfolio.holdings:  
                            entry_price = portfolio.entry_prices[ticker]
                            current_price = df.loc[date, 'Close']
                            ATR = df['ATR'].loc[date]
                            if current_price <= entry_price - ATR * 2:  
                                amount_to_sell = portfolio.holdings[ticker]
                                portfolio.sell(date, ticker, current_price, amount_to_sell)
                                portfolio.entry_prices.pop(ticker, None)  
                                print(f"Sold {amount_to_sell} of {ticker} at {current_price} on {date} due to ATR stop-loss")
                            elif portfolio.count[ticker] < 4:
                                if current_price >= entry_price * 1.05: 
                                    amount_to_buy = (portfolio.cash * portfolio.allocation[ticker] * 0.25) / current_price
                                    portfolio.buy(date, ticker, current_price, amount_to_buy)
                                    portfolio.entry_prices[ticker] = current_price  
                                    portfolio.count[ticker] += 1
                                    print(f"Add Buy: {amount_to_buy} of {ticker} at {current_price} on {date} due to 5% rise")
                                elif current_price <= entry_price * 0.90:  
                                    amount_to_buy = (portfolio.cash * portfolio.allocation[ticker] * 0.25) / current_price
                                    portfolio.buy(date, ticker, current_price, amount_to_buy)
                                    portfolio.entry_prices[ticker] = current_price  
                                    portfolio.count[ticker] += 1
                                    print(f"Add Buy: {amount_to_buy} of {ticker} at {current_price} on {date} due to 10% fall")
                elif ticker == "00632R.TW":  
                    if df.loc[date, 'Close'] > df['UpperBand'].loc[date]:  
                        if df['K'].loc[date] > 80 and df['K'].loc[date] < df['D'].loc[date]:  
                            amount_to_sell = portfolio.holdings.get(ticker, 0) * 0.25
                            portfolio.sell(date, ticker, df.loc[date, 'Close'], amount_to_sell)
                            print(f"Sold {amount_to_sell} of {ticker} at {df.loc[date, 'Close']} on {date} due to UpperBand")
                    elif df.loc[date, 'Close'] < df['LowerBand'].loc[date]:  
                        if df['K'].loc[date] < 20 and df['K'].loc[date] > df['D'].loc[date]:  
                            amount_to_buy = (portfolio.cash * portfolio.allocation[ticker] * 0.25) / df.loc[date, 'Close']
                            portfolio.buy(date, ticker, df.loc[date, 'Close'], amount_to_buy)
                            portfolio.entry_prices[ticker] = df.loc[date, 'Close']  
                            print(f"Bought {amount_to_buy} of {ticker} at {df.loc[date, 'Close']} on {date} due to LowerBand")
                elif ticker == "TWN": 
                    if df.loc[date, 'Close'] > df['UpperBand'].loc[date]:  
                        if df['K'].loc[date] > 80 and df['K'].loc[date] < df['D'].loc[date]:  
                            amount_to_sell = portfolio.holdings.get(ticker, 0)
                            portfolio.sell(date, ticker, df.loc[date, 'Close'], amount_to_sell)
                            print(f"Sold {amount_to_sell} of {ticker} at {df.loc[date, 'Close']} on {date} due to UpperBand")
                    elif df.loc[date, 'Close'] < df['LowerBand'].loc[date]:  
                        if df['K'].loc[date] < 20 and df['K'].loc[date] > df['D'].loc[date]:  
                            amount_to_buy = (portfolio.cash * portfolio.allocation[ticker]) / df.loc[date, 'Close']
                            portfolio.buy(date, ticker, df.loc[date, 'Close'], amount_to_buy)
                            portfolio.entry_prices[ticker] = df.loc[date, 'Close']  
                            print(f"Bought {amount_to_buy} of {ticker} at {df.loc[date, 'Close']} on {date} due to LowerBand")
            except KeyError:
                continue

portfolio = Portfolio(allocation=allocation)
trade_logic(data, portfolio)


history_df = pd.DataFrame(portfolio.history, columns=['Date', 'Ticker', 'Action', 'Amount', 'Price', 'Transaction Tax', 'Profit Tax'])
history_df.to_csv("data/trade_history.csv", index=False)


daily_values_df = pd.DataFrame(portfolio.daily_values, columns=['Date', 'Total Value'])
daily_values_df.to_csv("data/daily_values.csv", index=False)


daily_holdings_df = pd.DataFrame(portfolio.daily_holdings, columns=['Date', 'Holdings'])
daily_holdings_df.to_csv("data/daily_holdings.csv", index=False)


final_prices = {ticker: data[ticker].iloc[-1]['Close'] for ticker in data}
print(f"Final Portfolio Value: {portfolio.get_value(final_prices)}")


daily_values_df['Date'] = pd.to_datetime(daily_values_df['Date'])


fig, axs = plt.subplots(2, 1, figsize=(14, 14))


axs[0].plot(daily_values_df['Date'], daily_values_df['Total Value'], label='Total Value')
axs[0].set_xlabel('Date')
axs[0].set_ylabel('Total Value')
axs[0].set_title('Portfolio Total Value Over Time')
axs[0].legend()
axs[0].grid(True)


daily_values_df['Year'] = daily_values_df['Date'].dt.year
years = daily_values_df['Year'].unique()

for year in years:
    yearly_data = daily_values_df[daily_values_df['Year'] == year]
    if len(yearly_data) > 1:  
        X = np.array(range(len(yearly_data))).reshape(-1, 1)
        y = yearly_data['Total Value'].values
        model = LinearRegression().fit(X, y)
        trend = model.predict(X)
        axs[0].plot(yearly_data['Date'], trend, linestyle='--', label=f'{year} Trend')

axs[0].legend()
axs[0].grid(True)

daily_holdings_df['Date'] = pd.to_datetime(daily_holdings_df['Date'])
holdings_dict = daily_holdings_df.set_index('Date')['Holdings'].to_dict()
holdings_df = pd.DataFrame.from_dict(holdings_dict, orient='index').fillna(0)
proportion_df = holdings_df.div(daily_values_df.set_index('Date')['Total Value'], axis=0)


proportion_df['cash'] = portfolio.cash / daily_values_df.set_index('Date')['Total Value']


proportion_df = proportion_df.div(proportion_df.sum(axis=1), axis=0)

proportion_df.plot(ax=axs[1], kind='area', stacked=True)
axs[1].set_xlabel('Date')
axs[1].set_ylabel('Proportion of Total Value')
axs[1].set_title('Proportion of Each Asset Over Time')
axs[1].legend(loc='upper left')
axs[1].grid(True)

plt.tight_layout()
plt.show()


initial_value = daily_values_df.iloc[0]['Total Value']
final_value = daily_values_df.iloc[-1]['Total Value']
return_rate = (final_value - initial_value) / initial_value * 100
print(f"Return Rate: {return_rate:.2f}%")

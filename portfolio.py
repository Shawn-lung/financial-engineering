import pandas as pd
import matplotlib.pyplot as plt

class Portfolio:
    def __init__(self, initial_cash=1000000, allocation=None):
        self.cash = initial_cash
        self.holdings = {}
        self.history = []
        self.daily_values = []
        self.daily_holdings = []
        self.entry_prices = {}  # 添加 entry_prices 属性
        self.allocation = allocation if allocation else {}  # 初始化配置比例
        self.count = [0,0,0,0,0,0,0,0,0] #用來計算進場幾次，最多4次(股票部分)

    def buy(self, date, ticker, price, amount):
        cost = price * amount
        if self.cash >= cost:
            self.cash -= cost
            if ticker not in self.holdings:
                self.holdings[ticker] = 0
                self.entry_prices[ticker] = price  # 初始化 entry_prices
            self.holdings[ticker] += amount
            self.history.append((date, ticker, 'buy', amount, price))

    def sell(self, date, ticker, price, amount):
        if ticker in self.holdings and self.holdings[ticker] >= amount:
            self.holdings[ticker] -= amount
            self.cash += price * amount
            self.history.append((date, ticker, 'sell', amount, price))

    def update_daily_value(self, date, prices):
        value = self.cash
        holdings_value = {}
        for ticker, amount in self.holdings.items():
            asset_value = prices.get(ticker, 0) * amount
            value += asset_value
            holdings_value[ticker] = asset_value
        self.daily_values.append((date, value))
        self.daily_holdings.append((date, holdings_value))

    def get_value(self, prices):
        value = self.cash
        for ticker, amount in self.holdings.items():
            value += prices.get(ticker, 0) * amount
        return value

def trade_logic(data, portfolio):
    initial_invested = False
    for date in data['2330.TW'].index:
        prices = {ticker: data[ticker].loc[date, 'Close'] for ticker in data if date in data[ticker].index}
        portfolio.update_daily_value(date, prices)
        
        if not initial_invested:
            for ticker, allocation in portfolio.allocation.items():
                if ticker in prices:
                    amount_to_buy = (portfolio.cash * allocation) / prices[ticker]
                    portfolio.buy(date, ticker, prices[ticker], amount_to_buy)
            initial_invested = True

        for ticker in data:
            df = data[ticker]
            try:
                if (df.loc[date, 'EMA20'] > df.loc[date, 'EMA60'] and 
                    df.loc[date, 'Close'] > df.loc[date, 'EMA20'] and 
                    df.loc[date, 'MACD'] > df.loc[date, 'MACD_signal']):
                    amount_to_buy = portfolio.cash * 0.25 / df.loc[date, 'Close']
                    portfolio.buy(date, ticker, df.loc[date, 'Close'], amount_to_buy)
                # 加倉策略
                if ticker in portfolio.holdings:
                    entry_price = portfolio.entry_prices.get(ticker, df.loc[date, 'Close'])
                    current_price = df.loc[date, 'Close']
                    ATR = calculate_indicators(df)['ATR']
                    if current_price <= current_price-ATR*2:   #退場策略優先於加倉
                        amount_to_sell = portfolio.daily_holdings / current_price #全部賣出
                        portfolio.sell(date, ticker, current_price, amount_to_sell)
                        portfolio.count[ticker] = 0
                    elif portfolio.count[ticker] < 4:
                        if current_price >= entry_price * 1.05:  # 上漲5%加一倉
                            amount_to_buy = portfolio.cash / current_price
                            portfolio.sell(date, ticker, current_price, amount_to_buy)
                            portfolio.count[ticker] +=1 
                        elif current_price <= entry_price * 0.90:  # 下跌10%加一倉
                            amount_to_buy = portfolio.cash * 0.25 / current_price
                            portfolio.buy(date, ticker, current_price, amount_to_buy)
                            portfolio.count[ticker] +=1 
            except KeyError:
                # 忽略缺失的日期
                continue

if __name__ == "__main__":
    tickers = ["4763.TW", "8069.TWO", "2881.TW", "2882.TW", "2330.TW", "TWN", "TLT", "GLD", "00632R.TW"]
    data = {}
    for ticker in tickers:
        df = pd.read_csv(f"data/{ticker}_indicators.csv", index_col="Date", parse_dates=True)
        data[ticker] = df

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

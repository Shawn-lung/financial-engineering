import pandas as pd

class Portfolio:
    def __init__(self, allocation):
        self.allocation = allocation
        self.cash = 10000000  # Initial cash
        self.holdings = {}
        self.entry_prices = {}
        self.daily_values = []
        self.daily_holdings = []
        self.history = []
        self.count = {ticker: 0 for ticker in allocation}
        self.transaction_tax = {
            'securities': 0.003,  # 证券交易税
            'futures': 0.0025  # 期货交易税
        }
        self.profit_tax_rate = 0.10  # 利润税率

    def update_daily_value(self, date, prices):
        total_value = self.cash
        holdings_value = {}
        for ticker, amount in self.holdings.items():
            total_value += amount * prices[ticker]
            holdings_value[ticker] = amount * prices[ticker]
        self.daily_values.append({'Date': date, 'Total Value': total_value})
        self.daily_holdings.append({'Date': date, 'Holdings': holdings_value})

    def buy(self, date, ticker, price, amount):
        cost = price * amount
        tax = 0
        if 'TWN' in ticker or '00632R.TW' in ticker:  # 期货交易税
            tax = cost * self.transaction_tax['futures']
        else:  # 证券交易税
            tax = cost * self.transaction_tax['securities']
        
        total_cost = cost + tax
        if self.cash >= total_cost:
            self.cash -= total_cost
            if ticker in self.holdings:
                self.holdings[ticker] += amount
            else:
                self.holdings[ticker] = amount
            self.entry_prices[ticker] = price  # 重置entry_price
            self.history.append([date, ticker, 'buy', amount, price, tax])
        else:
            print(f"Not enough cash to buy {amount} of {ticker} at {price} on {date}")

    def sell(self, date, ticker, price, amount):
        if ticker in self.holdings and self.holdings[ticker] >= amount:
            cost = price * amount
            tax = 0
            if 'TWN' in ticker or '00632R.TW' in ticker:  # 期货交易税
                tax = cost * self.transaction_tax['futures']
            else:  # 证券交易税
                tax = cost * self.transaction_tax['securities']
            
            self.holdings[ticker] -= amount
            profit = (price - self.entry_prices[ticker]) * amount
            profit_tax = 0
            if profit > 0:
                profit_tax = profit * self.profit_tax_rate
            
            total_income = cost - tax - profit_tax
            self.cash += total_income
            self.history.append([date, ticker, 'sell', amount, price, tax, profit_tax])
            
            if self.holdings[ticker] == 0:
                del self.holdings[ticker]
                del self.entry_prices[ticker]
        else:
            print(f"Not enough holdings to sell {amount} of {ticker} at {price} on {date}")

    def get_value(self, prices):
        total_value = self.cash
        for ticker, amount in self.holdings.items():
            total_value += amount * prices[ticker]
        return total_value

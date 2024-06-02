#risk_analysis.py

import pandas as pd
import numpy as np

def calculate_annualized_volatility(daily_returns):
    return np.std(daily_returns) * np.sqrt(252)

def calculate_max_drawdown(daily_values):
    cumulative_max = daily_values.cummax()
    drawdown = (daily_values - cumulative_max) / cumulative_max
    max_drawdown = drawdown.min()
    return max_drawdown

def calculate_sharpe_ratio(daily_returns, risk_free_rate=0.016):
    excess_returns = daily_returns - risk_free_rate / 252
    annualized_return = np.mean(excess_returns) * 252
    annualized_volatility = calculate_annualized_volatility(daily_returns)
    sharpe_ratio = annualized_return / annualized_volatility
    return sharpe_ratio

def risk_analysis(daily_values_df, risk_free_rate=0.016):
    daily_values_df['Daily Return'] = daily_values_df['Total Value'].pct_change().dropna()
    
    annualized_volatility = calculate_annualized_volatility(daily_values_df['Daily Return'])
    max_drawdown = calculate_max_drawdown(daily_values_df['Total Value'])
    sharpe_ratio = calculate_sharpe_ratio(daily_values_df['Daily Return'], risk_free_rate)
    
    return {
        'Annualized Volatility': annualized_volatility,
        'Max Drawdown': max_drawdown,
        'Sharpe Ratio': sharpe_ratio
    }

if __name__ == "__main__":
    daily_values_df = pd.read_csv("data/daily_values.csv", parse_dates=['Date'])
    risk_free_rate = 0.016  
    results = risk_analysis(daily_values_df, risk_free_rate)
    
    print(f"Annualized Volatility: {results['Annualized Volatility']:.2%}")
    print(f"Max Drawdown: {results['Max Drawdown']:.2%}")
    print(f"Sharpe Ratio: {results['Sharpe Ratio']:.2f}")

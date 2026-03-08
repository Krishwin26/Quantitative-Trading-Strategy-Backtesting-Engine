import pandas as pd
import numpy as np
import os
from datetime import datetime, timedelta

def generate_mock_stock_data(ticker="AAPL", start_date="2020-01-01", days=1000, initial_price=100.0, volatility=0.02):
    """
    Generates synthetic daily OHLCV stock data using a geometric Brownian motion model.
    """
    np.random.seed(42)  # For reproducibility
    
    dates = pd.date_range(start=start_date, periods=days, freq='B') # Business days
    
    # Generate daily returns based on normal distribution
    returns = np.random.normal(0, volatility, len(dates))
    
    # Calculate closing prices
    prices = initial_price * np.exp(np.cumsum(returns))
    
    # Generate OHL and Volume based on close
    df = pd.DataFrame({
        'date': dates,
        'close': prices
    })
    
    # Introduce some random daily variation for High, Low, Open
    daily_range = df['close'] * np.random.uniform(0.005, 0.02, len(dates))
    
    df['open'] = df['close'] * (1 + np.random.normal(0, 0.005, len(dates)))
    df['high'] = df[['open', 'close']].max(axis=1) + daily_range / 2
    df['low'] = df[['open', 'close']].min(axis=1) - daily_range / 2
    df['volume'] = np.random.randint(1_000_000, 50_000_000, len(dates))
    
    # Rounding numeric columns
    for col in ['open', 'high', 'low', 'close']:
        df[col] = df[col].round(4)
        
    df['ticker'] = ticker
    
    # Reorder columns
    df = df[['ticker', 'date', 'open', 'high', 'low', 'close', 'volume']]
    
    return df

def save_to_csv(df: pd.DataFrame, filepath: str):
    """Saves DataFrame to CSV."""
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    df.to_csv(filepath, index=False)
    print(f"Saved synthetic data to {filepath}")

def load_data_from_csv(filepath: str) -> pd.DataFrame:
    """Loads CSV data and cleans it (handles missing values)."""
    df = pd.read_csv(filepath)
    # Simple cleaning: forward fill then backward fill
    df.ffill(inplace=True)
    df.bfill(inplace=True)
    return df

if __name__ == "__main__":
    # Generate sample data for backtesting
    aapl_data = generate_mock_stock_data(ticker="AAPL", days=1000)
    tsla_data = generate_mock_stock_data(ticker="TSLA", days=1000, initial_price=50.0, volatility=0.05)
    
    # Combine and save
    combined_data = pd.concat([aapl_data, tsla_data])
    data_path = os.path.join(os.path.dirname(__file__), "..", "data", "sample_stock_data.csv")
    
    # Ensure directory is ready
    os.makedirs(os.path.dirname(data_path), exist_ok=True)
    
    save_to_csv(combined_data, data_path)
    
    print(f"Generated {len(combined_data)} rows of market data.")

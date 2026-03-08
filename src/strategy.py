import pandas as pd
import numpy as np

class MeanReversionStrategy:
    """
    Implements a simple Mean Reversion Trading Strategy.
    
    Logic:
    - Compute 20-day moving average (SMA)
    - Compute 20-day rolling standard deviation
    - Calculate Z-score = (Current Price - SMA) / Standard Deviation
    - If Z-score < -2 -> BUY (Price is unusually low)
    - If Z-score > 2 -> SELL (Price is unusually high)
    """
    def __init__(self, window: int = 20, z_threshold: float = 2.0):
        self.window = window
        self.z_threshold = z_threshold

    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Generates buy/sell signals based on historical price data.
        Assumes df contains 'date' and 'close' columns.
        Returns a DataFrame with 'date', 'signal_type', and 'indicator_value' (Z-score).
        """
        if len(df) < self.window:
            raise ValueError(f"Not enough data points to compute {self.window}-day SMA.")

        # Create a copy to avoid SettingWithCopyWarning
        data = df.copy()
        
        # Calculate moving average and rolling standard deviation
        data['sma'] = data['close'].rolling(window=self.window).mean()
        data['std_dev'] = data['close'].rolling(window=self.window).std()

        # Calculate Z-score
        data['z_score'] = (data['close'] - data['sma']) / data['std_dev']

        # Determine signal type
        # Default is 'HOLD'
        data['signal_type'] = 'HOLD'
        
        # Vectorized operations for speed
        # Buy when price drops significantly below mean (oversold)
        data.loc[data['z_score'] < -self.z_threshold, 'signal_type'] = 'BUY'
        
        # Sell when price rises significantly above mean (overbought)
        data.loc[data['z_score'] > self.z_threshold, 'signal_type'] = 'SELL'
        
        # Filter out first `window - 1` days since Z-score is NaN
        data = data.dropna(subset=['z_score'])

        # We return only necessary columns for the Database Manager
        result_df = pd.DataFrame({
            'date': data['date'],
            'signal_type': data['signal_type'],
            'indicator_value': data['z_score'].round(4)
        })
        
        return result_df

if __name__ == "__main__":
    # Test strategy logic locally
    from data_loader import generate_mock_stock_data
    
    print("Testing Mean Reversion Strategy...")
    test_df = generate_mock_stock_data("TEST", days=100)
    
    strategy = MeanReversionStrategy(window=20, z_threshold=2.0)
    signals = strategy.generate_signals(test_df)
    
    # Print a snippet of buy/sell signals
    active_signals = signals[signals['signal_type'] != 'HOLD']
    print(f"Generated {len(active_signals)} active BUY/SELL signals out of {len(signals)} days.")
    print(active_signals.head())

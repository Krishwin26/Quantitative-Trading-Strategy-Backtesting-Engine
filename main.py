import os
import pandas as pd
from src.database_manager import DatabaseManager
from src.data_loader import generate_mock_stock_data, save_to_csv, load_data_from_csv
from src.strategy import MeanReversionStrategy
from src.backtester import Backtester
from src.metrics import PerformanceMetrics

def setup_data(db_manager: DatabaseManager, data_path: str):
    print("--- 1. Setting up Historical Data ---")
    if not os.path.exists(data_path):
        print("Generating new sample mock stock data...")
        aapl_data = generate_mock_stock_data("AAPL", days=1000)
        tsla_data = generate_mock_stock_data("TSLA", days=1000, initial_price=50.0, volatility=0.05)
        combined = pd.concat([aapl_data, tsla_data])
        save_to_csv(combined, data_path)
    else:
        print("Loading existing historical CSV data...")
        combined = load_data_from_csv(data_path)
    
    # Insert data into DB
    for ticker in combined['ticker'].unique():
        ticker_data = combined[combined['ticker'] == ticker].copy()
        
        # Check if already loaded to avoid duplicates
        existing_data = db_manager.get_stock_id(ticker)
        if not existing_data:
            print(f"Inserting into DB: {ticker} ({len(ticker_data)} records)")
            db_manager.insert_price_data(ticker_data, ticker)
        else:
            print(f"Data for {ticker} already initialized.")

def run_strategy(db_manager: DatabaseManager, tickers: list):
    print("\n--- 2. Generating Trading Signals ---")
    strategy = MeanReversionStrategy(window=20, z_threshold=2.0)
    
    for ticker in tickers:
        print(f"Running Mean Reversion strategy for: {ticker}")
        price_df = db_manager.load_price_data(ticker)
        
        if len(price_df) > 0:
            signals = strategy.generate_signals(price_df)
            
            # Filter solely for the database record
            db_manager.insert_signals(signals, ticker)
            print(f"Generated {len(signals)} signal indicators for {ticker}.")

def run_backtest(db_manager: DatabaseManager, tickers: list):
    print("\n--- 3. Running Backtest ---")
    backtester = Backtester(db_manager, initial_capital=100000.0)
    
    for ticker in tickers:
        print(f"Simulating trades on historical data for {ticker}...")
        backtester.run_backtest(ticker)
        
    print(f"Backtest completed. Final Portfolio Cash: ${backtester.cash:.2f}")

def calculate_metrics(db_manager: DatabaseManager):
    print("\n--- 4. Computing Performance Metrics ---")
    tickers = ["AAPL", "TSLA"]
    for ticker in tickers:
        stock_id = db_manager.get_stock_id(ticker)
        query = f"SELECT date, portfolio_value FROM portfolio_performance WHERE stock_id = {stock_id} ORDER BY date ASC"
        perf_df = pd.read_sql(query, db_manager.engine)
        
        if len(perf_df) == 0:
            print(f"No performance data found for {ticker}. Backtest might have failed.")
            continue
            
        metrics = PerformanceMetrics(perf_df)
        report = metrics.generate_report()
        
        print("\n===============================")
        print(f"  [{ticker}] PERFORMANCE REPORT  ")
        print("===============================")
        for k, v in report.items():
            print(f"  {k}: {v}")
        print("===============================")
    print("\n")

def main():
    db_url = "sqlite:///database/quant_trading.db"
    
    # Initialize connection
    db_manager = DatabaseManager(db_url)
    db_manager.init_db()
    
    data_path = os.path.join("data", "sample_stock_data.csv")
    tickers = ["AAPL", "TSLA"]
    
    # Pipeline Execution
    setup_data(db_manager, data_path)
    run_strategy(db_manager, tickers)
    run_backtest(db_manager, tickers)
    calculate_metrics(db_manager)
    
    print("Complete End-to-End Pipeline execution finished.")
    print("Check `database/quant_trading.db` and the `notebooks` directory for further analysis.")

if __name__ == "__main__":
    main()

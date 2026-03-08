import pandas as pd
from typing import Dict, List, Tuple
from datetime import datetime
from src.database_manager import DatabaseManager

class Backtester:
    """
    Simulates trades based on historical signals.
    Updates portfolio value over time and stores completed trades in the database.
    """
    def __init__(self, db_manager: DatabaseManager, initial_capital: float = 100000.0):
        self.db = db_manager
        self.initial_capital = initial_capital
        
        # Portfolio State
        self.cash = initial_capital
        # Dict mapping ticker -> { quantity, average_price, entry_date }
        self.holdings: Dict[str, dict] = {}
        
        self.portfolio_history: List[dict] = []
        self.completed_trades: List[dict] = []

    def run_backtest(self, ticker: str):
        """
        Runs the backtest simulation for a given ticker by reading its price and signals from the DB.
        """
        stock_id = self.db.get_stock_id(ticker)
        if not stock_id:
            raise ValueError(f"Ticker {ticker} not found in database.")

        # 1. Load Price and Signals Data in one combined query for efficiency
        query = f"""
            SELECT p.date, p.close, s.signal_type, s.indicator_value
            FROM price_data p
            LEFT JOIN trading_signals s ON p.stock_id = s.stock_id AND p.date = s.date
            WHERE p.stock_id = {stock_id}
            ORDER BY p.date ASC
        """
        data = pd.read_sql(query, self.db.engine)
        
        # 2. Iterate through daily data (Simulate time passing)
        for _, row in data.iterrows():
            current_date = row['date']
            current_price = row['close']
            signal = row['signal_type'] if pd.notna(row['signal_type']) else 'HOLD'
            
            # Execute Trade Logic
            self._execute_logic(ticker, current_date, current_price, signal)
            
            # Record daily portfolio value at end of day
            self._record_portfolio_state(current_date, ticker, current_price)
            
        # 3. Save Trades & Portfolio to Database
        self._commit_results_to_db(stock_id)

    def _execute_logic(self, ticker: str, date, current_price: float, signal: str):
        """Processes a single daily signal."""
        # Check if we already hold a position
        holding = self.holdings.get(ticker)

        if signal == 'BUY' and not holding:
            # Simple assumption: Invest 50% of available cash on a single trade
            invest_amount = self.cash * 0.5
            quantity_to_buy = int(invest_amount // current_price)
            
            if quantity_to_buy > 0:
                cost = quantity_to_buy * current_price
                self.cash -= cost
                
                # Record the new position
                self.holdings[ticker] = {
                    'quantity': quantity_to_buy,
                    'entry_price': current_price,
                    'entry_date': date
                }
                
                # print(f"[{date}] BUY {quantity_to_buy} shares of {ticker} @ {current_price:.2f}")

        elif signal == 'SELL' and holding:
            # We have a position, time to sell
            quantity_to_sell = holding['quantity']
            revenue = quantity_to_sell * current_price
            
            self.cash += revenue
            
            # Calculate PnL
            profit_loss = revenue - (quantity_to_sell * holding['entry_price'])
            
            # Record completed trade
            self.completed_trades.append({
                'stock_id': None, # Set at batch insert
                'entry_date': holding['entry_date'],
                'exit_date': date,
                'entry_price': holding['entry_price'],
                'exit_price': current_price,
                'profit_loss': profit_loss
            })
            
            # print(f"[{date}] SELL {quantity_to_sell} shares of {ticker} @ {current_price:.2f} (PnL: {profit_loss:.2f})")
            
            # Remove holding
            del self.holdings[ticker]
            
    def _record_portfolio_state(self, date, ticker: str, current_price: float):
        """Calculates total value (cash + mark-to-market holdings)"""
        # Mark to market
        holding_value = 0.0
        holding = self.holdings.get(ticker)
        if holding:
            holding_value = holding['quantity'] * current_price
            
        total_portfolio_value = self.cash + holding_value
        
        self.portfolio_history.append({
            'date': date,
            'portfolio_value': total_portfolio_value
        })

    def _commit_results_to_db(self, stock_id: int):
        """Writes accumulated trades and portfolio history to database."""
        
        # Save Trades
        if self.completed_trades:
            trades_df = pd.DataFrame(self.completed_trades)
            trades_df['stock_id'] = stock_id
            self.db.save_trades(trades_df)
            print(f"Saved {len(trades_df)} trades to DB.")
            
        # Save Portfolio Performance
        if self.portfolio_history:
            perf_df = pd.DataFrame(self.portfolio_history)
            
            # Calculate Daily Returns based on portfolio value changes
            perf_df['daily_return'] = perf_df['portfolio_value'].pct_change()
            
            # Replace NaNs with 0
            perf_df['daily_return'] = perf_df['daily_return'].fillna(0.0)
            perf_df['stock_id'] = stock_id
            
            self.db.save_portfolio_performance(perf_df)
            print(f"Saved portfolio performance for stock ID {stock_id} to DB.")
            
        # Clear state after backtest to prevent memory leaks and duplication across tickers
        self.portfolio_history.clear()
        self.completed_trades.clear()
        self.cash = self.initial_capital

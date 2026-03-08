from typing import List, Optional
import pandas as pd
from sqlalchemy import (
    create_engine, Column, Integer, String, Float, Date, ForeignKey, Numeric, BigInteger
)
from sqlalchemy.orm import sessionmaker, relationship, declarative_base

# Define declarative base
Base = declarative_base()

class Stock(Base):
    __tablename__ = 'stocks'
    
    stock_id = Column(Integer, primary_key=True, autoincrement=True)
    ticker = Column(String(10), nullable=False, unique=True)
    sector = Column(String(50))

class PriceData(Base):
    __tablename__ = 'price_data'
    
    price_id = Column(Integer, primary_key=True, autoincrement=True)
    stock_id = Column(Integer, ForeignKey('stocks.stock_id', ondelete='CASCADE'), nullable=False)
    date = Column(Date, nullable=False)
    open = Column(Numeric(15, 4))
    high = Column(Numeric(15, 4))
    low = Column(Numeric(15, 4))
    close = Column(Numeric(15, 4))
    volume = Column(BigInteger)
    
class TradingSignal(Base):
    __tablename__ = 'trading_signals'
    
    signal_id = Column(Integer, primary_key=True, autoincrement=True)
    stock_id = Column(Integer, ForeignKey('stocks.stock_id', ondelete='CASCADE'), nullable=False)
    date = Column(Date, nullable=False)
    signal_type = Column(String(10), nullable=False) # 'BUY', 'SELL', 'HOLD'
    indicator_value = Column(Numeric(15, 4))

class Trade(Base):
    __tablename__ = 'trades'
    
    trade_id = Column(Integer, primary_key=True, autoincrement=True)
    stock_id = Column(Integer, ForeignKey('stocks.stock_id', ondelete='CASCADE'), nullable=False)
    entry_date = Column(Date, nullable=False)
    exit_date = Column(Date)
    entry_price = Column(Numeric(15, 4), nullable=False)
    exit_price = Column(Numeric(15, 4))
    profit_loss = Column(Numeric(15, 4))

class PortfolioPerformance(Base):
    __tablename__ = 'portfolio_performance'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    stock_id = Column(Integer, ForeignKey('stocks.stock_id', ondelete='CASCADE'), nullable=False)
    date = Column(Date, nullable=False)
    portfolio_value = Column(Numeric(18, 4), nullable=False)
    daily_return = Column(Numeric(10, 6))

class DatabaseManager:
    """Manages connection to the database and provides data access methods."""

    def __init__(self, db_url="sqlite:///quant_trading.db"):
        """
        Initializes the DatabaseManager.
        Defaults to an SQLite database for simple local setups.
        For PostgreSQL: "postgresql://user:password@localhost/dbname"
        For MySQL:      "mysql+pymysql://user:password@localhost/dbname"
        """
        self.engine = create_engine(db_url, echo=False)
        self.Session = sessionmaker(bind=self.engine)
        
    def init_db(self):
        """Creates all tables in the database if they don't exist."""
        Base.metadata.create_all(self.engine)
        print("Database initialized.")

    def add_stock(self, ticker: str, sector: str = None) -> int:
        """Adds a stock to the database and returns its ID."""
        session = self.Session()
        try:
            # Check if stock exists
            stock = session.query(Stock).filter_by(ticker=ticker).first()
            if not stock:
                stock = Stock(ticker=ticker, sector=sector)
                session.add(stock)
                session.commit()
            return stock.stock_id
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
            
    def get_stock_id(self, ticker: str) -> Optional[int]:
        session = self.Session()
        stock = session.query(Stock).filter_by(ticker=ticker).first()
        session.close()
        return stock.stock_id if stock else None

    def insert_price_data(self, df: pd.DataFrame, ticker: str):
        """Inserts OHLCV data for a ticker from a pandas DataFrame."""
        stock_id = self.add_stock(ticker)
        
        # Ensure the date is in datetime format
        df['date'] = pd.to_datetime(df['date']).dt.date
        df['stock_id'] = stock_id
        
        # Using Pandas to_sql for fast batch insert
        df[['stock_id', 'date', 'open', 'high', 'low', 'close', 'volume']].to_sql(
            'price_data', con=self.engine, if_exists='append', index=False
        )

    def load_price_data(self, ticker: str) -> pd.DataFrame:
        """Loads price data for a given ticker into a pandas DataFrame."""
        stock_id = self.get_stock_id(ticker)
        if not stock_id:
            raise ValueError(f"Ticker {ticker} not found in database.")
            
        query = f"SELECT * FROM price_data WHERE stock_id = {stock_id} ORDER BY date ASC"
        df = pd.read_sql(query, self.engine)
        df['date'] = pd.to_datetime(df['date'])
        return df

    def insert_signals(self, signals_df: pd.DataFrame, ticker: str):
        """Inserts generated trading signals."""
        stock_id = self.get_stock_id(ticker)
        signals_df['stock_id'] = stock_id
        signals_df['date'] = pd.to_datetime(signals_df['date']).dt.date
        
        signals_df[['stock_id', 'date', 'signal_type', 'indicator_value']].to_sql(
            'trading_signals', con=self.engine, if_exists='append', index=False
        )

    def save_trades(self, trades_df: pd.DataFrame):
        """Saves a batch of trades completed by the backtester."""
        trades_df['entry_date'] = pd.to_datetime(trades_df['entry_date']).dt.date
        trades_df['exit_date'] = pd.to_datetime(trades_df['exit_date']).dt.date
        
        trades_df.to_sql('trades', con=self.engine, if_exists='append', index=False)

    def save_portfolio_performance(self, perf_df: pd.DataFrame):
        """Saves the daily portfolio value history."""
        perf_df['date'] = pd.to_datetime(perf_df['date']).dt.date
        perf_df.to_sql('portfolio_performance', con=self.engine, if_exists='append', index=False)

if __name__ == "__main__":
    # Quick Test
    db = DatabaseManager('sqlite:///test_quant.db')
    db.init_db()

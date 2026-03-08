import pandas as pd
import numpy as np

class PerformanceMetrics:
    """Calculates key performance indicators for a trading strategy."""
    
    def __init__(self, portfolio_df: pd.DataFrame, risk_free_rate: float = 0.02):
        """
        Expects a DataFrame with 'date' and 'portfolio_value' columns.
        """
        self.df = portfolio_df.copy()
        
        # Ensure date is sorted
        self.df = self.df.sort_values(by='date')
        
        # Calculate daily returns
        if 'daily_return' not in self.df.columns:
            self.df['daily_return'] = self.df['portfolio_value'].pct_change().fillna(0.0)
            
        self.risk_free_rate = risk_free_rate

    def annualized_return(self) -> float:
        """Calculates the annualized return based on trading frequency (assumed 252 trading days per year)"""
        if len(self.df) < 2:
            return 0.0
            
        total_return = (self.df['portfolio_value'].iloc[-1] / self.df['portfolio_value'].iloc[0]) - 1
        num_years = len(self.df) / 252.0
        
        if num_years == 0:
            return total_return
            
        annualized = (1 + total_return) ** (1 / num_years) - 1
        return float(annualized)

    def volatility(self) -> float:
        """Calculates annualized volatility of returns."""
        daily_vol = self.df['daily_return'].std()
        annualized_vol = daily_vol * np.sqrt(252)
        return float(annualized_vol)

    def sharpe_ratio(self) -> float:
        """Calculates the Sharpe Ratio: (Return - Risk-Free Rate) / Volatility"""
        ann_return = self.annualized_return()
        ann_vol = self.volatility()
        
        if ann_vol == 0:
            return 0.0
            
        sharpe = (ann_return - self.risk_free_rate) / ann_vol
        return float(sharpe)

    def maximum_drawdown(self) -> float:
        """Calculates the Maximum Drawdown (largest peak-to-trough drop)."""
        # Calculate rolling peak
        self.df['peak'] = self.df['portfolio_value'].cummax()
        
        # Calculate drawdown
        self.df['drawdown'] = (self.df['portfolio_value'] - self.df['peak']) / self.df['peak']
        
        max_dd = self.df['drawdown'].min()
        return float(max_dd)

    def generate_report(self) -> dict:
        """Returns a dictionary containing all key metrics."""
        return {
            "Annualized Return": f"{self.annualized_return()*100:.2f}%",
            "Volatility (Annualized)": f"{self.volatility()*100:.2f}%",
            "Sharpe Ratio": f"{self.sharpe_ratio():.2f}",
            "Maximum Drawdown": f"{self.maximum_drawdown()*100:.2f}%"
        }

if __name__ == "__main__":
    # Test logic
    dates = pd.date_range('2023-01-01', periods=100)
    # Simulate a portfolio going from 1.0 to 1.10
    values = np.linspace(100000, 110000, 100)
    test_df = pd.DataFrame({'date': dates, 'portfolio_value': values})
    
    metrics = PerformanceMetrics(test_df)
    report = metrics.generate_report()
    
    print("Performance Report:")
    for k, v in report.items():
        print(f"  {k}: {v}")

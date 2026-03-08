-- queries.sql
-- Sample SQL Queries for Quant Trading Strategy Engine

-- 1. Retrieve the latest 20 days of closing prices for a specific stock (e.g., AAPL)
SELECT p.date, p.close, p.volume
FROM Price_Data p
JOIN Stocks s ON p.stock_id = s.stock_id
WHERE s.ticker = 'AAPL'
ORDER BY p.date DESC
LIMIT 20;

-- 2. Find all 'BUY' trading signals generated in the last month
SELECT s.ticker, ts.date, ts.indicator_value
FROM Trading_Signals ts
JOIN Stocks s ON ts.stock_id = s.stock_id
WHERE ts.signal_type = 'BUY'
ORDER BY ts.date DESC;

-- 3. Calculate total profit/loss per stock from executed trades
SELECT s.ticker, COUNT(t.trade_id) AS total_trades, SUM(t.profit_loss) AS total_pnl
FROM Trades t
JOIN Stocks s ON t.stock_id = s.stock_id
WHERE t.exit_date IS NOT NULL
GROUP BY s.ticker
ORDER BY total_pnl DESC;

-- 4. Get the daily portfolio value and return for the last 30 days
SELECT date, portfolio_value, daily_return
FROM Portfolio_Performance
ORDER BY date DESC
LIMIT 30;

-- 5. Calculate the overall win rate of the strategy
SELECT 
    COUNT(CASE WHEN profit_loss > 0 THEN 1 END) * 100.0 / NULLIF(COUNT(trade_id), 0) AS win_rate_percentage
FROM Trades
WHERE exit_date IS NOT NULL;

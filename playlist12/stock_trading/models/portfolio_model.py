import sqlite3
from typing import Dict, List, Optional
from datetime import datetime
from .stock_model import StockModel

class PortfolioModel:
    def __init__(self):
        self.db_path = "stocks.db"
        self.stock_model = StockModel()
        self._conn = None  # For testing purposes

    def _get_db_connection(self):
        """Get database connection - either stored test connection or new one"""
        if self._conn is not None:
            return self._conn
        
        conn = sqlite3.connect(self.db_path)
        # Create table if it doesn't exist
        conn.execute("""
            CREATE TABLE IF NOT EXISTS portfolio (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                shares INTEGER NOT NULL,
                purchase_price REAL NOT NULL,
                purchase_date TIMESTAMP NOT NULL
            )
        """)
        conn.commit()
        return conn

    def buy_stock(self, symbol: str, shares: int) -> Dict:
        """Buy shares of a stock and add to portfolio."""
        if not isinstance(shares, int) or shares <= 0:
            raise ValueError("Shares must be a positive integer")

        # Get current stock price
        stock_info = self.stock_model.get_stock_info(symbol)
        current_price = stock_info["price"]
        
        try:
            conn = self._get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO portfolio (symbol, shares, purchase_price, purchase_date) VALUES (?, ?, ?, ?)",
                (symbol, shares, current_price, datetime.now())
            )
            if self._conn is None:  # Only commit if not using test connection
                conn.commit()
                conn.close()
            
            return {
                "symbol": symbol,
                "shares": shares,
                "price_per_share": current_price,
                "total_cost": current_price * shares
            }
        except sqlite3.Error as e:
            print(f"Database error: {str(e)}")
            raise ValueError("Failed to record purchase in database")

    def sell_stock(self, symbol: str, shares: int) -> Dict:
        """Sell shares of a stock from portfolio."""
        if not isinstance(shares, int) or shares <= 0:
            raise ValueError("Shares must be a positive integer")
        
        # Check if we have enough shares
        total_shares = self._get_total_shares(symbol)
        if total_shares < shares:
            raise ValueError(f"Not enough shares to sell. You own {total_shares} shares of {symbol}")
        
        # Get current stock price
        stock_info = self.stock_model.get_stock_info(symbol)
        current_price = stock_info["price"]
        
        try:
            conn = self._get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO portfolio (symbol, shares, purchase_price, purchase_date) VALUES (?, ?, ?, ?)",
                (symbol, -shares, current_price, datetime.now())
            )
            if self._conn is None:
                conn.commit()
                conn.close()
            
            return {
                "symbol": symbol,
                "shares_sold": shares,
                "price_per_share": current_price,
                "total_value": current_price * shares
            }
        except sqlite3.Error as e:
            print(f"Database error: {str(e)}")
            raise ValueError("Failed to record sale in database")

    def get_portfolio(self) -> List[Dict]:
        """Get current portfolio with latest stock prices."""
        portfolio = []
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Get unique symbols and total shares
            cursor.execute("""
                SELECT symbol, SUM(shares) as total_shares
                FROM portfolio
                GROUP BY symbol
                HAVING total_shares > 0
            """)
            
            holdings = cursor.fetchall()
            
            for symbol, shares in holdings:
                # Get current stock price
                stock_info = self.stock_model.get_stock_info(symbol)
                current_price = stock_info["price"]
                
                # Calculate average purchase price
                cursor.execute("""
                    SELECT AVG(purchase_price)
                    FROM portfolio
                    WHERE symbol = ?
                """, (symbol,))
                avg_purchase_price = cursor.fetchone()[0]
                
                portfolio.append({
                    "symbol": symbol,
                    "shares": shares,
                    "current_price": current_price,
                    "current_value": current_price * shares,
                    "avg_purchase_price": avg_purchase_price,
                    "total_gain_loss": (current_price - avg_purchase_price) * shares
                })
                
        return portfolio

    def get_portfolio_value(self) -> Dict:
        """Calculate total portfolio value and gains/losses."""
        portfolio = self.get_portfolio()
        
        total_value = sum(holding["current_value"] for holding in portfolio)
        total_cost = sum(holding["avg_purchase_price"] * holding["shares"] for holding in portfolio)
        total_gain_loss = sum(holding["total_gain_loss"] for holding in portfolio)
        
        return {
            "total_value": total_value,
            "total_cost": total_cost,
            "total_gain_loss": total_gain_loss,
            "total_gain_loss_percent": (total_gain_loss / total_cost * 100) if total_cost > 0 else 0
        }

    def _get_total_shares(self, symbol: str) -> int:
        """Get total shares owned of a particular stock."""
        conn = self._get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT SUM(shares) FROM portfolio WHERE symbol = ?",
            (symbol,)
        )
        result = cursor.fetchone()[0]
        if self._conn is None:
            conn.close()
        return result or 0

import sqlite3
from typing import Dict, List, Optional
from datetime import datetime
from .stock_model import StockModel
from music_collection.utils.sql_utils import get_db_connection


class PortfolioModel:
    def __init__(self):
        self.db_path = "stocks.db"
        self.stock_model = StockModel()

    def buy_stock(self, symbol: str, shares: int) -> Dict:
        """Buy shares of a stock and add to portfolio."""
        # Get current stock price
        stock_info = self.stock_model.get_stock_info(symbol)
        current_price = stock_info["price"]

        try:
        # Use the context manager to handle the database connection
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                "INSERT INTO portfolio (symbol, shares, purchase_price, purchase_date) VALUES (?, ?, ?, ?)",
                (symbol, shares, current_price, datetime.now())
                )
                conn.commit()
        except sqlite3.Error as e:
            raise sqlite3.Error(f"Database error: {str(e)}")

        
        # with sqlite3.connect(self.db_path) as conn:
        #     cursor = conn.cursor()
        #     cursor.execute(
        #         "INSERT INTO portfolio (symbol, shares, purchase_price, purchase_date) VALUES (?, ?, ?, ?)",
        #         (symbol, shares, current_price, datetime.now())
        #     )
        #     conn.commit()
            
        return {
            "symbol": symbol,
            "shares": shares,
            "price_per_share": current_price,
            "total_cost": current_price * shares
        }

    def sell_stock(self, symbol: str, shares: int) -> Dict:
        """Sell shares of a stock from portfolio."""
        # Check if we have enough shares
        total_shares = self._get_total_shares(symbol)
        if total_shares < shares:
            raise ValueError(f"Not enough shares to sell. You own {total_shares} shares of {symbol}")
        
        # Get current stock price
        stock_info = self.stock_model.get_stock_info(symbol)
        current_price = stock_info["price"]
        
        # Remove shares from portfolio
        shares_to_remove = shares
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                # Get portfolio entries ordered by purchase date (FIFO)
                cursor.execute(
                    "SELECT id, shares FROM portfolio WHERE symbol = ? ORDER BY purchase_date",
                    (symbol,)
                )
                entries = cursor.fetchall()
                
                for entry_id, entry_shares in entries:
                    if shares_to_remove <= 0:
                        break
                        
                    if entry_shares <= shares_to_remove:
                        # Remove entire entry
                        cursor.execute("DELETE FROM portfolio WHERE id = ?", (entry_id,))
                        shares_to_remove -= entry_shares
                    else:
                        # Update entry with remaining shares
                        cursor.execute(
                            "UPDATE portfolio SET shares = ? WHERE id = ?",
                            (entry_shares - shares_to_remove, entry_id)
                        )
                        shares_to_remove = 0
                        
                conn.commit()
        except sqlite3.Error as e:
            raise sqlite3.Error(f"Database error: {str(e)}")
            
        return {
            "symbol": symbol,
            "shares_sold": shares,
            "price_per_share": current_price,
            "total_value": current_price * shares
        }

    def get_portfolio(self) -> List[Dict]:
        """Get current portfolio with latest stock prices."""
        portfolio = []
        try:
            with get_db_connection() as conn:
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
        except sqlite3.Error as e:
            raise sqlite3.Error(f"Database error: {str(e)}")
                
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
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT SUM(shares) FROM portfolio WHERE symbol = ?",
                    (symbol,)
                )
                result = cursor.fetchone()[0]
        except sqlite3.Error as e:
            raise sqlite3.Error(f"Database error: {str(e)}")
        return result or 0

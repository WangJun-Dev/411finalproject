import sqlite3
import logging
from music_collection.utils.logger import configure_logger
from typing import Dict, List, Optional
from datetime import datetime
from .stock_model import StockModel

logger = logging.getLogger(__name__)
configure_logger(logger)


class PortfolioModel:
    def __init__(self):
        self.db_path = "stocks.db"
        self.stock_model = StockModel()
        logger.info("PortfolioModel initialized with database path: %s", self.db_path)
        
        # Create the portfolio table if it doesn't exist
        with sqlite3.connect(self.db_path) as conn:
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

    def buy_stock(self, symbol: str, shares: int) -> Dict:
        """
        Buys shares of a stock and adds them to the portfolio.

        Args:
            symbol (str): The stock symbol to purchase.
            shares (int): The number of shares to purchase.

        Returns:
            Dict: A dictionary containing the transaction details, including
                  the stock symbol, number of shares, price per share, and total cost.

        Raises:
            Exception: If an error occurs during the transaction.
        """
        logger.info("Attempting to buy %d shares of %s", shares, symbol)

        if not symbol or not isinstance(symbol, str):
                logger.error("Invalid symbol provided")
                raise ValueError("Invalid symbol provided")
        if not isinstance(shares, int) or shares <= 0:
                logger.error("Shares must be a positive integer")
                raise ValueError("Shares must be a positive integer")
        try:

            # Get current stock price
            stock_info = self.stock_model.get_stock_info(symbol)
            current_price = stock_info["price"]
            logger.debug("Fetched price for %s: %.2f", symbol, current_price)
            
            cursor = self._conn.cursor()
            cursor.execute(
                "INSERT INTO portfolio (symbol, shares, purchase_price, purchase_date) VALUES (?, ?, ?, ?)",
                (symbol, shares, current_price, datetime.now())
            )
            self._conn.commit()
            
            logger.info("Successfully bought %d shares of %s", shares, symbol)

            return {
                "symbol": symbol,
                "shares": shares,
                "price_per_share": current_price,
                "total_cost": current_price * shares
            }
        
        except sqlite3.Error as e:
            logger.error("Database error while buying stock: %s", str(e))
            raise ValueError("Failed to record purchase in database")
        except Exception as e:
            logger.error("Error buying stock: %s", str(e))
            raise ValueError(f"Failed to buy {shares} shares of {symbol}")
        
    def sell_stock(self, symbol: str, shares: int) -> Dict:
        """
        Sells shares of a stock from the portfolio.

        Args:
            symbol (str): The stock symbol to sell.
            shares (int): The number of shares to sell.

        Returns:
            Dict: A dictionary with transaction details (symbol, shares sold, price per share, total value).

        Raises:
            ValueError: For invalid input or insufficient shares.
            Exception: For database errors or unexpected issues.
        """
        logger.info("Attempting to sell %d shares of %s", shares, symbol)

        if not symbol or not isinstance(symbol, str):
            logger.error("Invalid symbol provided")
            raise ValueError("Invalid symbol provided")
        if not isinstance(shares, int) or shares <= 0:
            logger.error("Shares must be a positive integer")
            raise ValueError("Shares must be a positive integer")

        try:
            total_shares = self._get_total_shares(symbol)
            if total_shares < shares:
                logger.error("Not enough shares to sell: owned=%d, requested=%d", total_shares, shares)
                raise ValueError(f"Not enough shares to sell. You own {total_shares} shares of {symbol}")

            stock_info = self.stock_model.get_stock_info(symbol)
            current_price = stock_info["price"]
            logger.debug("Fetched stock price for %s: %.2f", symbol, current_price)

            cursor = self._conn.cursor()
            cursor.execute(
                "SELECT id, shares FROM portfolio WHERE symbol = ? ORDER BY purchase_date",
                (symbol,)
            )
            entries = cursor.fetchall()
            if not entries:
                logger.error("No portfolio entries found for symbol %s", symbol)
                raise ValueError(f"No portfolio entries found for {symbol}")

            shares_to_remove = shares
            for entry_id, entry_shares in entries:
                if shares_to_remove <= 0:
                    break
                if entry_shares <= shares_to_remove:
                    cursor.execute("DELETE FROM portfolio WHERE id = ?", (entry_id,))
                    shares_to_remove -= entry_shares
                else:
                    cursor.execute(
                        "UPDATE portfolio SET shares = ? WHERE id = ?",
                        (entry_shares - shares_to_remove, entry_id)
                    )
                    shares_to_remove = 0

            self._conn.commit()

            logger.info("Successfully sold %d shares of %s", shares, symbol)
            return {
                "symbol": symbol,
                "shares_sold": shares,
                "price_per_share": current_price,
                "total_value": current_price * shares
            }
        except sqlite3.Error as e:
            logger.error("Database error while selling stock: %s", str(e))
            raise Exception("Failed to record sale in database")
        except Exception as e:
            logger.error("Error selling stock: %s", str(e))
            raise Exception(f"Failed to sell {shares} shares of {symbol}")

    def get_portfolio(self) -> List[Dict]:
        """
        Retrieves the current portfolio with the latest stock prices and metrics.

        Returns:
            List[Dict]: A list of dictionaries representing each stock holding, including
                        the stock symbol, number of shares, current price, total value,
                        average purchase price, and total gain/loss.

        Raises:
            Exception: If an error occurs while fetching the portfolio.
        """

        logger.info("Fetching portfolio details.")
        portfolio = []

        try:
            cursor = self._conn.cursor()
            cursor.execute("""
                SELECT symbol, SUM(shares) as total_shares
                FROM portfolio
                GROUP BY symbol
                HAVING total_shares > 0
            """)
            holdings = cursor.fetchall()
            logger.debug("Fetched holdings: %s", holdings)

            for symbol, shares in holdings:
                stock_info = self.stock_model.get_stock_info(symbol)
                current_price = stock_info["price"]

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
                    "total_gain_loss": (current_price - avg_purchase_price) * shares,
                })

            if not portfolio:
                logger.warning("Portfolio is empty.")
                return []

            logger.info("Portfolio fetched successfully.")
            return portfolio
        except sqlite3.Error as e:
            logger.error("Database error while fetching portfolio: %s", str(e))
            raise Exception("Failed to fetch portfolio from the database.")
        except Exception as e:
            logger.error("Error fetching portfolio: %s", str(e))
            raise Exception("Failed to retrieve portfolio details.")

    def get_portfolio_value(self) -> Dict:
        """
        Calculates the total value, cost, and gains/losses of the portfolio.

        Returns:
            Dict: A dictionary containing the total portfolio value, total cost,
                  total gains/losses, and percentage gain/loss.

        Raises:
            Exception: If an error occurs during the calculation.
        """

        logger.info("Calculating portfolio value.")

        try:
            portfolio = self.get_portfolio()
            if not portfolio:
                logger.info("Portfolio is empty. Value calculation skipped.")
                return {
                    "total_value": 0.0,
                    "total_cost": 0.0,
                    "total_gain_loss": 0.0,
                    "total_gain_loss_percent": 0.0,
                }

            total_value = sum(holding["current_value"] for holding in portfolio)
            total_cost = sum(
                holding["avg_purchase_price"] * holding["shares"]
                for holding in portfolio
            )
            total_gain_loss = total_value - total_cost
            gain_loss_percent = (
                (total_gain_loss / total_cost * 100) if total_cost > 0 else 0.0
            )

            logger.info("Portfolio value calculated successfully.")
            return {
                "total_value": total_value,
                "total_cost": total_cost,
                "total_gain_loss": total_gain_loss,
                "total_gain_loss_percent": gain_loss_percent,
            }
        except Exception as e:
            logger.error("Error calculating portfolio value: %s", str(e))
            raise Exception("Failed to calculate portfolio value.")

    def _get_total_shares(self, symbol: str) -> int:
        """
        Retrieves the total number of shares owned for a specific stock.

        Args:
            symbol (str): The stock symbol to query.

        Returns:
            int: The total number of shares owned for the given stock.

        Raises:
            Exception: If an error occurs during the query.
        """

        logging.info("Getting total shares for %s", symbol)

        if not symbol or not isinstance(symbol, str):
            logger.error("Invalid symbol provided")
            raise ValueError("Invalid symbol provided")
        try:
            cursor = self._conn.cursor()
            cursor.execute(
                "SELECT SUM(shares) FROM portfolio WHERE symbol = ?",
                (symbol,)
            )
            result = cursor.fetchone()[0]
            return result or 0
        except sqlite3.Error as e:
            logger.error("Database error while retrieving total shares: %s", str(e))
            raise Exception("Failed to fetch total shares from database")
        except Exception as e:
            logger.error(f"Error getting total shares: {str(e)}")
            raise ValueError(f"Failed to get total shares for {symbol}")

import sqlite3
from typing import Dict, List, Optional, Tuple
import requests
from datetime import datetime
import os

class StockModel:
    def __init__(self):
        self.db_path = "stocks.db"
        self.api_key = os.getenv("ALPHA_VANTAGE_API_KEY")
        self._create_tables()

    def _create_tables(self):
        """Create the necessary tables if they don't exist."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Create stocks table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS stocks (
                    symbol TEXT PRIMARY KEY,
                    company_name TEXT,
                    last_price REAL,
                    last_updated TIMESTAMP
                )
            ''')
            
            # Create portfolio table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS portfolio (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT,
                    shares INTEGER,
                    purchase_price REAL,
                    purchase_date TIMESTAMP,
                    FOREIGN KEY (symbol) REFERENCES stocks(symbol)
                )
            ''')
            conn.commit()

    def get_stock_info(self, symbol: str) -> Dict:
        """Get current stock information from Alpha Vantage API."""
        url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey={self.api_key}"
        response = requests.get(url)
        data = response.json()
        
        if "Global Quote" not in data:
            raise ValueError(f"Could not fetch data for symbol {symbol}")
            
        quote = data["Global Quote"]
        current_price = float(quote.get("05. price", 0))
        
        # Update stock in database
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT OR REPLACE INTO stocks (symbol, last_price, last_updated) VALUES (?, ?, ?)",
                (symbol, current_price, datetime.now())
            )
            conn.commit()
            
        return {
            "symbol": symbol,
            "price": current_price,
            "change": float(quote.get("09. change", 0)),
            "change_percent": quote.get("10. change percent", "0%")
        }

    def get_company_info(self, symbol: str) -> Dict:
        """Get detailed company information from Alpha Vantage API."""
        url = f"https://www.alphavantage.co/query?function=OVERVIEW&symbol={symbol}&apikey={self.api_key}"
        response = requests.get(url)
        data = response.json()
        
        if not data:
            raise ValueError(f"Could not fetch company info for symbol {symbol}")
            
        # Update company name in database
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE stocks SET company_name = ? WHERE symbol = ?",
                (data.get("Name"), symbol)
            )
            conn.commit()
            
        return {
            "name": data.get("Name"),
            "description": data.get("Description"),
            "sector": data.get("Sector"),
            "pe_ratio": data.get("PERatio"),
            "market_cap": data.get("MarketCapitalization"),
            "dividend_yield": data.get("DividendYield")
        }

    def get_historical_data(self, symbol: str) -> List[Dict]:
        """Get historical daily price data from Alpha Vantage API."""
        url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={symbol}&apikey={self.api_key}"
        response = requests.get(url)
        data = response.json()
        
        if "Time Series (Daily)" not in data:
            raise ValueError(f"Could not fetch historical data for symbol {symbol}")
            
        time_series = data["Time Series (Daily)"]
        historical_data = []
        
        for date, values in time_series.items():
            historical_data.append({
                "date": date,
                "open": float(values["1. open"]),
                "high": float(values["2. high"]),
                "low": float(values["3. low"]),
                "close": float(values["4. close"]),
                "volume": int(values["5. volume"])
            })
            
        return historical_data

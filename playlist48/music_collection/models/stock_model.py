from typing import Dict, Any
import requests
import os
import logging
from utils import configure_logger
from dotenv import load_dotenv

logger = logging.getLogger(__name__)
configure_logger(logger)

class StockModel:
    """
    A class to interact with the Alpha Vantage API for fetching stock data.
    
    Attributes:
        api_key (str): The API key for accessing the Alpha Vantage API.
        base_url (str): The base URL of the Alpha Vantage API.
    """

    def __init__(self):
        """
        Initializes the StockModel with API key and base URL.
        Loads environment variables using dotenv.
        """
        load_dotenv()
        self.api_key = os.getenv('ALPHA_VANTAGE_API_KEY')
        self.base_url = 'https://www.alphavantage.co/query'

    def get_stock_info(self, symbol: str) -> Dict[str, Any]:
        """
        Fetches current stock information for a given symbol.

        Args:
            symbol (str): The stock symbol to fetch data for.

        Returns:
            Dict[str, Any]: A dictionary containing the current stock information, including
                            symbol, price, volume, latest trading day, previous close, change,
                            and change percentage.

        Raises:
            ValueError: If data for the given symbol cannot be fetched or is invalid.
        """
        logger.info("Fetching current stock information for symbol: %s", symbol)
        params = {
            'function': 'GLOBAL_QUOTE',
            'symbol': symbol,
            'apikey': self.api_key
        }
        
        try:
            response = requests.get(self.base_url, params=params)
            data = response.json()
            
            if "Global Quote" not in data or not data["Global Quote"]:
                print(f"API Response: {data}")
                raise ValueError(f"Could not fetch data for symbol {symbol}")
            
            quote = data["Global Quote"]

            stock_info = {
                "symbol": quote.get("01. symbol", symbol),
                "price": float(quote.get("05. price", 0)),
                "volume": int(quote.get("06. volume", 0)),
                "latest_trading_day": quote.get("07. latest trading day", ""),
                "previous_close": float(quote.get("08. previous close", 0)),
                "change": float(quote.get("09. change", 0)),
                "change_percent": quote.get("10. change percent", "0%")
            }
            logger.info("Successfully fetched stock information for symbol: %s", symbol)
            return stock_info
        except Exception as e:
            logger.error("Error while fetching stock info for symbol %s: %s", symbol, str(e))
            raise ValueError(f"Could not fetch data for symbol {symbol}")

    def get_historical_data(self, symbol: str) -> Dict[str, Any]:
        """
        Fetches historical stock data for a given symbol.

        Args:
            symbol (str): The stock symbol to fetch historical data for.

        Returns:
            Dict[str, Any]: A dictionary containing historical stock data, with dates as keys
                            and OHLCV (open, high, low, close, volume) data as values.

        Raises:
            ValueError: If historical data for the given symbol cannot be fetched or is invalid.
        """

        logger.info("Fetching historical stock data for symbol: %s", symbol)

        params = {
            'function': 'TIME_SERIES_DAILY',
            'symbol': symbol,
            'apikey': self.api_key
        }
        
        try:
            response = requests.get(self.base_url, params=params)
            data = response.json()
            
            if "Time Series (Daily)" not in data:
                logger.error("API Response for symbol %s: %s", symbol, data)
                raise ValueError(f"Could not fetch historical data for symbol {symbol}")
            
            time_series = data["Time Series (Daily)"]
            historical_data =  {date: {
                "open": float(values["1. open"]),
                "high": float(values["2. high"]),
                "low": float(values["3. low"]),
                "close": float(values["4. close"]),
                "volume": int(values["5. volume"])
            } for date, values in time_series.items()
            }
            logger.info("Successfully fetched historical data for symbol: %s", symbol)
            return historical_data
        
        except Exception as e:
            logger.error("Error while fetching historical data for symbol %s: %s", symbol, str(e))
            raise ValueError(f"Could not fetch historical data for symbol {symbol}")

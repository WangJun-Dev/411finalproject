import pytest
import sqlite3
from datetime import datetime
from unittest.mock import Mock, patch
from music_collection.models.portfolio_model import PortfolioModel

@pytest.fixture
def portfolio_model():
    """Create a test portfolio model with in-memory database"""
    # Create shared database connection
    conn = sqlite3.connect(":memory:")
    
    # Create the portfolio table
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
    
    # Create model and set connection
    model = PortfolioModel()
    model.db_path = ":memory:"
    model._conn = conn  # Store connection on model instance
    
    yield model
    
    # Cleanup
    conn.close()

@pytest.fixture
def mock_stock_info():
    """Mock stock information response"""
    return {
        "symbol": "AAPL",
        "price": 150.00,
        "change": 2.50,
        "change_percent": "1.5%"
    }

def test_buy_stock_success(portfolio_model, mock_stock_info):
    """Test successful stock purchase"""
    with patch.object(portfolio_model.stock_model, 'get_stock_info', return_value=mock_stock_info):
        result = portfolio_model.buy_stock("AAPL", 10)
        
        assert result["symbol"] == "AAPL"
        assert result["shares"] == 10
        assert result["price_per_share"] == 150.00
        assert result["total_cost"] == 1500.00

def test_buy_stock_invalid_shares(portfolio_model, mock_stock_info):
    """Test buying invalid number of shares"""
    with patch.object(portfolio_model.stock_model, 'get_stock_info', return_value=mock_stock_info):
        with pytest.raises(ValueError, match="Shares must be a positive integer"):
            portfolio_model.buy_stock("AAPL", -5)
        
        with pytest.raises(ValueError, match="Shares must be a positive integer"):
            portfolio_model.buy_stock("AAPL", 0)

def test_sell_stock_success(portfolio_model, mock_stock_info):
    """Test successful stock sale"""
    with patch.object(portfolio_model.stock_model, 'get_stock_info', return_value=mock_stock_info):
        # First buy some stock
        portfolio_model.buy_stock("AAPL", 10)
        
        # Then sell part of it
        result = portfolio_model.sell_stock("AAPL", 5)
        
        assert result["symbol"] == "AAPL"
        assert result["shares_sold"] == 5  # Changed from shares to shares_sold
        assert result["price_per_share"] == 150.00
        assert result["total_value"] == 750.00

def test_sell_stock_not_enough_shares(portfolio_model, mock_stock_info):
    """Test selling more shares than owned"""
    with patch.object(portfolio_model.stock_model, 'get_stock_info', return_value=mock_stock_info):
        portfolio_model.buy_stock("AAPL", 5)
        
        with pytest.raises(Exception, match="Failed to sell 10 shares of AAPL"):
            portfolio_model.sell_stock("AAPL", 10)

def test_get_portfolio_empty(portfolio_model):
    """Test getting empty portfolio"""
    portfolio = portfolio_model.get_portfolio()
    assert len(portfolio) == 0

def test_get_portfolio_with_stocks(portfolio_model, mock_stock_info):
    """Test getting portfolio with stocks"""
    with patch.object(portfolio_model.stock_model, 'get_stock_info', return_value=mock_stock_info):
        portfolio_model.buy_stock("AAPL", 10)
        portfolio = portfolio_model.get_portfolio()
        
        assert len(portfolio) == 1
        assert portfolio[0]["symbol"] == "AAPL"
        assert portfolio[0]["shares"] == 10

def test_get_portfolio_value(portfolio_model, mock_stock_info):
    """Test calculating portfolio value"""
    with patch.object(portfolio_model.stock_model, 'get_stock_info', return_value=mock_stock_info):
        portfolio_model.buy_stock("AAPL", 10)
        value = portfolio_model.get_portfolio_value()
        
        assert value["total_value"] == 1500.00  # Changed to check total_value in dict
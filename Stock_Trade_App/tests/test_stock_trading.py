import pytest
from unittest.mock import Mock, patch
from music_collection.models.stock_model import StockModel
from music_collection.models.portfolio_model import PortfolioModel

@pytest.fixture
def mock_stock_response():
    return {
        "Global Quote": {
            "01. symbol": "AAPL",
            "05. price": "150.25",
            "06. volume": "100000",
            "07. latest trading day": "2024-03-15",
            "08. previous close": "149.50",
            "09. change": "0.75",
            "10. change percent": "0.5%"
        }
    }

@pytest.fixture
def stock_model():
    return StockModel()

def test_get_stock_info(stock_model, mock_stock_response):
    with patch('requests.get') as mock_get:
        mock_get.return_value.json.return_value = mock_stock_response
        
        result = stock_model.get_stock_info("AAPL")
        
        assert result["symbol"] == "AAPL"
        assert result["price"] == 150.25
        assert result["volume"] == 100000
        assert result["change"] == 0.75
        assert result["change_percent"] == "0.5%"

def test_get_stock_info_invalid_symbol(stock_model):
    with patch('requests.get') as mock_get:
        mock_get.return_value.json.return_value = {"Global Quote": {}}
        
        with pytest.raises(ValueError, match="Could not fetch data for symbol INVALID"):
            stock_model.get_stock_info("INVALID")

def test_api_error_handling(stock_model):
    with patch('requests.get') as mock_get:
        mock_get.side_effect = Exception("API connection error")
        
        with pytest.raises(ValueError, match="Could not fetch data for symbol AAPL"):
            stock_model.get_stock_info("AAPL")

def test_malformed_response(stock_model):
    with patch('requests.get') as mock_get:
        mock_get.return_value.json.return_value = {"wrong_key": {}}
        
        with pytest.raises(ValueError, match="Could not fetch data for symbol AAPL"):
            stock_model.get_stock_info("AAPL")

def test_empty_response(stock_model):
    with patch('requests.get') as mock_get:
        mock_get.return_value.json.return_value = {}
        
        with pytest.raises(ValueError, match="Could not fetch data for symbol AAPL"):
            stock_model.get_stock_info("AAPL")
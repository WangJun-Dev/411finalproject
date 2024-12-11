from dotenv import load_dotenv
from flask import Flask, jsonify, make_response, Response, request
from music_collection.models.stock_model import StockModel
from music_collection.models.portfolio_model import PortfolioModel
from music_collection.utils.sql_utils import check_database_connection, check_table_exists


# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

stock_model = StockModel()
portfolio_model = PortfolioModel()

####################################################
#
# Healthchecks
#
####################################################

@app.route('/api/health', methods=['GET'])
def healthcheck() -> Response:
    """
    Health check route to verify the service is running.

    Returns:
        JSON response indicating the health status of the service.
    """
    app.logger.info('Health check')
    return make_response(jsonify({'status': 'healthy'}), 200)

@app.route('/api/db-check', methods=['GET'])
def db_check() -> Response:
    """
    Route to check if the database connection and songs table are functional.

    Returns:
        JSON response indicating the database health status.
    Raises:
        404 error if there is an issue with the database.
    """
    try:
        app.logger.info("Checking database connection...")
        check_database_connection()
        app.logger.info("Database connection is OK.")
        app.logger.info("Checking if stocks table exists...")
        check_table_exists("stocks")
        app.logger.info("stocks table exists.")
        app.logger.info("Checking if portfolio table exists...")
        check_table_exists("portfolio")
        app.logger.info("portfolio table exists.")
        return make_response(jsonify({'database_status': 'healthy'}), 200)
    except Exception as e:
        return make_response(jsonify({'error': str(e)}), 404)

####################################################
#
# Stock Information
#
####################################################

@app.route('/api/stock/<symbol>', methods=['GET'])
def get_stock_info(symbol: str) -> Response:
    """
    Get current stock information.

    Path Parameter:
        - symbol (str): The stock symbol to look up.

    Returns:
        JSON response with current stock information.
    """
    try:
        stock_info = stock_model.get_stock_info(symbol)
        return make_response(jsonify(stock_info), 200)
    except Exception as e:
        return make_response(jsonify({'error': str(e)}), 404)

@app.route('/api/stock/<symbol>/company', methods=['GET'])
def get_company_info(symbol: str) -> Response:
    """
    Get detailed company information.

    Path Parameter:
        - symbol (str): The stock symbol to look up.

    Returns:
        JSON response with company information.
    """
    try:
        company_info = stock_model.get_company_info(symbol)
        return make_response(jsonify(company_info), 200)
    except Exception as e:
        return make_response(jsonify({'error': str(e)}), 404)

@app.route('/api/stock/<symbol>/history', methods=['GET'])
def get_stock_history(symbol: str) -> Response:
    """
    Get historical stock data.

    Path Parameter:
        - symbol (str): The stock symbol to look up.

    Returns:
        JSON response with historical price data.
    """
    try:
        historical_data = stock_model.get_historical_data(symbol)
        return make_response(jsonify(historical_data), 200)
    except Exception as e:
        return make_response(jsonify({'error': str(e)}), 404)

####################################################
#
# Portfolio Management
#
####################################################

@app.route('/api/portfolio', methods=['GET'])
def get_portfolio() -> Response:
    """
    Get current portfolio holdings.

    Returns:
        JSON response with portfolio holdings and their current values.
    """
    try:
        portfolio = portfolio_model.get_portfolio()
        return make_response(jsonify(portfolio), 200)
    except Exception as e:
        return make_response(jsonify({'error': str(e)}), 500)

@app.route('/api/portfolio/value', methods=['GET'])
def get_portfolio_value() -> Response:
    """
    Get total portfolio value and performance metrics.

    Returns:
        JSON response with portfolio value and gains/losses.
    """
    try:
        portfolio_value = portfolio_model.get_portfolio_value()
        return make_response(jsonify(portfolio_value), 200)
    except Exception as e:
        return make_response(jsonify({'error': str(e)}), 500)

@app.route('/api/portfolio/buy', methods=['POST'])
def buy_stock() -> Response:
    """
    Buy shares of a stock.

    Expected JSON Input:
        - symbol (str): The stock symbol to buy.
        - shares (int): Number of shares to buy.

    Returns:
        JSON response with transaction details.
    """
    try:
        data = request.get_json()
        symbol = data.get('symbol')
        shares = data.get('shares')

        if not symbol or not shares:
            return make_response(jsonify({'error': 'Symbol and shares are required'}), 400)

        if not isinstance(shares, int) or shares <= 0:
            return make_response(jsonify({'error': 'Shares must be a positive integer'}), 400)

        result = portfolio_model.buy_stock(symbol, shares)
        return make_response(jsonify(result), 201)
    except Exception as e:
        return make_response(jsonify({'error': str(e)}), 500)

@app.route('/api/portfolio/sell', methods=['POST'])
def sell_stock() -> Response:
    """
    Sell shares of a stock.

    Expected JSON Input:
        - symbol (str): The stock symbol to sell.
        - shares (int): Number of shares to sell.

    Returns:
        JSON response with transaction details.
    """
    try:
        data = request.get_json()
        symbol = data.get('symbol')
        shares = data.get('shares')

        if not symbol or not shares:
            return make_response(jsonify({'error': 'Symbol and shares are required'}), 400)

        if not isinstance(shares, int) or shares <= 0:
            return make_response(jsonify({'error': 'Shares must be a positive integer'}), 400)

        result = portfolio_model.sell_stock(symbol, shares)
        return make_response(jsonify(result), 200)
    except ValueError as e:
        return make_response(jsonify({'error': str(e)}), 400)
    except Exception as e:
        return make_response(jsonify({'error': str(e)}), 500)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=6000)

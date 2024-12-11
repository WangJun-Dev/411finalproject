# Stock Trading API

A Flask-based REST API that enables users to view stock information and manage a simulated stock portfolio. The application integrates with Alpha Vantage for real-time market data.

## Running the Application

1. Clone the repository:

2. Build and run with Docker Compose:
docker build -t stock-app .

docker run -d -p 6000:6000 stock-app

The API will be available at http://localhost:6000

## Docker Management Commands

Stop the application:
docker-compose down

View logs:
docker-compose logs -f

Rebuild after making changes:
docker-compose up --build

## Testing the Setup
Verify the API is running:
curl http://localhost:6000/api/health

Expected response:
{
    "status": "healthy"
}

## API Routes

### 1. Health Check
- **Path:** `/api/health`
- **Request Type:** GET
- **Purpose:** Check if the service is running properly
- **Request Format:** None
- **Response Format:**
  ```json
  {
    "status": "string"  // "healthy" when service is running
  }
  ```
- **Example:**
  ```bash
  curl http://localhost:6000/api/health
  ```

### 2. Get Stock Information
- **Path:** `/api/stock/<symbol>`
- **Request Type:** GET
- **Purpose:** Retrieve current price and information for a stock
- **Request Format:**
  - Path Parameter: `symbol` (stock ticker e.g., AAPL)
- **Response Format:**
  ```json
  {
    "symbol": "string",
    "price": "number",
    "volume": "number",
    "change": "number",
    "change_percent": "string"
  }
  ```
- **Example:**
  ```bash
  curl http://localhost:6000/api/stock/AAPL
  ```

### 3. Get Historical Stock Data
- **Path:** `/api/stock/<symbol>/history`
- **Request Type:** GET
- **Purpose:** Retrieve historical price data for a stock
- **Request Format:**
  - Path Parameter: `symbol` (stock ticker e.g., AAPL)
- **Response Format:**
  ```json
  {
    "dates": ["string"],
    "prices": ["number"],
    "volumes": ["number"]
  }
  ```
- **Example:**
  ```bash
  curl http://localhost:6000/api/stock/AAPL/history
  ```

### 4. View Portfolio
- **Path:** `/api/portfolio`
- **Request Type:** GET
- **Purpose:** Get current portfolio holdings and values
- **Request Format:** None
- **Response Format:**
  ```json
  {
    "holdings": [
      {
        "symbol": "string",
        "shares": "integer",
        "current_value": "number",
        "purchase_price": "number",
        "gain_loss": "number"
      }
    ],
    "total_value": "number"
  }
  ```
- **Example:**
  ```bash
  curl http://localhost:6000/api/portfolio
  ```

### 5. Buy Stock
- **Path:** `/api/portfolio/buy`
- **Request Type:** POST
- **Purpose:** Purchase shares of a stock
- **Request Format:**
  ```json
  {
    "symbol": "string",
    "shares": "integer"
  }
  ```
- **Response Format:**
  ```json
  {
    "symbol": "string",
    "shares": "integer",
    "price_per_share": "number",
    "total_cost": "number"
  }
  ```
- **Example:**
  ```bash
  curl -X POST http://localhost:6000/api/portfolio/buy \
    -H 'Content-Type: application/json' \
    -d '{"symbol": "AAPL", "shares": 10}'
  ```

### 6. Sell Stock
- **Path:** `/api/portfolio/sell`
- **Request Type:** POST
- **Purpose:** Sell shares of a stock from portfolio
- **Request Format:**
  ```json
  {
    "symbol": "string",
    "shares": "integer"
  }
  ```
- **Response Format:**
  ```json
  {
    "symbol": "string",
    "shares": "integer",
    "price_per_share": "number",
    "total_proceeds": "number"
  }
  ```
- **Example:**
  ```bash
  curl -X POST http://localhost:6000/api/portfolio/sell \
    -H 'Content-Type: application/json' \
    -d '{"symbol": "AAPL", "shares": 5}'
  ```


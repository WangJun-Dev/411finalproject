DROP TABLE IF EXISTS stocks; 
CREATE TABLE stocks (
    symbol TEXT, 
    company_name TEXT, 
    last_price REAL, 
    last_updated TIMESTAMP
);
DROP TABLE IF EXISTS portfolio;
CREATE TABLE portfolio (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT,
    shares INTEGER,
    purchase_price REAL,
    purchase_date TIMESTAMP,
    FOREIGN KEY (symbol) REFERENCES stocks(symbol)
);
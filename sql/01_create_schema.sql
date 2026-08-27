CREATE SCHEMA IF NOT EXISTS retail;

CREATE TABLE IF NOT EXISTS retail.customers (
    customer_id BIGINT PRIMARY KEY,
    country VARCHAR(100),
    first_purchase_date DATE,
    last_purchase_date DATE,
    total_orders INTEGER DEFAULT 0,
    total_revenue NUMERIC(14,2) DEFAULT 0,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS retail.products (
    stock_code VARCHAR(50) PRIMARY KEY,
    description TEXT,
    first_seen_date DATE,
    last_seen_date DATE,
    avg_unit_price NUMERIC(12,2),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS retail.transactions (
    transaction_id BIGSERIAL PRIMARY KEY,
    invoice_no VARCHAR(50) NOT NULL,
    stock_code VARCHAR(50) NOT NULL,
    description TEXT,
    quantity INTEGER NOT NULL,
    invoice_ts TIMESTAMP NOT NULL,
    unit_price NUMERIC(12,2) NOT NULL,
    customer_id BIGINT,
    country VARCHAR(100),
    revenue NUMERIC(14,2) NOT NULL,
    is_return BOOLEAN DEFAULT FALSE,
    invoice_date DATE GENERATED ALWAYS AS (invoice_ts::date) STORED
);

CREATE INDEX IF NOT EXISTS idx_transactions_invoice_date
    ON retail.transactions(invoice_date);
CREATE INDEX IF NOT EXISTS idx_transactions_customer
    ON retail.transactions(customer_id);
CREATE INDEX IF NOT EXISTS idx_transactions_stock_code
    ON retail.transactions(stock_code);

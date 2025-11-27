-- =========================
--  COMPANY INFORMATION
-- =========================
CREATE TABLE IF NOT EXISTS company (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    address TEXT,
    contact TEXT,
    ntn TEXT,
    strn TEXT
);

-- =========================
--  CUSTOMERS
-- =========================
CREATE TABLE IF NOT EXISTS customers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    address TEXT,
    ntn TEXT,
    strn TEXT,
    contact TEXT,
    email TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =========================
--  PRODUCTS
-- =========================
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    sku TEXT,
    barcode TEXT,
    unit_price DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    tax_rate DECIMAL(5,2) DEFAULT 18.00,
    active INTEGER DEFAULT 1
);

-- =========================
--  INVOICES
-- =========================
CREATE TABLE IF NOT EXISTS invoices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    invoice_no TEXT NOT NULL UNIQUE,
    customer_id INTEGER NOT NULL,
    company_id INTEGER DEFAULT 1,
    date TEXT NOT NULL,
    subtotal DECIMAL(10,2) DEFAULT 0.00,
    sales_tax DECIMAL(10,2) DEFAULT 0.00,
    advance_tax DECIMAL(10,2) DEFAULT 0.00,
    total_amount DECIMAL(10,2) DEFAULT 0.00,
    notes TEXT,
    pdf_path TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(id),
    FOREIGN KEY (company_id) REFERENCES company(id)
);

-- =========================
--  INVOICE ITEMS
-- =========================
CREATE TABLE IF NOT EXISTS invoice_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    invoice_id INTEGER NOT NULL,
    product_id INTEGER,
    description TEXT,
    qty INTEGER NOT NULL,
    unit_price DECIMAL(10,2),
    value DECIMAL(10,2),
    sales_tax_amount DECIMAL(10,2),
    advance_tax_amount DECIMAL(10,2),
    total_amount DECIMAL(10,2),
    FOREIGN KEY (invoice_id) REFERENCES invoices(id),
    FOREIGN KEY (product_id) REFERENCES products(id)
);

-- =========================
--  SETTINGS
-- =========================
CREATE TABLE IF NOT EXISTS settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    key TEXT UNIQUE,
    value TEXT
);

-- =========================
--  CUSTOMER PRODUCT PRICES
-- =========================
CREATE TABLE IF NOT EXISTS customer_product_prices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    custom_price DECIMAL(10,2) NOT NULL,
    UNIQUE(customer_id, product_id),
    FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
);



import os
import sqlite3
import logging
from typing import List, Dict, Any, Optional

# -----------------------------------------
# Database file & schema file paths
# -----------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "..", "data", "invoices.db")
SCHEMA_PATH = os.path.join(BASE_DIR, "db_schema.sql")


class Database:
    """
    Core Database Access Layer.
    Handles all CRUD operations for:
        • company
        • customers
        • products
        • invoices
        • invoice_items
        • settings
    
    Also handles invoice search and PDF path storage.
    """

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = os.path.abspath(db_path)

        # Ensure /data directory exists
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

        # Connect and set row_factory so rows behave like dicts
        # Set a higher timeout to avoid "database is locked" in case of concurrency
        self.conn = sqlite3.connect(self.db_path, timeout=20)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")

        # Load schema if tables do not exist and ensure migrations
        self.initialize_schema()
        self.ensure_schema_migrations()

    # ---------------------------------------------------------
    # Schema Initialization
    # ---------------------------------------------------------
    def initialize_schema(self):
        """Read and run db_schema.sql on first run."""
        if not os.path.isfile(SCHEMA_PATH):
            raise FileNotFoundError(f"Schema file missing at {SCHEMA_PATH}")

        with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
            schema_sql = f.read()

        self.conn.executescript(schema_sql)
        self.conn.commit()

    def ensure_schema_migrations(self):
        """Apply lightweight migrations that CREATE TABLE IF NOT EXISTS cannot cover."""
        self._ensure_product_identifiers()
        self._ensure_invoice_shipped_to()

    def _ensure_product_identifiers(self):
        """Add SKU / barcode columns if the database was created before they existed."""
        cur = self.conn.execute("PRAGMA table_info(products)")
        columns = {row["name"] for row in cur.fetchall()}
        altered = False

        if "sku" not in columns:
            self.conn.execute("ALTER TABLE products ADD COLUMN sku TEXT")
            altered = True

        if "barcode" not in columns:
            self.conn.execute("ALTER TABLE products ADD COLUMN barcode TEXT")
            altered = True

        if altered:
            self.conn.commit()

    def _ensure_invoice_shipped_to(self):
        """Add shipped_to column to invoices if missing."""
        cur = self.conn.execute("PRAGMA table_info(invoices)")
        columns = {row["name"] for row in cur.fetchall()}
        
        if "shipped_to" not in columns:
            self.conn.execute("ALTER TABLE invoices ADD COLUMN shipped_to TEXT")
            self.conn.commit()

    # ---------------------------------------------------------
    # Generic Helpers
    # ---------------------------------------------------------
    def execute(self, query: str, params: tuple = ()):
        """Execute INSERT/UPDATE/DELETE and commit."""
        try:
            cur = self.conn.cursor()
            cur.execute(query, params)
            self.conn.commit()
            return cur
        except sqlite3.Error as e:
            self.conn.rollback()
            logging.error(f"DB Execute Error: {e} | Query: {query} | Params: {params}")
            raise

    def fetch_all(self, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """Run SELECT and return multiple rows as dicts."""
        try:
            cur = self.conn.cursor()
            cur.execute(query, params)
            rows = cur.fetchall()
            return [dict(row) for row in rows]
        except sqlite3.Error as e:
            logging.error(f"DB FetchAll Error: {e} | Query: {query} | Params: {params}")
            raise

    def fetch_one(self, query: str, params: tuple = ()) -> Optional[Dict[str, Any]]:
        """Run SELECT and return a single row as a dict."""
        try:
            cur = self.conn.cursor()
            cur.execute(query, params)
            row = cur.fetchone()
            return dict(row) if row else None
        except sqlite3.Error as e:
            logging.error(f"DB FetchOne Error: {e} | Query: {query} | Params: {params}")
            raise

    # ---------------------------------------------------------
    # Company
    # ---------------------------------------------------------
    def get_company(self) -> Optional[Dict[str, Any]]:
        return self.fetch_one("SELECT * FROM company LIMIT 1")

    def update_company(self, data: Dict[str, Any]):
        """Insert or update company info (only one record allowed)."""
        existing = self.get_company()

        if existing:
            # Update
            self.execute(
                """
                UPDATE company 
                SET name=?, address=?, contact=?, ntn=?, strn=? 
                WHERE id=?
                """,
                (data["name"], data["address"], data["contact"],
                 data["ntn"], data["strn"], existing["id"]),
            )
        else:
            # Insert
            self.execute(
                """
                INSERT INTO company (name, address, contact, ntn, strn)
                VALUES (?, ?, ?, ?, ?)
                """,
                (data["name"], data["address"], data["contact"],
                 data["ntn"], data["strn"]),
            )

    # ---------------------------------------------------------
    # Customers
    # ---------------------------------------------------------
    def add_customer(self, data: Dict[str, Any]) -> int:
        cur = self.execute(
            """
            INSERT INTO customers (name, address, ntn, strn, contact, email)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (data["name"], data["address"], data["ntn"], data["strn"],
             data["contact"], data["email"]),
        )
        return cur.lastrowid

    def update_customer(self, customer_id: int, data: Dict[str, Any]):
        self.execute(
            """
            UPDATE customers
            SET name=?, address=?, ntn=?, strn=?, contact=?, email=?
            WHERE id=?
            """,
            (data["name"], data["address"], data["ntn"], data["strn"],
             data["contact"], data["email"], customer_id),
        )

    def get_customer(self, customer_id: int) -> Optional[Dict[str, Any]]:
        return self.fetch_one(
            "SELECT * FROM customers WHERE id=?",
            (customer_id,),
        )

    def get_customers(self) -> List[Dict[str, Any]]:
        return self.fetch_all(
            "SELECT * FROM customers ORDER BY name ASC"
        )

    def search_customers(self, query: str) -> List[Dict[str, Any]]:
        q = f"%{query}%"
        return self.fetch_all(
            """
            SELECT *
            FROM customers
            WHERE name LIKE ?
                OR contact LIKE ?
                OR email LIKE ?
            ORDER BY name ASC
            """,
            (q, q, q),
        )

    def delete_customer(self, customer_id: int):
        self.execute("DELETE FROM customers WHERE id=?", (customer_id,))

    # ---------------------------------------------------------
    # Products
    # ---------------------------------------------------------
    def add_product(self, data: Dict[str, Any]) -> int:
        cur = self.execute(
            """
            INSERT INTO products (name, description, sku, barcode, unit_price, tax_rate, active)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                data["name"],
                data.get("description", ""),
                data.get("sku", ""),
                data.get("barcode", ""),
                data["unit_price"],
                data["tax_rate"],
                data.get("active", 1),
            ),
        )
        return cur.lastrowid

    def get_products(self) -> List[Dict[str, Any]]:
        return self.fetch_all(
            "SELECT * FROM products WHERE active=1 ORDER BY name ASC"
        )

    def update_product(self, product_id: int, data: Dict[str, Any]):
        self.execute(
            """
            UPDATE products
            SET name=?, description=?, sku=?, barcode=?, unit_price=?, tax_rate=?, active=?
            WHERE id=?
            """,
            (
                data["name"],
                data.get("description", ""),
                data.get("sku", ""),
                data.get("barcode", ""),
                data["unit_price"],
                data["tax_rate"],
                data.get("active", 1),
                product_id,
            ),
        )

    def update_product_price(self, product_id: int, new_price: float):
        self.execute(
            "UPDATE products SET unit_price=? WHERE id=?",
            (new_price, product_id)
        )

    def get_product(self, product_id: int) -> Optional[Dict[str, Any]]:
        return self.fetch_one(
            "SELECT * FROM products WHERE id=?",
            (product_id,),
        )

    def search_products(self, query: str) -> List[Dict[str, Any]]:
        q = f"%{query}%"
        return self.fetch_all(
            """
            SELECT *
            FROM products
            WHERE (name LIKE ? OR description LIKE ? OR sku LIKE ? OR barcode LIKE ?)
              AND active=1
            ORDER BY name ASC
            """,
            (q, q, q, q),
        )

    def delete_product(self, product_id: int):
        """Soft delete: set active=0 instead of hard delete."""
        self.execute(
            "UPDATE products SET active=0 WHERE id=?",
            (product_id,)
        )

    def get_customer_price_for_product(self, customer_id: int, product_id: int) -> Optional[float]:
        if not customer_id:
            return None
        row = self.fetch_one(
            """
            SELECT custom_price
            FROM customer_product_prices
            WHERE customer_id=? AND product_id=?
            """,
            (customer_id, product_id),
        )
        return float(row["custom_price"]) if row else None

    def upsert_customer_product_price(self, customer_id: int, product_id: int, custom_price: float):
        self.execute(
            """
            INSERT INTO customer_product_prices (customer_id, product_id, custom_price)
            VALUES (?, ?, ?)
            ON CONFLICT(customer_id, product_id) DO UPDATE SET custom_price=excluded.custom_price
            """,
            (customer_id, product_id, custom_price),
        )

    def get_customer_product_prices(self, customer_id: int) -> List[Dict[str, Any]]:
        return self.fetch_all(
            """
            SELECT cpp.id,
            cpp.custom_price,
            p.id AS product_id,
            p.name AS product_name,
            p.unit_price AS default_price
            FROM customer_product_prices cpp
            JOIN products p ON p.id = cpp.product_id
            WHERE cpp.customer_id = ?
            ORDER BY p.name ASC
            """,
            (customer_id,),
        )

    def delete_customer_product_price(self, customer_id: int, product_id: int):
        self.execute(
            """
            DELETE FROM customer_product_prices
            WHERE customer_id=? AND product_id=?
            """,
            (customer_id, product_id),
        )

    # ---------------------------------------------------------
    # Invoices
    # ---------------------------------------------------------
    def add_invoice(self, data: Dict[str, Any]) -> int:
        """
        Insert invoice header ONLY.
        Returns invoice_id so caller can add items.
        """
        cur = self.execute(
            """
            INSERT INTO invoices (
                invoice_no, customer_id, company_id, date,
                subtotal, sales_tax, advance_tax, total_amount,
                notes, pdf_path, shipped_to
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                data["invoice_no"],
                data["customer_id"],
                data.get("company_id", 1),
                data["date"],
                data["subtotal"],
                data["sales_tax"],
                data["advance_tax"],
                data["total_amount"],
                data.get("notes", ""),
                data.get("pdf_path", ""),   # may be empty before PDF generation
                data.get("shipped_to", ""),
            ),
        )
        return cur.lastrowid

    def add_invoice_items(self, invoice_id: int, items: List[Dict[str, Any]]):
        """Insert line items for an invoice."""
        for item in items:
            self.execute(
                """
                INSERT INTO invoice_items (
                    invoice_id, product_id, description, qty,
                    unit_price, value, sales_tax_amount,
                    advance_tax_amount, total_amount
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    invoice_id,
                    item.get("product_id"),
                    item.get("description"),
                    float(item.get("qty", 0)),
                    float(item.get("unit_price", 0)),
                    float(item.get("value", 0)),
                    float(item.get("sales_tax_amount", 0)),
                    float(item.get("advance_tax_amount", 0)),
                    float(item.get("total_amount", 0)),
                ),
            )

    def create_invoice_with_items(self, invoice_data, items) -> int:
        """
        Atomic helper — ensures invoice + items are saved together.
        Rolls back if anything fails.
        """
        try:
            cur = self.conn.cursor()
            cur.execute("BEGIN")

            invoice_id = self.add_invoice(invoice_data)
            self.add_invoice_items(invoice_id, items)

            self.conn.commit()
            return invoice_id

        except Exception:
            self.conn.rollback()
            raise

    # ---------------------------------------------------------
    # Invoice Retrieval & Search
    # ---------------------------------------------------------
    def get_invoices(self) -> List[Dict[str, Any]]:
        """Return all invoices with customer name."""
        return self.fetch_all(
            """
            SELECT i.*, c.name AS customer_name
            FROM invoices i
            LEFT JOIN customers c ON i.customer_id = c.id
            ORDER BY date DESC
            """
        )

    def search_invoices(self, query: str) -> List[Dict[str, Any]]:
        """Search by invoice number OR customer name."""
        q = f"%{query}%"
        return self.fetch_all(
            """
            SELECT i.*, c.name AS customer_name
            FROM invoices i
            LEFT JOIN customers c ON i.customer_id = c.id
            WHERE i.invoice_no LIKE ?
               OR c.name LIKE ?
            ORDER BY i.date DESC
            """,
            (q, q),
        )

    def get_invoice(self, invoice_id: int) -> Optional[Dict[str, Any]]:
        """Get invoice header with joined customer data."""
        return self.fetch_one(
            """
            SELECT i.*,
                   c.name AS customer_name,
                   c.address AS customer_address,
                   c.ntn AS customer_ntn,
                   c.strn AS customer_strn
            FROM invoices i
            LEFT JOIN customers c ON i.customer_id = c.id
            WHERE i.id=?
            """,
            (invoice_id,),
        )

    def get_invoice_items(self, invoice_id: int) -> List[Dict[str, Any]]:
        return self.fetch_all(
            "SELECT * FROM invoice_items WHERE invoice_id=?",
            (invoice_id,)
        )

    def update_invoice_pdf_path(self, invoice_id, pdf_path):
        self.execute(
            "UPDATE invoices SET pdf_path = ? WHERE id = ?",
            (pdf_path, invoice_id)
        )
        
    def delete_invoice(self, invoice_id):
        # First delete invoice items (FK requires this)
        self.execute("DELETE FROM invoice_items WHERE invoice_id = ?", (invoice_id,))
        # Then delete invoice itself
        self.execute("DELETE FROM invoices WHERE id = ?", (invoice_id,))


    # ---------------------------------------------------------
    # Settings
    # ---------------------------------------------------------
    def set_setting(self, key: str, value: str):
        """Insert or update a setting."""
        self.execute(
            """
            INSERT INTO settings (key, value)
            VALUES (?, ?)
            ON CONFLICT(key) DO UPDATE SET value=excluded.value
            """,
            (key, value),
        )

    def get_setting(self, key: str) -> Optional[str]:
        result = self.fetch_one("SELECT value FROM settings WHERE key=?", (key,))
        return result["value"] if result else None

    # ---------------------------------------------------------
    # Cleanup
    # ---------------------------------------------------------
    def close(self):
        if self.conn:
            self.conn.close()


# Manual test hook
if __name__ == "__main__":
    db = Database()
    print("Company:", db.get_company())
    print("Customers:", db.get_customers())
    db.close()

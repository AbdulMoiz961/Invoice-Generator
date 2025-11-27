import csv
import os
import sqlite3
from typing import List, Dict, Any
from contextlib import closing

BASE_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(BASE_DIR, "..", "data")
DB_FILE = os.path.join(DATA_DIR, "invoices.db")

def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def export_to_csv(table_name: str, output_path: str):
    """Export a table to a CSV file."""
    with closing(_connect()) as conn:
        cursor = conn.execute(f"SELECT * FROM {table_name}")
        rows = cursor.fetchall()
        if not rows:
            return
        
        headers = rows[0].keys()
        
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            for row in rows:
                writer.writerow(list(row))

def import_customers_from_csv(csv_path: str) -> int:
    """Import customers from CSV. Updates existing by name or inserts new."""
    count = 0
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        with closing(_connect()) as conn:
            for row in reader:
                # Basic upsert based on name
                name = row.get('name')
                if not name:
                    continue
                
                exists = conn.execute("SELECT id FROM customers WHERE name = ?", (name,)).fetchone()
                if exists:
                    conn.execute("""
                        UPDATE customers SET 
                            address=?, ntn=?, strn=?, contact=?, email=?
                        WHERE id=?
                    """, (
                        row.get('address', ''),
                        row.get('ntn', ''),
                        row.get('strn', ''),
                        row.get('contact', ''),
                        row.get('email', ''),
                        exists['id']
                    ))
                else:
                    conn.execute("""
                        INSERT INTO customers (name, address, ntn, strn, contact, email)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (
                        name,
                        row.get('address', ''),
                        row.get('ntn', ''),
                        row.get('strn', ''),
                        row.get('contact', ''),
                        row.get('email', '')
                    ))
                count += 1
            conn.commit()
    return count

def import_products_from_csv(csv_path: str) -> int:
    """Import products from CSV. Updates existing by name or inserts new."""
    count = 0
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        with closing(_connect()) as conn:
            for row in reader:
                name = row.get('name')
                if not name:
                    continue
                
                exists = conn.execute("SELECT id FROM products WHERE name = ?", (name,)).fetchone()
                
                # Handle numeric fields safely
                try:
                    unit_price = float(row.get('unit_price', 0))
                except ValueError:
                    unit_price = 0.0
                    
                try:
                    tax_rate = float(row.get('tax_rate', 0))
                except ValueError:
                    tax_rate = 0.0
                    
                active = 1
                if row.get('active') and str(row.get('active')).lower() in ['0', 'false', 'no']:
                    active = 0

                if exists:
                    conn.execute("""
                        UPDATE products SET 
                            description=?, sku=?, barcode=?, unit_price=?, tax_rate=?, active=?
                        WHERE id=?
                    """, (
                        row.get('description', ''),
                        row.get('sku', ''),
                        row.get('barcode', ''),
                        unit_price,
                        tax_rate,
                        active,
                        exists['id']
                    ))
                else:
                    conn.execute("""
                        INSERT INTO products (name, description, sku, barcode, unit_price, tax_rate, active)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        name,
                        row.get('description', ''),
                        row.get('sku', ''),
                        row.get('barcode', ''),
                        unit_price,
                        tax_rate,
                        active
                    ))
                count += 1
            conn.commit()
    return count

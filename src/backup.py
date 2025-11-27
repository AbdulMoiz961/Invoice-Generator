import os
import shutil
import datetime
from src.pdfgen import generate_invoice_pdf
import sqlite3
from typing import List, Dict

BASE_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(BASE_DIR, "..", "data")
DB_FILE = os.path.join(DATA_DIR, "invoices.db")
BACKUP_DIR = os.path.join(DATA_DIR, "backups")

os.makedirs(BACKUP_DIR, exist_ok=True)


# ---------------------------
# Backup SQLite database
# ---------------------------
def backup_database():
    """Create a timestamped backup of the SQLite DB."""
    if not os.path.exists(DB_FILE):
        raise FileNotFoundError("Database file not found.")
    
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"invoices_backup_{ts}.db"
    backup_path = os.path.join(BACKUP_DIR, backup_name)
    
    shutil.copy2(DB_FILE, backup_path)
    print(f"✅ Database backup created: {backup_path}")
    return backup_path


# --------------------------
# Restore SQLite database
# --------------------------
def restore_database(backup_file: str):
    """Restore DB from a chosen backup file."""
    if not os.path.exists(backup_file):
        raise FileNotFoundError("Backup file not found.")
    shutil.copy2(backup_file, DB_FILE)
    print(f"✅ Database restored from: {backup_file}")
    return DB_FILE


# --------------------------
# Invoice regeneration utility
# --------------------------
def regenerate_all_pdfs(output_dir=None) -> List[str]:
    """Recreate PDF files for all invoices from DB (useful after layout updates)."""
    if output_dir is None:
        output_dir = os.path.join(DATA_DIR, "pdf_exports")
    os.makedirs(output_dir, exist_ok=True)
    
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    
    pdf_paths = []
    invoices = conn.execute("SELECT * FROM invoices").fetchall()
    for inv_row in invoices:
        inv = dict(inv_row)
        inv_id = inv_row["id"]
        
        items = [
            dict(r)
            for r in conn.execute(
                "SELECT * FROM invoice_items WHERE invoice_id=?", (inv_id,)
            )
        ]
        
        file_name = f"Invoice_{inv['invoice_no']}.pdf"
        file_path = os.path.join(output_dir, file_name)
        generate_invoice_pdf(inv, items, file_path)
        pdf_paths.append(file_path)
        
    conn.close()
    print(f"✅ {len(pdf_paths)} invoices regenerated in {output_dir}")
    return pdf_paths

if __name__ == "__main__":
    # Example usage
    backup_database()
    # restore_database(r"data\backups\invoices_backup_20251016_142030.db")
    regenerate_all_pdfs()
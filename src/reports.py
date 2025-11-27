import os
import sqlite3
import tempfile
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from PyPDF2 import PdfMerger

from src.pdfgen import generate_invoice_pdf

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "invoices.db")


def _load_company(conn: sqlite3.Connection) -> Dict:
    """Fetch the single company record (if present)."""
    row = conn.execute("SELECT * FROM company LIMIT 1").fetchone()
    return dict(row) if row else {}


def _format_customer(row: sqlite3.Row) -> Dict:
    return {
        "name": row.get("customer_name", "") if isinstance(row, dict) else row["customer_name"],
        "address": row.get("customer_address", "") if isinstance(row, dict) else row["customer_address"],
        "ntn": row.get("customer_ntn", "") if isinstance(row, dict) else row["customer_ntn"],
        "strn": row.get("customer_strn", "") if isinstance(row, dict) else row["customer_strn"],
        "contact": row.get("customer_contact", "") if isinstance(row, dict) else row["customer_contact"],
    }


def get_invoices_for_month(year: int, month: int) -> List[Dict]:
    """Return all invoices (with company, customer and items) for a given month."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    start = f"{year:04d}-{month:02d}-01"
    end = f"{year:04d}-{month:02d}-31"

    company_data = _load_company(conn)

    query = """
        SELECT i.*,
               c.name   AS customer_name,
               c.address AS customer_address,
               c.ntn    AS customer_ntn,
               c.strn   AS customer_strn,
               c.contact AS customer_contact
          FROM invoices i
          LEFT JOIN customers c ON c.id = i.customer_id
         WHERE i.date BETWEEN ? AND ?
         ORDER BY i.date ASC, i.invoice_no ASC
    """

    invoices: List[Dict] = []
    try:
        rows = conn.execute(query, (start, end)).fetchall()
        for row in rows:
            inv = dict(row)
            inv_id = row["id"]
            items = [
                dict(ir)
                for ir in conn.execute(
                    "SELECT * FROM invoice_items WHERE invoice_id = ?", (inv_id,)
                )
            ]
            inv["items"] = items
            inv["company"] = company_data
            inv["customer"] = _format_customer(inv)
            invoices.append(inv)
        return invoices
    finally:
        conn.close()


# --------------------------
# Monthly summary cover
# --------------------------
def create_summary_page(
    invoices: List[Dict], output_path: str, year: Optional[int] = None, month: Optional[int] = None
):
    """Create a one-page summary with totals for the month."""
    total_sales = Decimal("0")
    total_sales_tax = Decimal("0")
    total_advance_tax = Decimal("0")
    total_qty = Decimal("0")
    
    for inv in invoices:
        total_sales += Decimal(str(inv.get("subtotal", 0)))
        total_sales_tax += Decimal(str(inv.get("sales_tax", inv.get("sales_tax_total", 0))))
        total_advance_tax += Decimal(str(inv.get("advance_tax", inv.get("advance_tax_total", 0))))
        items = inv.get("items", [])
        total_qty += sum(Decimal(str(i.get("qty", 0))) for i in items)
        
    doc = SimpleDocTemplate(output_path, pagesize=A4, leftMargin=40, rightMargin=40, topMargin=50, bottomMargin=40)
    styles = getSampleStyleSheet()
    story = []
    
    title_style = ParagraphStyle("title", parent=styles["Heading1"], fontSize=18, alignment=1)
    if year and month:
        month_label = datetime(year, month, 1).strftime("%B %Y")
        title_text = f"{month_label} Summary"
    else:
        title_text = "Monthly Invoice Summary"
    story.append(Paragraph(title_text, title_style))
    story.append(Spacer(1, 12))
    
    data = [
        ["Metric", "Total"],
        ["Total Sales", f"{total_sales:,.2f}"],
        ["Sales Tax Collected", f"{total_sales_tax:,.2f}"],
        ["Advance Tax Collected", f"{total_advance_tax:,.2f}"],
        ["Total Quantity (pcs)", f"{total_qty:,.0f}"],
        ["Number of Invoices", str(len(invoices))],
    ]
    
    tbl = Table(data, colWidths=[120, 120])
    tbl.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.lightgrey),
        ("GRID", (0,0), (-1,-1), 0.5, colors.grey),
        ("ALIGN", (1,1), (-1,-1), "RIGHT"),
    ]))
    story.append(tbl)
    
    doc.build(story)
    return output_path

# --------------------------
# Main monthly generator
# --------------------------
def _default_output_dir() -> str:
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    invoices_dir = os.path.join(root, "invoices")
    os.makedirs(invoices_dir, exist_ok=True)
    return invoices_dir


def generate_monthly_report(year: int, month: int, output_dir=None, include_summary: bool = True) -> str:
    """Generate merged PDF with all invoices for a month plus optional summary page."""
    invoices = get_invoices_for_month(year, month)
    if not invoices:
        raise ValueError(f"No invoices found for {year}-{month:02d}")
    
    if output_dir is None:
        output_dir = _default_output_dir()
    os.makedirs(output_dir, exist_ok=True)
        
    month_name = datetime(year, month, 1).strftime("%B")
    merged_path = os.path.join(output_dir, f"Invoices_{month_name}_{year}.pdf")
    
    tmp_files = []
    
    # Create summary page first
    if include_summary:
        summary_tmp = tempfile.NamedTemporaryFile(delete=False, suffix="_summary.pdf")
        summary_tmp.close()
        create_summary_page(invoices, summary_tmp.name, year, month)
        tmp_files.append(summary_tmp.name)
    
    # Generate each invoice
    for inv in invoices:
        inv_no = inv["invoice_no"]
        items = inv["items"]
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=f"_inv_{inv_no}.pdf")
        tmp.close()
        generate_invoice_pdf(inv, items, tmp.name)
        tmp_files.append(tmp.name)
        
    # Merge them all
    merger = PdfMerger()
    for f in tmp_files:
        merger.append(f)
    merger.write(merged_path)
    merger.close()
    
    # Clean temp files
    for f in tmp_files:
        try:
            os.remove(f)
        except Exception:
            pass
        
    return merged_path

if __name__ == "__main__":
    path = generate_monthly_report(2025, 10)
    print("Merged PDF:", path)
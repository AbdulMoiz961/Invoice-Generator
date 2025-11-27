from decimal import Decimal
import os
import tempfile
from typing import List, Dict
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Flowable, Indenter
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.fonts import addMapping
from PyPDF2 import PdfMerger

# -----------------------------------
# Safe import of calculation helpers
# -----------------------------------
try:
    from .calculations import _money
except Exception:
    from calculations import _money


# -----------------------------------
# Font registration helpers
# -----------------------------------
def register_fonts(font_dir: str):
    """Register fonts used by the invoice generator."""
    def try_register(name, filename):
        path = os.path.join(font_dir, filename)
        if os.path.isfile(path):
            try:
                pdfmetrics.registerFont(TTFont(name, path))
                return True
            except Exception:
                return False
        return False

    # Lora Semibold for logo
    if not try_register("Lora-Semibold", "Lora-SemiBold.ttf"):
        try_register("Lora-Semibold", "Lora-Semibold.ttf")

    # Cambria for table text
    has_cambria = try_register("Cambria", "Cambria.ttf")
    has_cambria_bold = try_register("Cambria-Bold", "Cambria-Bold.ttf")

    if has_cambria and has_cambria_bold:
        addMapping('Cambria', 0, 0, 'Cambria')
        addMapping('Cambria', 1, 0, 'Cambria-Bold')

    # Arial Rounded for company/buyer
    if not try_register("ArialRounded", "ArialRoundedMTBold.ttf"):
        try_register("ArialRounded", "ARLRDBD.TTF")

    # Helvetica (Custom)
    try_register("Helvetica", "Helvetica.ttf")


# -----------------------------------
# Simple layout helpers
# -----------------------------------
class HR(Flowable):
    """A horizontal rule for spacing."""
    def __init__(self, width=450):
        super().__init__()
        self.width = width

    def draw(self):
        self.canv.setLineWidth(0.5)
        self.canv.line(0, 0, self.width, 0)


def money_str(value: Decimal) -> str:
    return f"{_money(value):,.2f}"

def int_str(value) -> str:
    """Formats integers cleanly (no .00)."""
    try:
        value = Decimal(str(value))
        return f"{int(value):,}"
    except Exception:
        return str(value)
    
# -----------------------------------
# Page numbering helper
# -----------------------------------
def add_page_number(canvas, doc):
    canvas.setFont("Helvetica", 8)
    page_num = canvas.getPageNumber()
    text = f"Page {page_num}"
    canvas.drawRightString(200 * mm, 10 * mm, text)


# -----------------------------------
# Main generator
# -----------------------------------
def generate_invoice_pdf(invoice: Dict, items: List[Dict], output_path: str, fonts_path=None):
    """Generate a single invoice PDF identical to the reference layout (inv-214)."""
    from reportlab.platypus import Paragraph, Spacer, Table, TableStyle, Flowable
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib import colors
    from reportlab.lib.units import mm
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfbase import pdfmetrics
    from decimal import Decimal

    if fonts_path is None:
        base = os.path.dirname(__file__)
        fonts_path = os.path.join(base, "resources", "fonts")

    register_fonts(fonts_path)

    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        leftMargin=15 * mm,
        rightMargin=15 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
        title=f"Shaguftaz",
        author="Shaguftaz"
    )

    styles = getSampleStyleSheet()
    normal = styles["Normal"]
    normal.fontName = "Cambria" if "Cambria" in pdfmetrics.getRegisteredFontNames() else "Times-Roman"
    normal.fontSize = 9
    normal.wordWrap = "LTR"

    heading_style = ParagraphStyle(
        "Heading",
        parent=styles["Heading1"],
        fontName="Lora-Semibold" if "Lora-Semibold" in pdfmetrics.getRegisteredFontNames() else normal.fontName,
        fontSize=26,
        leading=28,
        spaceAfter=2,
    )

    small_bold = ParagraphStyle(
        "small_bold",
        parent=styles["Normal"],
        fontSize=10,
        leading=13,
        fontName="Cambria",
    )

    story = []

    # ------------------ HEADER ------------------
    story.append(Paragraph("Shaguftaz", heading_style))
    
    subtitle_style = ParagraphStyle(
        "Subtitle",
        parent=normal,
        fontSize=11,
        leading=12,
        spaceAfter=4,
    )
    story.append(Paragraph("Distributor, Communication", subtitle_style))

    story.append(Spacer(1, 4))

    company = invoice.get("company", {})
    cust = invoice.get("customer", {})

    left_col = f"""
    {company.get("address") or ""}<br/>
    Contact: {company.get("contact") or ""}<br/>
    NTN: {company.get("ntn") or ""}
    {"<br/>STRN: "+company.get("strn") if company.get("strn") else ""}
    """

    right_col = f"""
    <b>Invoice No:</b> {invoice.get("invoice_no") or ""}<br/><br/>
    <b>Date:</b> {invoice.get("date") or ""}<br/><br/>
    <b>Bill To:</b><br/>
    {cust.get("name") or ""}<br/>
    NTN: {cust.get("ntn") or ""}<br/>
    STRN: {cust.get("strn") or ""}<br/>
    <b>Shipped to:</b> {invoice.get("shipped_to") or cust.get("address") or ""}
    {"<br/>Contact: " + cust.get("contact") if cust.get("contact") else ""}
    """
    
    header_table = Table(
        [[Paragraph(left_col, small_bold), Paragraph(right_col, small_bold)]],
        colWidths=[102 * mm, 80 * mm],
        hAlign="LEFT",
    )
    header_table.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ]
        )
    )
    story.append(header_table)
    story.append(Spacer(1, 15))
    
    # ------------------ SalesTaxInvoice Heading ------------------
    sales_tax_style = ParagraphStyle(
        "sales_tax_heading",
        parent=normal,
        fontSize=12,
        leading=14,
        alignment=1,  # 1 = center
        fontName=normal.fontName,
        spaceAfter=8,
    )

    story.append(Paragraph("<b><u>Sales Tax Invoice</u></b>", sales_tax_style))
    story.append(Spacer(1, 2))
    
    # ------------------ TABLE ------------------
    header_center = ParagraphStyle(
        "header_center",
        parent=normal,
        alignment=1, # 0=left, 1=center, 2=right
        leading=10, # adjust spacing between lines if needed
        fontName="Cambria-Bold" if "Cambria-Bold" in pdfmetrics.getRegisteredFontNames() else "Cambria",
    )
    headers = [
        Paragraph("S. No.", header_center),
        Paragraph("Description", header_center),
        Paragraph("Qty", header_center),
        Paragraph("Unit<br/>Price", header_center),
        Paragraph("Value", header_center),
        # Paragraph("S/Tax %", header_center),
        Paragraph("S/Tax<br/>Amount (18%)", header_center),
        Paragraph("Adv Tax<br/>Amount (0.5%)", header_center),
        Paragraph("Amount", header_center),
    ]
    rows = [headers]

    for it in items:
        rows.append(
            [
                str(it.get("sno", "")),
                Paragraph(it.get("description", ""), normal),
                int_str(it.get("qty", 0)),  # no decimals for quantity
                money_str(Decimal(str(it.get("unit_price", 0)))),  # keep decimals for price
                money_str(Decimal(str(it.get("value", 0)))),
                # f"{int_str(it.get('sales_tax_percent', 0))}%",  # whole number percent
                money_str(Decimal(str(it.get("sales_tax_amount", 0)))),
                money_str(Decimal(str(it.get("advance_tax_amount", 0)))),
                money_str(Decimal(str(it.get("total_amount", 0)))),
            ]
        )

    subtotal = sum(Decimal(str(it.get("value", 0))) for it in items)
    sales_tax_total = sum(Decimal(str(it.get("sales_tax_amount", 0))) for it in items)
    advance_tax_total = sum(Decimal(str(it.get("advance_tax_amount", 0))) for it in items)
    grand_total = sum(Decimal(str(it.get("total_amount", 0))) for it in items)
    total_pieces = sum(Decimal(str(it.get("qty", 0))) for it in items)

    col_widths = [
        10 * mm,   # S. No.
        60 * mm,   # Description
        12 * mm,   # Qty
        16 * mm,   # Unit Price
        22 * mm,   # Value
        20 * mm,   # S/Tax Amount
        18 * mm,   # Adv Tax Amount
        26 * mm,   # Amount
    ]

    # Force-fit to printable width by scaling up or down so total == doc.width
    usable_width = doc.width  # points
    total_width = sum(col_widths)

    if total_width == 0:
        raise ValueError("col_widths sum to zero")

    scale = usable_width / total_width
    col_widths = [w * scale for w in col_widths]

    # Build the table that now fills the printable width exactly
    tbl = Table(rows, colWidths=col_widths, repeatRows=1, hAlign="LEFT")
    tbl.setStyle(TableStyle(
        [
            ("FONTNAME", (0, 0), (-1, 0), normal.fontName),
            ("FONTSIZE", (0, 0), (-1, 0), 7),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
            ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
            ("ALIGN", (0, 0), (-1, 0), "CENTER"),
            ("VALIGN", (0, 0), (-1, 0), "MIDDLE"),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
            ("TOPPADDING", (0, 0), (-1, 0), 6),

            ("FONTNAME", (0, 1), (-1, -1), normal.fontName),
            ("FONTSIZE", (0, 1), (-1, -1), 9),
            ("ALIGN", (2, 1), (7, -1), "RIGHT"),
            ("VALIGN", (0, 1), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 2),
            ("RIGHTPADDING", (0, 0), (-1, -1), 2),
            ("TOPPADDING", (0, 1), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 1), (-1, -1), 4),
            
            ("GRID", (0, 0), (-1, -1), 0.3, colors.grey),
            ]
        )
    )
    story.append(tbl)
    story.append(Spacer(1, 12))

    # Total quantity pieces:
    # Total quantity pieces:
    # We want the label "Total Quantity (pcs):" to span across the first two columns (S.No + Description)
    # and align to the RIGHT, so it sits right next to the Qty column.
    qty_row_data = [
        [
            Paragraph(f"<b><font size='{normal.fontSize + 1}'>Total Quantity (pcs):</font></b>", normal),
            "", # Merged with previous
            Paragraph(f"<b><font size='{normal.fontSize + 1}'>{int(total_pieces)}</font></b>", normal),
            "", "", "", "", ""
        ]
    ]
    
    qty_tbl = Table(qty_row_data, colWidths=col_widths)
    qty_tbl.setStyle(
        TableStyle(
            [
                # Merge first two columns for the label
                ("SPAN", (0, 0), (1, 0)),
                ("ALIGN", (0, 0), (1, 0), "RIGHT"),
                
                # The value is in column 2 (Qty column)
                ("ALIGN", (2, 0), (2, 0), "RIGHT"),
                
                # Styling
                ("FONTNAME", (0, 0), (-1, -1), normal.fontName),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 2),
                ("TOPPADDING", (0, 0), (-1, -1), 1),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                
                # Underline across label and value
                ("LINEBELOW", (0, 0), (2, 0), 0.5, colors.black),
            ]
        )
    )
    
    story.append(qty_tbl)
    story.append(Spacer(1, 20))
    
    # Totals / subtotals table
    totals_data = [
        ["Subtotal:", money_str(subtotal)],
        ["Sales Tax Total:", money_str(sales_tax_total)],
        ["Advance Tax Total:", money_str(advance_tax_total)],
        ["Grand Total:", money_str(grand_total)],
    ]
    totals_tbl = Table(totals_data, colWidths=[110 * mm, 50 * mm], hAlign="RIGHT")
    totals_tbl.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (-1, -1), normal.fontName),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("ALIGN", (1, 0), (1, -1), "RIGHT"),
            ]
        )
    )
    story.append(totals_tbl)
    story.append(Spacer(1, 14))

    if invoice.get("notes"):
        story.append(Paragraph(f"<b>Notes:</b><br/>{invoice['notes']}", normal))
        story.append(Spacer(1, 10))

    # Push footer to the bottom of the page
    from reportlab.platypus import TopPadder
    
    # Wrap footer content in a Table to treat it as a single flowable
    footer_table = Table(
        [[HR(530)],
         [Spacer(1, 6)],
         [Paragraph("This is a system generated document and does not require signature or company stamp.", 
                    ParagraphStyle("footer", fontSize=8, alignment=1, fontName=normal.fontName))]],
        colWidths=[190 * mm]
    )
    footer_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "BOTTOM"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
    ]))
    
    story.append(TopPadder(footer_table))

    doc.build(
        story,
        onFirstPage=add_page_number,
        onLaterPages=add_page_number
    )
    return output_path


# -----------------------------------
# Monthly merge helper
# -----------------------------------
def generate_monthly_pdf(invoice_file_paths: List[str], output_path: str):
    """Merge multiple invoice PDFs into a single monthly report."""
    merger = PdfMerger()
    for p in invoice_file_paths:
        merger.append(p)
    merger.write(output_path)
    merger.close()
    return output_path


# -----------------------------------
# Example: quick demo
# -----------------------------------
def demo_generate_sample(output_path=None):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    docs_dir = os.path.join(base_dir, "..", "doc")
    os.makedirs(docs_dir, exist_ok=True)

    if output_path is None:
        output_path = os.path.join(docs_dir, "sample_invoice.pdf")
        
    invoice = {
        "invoice_no": "219",
        "date": "07/11/2025",
        "ref": "IMTIAZ GROUP (SMC-PRIVATE) LIMITED",
        "company": {"name": "Shaguftaz", "address": "Distributor, Communication", "contact": "03202019669, 03032031101", "ntn": "4376561-7", "strn": ""},
        "customer": {"name": "IMTIAZ GROUP (SMC-PRIVATE) LIMITED", "address": "KHI - MEGA - PORT QASIM", "ntn": "B353738", 'strn': "3277876321298"},
        "notes": "",
    }
    items = [
        {"sno": 1, "description": "Maykey Hair color Dark Brown 250ml", "qty": 240, "unit_price": 700, "value": 168000, "sales_tax_percent": 18, "sales_tax_amount": 30240, "advance_tax_amount": 840, "total_amount": 199080},
        {"sno": 2, "description": "Maykey Hair color Black 250ml", "qty": 144, "unit_price": 700, "value": 100800, "sales_tax_percent": 18, "sales_tax_amount": 18144, "advance_tax_amount": 504, "total_amount": 119448},
    ]
    return generate_invoice_pdf(invoice, items, output_path)

from decimal import Decimal

# -------------------------------
# Money formatting
# -------------------------------
def _money(value) -> Decimal:
    """
    Safely convert a number into a Decimal with 2 fixed places.
    """
    try:
        return Decimal(str(value)).quantize(Decimal("0.01"))
    except Exception:
        return Decimal("0.00")


# -------------------------------
# Item Calculation
# -------------------------------
def calculate_item(qty, unit_price, sales_tax_percent=18, advance_tax_percent=0.5):
    """
    Calculate the amounts for a single invoice line item.
    Returns a dict with standardized keys.
    """
    qty = Decimal(str(qty))
    unit_price = _money(unit_price)

    value = (qty * unit_price).quantize(Decimal("0.01"))

    sales_tax_amount = (value * Decimal(str(sales_tax_percent)) / 100).quantize(Decimal("0.01"))
    advance_tax_amount = (value * Decimal(str(advance_tax_percent)) / 100).quantize(Decimal("0.01"))

    total_amount = value + sales_tax_amount + advance_tax_amount

    return {
        "qty": qty,
        "unit_price": unit_price,
        "value": value,
        "sales_tax_amount": sales_tax_amount,
        "advance_tax_amount": advance_tax_amount,
        "total_amount": total_amount,
    }


# -------------------------------
# Invoice Totals
# -------------------------------
def summarize_invoice(items):
    """
    Given a list of dictionaries returned by calculate_item(),
    compute the final totals for the invoice.
    """
    subtotal = Decimal("0")
    sales_tax_total = Decimal("0")
    advance_tax_total = Decimal("0")
    grand_total = Decimal("0")
    total_qty_pieces = Decimal("0")

    for it in items:
        subtotal += _money(it["value"])
        sales_tax_total += _money(it["sales_tax_amount"])
        advance_tax_total += _money(it["advance_tax_amount"])
        grand_total += _money(it["total_amount"])
        total_qty_pieces += Decimal(str(it["qty"]))

    return {
        "subtotal": subtotal.quantize(Decimal("0.01")),
        "sales_tax_total": sales_tax_total.quantize(Decimal("0.01")),
        "advance_tax_total": advance_tax_total.quantize(Decimal("0.01")),
        "grand_total": grand_total.quantize(Decimal("0.01")),
        "total_qty_pieces": int(total_qty_pieces),
    }


# -------------------------------
# Invoice Number Generation
# -------------------------------
def generate_next_invoice_number(last_number: str):
    """
    Given last invoice number as string, produce next increment.
    Example:
        "INV-0059" → "INV-0060"
        "2025-14"  → "2025-15"
        "214"      → "215"
    """
    if not last_number:
        return "1"

    # Extract trailing digits
    num_str = ""
    prefix = ""

    for char in last_number:
        if char.isdigit():
            num_str += char
        else:
            prefix += char

    if num_str == "":
        # No digits found; just append 1
        return last_number + "1"

    next_num = str(int(num_str) + 1).zfill(len(num_str))
    return prefix + next_num

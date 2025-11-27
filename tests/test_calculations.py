import unittest
from decimal import Decimal
from src.calculations import (
    calculate_item,
    summarize_invoice,
    generate_next_invoice_number,
    _money,
)

class TestCalculations(unittest.TestCase):

    def test_money(self):
        self.assertEqual(_money("12.345"), Decimal("12.35"))
        self.assertEqual(_money(100), Decimal("100.00"))

    def test_calculate_item(self):
        item = calculate_item(qty=10, unit_price=100)
        self.assertEqual(item["value"], Decimal("1000.00"))
        self.assertEqual(item["sales_tax_amount"], Decimal("180.00"))
        self.assertEqual(item["advance_tax_amount"], Decimal("5.00"))
        self.assertEqual(item["total_amount"], Decimal("1185.00"))

    def test_summarize_invoice(self):
        items = [
            calculate_item(10, 100),
            calculate_item(5, 200),
        ]
        summary = summarize_invoice(items)

        self.assertEqual(summary["subtotal"], Decimal("2000.00"))
        self.assertEqual(summary["sales_tax_total"], Decimal("360.00"))
        self.assertEqual(summary["advance_tax_total"], Decimal("10.00"))
        self.assertEqual(summary["grand_total"], Decimal("2370.00"))
        self.assertEqual(summary["total_qty_pieces"], 15)

    def test_invoice_number(self):
        self.assertEqual(generate_next_invoice_number("214"), "215")
        self.assertEqual(generate_next_invoice_number("INV-0059"), "INV-0060")
        self.assertEqual(generate_next_invoice_number("2025-14"), "2025-15")
        self.assertEqual(generate_next_invoice_number("INV"), "INV1")

if __name__ == "__main__":
    unittest.main()

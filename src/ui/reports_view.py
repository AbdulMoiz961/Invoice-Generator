from datetime import date
from calendar import month_name
import os
import subprocess
import sys

from PySide6.QtCore import Qt, QDate
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QMessageBox,
    QFileDialog,
    QComboBox,
    QSpinBox,
    QCheckBox,
    QFrame,
    QDateEdit,
    QGroupBox,
    QFormLayout,
    QHeaderView,
)

from src.db import Database
from src.reports import generate_monthly_report
from src.reports_analytics import (
    export_summary_to_csv,
    export_summary_to_excel,
    fetch_summary,
    fetch_top_products,
    fetch_top_customers,
)


def open_pdf(path: str):
    """Cross-platform open-PDF helper."""
    if not path or not os.path.isfile(path):
        return

    if sys.platform.startswith("win"):
        os.startfile(path)
    elif sys.platform == "darwin":
        subprocess.call(["open", path])
    else:
        subprocess.call(["xdg-open", path])


class ReportsView(QWidget):
    """
    Invoice List / Search + Open PDF Screen
    Step 9 Deliverable:
        • Search invoices
        • Display invoices in table
        • Double click → open PDF
    """

    def __init__(self):
        super().__init__()

        self.db = Database()
        self.default_output_dir = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "..", "invoices")
        )
        os.makedirs(self.default_output_dir, exist_ok=True)
        self.summary_data = None
        self.summary_rows = []

        # ---------- Layout root ----------
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)

        # ---------- Title ----------
        title = QLabel("Invoice Reports")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 20px; font-weight: bold;")
        layout.addWidget(title)

        # ---------- Monthly batch generator ----------
        layout.addWidget(self._build_monthly_batch_section())

        # ---------- Analytics / exports ----------
        layout.addWidget(self._build_analytics_section())
        
        # ---------- Insights ----------
        layout.addWidget(self._build_insights_section())

        # ---------- Search bar ----------
        search_row = QHBoxLayout()

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search by invoice number or customer name...")
        self.search_input.textChanged.connect(self.load_invoices)

        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.load_invoices)

        search_row.addWidget(self.search_input)
        search_row.addWidget(refresh_btn)
        layout.addLayout(search_row)

        # ---------- Invoice table ----------
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "Invoice No", "Customer", "Date", "Total Amount", "PDF Path", "Actions"
        ])
        self.table.setColumnWidth(0, 120)  # Invoice
        self.table.setColumnWidth(1, 200)  # Customer
        self.table.setColumnWidth(2, 120)  # Date
        self.table.setColumnWidth(3, 150)  # Total
        self.table.setColumnWidth(4, 300)  # PDF Path
        self.table.setColumnWidth(5, 120)  # Actions

        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)

        # Double-click event: open PDF
        self.table.itemDoubleClicked.connect(self.on_row_double_clicked)

        layout.addWidget(self.table)

        self.setLayout(layout)

        # Load initial data
        self.load_invoices()

    # ----------------------------------------------------------
    # Monthly batch helpers
    # ----------------------------------------------------------
    def _build_monthly_batch_section(self):
        frame = QFrame()
        frame.setObjectName("MonthlyBatch")
        frame.setStyleSheet(
            """
            QFrame#MonthlyBatch {
                border: 1px solid #dcdcdc;
                border-radius: 8px;
                background-color: #fafafa;
            }
            """
        )
        wrapper = QVBoxLayout(frame)
        wrapper.setContentsMargins(12, 10, 12, 10)
        wrapper.setSpacing(8)

        header = QLabel("Monthly Invoice Batch")
        header.setStyleSheet("font-size: 14px; font-weight: 600;")
        wrapper.addWidget(header)

        selectors = QHBoxLayout()
        selectors.setSpacing(10)
        selectors.addWidget(QLabel("Month:"))

        self.month_combo = QComboBox()
        for idx in range(1, 13):
            self.month_combo.addItem(month_name[idx], idx)
        self.month_combo.setCurrentIndex(date.today().month - 1)
        selectors.addWidget(self.month_combo)

        selectors.addWidget(QLabel("Year:"))
        self.year_spin = QSpinBox()
        self.year_spin.setRange(2000, 2100)
        self.year_spin.setValue(date.today().year)
        self.year_spin.setFixedWidth(90)
        selectors.addWidget(self.year_spin)
        selectors.addStretch()
        wrapper.addLayout(selectors)

        path_row = QHBoxLayout()
        path_row.setSpacing(10)
        path_row.addWidget(QLabel("Save to:"))
        self.output_dir_input = QLineEdit()
        self.output_dir_input.setPlaceholderText("e.g. E:/Invoices/Exports")
        self.output_dir_input.setText(self.default_output_dir)
        path_row.addWidget(self.output_dir_input)
        browse_btn = QPushButton("Browse…")
        browse_btn.clicked.connect(self.choose_output_dir)
        path_row.addWidget(browse_btn)
        wrapper.addLayout(path_row)

        options_row = QHBoxLayout()
        self.summary_checkbox = QCheckBox("Include summary cover page")
        self.summary_checkbox.setChecked(True)
        options_row.addWidget(self.summary_checkbox)
        options_row.addStretch()
        wrapper.addLayout(options_row)

        action_row = QHBoxLayout()
        action_row.addStretch()
        generate_btn = QPushButton("Generate Monthly PDF")
        generate_btn.clicked.connect(self.handle_generate_monthly_pdf)
        action_row.addWidget(generate_btn)
        wrapper.addLayout(action_row)

        return frame

    def _build_analytics_section(self):
        group = QGroupBox("Sales Summary & Exports")
        group_layout = QVBoxLayout(group)
        group_layout.setSpacing(10)

        dates_row = QHBoxLayout()
        dates_row.setSpacing(10)

        today = date.today()
        start_qdate = QDate(today.year, today.month, 1)

        dates_row.addWidget(QLabel("Start date:"))
        self.summary_start = QDateEdit()
        self.summary_start.setCalendarPopup(True)
        self.summary_start.setDate(start_qdate)
        dates_row.addWidget(self.summary_start)

        dates_row.addWidget(QLabel("End date:"))
        self.summary_end = QDateEdit()
        self.summary_end.setCalendarPopup(True)
        self.summary_end.setDate(QDate.currentDate())
        dates_row.addWidget(self.summary_end)
        dates_row.addStretch()

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        refresh_btn = QPushButton("Compute Summary")
        refresh_btn.clicked.connect(self.handle_generate_summary)
        btn_row.addWidget(refresh_btn)

        self.summary_csv_btn = QPushButton("Export CSV")
        self.summary_csv_btn.setEnabled(False)
        self.summary_csv_btn.clicked.connect(self.handle_export_csv)
        btn_row.addWidget(self.summary_csv_btn)

        self.summary_excel_btn = QPushButton("Export Excel")
        self.summary_excel_btn.setEnabled(False)
        self.summary_excel_btn.clicked.connect(self.handle_export_excel)
        btn_row.addWidget(self.summary_excel_btn)

        metrics_form = QFormLayout()
        metrics_form.setLabelAlignment(Qt.AlignRight)
        metrics_form.setHorizontalSpacing(16)
        metrics_form.setVerticalSpacing(6)

        self.summary_labels = {}
        metric_labels = [
            ("total_sales", "Total Sales"),
            ("total_sales_tax", "Sales Tax"),
            ("total_advance_tax", "Advance Tax"),
            ("total_quantity", "Total Quantity (pcs)"),
            ("invoice_count", "Invoices Count"),
        ]
        for key, title in metric_labels:
            lbl = QLabel("—")
            lbl.setStyleSheet("font-weight: 600;")
            self.summary_labels[key] = lbl
            metrics_form.addRow(title + ":", lbl)

        group_layout.addLayout(dates_row)
        group_layout.addLayout(btn_row)
        group_layout.addLayout(metrics_form)
        return group

    def _build_insights_section(self):
        group = QGroupBox("Performance Insights")
        layout = QHBoxLayout(group)
        layout.setSpacing(20)

        # Top Products Table
        prod_layout = QVBoxLayout()
        prod_layout.addWidget(QLabel("Top 5 Products (Revenue)"))
        self.top_products_table = QTableWidget(0, 3)
        self.top_products_table.setHorizontalHeaderLabels(["Product", "Qty", "Revenue"])
        self.top_products_table.verticalHeader().setVisible(False)
        self.top_products_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.top_products_table.setSelectionMode(QTableWidget.NoSelection)
        self.top_products_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.top_products_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.top_products_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.top_products_table.setFixedHeight(150)
        prod_layout.addWidget(self.top_products_table)
        
        # Top Customers Table
        cust_layout = QVBoxLayout()
        cust_layout.addWidget(QLabel("Top 5 Customers (Spend)"))
        self.top_customers_table = QTableWidget(0, 3)
        self.top_customers_table.setHorizontalHeaderLabels(["Customer", "Invoices", "Total Spent"])
        self.top_customers_table.verticalHeader().setVisible(False)
        self.top_customers_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.top_customers_table.setSelectionMode(QTableWidget.NoSelection)
        self.top_customers_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.top_customers_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.top_customers_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.top_customers_table.setFixedHeight(150)
        cust_layout.addWidget(self.top_customers_table)

        layout.addLayout(prod_layout)
        layout.addLayout(cust_layout)
        
        return group

    def choose_output_dir(self):
        base = self.output_dir_input.text().strip() or self.default_output_dir
        path = QFileDialog.getExistingDirectory(self, "Select output folder", base)
        if path:
            self.output_dir_input.setText(path)

    def handle_generate_monthly_pdf(self):
        month = self.month_combo.currentData()
        year = self.year_spin.value()
        include_summary = self.summary_checkbox.isChecked()
        output_dir = self.output_dir_input.text().strip() or None

        try:
            pdf_path = generate_monthly_report(
                year, month, output_dir=output_dir, include_summary=include_summary
            )
        except ValueError as exc:
            QMessageBox.information(self, "No Invoices", str(exc))
            return
        except Exception as exc:
            QMessageBox.critical(
                self,
                "Generation Failed",
                f"Could not generate monthly PDF:\n{exc}",
            )
            return

        msg = QMessageBox(self)
        msg.setWindowTitle("Monthly PDF Ready")
        msg.setIcon(QMessageBox.Information)
        msg.setText(f"Monthly PDF saved to:\n{pdf_path}")
        open_btn = msg.addButton("Open PDF", QMessageBox.AcceptRole)
        msg.addButton(QMessageBox.Ok)
        msg.exec()
        if msg.clickedButton() == open_btn:
            open_pdf(pdf_path)

    # ----------------------------------------------------------
    # Analytics summary helpers
    # ----------------------------------------------------------
    def handle_generate_summary(self):
        start_date = self.summary_start.date().toString("yyyy-MM-dd")
        end_date = self.summary_end.date().toString("yyyy-MM-dd")

        if start_date > end_date:
            QMessageBox.warning(self, "Invalid Range", "Start date must be before end date.")
            return

        try:
            summary, rows = fetch_summary(start_date, end_date)
            top_products = fetch_top_products(start_date, end_date)
            top_customers = fetch_top_customers(start_date, end_date)
        except Exception as exc:
            QMessageBox.critical(
                self,
                "Summary Failed",
                f"Unable to compute summary:\n{exc}",
            )
            return

        self.summary_data = summary
        self.summary_rows = rows
        self._update_summary_labels(summary)
        self._update_insights_tables(top_products, top_customers)
        
        has_data = bool(rows)
        self.summary_csv_btn.setEnabled(has_data)
        self.summary_excel_btn.setEnabled(has_data)

        if not has_data:
            QMessageBox.information(self, "No Invoices", "No invoices found for the selected range.")

    def _update_summary_labels(self, summary: dict):
        if not summary:
            for label in self.summary_labels.values():
                label.setText("—")
            return

        def fmt_currency(value):
            return f"{value:,.2f}"

        def fmt_qty(value):
            return f"{value:,.0f}"

        mapping = {
            "total_sales": fmt_currency(summary.get("total_sales", 0)),
            "total_sales_tax": fmt_currency(summary.get("total_sales_tax", 0)),
            "total_advance_tax": fmt_currency(summary.get("total_advance_tax", 0)),
            "total_quantity": fmt_qty(summary.get("total_quantity", 0)),
            "invoice_count": str(summary.get("invoice_count", 0)),
        }

        for key, label in self.summary_labels.items():
            label.setText(mapping.get(key, "—"))

    def _update_insights_tables(self, products, customers):
        # Products
        self.top_products_table.setRowCount(len(products))
        for row, p in enumerate(products):
            self.top_products_table.setItem(row, 0, QTableWidgetItem(p["product_name"]))
            self.top_products_table.setItem(row, 1, QTableWidgetItem(f"{p['total_qty']:.0f}"))
            self.top_products_table.setItem(row, 2, QTableWidgetItem(f"{p['total_revenue']:,.2f}"))
            
        # Customers
        self.top_customers_table.setRowCount(len(customers))
        for row, c in enumerate(customers):
            self.top_customers_table.setItem(row, 0, QTableWidgetItem(c["customer_name"]))
            self.top_customers_table.setItem(row, 1, QTableWidgetItem(str(c["invoice_count"])))
            self.top_customers_table.setItem(row, 2, QTableWidgetItem(f"{c['total_spent']:,.2f}"))

    def handle_export_csv(self):
        if not self.summary_data:
            QMessageBox.information(self, "Summary Required", "Compute a summary before exporting.")
            return

        path, _ = QFileDialog.getSaveFileName(
            self,
            "Save CSV Summary",
            os.path.join(self.default_output_dir, "invoice_summary.csv"),
            "CSV files (*.csv)",
        )
        if not path:
            return

        try:
            export_summary_to_csv(self.summary_data, self.summary_rows, path)
        except Exception as exc:
            QMessageBox.critical(self, "Export Failed", f"Could not export CSV:\n{exc}")
            return

        QMessageBox.information(self, "Export Complete", f"CSV saved to:\n{path}")

    def handle_export_excel(self):
        if not self.summary_data:
            QMessageBox.information(self, "Summary Required", "Compute a summary before exporting.")
            return

        path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Excel Summary",
            os.path.join(self.default_output_dir, "invoice_summary.xlsx"),
            "Excel files (*.xlsx)",
        )
        if not path:
            return

        try:
            export_summary_to_excel(self.summary_data, self.summary_rows, path)
        except Exception as exc:
            QMessageBox.critical(self, "Export Failed", f"Could not export Excel:\n{exc}")
            return

        QMessageBox.information(self, "Export Complete", f"Excel saved to:\n{path}")

    # ----------------------------------------------------------
    # Load all invoices or filtered by search
    # ----------------------------------------------------------
    def load_invoices(self):
        query = self.search_input.text().strip()

        if query:
            invoices = self.db.search_invoices(query)
        else:
            invoices = self.db.get_invoices()

        self.table.setRowCount(len(invoices))

        for row, inv in enumerate(invoices):
            self.table.setItem(row, 0, QTableWidgetItem(inv["invoice_no"]))
            self.table.setItem(row, 1, QTableWidgetItem(inv.get("customer_name", "")))
            self.table.setItem(row, 2, QTableWidgetItem(inv["date"]))
            self.table.setItem(row, 3, QTableWidgetItem(str(inv["total_amount"])))
            self.table.setItem(row, 4, QTableWidgetItem(inv.get("pdf_path", "")))

            delete_btn = QPushButton("Delete")
            delete_btn.setStyleSheet("color: white; background-color: #c0392b;")
            delete_btn.clicked.connect(
                lambda _, invoice_id=inv["id"]: self.delete_invoice(invoice_id)
            )
            self.table.setCellWidget(row, 5, delete_btn)

    # ----------------------------------------------------------
    # Open invoice PDF on double click
    # ----------------------------------------------------------
    def on_row_double_clicked(self, item):
        row = item.row()
        pdf_path = self.table.item(row, 4).text()

        if not pdf_path:
            return

        open_pdf(pdf_path)

    # ----------------------------------------------------------
    # Delete invoice helper
    # ----------------------------------------------------------
    def delete_invoice(self, invoice_id: int):
        confirm = QMessageBox.question(
            self,
            "Delete Invoice",
            "Are you sure you want to delete this invoice? This action cannot be undone.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if confirm != QMessageBox.Yes:
            return

        try:
            self.db.delete_invoice(invoice_id)
            QMessageBox.information(self, "Deleted", "Invoice deleted successfully.")
            self.load_invoices()
        except Exception as exc:
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to delete invoice:\n{exc}",
            )

from PySide6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout, QPushButton,
    QComboBox, QLineEdit, QTableWidget, QTableWidgetItem,
    QMessageBox, QHeaderView, QSpinBox, QFrame
)
from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QFileDialog
import os


from src.db import Database
from src.calculations import calculate_item, summarize_invoice


class InvoiceForm(QWidget):
    def __init__(self):
        super().__init__()

        self.db = Database()
        self.items = []  # internal storage

        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)

        self.setStyleSheet(
            """
            QWidget {
                font-size: 12px;
                background-color: #f7f7fb;
            }
            QWidget#Card {
                background-color: #ffffff;
                border: 1px solid #e0e0e0;
                border-radius: 10px;
            }
            QLabel[class="section-title"] {
                font-size: 15px;
                font-weight: 700;
                letter-spacing: 1px;
                color: #2f2f2f;
                margin: 18px 0 6px;
                text-transform: uppercase;
                padding-left: 8px;
                border-left: 4px solid #4a63e7;
            }
            QPushButton[class="primary"] {
                background-color: #4a63e7;
                color: #ffffff;
                padding: 6px 14px;
                border-radius: 6px;
            }
            QPushButton[class="primary"]:hover {
                background-color: #3a53d6;
            }
            QPushButton[class="danger"] {
                background-color: #ffe6e6;
                color: #c62828;
                border: 1px solid #ffb3b3;
                padding: 6px 14px;
                border-radius: 6px;
            }
            QPushButton[class="danger"]:hover {
                background-color: #ffd6d6;
            }
            QPushButton[class="ghost"] {
                background-color: transparent;
                color: #c62828;
                border: none;
                font-weight: bold;
            }
            QLabel#CustomerDetails {
                color: #2f2f2f;
                font-size: 12px;
                background-color: #eff2ff;
                border: 1px dashed #b9c4ff;
                border-radius: 8px;
                padding: 6px 10px;
            }
            QTableWidget#InvoiceItemsTable {
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                background-color: #ffffff;
                gridline-color: #f0f0f0;
            }
            QTableWidget#InvoiceItemsTable::item {
                padding: 6px;
            }
            QTableWidget#InvoiceItemsTable::item:selected {
                background-color: #e8edff;
            }
            QHeaderView::section {
                background-color: #f3f4f8;
                border: none;
                padding: 6px;
                font-weight: 600;
            }
            """
        )

        layout.addWidget(self._section_label("Invoice Details"))
        
        # ------------------------------
        # Invoice Number + Date Picker Row
        # ------------------------------
        invoice_card = self._make_card()
        invoice_row = QHBoxLayout()

        invoice_row.addWidget(QLabel("Invoice No:"))

        self.invoice_no_input = QLineEdit()
        self.invoice_no_input.setFixedWidth(120)
        self.invoice_no_input.setPlaceholderText("Auto-generated")
        # self.invoice_no_input.setReadOnly(True)  # auto-filled from DB
        self.invoice_no_input.setText(self.get_next_invoice_no())
        invoice_row.addWidget(self.invoice_no_input)

        invoice_row.addSpacing(30)

        invoice_row.addWidget(QLabel("Date:"))

        from PySide6.QtWidgets import QDateEdit
        from PySide6.QtCore import QDate

        self.date_picker = QDateEdit()
        self.date_picker.setDate(QDate.currentDate())
        self.date_picker.setCalendarPopup(True)
        self.date_picker.setFixedWidth(130)
        invoice_row.addWidget(self.date_picker)

        invoice_row.addStretch()

        invoice_card.layout().addLayout(invoice_row)
        layout.addWidget(invoice_card)


        # ------------------------------
        # Customer Selection
        # ------------------------------
        layout.addWidget(self._section_label("Customer"))
        customer_card = self._make_card()
        top_row = QHBoxLayout()

        self.customer_cb = QComboBox()
        self.load_customers()
        self.customer_cb.currentIndexChanged.connect(lambda _: self.update_customer_details())
        line_edit_customer = self.customer_cb.lineEdit()
        if line_edit_customer:
            line_edit_customer.setPlaceholderText("Search or select a customer")

        top_row.addWidget(QLabel("Customer:"))
        top_row.addWidget(self.customer_cb)
        
        # Shipped To / City Input
        top_row.addSpacing(20)
        top_row.addWidget(QLabel("Shipped To / City:"))
        self.shipped_to_input = QLineEdit()
        self.shipped_to_input.setPlaceholderText("Enter city or location")
        top_row.addWidget(self.shipped_to_input)
        
        customer_card.layout().addLayout(top_row)
        
        # Customer detail labels
        self.customer_details = QLabel("")
        self.customer_details.setObjectName("CustomerDetails")
        customer_card.layout().addWidget(self.customer_details)
        layout.addWidget(customer_card)
        self.update_customer_details()

        # ------------------------------
        # Product selection row
        # ------------------------------
        layout.addWidget(self._section_label("Add Items"))
        product_card = self._make_card()
        form_row = QHBoxLayout()

        self.product_cb = QComboBox()
        self.load_products()
        product_line_edit = self.product_cb.lineEdit()
        if product_line_edit:
            product_line_edit.setPlaceholderText("Search or select a product")

        self.qty_input = QSpinBox()
        self.qty_input.setMinimum(1)
        self.qty_input.setMaximum(100000)
        self.qty_input.setSuffix(" pcs")
        self.qty_input.setFixedWidth(110)

        add_btn = QPushButton("Add Item")
        add_btn.setProperty("class", "primary")
        add_btn.clicked.connect(self.add_item)

        form_row.addWidget(QLabel("Product:"))
        form_row.addWidget(self.product_cb)
        form_row.addWidget(QLabel("Qty:"))
        form_row.addWidget(self.qty_input)
        form_row.addWidget(add_btn)

        product_card.layout().addLayout(form_row)
        layout.addWidget(product_card)

        # ------------------------------
        # Table for Line Items
        # ------------------------------
        self.table = QTableWidget(0, 8)
        self.table.setObjectName("InvoiceItemsTable")
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.ExtendedSelection)
        self.table.setHorizontalHeaderLabels([
            "Description", "Qty", "Unit Price",
            "Value", "Sales Tax", "Adv Tax", "Total", "Remove"
        ])
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        # Other columns auto-size to content but still draggable
        for i in range(1, 8):
            header.setSectionResizeMode(i, QHeaderView.Interactive)

        self._style_table()
        layout.addWidget(self.table)

        # ------------------------------
        # Slim totals panel on right
        # ------------------------------
        totals_container = QWidget()
        totals_container.setFixedWidth(250)

        totals_layout = QVBoxLayout(totals_container)
        totals_layout.setAlignment(Qt.AlignTop)
        totals_layout.setSpacing(6)

        def make_total_label(text):
            lbl = QLabel(f"<b>{text}</b>")
            lbl.setAlignment(Qt.AlignRight)
            lbl.setStyleSheet("font-size: 12px;")
            return lbl

        self.lbl_subtotal = make_total_label("Subtotal: 0")
        self.lbl_tax = make_total_label("Sales Tax: 0")
        self.lbl_adv = make_total_label("Advance Tax: 0")
        self.lbl_grand = make_total_label("Grand Total: 0")
        self.lbl_qty = make_total_label("Total Qty (pcs): 0")

        for lbl in [
            self.lbl_subtotal,
            self.lbl_tax,
            self.lbl_adv,
            self.lbl_grand,
            self.lbl_qty
        ]:
            totals_layout.addWidget(lbl)

        # -----------------------------------
        # Layout: table left, totals right
        # -----------------------------------
        center_row = QHBoxLayout()
        center_row.addWidget(self.table, stretch=4)
        center_row.addWidget(totals_container, stretch=1)

        layout.addLayout(center_row)


        # ------------------------------
        # Bottom Buttons
        # ------------------------------
        bottom_row = QHBoxLayout()
        
        self.remove_selected_btn = QPushButton("Remove Selected")
        self.remove_selected_btn.setProperty("class", "danger")
        self.remove_selected_btn.clicked.connect(self.remove_selected_rows)
        
        save_btn = QPushButton("Save Invoice")
        save_btn.setProperty("class", "primary")
        save_btn.clicked.connect(self.save_invoice)
        
        bottom_row.addWidget(self.remove_selected_btn)
        bottom_row.addStretch()
        bottom_row.addWidget(save_btn)
        
        layout.addLayout(bottom_row)
        

    def _make_card(self):
        card = QFrame()
        card.setObjectName("Card")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(16, 12, 16, 12)
        card_layout.setSpacing(10)
        return card

    def _section_label(self, text):
        lbl = QLabel(text)
        lbl.setProperty("class", "section-title")
        return lbl

    def _style_table(self):
        self.table.setAlternatingRowColors(True)
        self.table.setWordWrap(False)
        self.table.verticalHeader().setVisible(False)
        self.table.setFocusPolicy(Qt.NoFocus)
        self.table.setMinimumHeight(260)

    # =====================================================
    # Loaders
    # =====================================================

    def load_products(self):
        self.product_cb.clear()
        products = self.db.get_products()

        for p in products:
            text = f"{p['name']} ({p['unit_price']})"
            self.product_cb.addItem(text, p["id"])

        # Make it editable AFTER filling items
        self.product_cb.setEditable(True)
        self.product_cb.setInsertPolicy(QComboBox.NoInsert)

        completer = self.product_cb.completer()
        if completer:
            completer.setFilterMode(Qt.MatchContains)
            completer.setCaseSensitivity(Qt.CaseInsensitive)


    def load_customers(self):
        self.customer_cb.clear()
        customers = self.db.get_customers()

        for c in customers:
            self.customer_cb.addItem(c["name"], c["id"])

        self.customer_cb.setEditable(True)
        self.customer_cb.setInsertPolicy(QComboBox.NoInsert)

        completer = self.customer_cb.completer()
        if completer:
            completer.setFilterMode(Qt.MatchContains)
            completer.setCaseSensitivity(Qt.CaseInsensitive)

            
    # =====================================================
    # Fetch & show customer info
    # =====================================================
    
    def update_customer_details(self):
        customer_id = self.customer_cb.currentData()
        if not customer_id:
            self.customer_details.setText("")
            return

        customer = self.db.fetch_one("SELECT * FROM customers WHERE id=?", (customer_id,))
        if not customer:
            self.customer_details.setText("")
            return

        ntn = customer.get("ntn") or "N/A"
        strn = customer.get("strn") or "N/A"
        text = (
            f"<b>NTN:</b> {ntn}&nbsp;&nbsp;&nbsp;&nbsp;"
            f"<b>STRN:</b> {strn}"
        )
        self.customer_details.setText(text)

    
    # =====================================================
    # Invoice No. Fetch
    # =====================================================        
    
    def get_next_invoice_no(self):
        last = self.db.fetch_one("SELECT invoice_no FROM invoices ORDER BY id DESC LIMIT 1;")
        if last and last["invoice_no"].isdigit():
            return str(int(last["invoice_no"]) + 1)
        return "1"
    
    
    # =====================================================
    # invoice_no validation
    # ===================================================== 

    def invoice_no_exists(self, invoice_no):
        row = self.db.fetch_one(
            "SELECT id FROM invoices WHERE invoice_no = ? LIMIT 1",
            (invoice_no,)
        )
        return row is not None

    
    # =====================================================
    # Add & Remove Items
    # =====================================================

    def add_item(self):
        product_id = self.product_cb.currentData()
        qty = self.qty_input.value()

        product = self.db.fetch_one("SELECT * FROM products WHERE id=?", (product_id,))
        if not product:
            QMessageBox.warning(self, "Error", "Invalid product.")
            return

        unit_price = float(product["unit_price"])
        customer_id = self.customer_cb.currentData()
        custom_price = self.db.get_customer_price_for_product(customer_id, product_id) if customer_id else None
        if custom_price is not None:
            unit_price = float(custom_price)

        calc = calculate_item(
            qty=qty,
            unit_price=unit_price,
            sales_tax_percent=product["tax_rate"],
            advance_tax_percent=0.5,
        )

        row = self.table.rowCount()
        self.table.insertRow(row)

        # Table cells
        self.table.setItem(row, 0, QTableWidgetItem(product["name"]))
        self.table.setItem(row, 1, QTableWidgetItem(str(calc["qty"])))
        self.table.setItem(row, 2, QTableWidgetItem(str(calc["unit_price"])))
        self.table.setItem(row, 3, QTableWidgetItem(str(calc["value"])))
        self.table.setItem(row, 4, QTableWidgetItem(str(calc["sales_tax_amount"])))
        self.table.setItem(row, 5, QTableWidgetItem(str(calc["advance_tax_amount"])))
        self.table.setItem(row, 6, QTableWidgetItem(str(calc["total_amount"])))

        # Remove button
        remove_btn = QPushButton("X")
        remove_btn.setProperty("class", "ghost")
        remove_btn.setToolTip("Remove this line")
        remove_btn.clicked.connect(lambda _, r=row: self.remove_item(r))

        self.table.setCellWidget(row, 7, remove_btn)

        # Store internally
        # We will assign 'sno' dynamically when saving or generating PDF, 
        # but let's keep it consistent if we need it.
        self.items.append({
            "product_id": product_id,
            "description": product["name"],
            "qty": calc["qty"],
            "unit_price": float(calc["unit_price"]),
            "value": float(calc["value"]),
            "sales_tax_amount": float(calc["sales_tax_amount"]),
            "advance_tax_amount": float(calc["advance_tax_amount"]),
            "total_amount": float(calc["total_amount"]),
        })

        self.update_totals()

    def remove_item(self, row):
        if row < 0 or row >= len(self.items):
            return

        self.items.pop(row)
        self.table.removeRow(row)

        # Rebind remove buttons for new row numbers
        for r in range(self.table.rowCount()):
            btn = self.table.cellWidget(r, 7)
            btn.clicked.disconnect()
            btn.clicked.connect(lambda _, rr=r: self.remove_item(rr))

        self.update_totals()
        
    # MULTI-ROW REMOVE
    def remove_selected_rows(self):
        selected = self.table.selectionModel().selectedRows()

        if not selected:
            QMessageBox.information(self, "No Selection", "Please select one or more rows to remove.")
            return

        # Remove from bottom → top so indices don't shift
        rows = sorted([idx.row() for idx in selected], reverse=True)

        for row in rows:
            if 0 <= row < len(self.items):
                self.items.pop(row)
                self.table.removeRow(row)

        # Re-bind row delete buttons (since row indices shifted)
        for r in range(self.table.rowCount()):
            btn = self.table.cellWidget(r, 7)
            if btn:
                btn.clicked.disconnect()
                btn.clicked.connect(lambda _, rr=r: self.remove_item(rr))

        self.update_totals()

    # =====================================================
    # Totals
    # =====================================================

    def update_totals(self):
        if not self.items:
            self.lbl_subtotal.setText("<b>Subtotal: 0</b>")
            self.lbl_tax.setText("<b>Sales Tax: 0</b>")
            self.lbl_adv.setText("<b>Advance Tax: 0</b>")
            self.lbl_grand.setText("<b>Grand Total: 0</b>")
            self.lbl_qty.setText("<b>Total Quantity (pcs): 0</b>")
            return

        summary = summarize_invoice(self.items)

        self.lbl_subtotal.setText(f"<b>Subtotal: {summary['subtotal']}</b>")
        self.lbl_tax.setText(f"<b>Sales Tax: {summary['sales_tax_total']}</b>")
        self.lbl_adv.setText(f"<b>Advance Tax: {summary['advance_tax_total']}</b>")
        self.lbl_grand.setText(f"<b>Grand Total: {summary['grand_total']}</b>")
        self.lbl_qty.setText(f"<b>Total Quantity (pcs): {summary['total_qty_pieces']}</b>")

    # =====================================================
    # Save Invoice
    # =====================================================

    def save_invoice(self):
        if not self.items:
            QMessageBox.warning(self, "Error", "No items added.")
            return

        customer_id = self.customer_cb.currentData()
        if customer_id is None:
            QMessageBox.warning(self, "Error", "Please select a customer.")
            return

        summary = summarize_invoice(self.items)

        company = self.db.get_company()
        if not company:
            QMessageBox.warning(
                self,
                "Company Missing",
                "Please set up your company profile before saving invoices."
            )
            return

        # Use manually entered invoice number, or auto-generate if empty
        manual_no = self.invoice_no_input.text().strip()
        if manual_no:
            invoice_no = manual_no
        else:
            # Generate next invoice number
            last = self.db.fetch_one("SELECT invoice_no FROM invoices ORDER BY id DESC LIMIT 1;")
            last_no = last["invoice_no"] if last else None
            invoice_no = str(int(last_no) + 1) if last_no else "1"

        # Validate duplicate invoice number
        if self.invoice_no_exists(invoice_no):
            QMessageBox.warning(
                self,
                "Duplicate Invoice No",
                f"Invoice number '{invoice_no}' already exists.\nPlease choose another."
            )
            return

        # Add S.No to items (1-based index)
        for idx, item in enumerate(self.items, start=1):
            item["sno"] = idx

        invoice_data = {
            "invoice_no": invoice_no,
            "customer_id": customer_id,
            "company_id": company["id"],
            "date": self.date_picker.date().toString("yyyy-MM-dd"),
            "subtotal": float(summary["subtotal"]),
            "sales_tax": float(summary["sales_tax_total"]),
            "advance_tax": float(summary["advance_tax_total"]),
            "total_amount": float(summary["grand_total"]),
            "notes": "",
            "pdf_path": "",  # will update after generating PDF
            "shipped_to": self.shipped_to_input.text().strip(),
        }

        # 1️⃣ Save invoice and items
        invoice_id = self.db.add_invoice(invoice_data)
        self.db.add_invoice_items(invoice_id, self.items)
        
        # Keep a default folder with optional filename
        default_folder = "invoices"
        os.makedirs(default_folder, exist_ok=True)
        pdf_path = os.path.join(default_folder, f"invoice_{invoice_no}.pdf")

        # 2️⃣ Generate PDF
        # Prepare data for PDF (enrich with full objects & formatted date)
        customer = self.db.get_customer(customer_id)
        
        pdf_invoice_data = invoice_data.copy()
        pdf_invoice_data["company"] = dict(company) if company else {}
        pdf_invoice_data["customer"] = dict(customer) if customer else {}
        pdf_invoice_data["date"] = self.date_picker.date().toString("dd-MM-yyyy")

        from ..pdfgen import generate_invoice_pdf  # import your PDF function
        generate_invoice_pdf(
            invoice=pdf_invoice_data,
            items=self.items,
            output_path=pdf_path
        )

        # 3️⃣ Update DB with PDF path
        self.db.update_invoice_pdf_path(invoice_id, pdf_path)

        # 4️⃣ Popup to confirm
        msg = QMessageBox(self)
        msg.setWindowTitle("Invoice Saved")
        msg.setIcon(QMessageBox.Information)
        msg.setText(f"<b>Invoice #{invoice_no} saved successfully.</b>")
        msg.setInformativeText(
            f"Grand Total: {summary['grand_total']}\n"
            f"PDF Path:\n{os.path.abspath(pdf_path)}"
        )
        msg.setDetailedText(
            "Totals\n"
            f"Subtotal: {summary['subtotal']}\n"
            f"Sales Tax: {summary['sales_tax_total']}\n"
            f"Advance Tax: {summary['advance_tax_total']}\n"
            f"Items: {len(self.items)} line(s)"
        )
        msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Open)
        open_btn = msg.button(QMessageBox.Open)
        if open_btn:
            open_btn.setText("Open PDF")
        clicked = msg.exec()
        if clicked == QMessageBox.Open:
            QDesktopServices.openUrl(QUrl.fromLocalFile(os.path.abspath(pdf_path)))

        # Reset form
        self.items.clear()
        self.table.setRowCount(0)
        self.update_totals()
        self.invoice_no_input.setText(self.get_next_invoice_no())
        self.shipped_to_input.clear()


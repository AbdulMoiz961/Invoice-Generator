from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QMessageBox,
    QFrame,
    QDoubleSpinBox,
    QCheckBox,
)

from src.db import Database


class ProductsForm(QWidget):
    """
    Product master data manager.

    Lets the user:
        • Add / edit / delete products
        • Search within the product list
        • Manage product details (name, description, price, tax rate)
    """

    def __init__(self):
        super().__init__()

        self.db = Database()
        self.editing_product_id = None
        self.current_products = []

        self._build_ui()
        self.load_products()

    # ------------------------------------------------------------------ #
    # UI Construction
    # ------------------------------------------------------------------ #
    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(16)

        self.setStyleSheet(
            """
            QWidget {
                font-size: 12px;
            }
            QLineEdit, QDoubleSpinBox {
                padding: 6px;
            }
            QPushButton[class="primary"] {
                background-color: #4a63e7;
                color: white;
                border: none;
                padding: 6px 16px;
                border-radius: 6px;
                font-weight: 600;
            }
            QPushButton[class="primary"]:disabled {
                background-color: #ccc;
                color: #6f6f6f;
            }
            QPushButton[class="ghost"] {
                border: 1px solid #d0d0d0;
                padding: 6px 14px;
                border-radius: 6px;
            }
            QPushButton[class="danger"] {
                background-color: #ffe8e8;
                border: 1px solid #ffb3b3;
                color: #c62828;
                padding: 6px 12px;
                border-radius: 6px;
            }
            QTableWidget {
                background-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 10px;
            }
            QCheckBox {
                spacing: 8px;
            }
            """
        )

        # Header
        header_row = QHBoxLayout()
        title = QLabel("Products")
        title.setStyleSheet("font-size: 20px; font-weight: 600;")

        self.summary_label = QLabel("")
        self.summary_label.setStyleSheet("color: #6c6c6c;")

        header_row.addWidget(title)
        header_row.addStretch()
        header_row.addWidget(self.summary_label)
        root.addLayout(header_row)

        # Search
        search_row = QHBoxLayout()
        search_label = QLabel("Search:")
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search by name, SKU, barcode or description…")
        self.search_input.textChanged.connect(self.load_products)

        clear_search_btn = QPushButton("Clear")
        clear_search_btn.setProperty("class", "ghost")
        clear_search_btn.clicked.connect(lambda: self.reset_form(clear_search=True))

        search_row.addWidget(search_label)
        search_row.addWidget(self.search_input)
        search_row.addWidget(clear_search_btn)
        root.addLayout(search_row)

        # Form card
        form_card = self._make_card()
        form_layout = QGridLayout()
        form_layout.setHorizontalSpacing(12)
        form_layout.setVerticalSpacing(10)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Product name *")

        self.description_input = QLineEdit()
        self.description_input.setPlaceholderText("Product description or code")

        self.sku_input = QLineEdit()
        self.sku_input.setPlaceholderText("Internal SKU / item code")

        self.barcode_input = QLineEdit()
        self.barcode_input.setPlaceholderText("Barcode / GTIN")

        self.price_input = QDoubleSpinBox()
        self.price_input.setPrefix("Rs ")
        self.price_input.setDecimals(2)
        self.price_input.setMaximum(1_000_000)
        self.price_input.setMinimum(0.0)
        self.price_input.setValue(0.0)

        self.tax_rate_input = QDoubleSpinBox()
        self.tax_rate_input.setSuffix(" %")
        self.tax_rate_input.setDecimals(2)
        self.tax_rate_input.setMaximum(100.0)
        self.tax_rate_input.setMinimum(0.0)
        self.tax_rate_input.setValue(18.0)

        self.active_checkbox = QCheckBox("Active")
        self.active_checkbox.setChecked(True)

        form_layout.addWidget(QLabel("Name"), 0, 0)
        form_layout.addWidget(self.name_input, 0, 1)
        form_layout.addWidget(QLabel("Description"), 0, 2)
        form_layout.addWidget(self.description_input, 0, 3)

        form_layout.addWidget(QLabel("SKU"), 1, 0)
        form_layout.addWidget(self.sku_input, 1, 1)
        form_layout.addWidget(QLabel("Barcode"), 1, 2)
        form_layout.addWidget(self.barcode_input, 1, 3)

        form_layout.addWidget(QLabel("Unit Price"), 2, 0)
        form_layout.addWidget(self.price_input, 2, 1)
        form_layout.addWidget(QLabel("Tax Rate"), 2, 2)
        form_layout.addWidget(self.tax_rate_input, 2, 3)

        form_layout.addWidget(self.active_checkbox, 3, 0, 1, 2)

        form_card.layout().addLayout(form_layout)

        btn_row = QHBoxLayout()
        self.save_btn = QPushButton("Add Product")
        self.save_btn.setProperty("class", "primary")
        self.save_btn.clicked.connect(self.save_product)

        self.delete_btn = QPushButton("Delete")
        self.delete_btn.setProperty("class", "danger")
        self.delete_btn.clicked.connect(self.delete_product)
        self.delete_btn.setEnabled(False)

        clear_btn = QPushButton("Reset Form")
        clear_btn.setProperty("class", "ghost")
        clear_btn.clicked.connect(self.reset_form)

        btn_row.addWidget(self.save_btn)
        btn_row.addWidget(clear_btn)
        btn_row.addStretch()
        btn_row.addWidget(self.delete_btn)

        form_card.layout().addLayout(btn_row)
        root.addWidget(form_card)

        # Product list
        list_card = self._make_card()
        list_header = QLabel("Product List")
        list_header.setStyleSheet("font-weight: 600;")
        list_card.layout().addWidget(list_header)

        self.products_table = QTableWidget(0, 7)
        self.products_table.setHorizontalHeaderLabels(
            ["Name", "SKU", "Barcode", "Description", "Unit Price", "Tax Rate", "Status"]
        )
        self.products_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.products_table.setSelectionMode(QTableWidget.SingleSelection)
        self.products_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.products_table.verticalHeader().setVisible(False)
        self.products_table.itemSelectionChanged.connect(self._handle_selection_change)

        header = self.products_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(3, QHeaderView.Stretch)
        for idx in (1, 2, 4, 5, 6):
            header.setSectionResizeMode(idx, QHeaderView.ResizeToContents)

        list_card.layout().addWidget(self.products_table)
        list_hint = QLabel("Tip: Select a row to edit the product.")
        list_hint.setStyleSheet("color: #7f7f7f; font-style: italic;")
        list_card.layout().addWidget(list_hint)
        root.addWidget(list_card)

    def _make_card(self):
        card = QFrame()
        card.setObjectName("Card")
        card.setStyleSheet(
            """
            QFrame#Card {
                background-color: #ffffff;
                border: 1px solid #e0e0e0;
                border-radius: 12px;
            }
            """
        )
        layout = QVBoxLayout(card)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(12)
        return card

    # ------------------------------------------------------------------ #
    # Data loading
    # ------------------------------------------------------------------ #
    def load_products(self):
        query = self.search_input.text().strip()
        if query:
            products = self.db.search_products(query)
        else:
            products = self.db.get_products()

        self.current_products = products
        self.products_table.setRowCount(len(products))

        for row, product in enumerate(products):
            name_item = QTableWidgetItem(product["name"])
            name_item.setData(Qt.UserRole, product["id"])
            self.products_table.setItem(row, 0, name_item)

            sku_item = QTableWidgetItem(product.get("sku") or "—")
            self.products_table.setItem(row, 1, sku_item)

            barcode_item = QTableWidgetItem(product.get("barcode") or "—")
            self.products_table.setItem(row, 2, barcode_item)

            self.products_table.setItem(row, 3, QTableWidgetItem(product.get("description") or "—"))
            
            price_item = QTableWidgetItem(f"Rs {product['unit_price']:.2f}")
            price_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.products_table.setItem(row, 4, price_item)
            
            tax_item = QTableWidgetItem(f"{product['tax_rate']:.2f}%")
            tax_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.products_table.setItem(row, 5, tax_item)
            
            status = "Active" if product.get("active", 1) else "Inactive"
            status_item = QTableWidgetItem(status)
            status_item.setTextAlignment(Qt.AlignCenter)
            if not product.get("active", 1):
                status_item.setForeground(Qt.GlobalColor.gray)
            self.products_table.setItem(row, 6, status_item)

        if products:
            self.summary_label.setText(f"{len(products)} products")
        else:
            self.summary_label.setText("No products yet. Add your first one.")

        # Keep selection if editing id still exists
        if self.editing_product_id:
            self._select_row_by_id(self.editing_product_id)

    # ------------------------------------------------------------------ #
    # CRUD actions
    # ------------------------------------------------------------------ #
    def save_product(self):
        data = {
            "name": self.name_input.text().strip(),
            "description": self.description_input.text().strip(),
            "sku": self.sku_input.text().strip(),
            "barcode": self.barcode_input.text().strip(),
            "unit_price": float(self.price_input.value()),
            "tax_rate": float(self.tax_rate_input.value()),
            "active": 1 if self.active_checkbox.isChecked() else 0,
        }

        if not data["name"]:
            QMessageBox.warning(self, "Missing data", "Product name is required.")
            return

        if data["unit_price"] < 0:
            QMessageBox.warning(self, "Invalid price", "Unit price cannot be negative.")
            return

        if data["tax_rate"] < 0 or data["tax_rate"] > 100:
            QMessageBox.warning(self, "Invalid tax rate", "Tax rate must be between 0 and 100.")
            return

        try:
            if self.editing_product_id:
                self.db.update_product(self.editing_product_id, data)
                QMessageBox.information(self, "Product updated", "Changes saved successfully.")
            else:
                self.db.add_product(data)
                QMessageBox.information(self, "Product added", "Product saved successfully.")

            self.load_products()
            if self.editing_product_id:
                self._select_row_by_id(self.editing_product_id)

        except Exception as exc:
            QMessageBox.critical(self, "Error", f"Failed to save product.\n{exc}")

    def delete_product(self):
        if not self.editing_product_id:
            return

        confirm = QMessageBox.question(
            self,
            "Delete product",
            "This will deactivate the product. Are you sure?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if confirm != QMessageBox.Yes:
            return

        try:
            self.db.delete_product(self.editing_product_id)
            QMessageBox.information(self, "Deleted", "Product deactivated successfully.")
            self.reset_form()
            self.load_products()
        except Exception as exc:
            QMessageBox.critical(self, "Error", f"Failed to delete product.\n{exc}")

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #
    def _handle_selection_change(self):
        selected = self.products_table.selectedItems()
        if not selected:
            self.editing_product_id = None
            self.delete_btn.setEnabled(False)
            self.save_btn.setText("Add Product")
            self._clear_form_fields(keep_search=True)
            return

        row = selected[0].row()
        product_id = self.products_table.item(row, 0).data(Qt.UserRole)
        product = next((p for p in self.current_products if p["id"] == product_id), None)
        if not product:
            return

        self.editing_product_id = product_id
        self.populate_form(product)
        self.delete_btn.setEnabled(True)
        self.save_btn.setText("Update Product")

    def populate_form(self, product):
        self.name_input.setText(product.get("name", ""))
        self.description_input.setText(product.get("description", ""))
        self.sku_input.setText(product.get("sku", ""))
        self.barcode_input.setText(product.get("barcode", ""))
        self.price_input.setValue(float(product.get("unit_price", 0.0)))
        self.tax_rate_input.setValue(float(product.get("tax_rate", 18.0)))
        self.active_checkbox.setChecked(bool(product.get("active", 1)))

    def reset_form(self, clear_search: bool = False):
        self.editing_product_id = None
        self.products_table.clearSelection()
        self._clear_form_fields(keep_search=not clear_search)
        if clear_search:
            self.search_input.clear()
        self.delete_btn.setEnabled(False)
        self.save_btn.setText("Add Product")

    def _clear_form_fields(self, keep_search: bool = True):
        self.name_input.clear()
        self.description_input.clear()
        self.sku_input.clear()
        self.barcode_input.clear()
        self.price_input.setValue(0.0)
        self.tax_rate_input.setValue(18.0)
        self.active_checkbox.setChecked(True)
        if not keep_search:
            self.search_input.clear()

    def _select_row_by_id(self, product_id: int):
        for row in range(self.products_table.rowCount()):
            item = self.products_table.item(row, 0)
            if item and item.data(Qt.UserRole) == product_id:
                self.products_table.blockSignals(True)
                self.products_table.selectRow(row)
                self.products_table.blockSignals(False)
                break

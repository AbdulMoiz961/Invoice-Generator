from PySide6.QtCore import Qt
import sqlite3
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
    QComboBox,
    QDoubleSpinBox,
)

from src.db import Database


class CustomersForm(QWidget):
    """
    Customer master data manager.

    Lets the user:
        • Add / edit / delete customers
        • Search within the customer list
        • Configure per-customer custom product prices
    """

    def __init__(self):
        super().__init__()

        self.db = Database()
        self.editing_customer_id = None
        self.current_customers = []
        self.has_products = False

        self._build_ui()
        self.load_products()
        self.load_customers()

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
            QLineEdit, QComboBox {
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
            """
        )

        # Header
        header_row = QHBoxLayout()
        title = QLabel("Customers")
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
        self.search_input.setPlaceholderText("Search by name, contact or email…")
        self.search_input.textChanged.connect(self.load_customers)

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
        self.name_input.setPlaceholderText("Customer name *")

        self.contact_input = QLineEdit()
        self.contact_input.setPlaceholderText("Contact person or number")

        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Email address")

        self.address_input = QLineEdit()
        self.address_input.setPlaceholderText("Head office address")

        self.ntn_input = QLineEdit()
        self.ntn_input.setPlaceholderText("NTN")

        self.strn_input = QLineEdit()
        self.strn_input.setPlaceholderText("STRN")

        form_layout.addWidget(QLabel("Name"), 0, 0)
        form_layout.addWidget(self.name_input, 0, 1)
        form_layout.addWidget(QLabel("Contact"), 0, 2)
        form_layout.addWidget(self.contact_input, 0, 3)

        form_layout.addWidget(QLabel("Email"), 1, 0)
        form_layout.addWidget(self.email_input, 1, 1)
        form_layout.addWidget(QLabel("Address"), 1, 2)
        form_layout.addWidget(self.address_input, 1, 3)

        form_layout.addWidget(QLabel("NTN"), 2, 0)
        form_layout.addWidget(self.ntn_input, 2, 1)
        form_layout.addWidget(QLabel("STRN"), 2, 2)
        form_layout.addWidget(self.strn_input, 2, 3)

        form_card.layout().addLayout(form_layout)

        btn_row = QHBoxLayout()
        self.save_btn = QPushButton("Add Customer")
        self.save_btn.setProperty("class", "primary")
        self.save_btn.clicked.connect(self.save_customer)

        self.delete_btn = QPushButton("Delete")
        self.delete_btn.setProperty("class", "danger")
        self.delete_btn.clicked.connect(self.delete_customer)
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

        # Customer list
        list_card = self._make_card()
        list_header = QLabel("Customer List")
        list_header.setStyleSheet("font-weight: 600;")
        list_card.layout().addWidget(list_header)

        self.customers_table = QTableWidget(0, 5)
        self.customers_table.setHorizontalHeaderLabels(
            ["Name", "Contact", "Email", "NTN", "STRN"]
        )
        self.customers_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.customers_table.setSelectionMode(QTableWidget.SingleSelection)
        self.customers_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.customers_table.verticalHeader().setVisible(False)
        self.customers_table.itemSelectionChanged.connect(self._handle_selection_change)

        header = self.customers_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        for idx in range(1, 5):
            header.setSectionResizeMode(idx, QHeaderView.ResizeToContents)

        list_card.layout().addWidget(self.customers_table)
        list_hint = QLabel("Tip: Select a row to edit the customer or configure prices.")
        list_hint.setStyleSheet("color: #7f7f7f; font-style: italic;")
        list_card.layout().addWidget(list_hint)
        root.addWidget(list_card)

        # Custom price overrides
        price_card = self._make_card()
        price_header_row = QHBoxLayout()
        self.price_title = QLabel("Custom Product Prices")
        self.price_subtitle = QLabel("Select a customer to see overrides.")
        self.price_subtitle.setStyleSheet("color: #7f7f7f;")

        price_header_row.addWidget(self.price_title)
        price_header_row.addStretch()
        price_header_row.addWidget(self.price_subtitle)
        price_card.layout().addLayout(price_header_row)

        price_form_row = QHBoxLayout()
        self.product_cb = QComboBox()
        self.product_cb.setEnabled(False)
        self.product_cb.currentIndexChanged.connect(self._handle_product_changed)

        self.price_input = QDoubleSpinBox()
        self.price_input.setPrefix("Rs ")
        self.price_input.setDecimals(2)
        self.price_input.setMaximum(1_000_000)
        self.price_input.setEnabled(False)

        self.save_price_btn = QPushButton("Save Price")
        self.save_price_btn.setProperty("class", "primary")
        self.save_price_btn.setEnabled(False)
        self.save_price_btn.clicked.connect(self.save_price_override)

        price_form_row.addWidget(QLabel("Product"))
        price_form_row.addWidget(self.product_cb, stretch=2)
        price_form_row.addWidget(QLabel("Custom Price"))
        price_form_row.addWidget(self.price_input)
        price_form_row.addWidget(self.save_price_btn)
        price_card.layout().addLayout(price_form_row)

        self.price_table = QTableWidget(0, 4)
        self.price_table.setHorizontalHeaderLabels(
            ["Product", "Default Price", "Custom Price", "Remove"]
        )
        self.price_table.verticalHeader().setVisible(False)
        self.price_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.price_table.setSelectionMode(QTableWidget.NoSelection)

        price_header = self.price_table.horizontalHeader()
        price_header.setSectionResizeMode(0, QHeaderView.Stretch)
        for idx in range(1, 3):
            price_header.setSectionResizeMode(idx, QHeaderView.ResizeToContents)
        price_header.setSectionResizeMode(3, QHeaderView.ResizeToContents)

        price_card.layout().addWidget(self.price_table)
        root.addWidget(price_card)

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
    def load_customers(self):
        query = self.search_input.text().strip()
        if query:
            customers = self.db.search_customers(query)
        else:
            customers = self.db.get_customers()

        self.current_customers = customers
        self.customers_table.setRowCount(len(customers))

        for row, customer in enumerate(customers):
            name_item = QTableWidgetItem(customer["name"])
            name_item.setData(Qt.UserRole, customer["id"])
            self.customers_table.setItem(row, 0, name_item)
            self.customers_table.setItem(row, 1, QTableWidgetItem(customer.get("contact") or "—"))
            self.customers_table.setItem(row, 2, QTableWidgetItem(customer.get("email") or "—"))
            self.customers_table.setItem(row, 3, QTableWidgetItem(customer.get("ntn") or "—"))
            self.customers_table.setItem(row, 4, QTableWidgetItem(customer.get("strn") or "—"))

        if customers:
            self.summary_label.setText(f"{len(customers)} customers")
        else:
            self.summary_label.setText("No customers yet. Add your first one.")

        # Keep selection if editing id still exists
        if self.editing_customer_id:
            self._select_row_by_id(self.editing_customer_id)

    def load_products(self):
        self.product_cb.clear()
        products = self.db.get_products()
        self.has_products = bool(products)
        if not products:
            self.product_cb.addItem("No products available", None)
            self.product_cb.setEnabled(False)
            return

        for product in products:
            display = f"{product['name']} (Rs {product['unit_price']})"
            self.product_cb.addItem(display, product["id"])

        self.product_cb.setEnabled(False)

    def load_customer_prices(self, customer_id: int):
        prices = self.db.get_customer_product_prices(customer_id)
        self.price_table.setRowCount(len(prices))

        for row, item in enumerate(prices):
            product_item = QTableWidgetItem(item["product_name"])
            product_item.setData(Qt.UserRole, item["product_id"])
            self.price_table.setItem(row, 0, product_item)

            self.price_table.setItem(row, 1, QTableWidgetItem(f"Rs {item['default_price']:.2f}"))
            self.price_table.setItem(row, 2, QTableWidgetItem(f"Rs {item['custom_price']:.2f}"))

            remove_btn = QPushButton("Remove")
            remove_btn.setProperty("class", "danger")
            remove_btn.clicked.connect(
                lambda _, pid=item["product_id"]: self.remove_price_override(pid)
            )
            self.price_table.setCellWidget(row, 3, remove_btn)

        if prices:
            self.price_subtitle.setText(f"{len(prices)} override(s) configured.")
        else:
            self.price_subtitle.setText("No overrides for this customer.")

    # ------------------------------------------------------------------ #
    # CRUD actions
    # ------------------------------------------------------------------ #
    def save_customer(self):
        data = {
            "name": self.name_input.text().strip(),
            "contact": self.contact_input.text().strip(),
            "email": self.email_input.text().strip(),
            "address": self.address_input.text().strip(),
            "ntn": self.ntn_input.text().strip(),
            "strn": self.strn_input.text().strip(),
        }

        if not data["name"]:
            QMessageBox.warning(self, "Missing data", "Customer name is required.")
            return

        try:
            if self.editing_customer_id:
                self.db.update_customer(self.editing_customer_id, data)
                QMessageBox.information(self, "Customer updated", "Changes saved successfully.")
            else:
                new_id = self.db.add_customer(data)
                self.editing_customer_id = new_id
                QMessageBox.information(self, "Customer added", "Customer saved successfully.")

            self.load_customers()
            if self.editing_customer_id:
                self._select_row_by_id(self.editing_customer_id)
                self._enable_price_controls(True)

        except Exception as exc:
            QMessageBox.critical(self, "Error", f"Failed to save customer.\n{exc}")

    def delete_customer(self):
        if not self.editing_customer_id:
            return

        confirm = QMessageBox.question(
            self,
            "Delete customer",
            "Delete this customer and all its price overrides?",
        )
        if confirm != QMessageBox.Yes:
            return

        try:
            self.db.delete_customer(self.editing_customer_id)
            QMessageBox.information(self, "Deleted", "Customer removed successfully.")
            self.reset_form()
            self.load_customers()
        except sqlite3.IntegrityError:
            QMessageBox.warning(
                self,
                "Cannot Delete",
                "This customer cannot be deleted because they have existing invoices.\n\n"
                "To delete this customer, you must first delete all their invoices."
            )
        except Exception as exc:
            QMessageBox.critical(self, "Error", f"Failed to delete customer.\n{exc}")

    # ------------------------------------------------------------------ #
    # Price overrides
    # ------------------------------------------------------------------ #
    def save_price_override(self):
        if not self.editing_customer_id:
            QMessageBox.warning(
                self,
                "Select customer",
                "Select a customer before setting custom prices.",
            )
            return

        if not self.has_products:
            QMessageBox.warning(self, "No products", "Add products before configuring prices.")
            return

        product_id = self.product_cb.currentData()
        if not product_id:
            QMessageBox.warning(self, "Invalid product", "Please choose a valid product.")
            return

        custom_price = float(self.price_input.value())
        if custom_price <= 0:
            QMessageBox.warning(self, "Invalid price", "Price must be greater than zero.")
            return

        try:
            self.db.upsert_customer_product_price(
                self.editing_customer_id,
                product_id,
                custom_price,
            )
            self.load_customer_prices(self.editing_customer_id)
            QMessageBox.information(self, "Saved", "Custom price saved.")
        except Exception as exc:
            QMessageBox.critical(self, "Error", f"Failed to save custom price.\n{exc}")

    def remove_price_override(self, product_id: int):
        if not self.editing_customer_id:
            return
        self.db.delete_customer_product_price(self.editing_customer_id, product_id)
        self.load_customer_prices(self.editing_customer_id)

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #
    def _handle_selection_change(self):
        selected = self.customers_table.selectedItems()
        if not selected:
            self.editing_customer_id = None
            self._enable_price_controls(False)
            self.price_table.setRowCount(0)
            self.price_subtitle.setText("Select a customer to see overrides.")
            self.price_title.setText("Custom Product Prices")
            self.delete_btn.setEnabled(False)
            self.save_btn.setText("Add Customer")
            self._clear_form_fields(keep_search=True)
            return

        row = selected[0].row()
        customer_id = self.customers_table.item(row, 0).data(Qt.UserRole)
        customer = next((c for c in self.current_customers if c["id"] == customer_id), None)
        if not customer:
            return

        self.editing_customer_id = customer_id
        self.populate_form(customer)
        self.price_title.setText(f"Custom Product Prices — {customer['name']}")
        self.load_customer_prices(customer_id)
        self._enable_price_controls(True)
        self.delete_btn.setEnabled(True)
        self.save_btn.setText("Update Customer")

    def populate_form(self, customer):
        self.name_input.setText(customer.get("name", ""))
        self.contact_input.setText(customer.get("contact", ""))
        self.email_input.setText(customer.get("email", ""))
        self.address_input.setText(customer.get("address", ""))
        self.ntn_input.setText(customer.get("ntn", ""))
        self.strn_input.setText(customer.get("strn", ""))

    def reset_form(self, clear_search: bool = False):
        self.editing_customer_id = None
        self.customers_table.clearSelection()
        self._clear_form_fields(keep_search=not clear_search)
        if clear_search:
            self.search_input.clear()
        self.delete_btn.setEnabled(False)
        self.save_btn.setText("Add Customer")
        self._enable_price_controls(False)
        self.price_table.setRowCount(0)
        self.price_subtitle.setText("Select a customer to see overrides.")
        self.price_title.setText("Custom Product Prices")

    def _clear_form_fields(self, keep_search: bool = True):
        self.name_input.clear()
        self.contact_input.clear()
        self.email_input.clear()
        self.address_input.clear()
        self.ntn_input.clear()
        self.strn_input.clear()
        if not keep_search:
            self.search_input.clear()

    def _enable_price_controls(self, enabled: bool):
        can_use = enabled and self.has_products
        self.product_cb.setEnabled(can_use)
        self.price_input.setEnabled(enabled)
        self.save_price_btn.setEnabled(can_use)
        if can_use:
            self._handle_product_changed(self.product_cb.currentIndex())
        else:
            self.price_input.setValue(0.0)

    def _suggest_price(self) -> float:
        product_id = self.product_cb.currentData()
        if product_id:
            product = self.db.get_product(product_id)
            if product:
                return float(product["unit_price"])
        return 0.0

    def _select_row_by_id(self, customer_id: int):
        for row in range(self.customers_table.rowCount()):
            item = self.customers_table.item(row, 0)
            if item and item.data(Qt.UserRole) == customer_id:
                self.customers_table.blockSignals(True)
                self.customers_table.selectRow(row)
                self.customers_table.blockSignals(False)
                break

    def _handle_product_changed(self, _index):
        if not self.has_products:
            return
        product_id = self.product_cb.currentData()
        if not product_id:
            self.price_input.setValue(0.0)
            return

        if self.editing_customer_id:
            custom_price = self.db.get_customer_price_for_product(
                self.editing_customer_id,
                product_id,
            )
            if custom_price is not None:
                self.price_input.setValue(float(custom_price))
                return

        suggested = self._suggest_price()
        if suggested:
            self.price_input.setValue(suggested)
        else:
            self.price_input.setValue(0.0)


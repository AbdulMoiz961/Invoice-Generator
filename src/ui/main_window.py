from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QLabel,
    QInputDialog, QLineEdit, QMessageBox, QScrollArea
)
from PySide6.QtCore import Qt

from .dashboard import Dashboard
from .invoice_form import InvoiceForm
from .customers_form import CustomersForm
from .products_form import ProductsForm
from .settings_form import SettingsForm
from .reports_view import ReportsView
from src.settings_manager import is_password_protected, verify_app_password


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Invoice Generator")
        self.resize(1000, 600)

        # Main container layout
        main_widget = QWidget()
        main_layout = QHBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # -------- Sidebar navigation --------
        self.sidebar = QWidget()
        self.sidebar.setFixedWidth(220)
        self.sidebar.setStyleSheet("""
            QWidget {
                background-color: #2c3e50;
                color: #ecf0f1;
            }
            QPushButton {
                background-color: transparent;
                border: none;
                text-align: left;
                padding: 12px 20px;
                font-size: 14px;
                color: #ecf0f1;
                border-left: 4px solid transparent;
            }
            QPushButton:hover {
                background-color: #34495e;
            }
            QPushButton:checked {
                background-color: #34495e;
                border-left: 4px solid #3498db;
                font-weight: bold;
            }
            QLabel#SidebarTitle {
                font-size: 18px;
                font-weight: bold;
                padding: 20px;
                color: #ffffff;
            }
        """)
        
        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(0)

        # Title
        title_label = QLabel("Invoice Generator")
        title_label.setObjectName("SidebarTitle")
        sidebar_layout.addWidget(title_label)
        
        sidebar_layout.addSpacing(10)

        # Buttons
        self.nav_buttons = []
        
        btn_dashboard = self._create_nav_btn("Dashboard")
        btn_invoice = self._create_nav_btn("New Invoice")
        btn_customers = self._create_nav_btn("Customers")
        btn_products = self._create_nav_btn("Products")
        btn_reports = self._create_nav_btn("Reports")
        btn_settings = self._create_nav_btn("Settings")

        sidebar_layout.addWidget(btn_dashboard)
        sidebar_layout.addWidget(btn_invoice)
        sidebar_layout.addWidget(btn_customers)
        sidebar_layout.addWidget(btn_products)
        sidebar_layout.addWidget(btn_reports)
        sidebar_layout.addWidget(btn_settings)
        sidebar_layout.addStretch()

        # -------- Content area --------
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        # Remove border from scroll area to blend in
        self.scroll_area.setStyleSheet("QScrollArea { border: none; }")

        self.content_area = QWidget()
        self.content_layout = QVBoxLayout(self.content_area)
        self.content_layout.setContentsMargins(20, 20, 20, 20)
        
        self.scroll_area.setWidget(self.content_area)

        # Load default screen
        self.set_screen(Dashboard())
        self._highlight_btn(btn_dashboard)

        # Button navigation bindings
        btn_dashboard.clicked.connect(lambda: [self.set_screen(Dashboard()), self._highlight_btn(btn_dashboard)])
        btn_invoice.clicked.connect(lambda: [self.set_screen(InvoiceForm()), self._highlight_btn(btn_invoice)])
        btn_customers.clicked.connect(lambda: [self.set_screen(CustomersForm()), self._highlight_btn(btn_customers)])
        btn_products.clicked.connect(lambda: [self.set_screen(ProductsForm()), self._highlight_btn(btn_products)])
        btn_reports.clicked.connect(lambda: [self.set_screen(ReportsView()), self._highlight_btn(btn_reports)])
        btn_settings.clicked.connect(lambda: [self._open_settings_wrapper(btn_settings)])

        main_layout.addWidget(self.sidebar)
        main_layout.addWidget(self.scroll_area, stretch=1)

        self.setCentralWidget(main_widget)

    def set_screen(self, widget):
        # Clear previous widgets
        for i in reversed(range(self.content_layout.count())):
            item = self.content_layout.takeAt(i)
            if item.widget():
                item.widget().deleteLater()

        # Add new widget
        self.content_layout.addWidget(widget)

    def _create_nav_btn(self, text):
        btn = QPushButton(text)
        btn.setCheckable(True)
        btn.setCursor(Qt.PointingHandCursor)
        self.nav_buttons.append(btn)
        return btn

    def _highlight_btn(self, active_btn):
        for btn in self.nav_buttons:
            btn.setChecked(False)
        active_btn.setChecked(True)

    def _open_settings_wrapper(self, btn):
        self._highlight_btn(btn)
        self._open_settings()

    def _open_settings(self):
        if is_password_protected():
            pw, ok = QInputDialog.getText(self, "Security", "Enter password:", QLineEdit.Password)
            if not ok:
                # Revert highlight if cancelled (optional, but tricky to know previous)
                return
            if not verify_app_password(pw):
                QMessageBox.warning(self, "Security", "Incorrect password.")
                return
        self.set_screen(SettingsForm())

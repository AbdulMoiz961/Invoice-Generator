from datetime import date

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QFrame,
    QGridLayout,
    QTableWidget,
    QTableWidgetItem,
    QSizePolicy,
)

from src.db import Database


class Dashboard(QWidget):
    """
    Minimal dashboard that surfaces the health of the invoicing activity.
    Shows quick KPI cards and a compact list of the most recent invoices.
    """

    def __init__(self):
        super().__init__()
        self.db = Database()
        self.stat_labels = {}

        self._build_ui()
        self.refresh_data()

    # ------------------------------------------------------------------ #
    # UI Construction
    # ------------------------------------------------------------------ #
    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(18)

        # Header
        header_row = QHBoxLayout()
        title_block = QVBoxLayout()
        title = QLabel("Dashboard")
        title.setStyleSheet("font-size: 22px; font-weight: 600;")
        subtitle = QLabel("A snapshot of invoices, revenue and customers")
        subtitle.setStyleSheet("color: #6c6c6c; font-size: 12px;")

        title_block.addWidget(title)
        title_block.addWidget(subtitle)

        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.setFixedWidth(120)
        self.refresh_btn.clicked.connect(self.refresh_data)

        header_row.addLayout(title_block)
        header_row.addStretch()
        header_row.addWidget(self.refresh_btn)
        root.addLayout(header_row)

        # KPI Grid
        metrics_grid = QGridLayout()
        metrics_grid.setSpacing(12)

        metric_specs = [
            ("total_revenue", f"Revenue ({date.today().year})"),
            ("mtd_revenue", "Month-to-Date Revenue"),
            ("total_invoices", "Invoices Issued"),
            ("total_customers", "Active Customers"),
        ]

        for idx, (key, label_text) in enumerate(metric_specs):
            card, value_label = self._create_stat_card(label_text)
            metrics_grid.addWidget(card, idx // 2, idx % 2)
            self.stat_labels[key] = value_label

        root.addLayout(metrics_grid)

        # Summary line
        self.summary_label = QLabel("Loading latest activity…")
        self.summary_label.setAlignment(Qt.AlignLeft)
        self.summary_label.setStyleSheet("color: #555; font-size: 12px;")
        root.addWidget(self.summary_label)

        # Recent invoices section
        section_header = QHBoxLayout()
        recent_title = QLabel("Recent Invoices")
        recent_title.setStyleSheet("font-size: 16px; font-weight: 600;")
        section_header.addWidget(recent_title)
        section_header.addStretch()

        root.addLayout(section_header)

        self.recent_table = QTableWidget(0, 4)
        self.recent_table.setHorizontalHeaderLabels(
            ["Invoice #", "Date", "Customer", "Total"]
        )
        header = self.recent_table.horizontalHeader()
        header.setStretchLastSection(True)
        self.recent_table.verticalHeader().setVisible(False)
        self.recent_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.recent_table.setSelectionMode(QTableWidget.NoSelection)
        self.recent_table.setFocusPolicy(Qt.NoFocus)
        self.recent_table.setAlternatingRowColors(True)
        self.recent_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        root.addWidget(self.recent_table)

        self.empty_state = QLabel("No invoices yet. Create one to see activity here.")
        self.empty_state.setAlignment(Qt.AlignCenter)
        self.empty_state.setStyleSheet("color: #8c8c8c; font-style: italic;")
        self.empty_state.hide()
        root.addWidget(self.empty_state)

    def _create_stat_card(self, title_text):
        card = QFrame()
        card.setFrameShape(QFrame.StyledPanel)
        card.setObjectName("statCard")
        card.setStyleSheet(
            """
            QFrame#statCard {
                border: 1px solid #e2e2e2;
                border-radius: 10px;
                background-color: #fcfcfc;
            }
            """
        )
        layout = QVBoxLayout(card)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(4)

        title = QLabel(title_text.upper())
        title.setStyleSheet("color: #7f7f7f; font-size: 11px; letter-spacing: 0.6px;")

        value = QLabel("—")
        value.setStyleSheet("font-size: 24px; font-weight: bold;")

        layout.addWidget(title)
        layout.addWidget(value)
        layout.addStretch()

        return card, value

    # ------------------------------------------------------------------ #
    # Data loading
    # ------------------------------------------------------------------ #
    def refresh_data(self):
        self.refresh_btn.setEnabled(False)
        try:
            self._load_metrics()
            self._load_recent_invoices()
        finally:
            self.refresh_btn.setEnabled(True)

    def _load_metrics(self):
        year_start = date.today().replace(month=1, day=1).isoformat()
        total_revenue = self._scalar(
            "SELECT COALESCE(SUM(total_amount), 0) AS value FROM invoices WHERE date >= ?",
            (year_start,)
        )

        month_start = date.today().replace(day=1).isoformat()
        mtd_revenue = self._scalar(
            "SELECT COALESCE(SUM(total_amount), 0) AS value FROM invoices WHERE date >= ?",
            (month_start,)
        )

        total_invoices = self._scalar(
            "SELECT COUNT(*) AS value FROM invoices"
        )

        total_customers = self._scalar(
            "SELECT COUNT(*) AS value FROM customers"
        )

        self.stat_labels["total_revenue"].setText(self._format_currency(total_revenue))
        self.stat_labels["mtd_revenue"].setText(self._format_currency(mtd_revenue))
        self.stat_labels["total_invoices"].setText(self._format_number(total_invoices))
        self.stat_labels["total_customers"].setText(
            self._format_number(total_customers)
        )

    def _load_recent_invoices(self):
        rows = self.db.fetch_all(
            """
            SELECT i.invoice_no, i.date, i.total_amount, c.name AS customer_name
            FROM invoices i
            LEFT JOIN customers c ON c.id = i.customer_id
            ORDER BY i.date DESC, i.id DESC
            LIMIT 6
            """
        )

        self.recent_table.setRowCount(len(rows))

        if not rows:
            self.empty_state.show()
            self.summary_label.setText(
                "You have not created any invoices yet. Use 'New Invoice' to get started."
            )
            return

        self.empty_state.hide()

        latest = rows[0]
        self.summary_label.setText(
            f"Last invoice {latest.get('invoice_no')} for {latest.get('customer_name') or 'Unknown'} "
            f"on {latest.get('date')} totaling {self._format_currency(latest.get('total_amount', 0))}."
        )

        for row_idx, invoice in enumerate(rows):
            self.recent_table.setItem(
                row_idx, 0, QTableWidgetItem(str(invoice.get("invoice_no", "—")))
            )
            self.recent_table.setItem(
                row_idx, 1, QTableWidgetItem(invoice.get("date", "—"))
            )
            self.recent_table.setItem(
                row_idx, 2, QTableWidgetItem(invoice.get("customer_name") or "—")
            )
            self.recent_table.setItem(
                row_idx,
                3,
                QTableWidgetItem(self._format_currency(invoice.get("total_amount", 0))),
            )

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #
    def _scalar(self, query, params=(), default=0):
        row = self.db.fetch_one(query, params)
        if not row:
            return default
        value = row.get("value")
        return value if value is not None else default

    @staticmethod
    def _format_currency(value):
        try:
            return f"PKR {float(value):,.2f}"
        except (TypeError, ValueError):
            return "PKR 0.00"

    @staticmethod
    def _format_number(value):
        try:
            return f"{int(value):,}"
        except (TypeError, ValueError):
            return "0"

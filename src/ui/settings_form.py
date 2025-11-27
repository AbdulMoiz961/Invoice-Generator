import os

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QVBoxLayout,
    QGroupBox,
    QFormLayout,
    QLineEdit,
    QTextEdit,
    QPushButton,
    QHBoxLayout,
    QFileDialog,
    QMessageBox,
    QSpinBox,
    QCheckBox,
    QInputDialog,
)

from src.backup import backup_database, regenerate_all_pdfs, restore_database
from src.import_export import (
    export_to_csv,
    import_customers_from_csv,
    import_products_from_csv,
)
from src.settings_manager import (
    CompanyProfile,
    Preferences,
    get_company_profile,
    save_company_profile,
    get_preferences,
    save_preferences,
    set_app_password,
    is_password_protected,
    verify_app_password,
)


class SettingsForm(QWidget):
    """
    Screen that allows editing the company profile (used across invoices
    and reports) plus a handful of application-level preferences.
    """

    def __init__(self):
        super().__init__()
        self.setObjectName("SettingsForm")
        self._build_ui()
        self.load_data()

    # ------------------------------------------------------------------ #
    # UI construction
    # ------------------------------------------------------------------ #
    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(32, 24, 32, 24)
        root.setSpacing(18)

        title = QLabel("Settings")
        title.setStyleSheet("font-size: 22px; font-weight: 600;")
        blurb = QLabel("Update company profile details and tweak invoice preferences.")
        blurb.setStyleSheet("color: #646464;")
        blurb.setWordWrap(True)

        root.addWidget(title)
        root.addWidget(blurb)

        self.company_group = self._create_company_group()
        self.pref_group = self._create_preferences_group()
        self.security_group = self._create_security_group()
        self.data_group = self._create_data_tools_group()
        self.io_group = self._create_io_group()

        root.addWidget(self.company_group)
        root.addWidget(self.pref_group)
        root.addWidget(self.security_group)
        root.addWidget(self.data_group)
        root.addWidget(self.io_group)

        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #2e7d32; font-weight: 500;")
        root.addWidget(self.status_label)
        root.addStretch()

    def _create_company_group(self) -> QGroupBox:
        group = QGroupBox("Company Profile")
        group.setStyleSheet("QGroupBox { font-size: 14px; font-weight: 600; }")

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignRight)
        form.setHorizontalSpacing(14)
        form.setVerticalSpacing(10)

        self.name_input = QLineEdit()
        self.address_input = QTextEdit()
        self.address_input.setFixedHeight(70)
        self.contact_input = QLineEdit()
        self.ntn_input = QLineEdit()
        self.strn_input = QLineEdit()

        form.addRow("Legal Name*", self.name_input)
        form.addRow("Mailing Address", self.address_input)
        form.addRow("Primary Contact", self.contact_input)
        form.addRow("NTN", self.ntn_input)
        form.addRow("STRN", self.strn_input)

        save_btn = QPushButton("Save Company Profile")
        save_btn.clicked.connect(self._on_save_company)
        save_btn.setDefault(True)
        self.company_refresh_btn = QPushButton("Reload")
        self.company_refresh_btn.clicked.connect(self.load_data)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_row.addWidget(self.company_refresh_btn)
        btn_row.addWidget(save_btn)

        wrapper = QVBoxLayout()
        wrapper.addLayout(form)
        wrapper.addLayout(btn_row)
        group.setLayout(wrapper)
        return group

    def _create_data_tools_group(self) -> QGroupBox:
        group = QGroupBox("Data Maintenance")
        group.setStyleSheet("QGroupBox { font-size: 14px; font-weight: 600; }")

        layout = QVBoxLayout()
        layout.setSpacing(10)

        blurb = QLabel(
            "Create database backups, restore from an earlier copy, "
            "or regenerate all invoice PDFs after layout changes."
        )
        blurb.setWordWrap(True)
        blurb.setStyleSheet("color: #555;")

        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        backup_btn = QPushButton("Backup Database")
        backup_btn.clicked.connect(self._on_backup_database)
        restore_btn = QPushButton("Restore Database…")
        restore_btn.clicked.connect(self._on_restore_database)
        regen_btn = QPushButton("Regenerate PDFs…")
        regen_btn.clicked.connect(self._on_regenerate_pdfs)

        btn_row.addWidget(backup_btn)
        btn_row.addWidget(restore_btn)
        btn_row.addWidget(regen_btn)
        btn_row.addStretch()

        layout.addWidget(blurb)
        layout.addLayout(btn_row)
        group.setLayout(layout)

        self.backup_btn = backup_btn
        self.restore_btn = restore_btn
        self.regen_btn = regen_btn

        return group

    def _create_preferences_group(self) -> QGroupBox:
        group = QGroupBox("Invoice & App Preferences")
        group.setStyleSheet("QGroupBox { font-size: 14px; font-weight: 600; }")

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignRight)
        form.setHorizontalSpacing(14)
        form.setVerticalSpacing(10)

        self.invoice_prefix_input = QLineEdit()
        self.invoice_sequence_input = QSpinBox()
        self.invoice_sequence_input.setRange(1, 999999)
        self.invoice_sequence_input.setAccelerated(True)

        self.pdf_dir_input = QLineEdit()
        self.pdf_dir_input.setReadOnly(True)
        browse_btn = QPushButton("Browse…")
        browse_btn.clicked.connect(self._browse_pdf_dir)

        pdf_dir_row = QHBoxLayout()
        pdf_dir_row.addWidget(self.pdf_dir_input, stretch=1)
        pdf_dir_row.addWidget(browse_btn)

        self.auto_open_checkbox = QCheckBox("Open PDF after saving invoice")

        form.addRow("Invoice Prefix", self.invoice_prefix_input)
        form.addRow("Next Number", self.invoice_sequence_input)
        form.addRow("PDF Output Folder", pdf_dir_row)
        form.addRow("", self.auto_open_checkbox)

        save_btn = QPushButton("Save Preferences")
        save_btn.clicked.connect(self._on_save_preferences)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_row.addWidget(save_btn)

        wrapper = QVBoxLayout()
        wrapper.addLayout(form)
        wrapper.addLayout(btn_row)
        group.setLayout(wrapper)
        return group

    def _create_security_group(self) -> QGroupBox:
        group = QGroupBox("Security")
        group.setStyleSheet("QGroupBox { font-size: 14px; font-weight: 600; }")
        
        layout = QHBoxLayout()
        
        self.password_status_label = QLabel()
        self._update_password_status()
        
        change_pw_btn = QPushButton("Change Password")
        change_pw_btn.clicked.connect(self._on_change_password)
        
        layout.addWidget(self.password_status_label)
        layout.addStretch()
        layout.addWidget(change_pw_btn)
        
        group.setLayout(layout)
        return group

    def _create_io_group(self) -> QGroupBox:
        group = QGroupBox("Import / Export")
        group.setStyleSheet("QGroupBox { font-size: 14px; font-weight: 600; }")
        
        layout = QVBoxLayout()
        
        # Export Row
        export_layout = QHBoxLayout()
        export_label = QLabel("Export Data (CSV):")
        export_cust_btn = QPushButton("Customers")
        export_cust_btn.clicked.connect(lambda: self._on_export_data("customers"))
        export_prod_btn = QPushButton("Products")
        export_prod_btn.clicked.connect(lambda: self._on_export_data("products"))
        export_inv_btn = QPushButton("Invoices")
        export_inv_btn.clicked.connect(lambda: self._on_export_data("invoices"))
        
        export_layout.addWidget(export_label)
        export_layout.addWidget(export_cust_btn)
        export_layout.addWidget(export_prod_btn)
        export_layout.addWidget(export_inv_btn)
        export_layout.addStretch()
        
        # Import Row
        import_layout = QHBoxLayout()
        import_label = QLabel("Import Data (CSV):")
        import_cust_btn = QPushButton("Customers")
        import_cust_btn.clicked.connect(self._on_import_customers)
        import_prod_btn = QPushButton("Products")
        import_prod_btn.clicked.connect(self._on_import_products)
        
        import_layout.addWidget(import_label)
        import_layout.addWidget(import_cust_btn)
        import_layout.addWidget(import_prod_btn)
        import_layout.addStretch()
        
        layout.addLayout(export_layout)
        layout.addLayout(import_layout)
        group.setLayout(layout)
        return group

    # ------------------------------------------------------------------ #
    # Data loading / saving
    # ------------------------------------------------------------------ #
    def load_data(self):
        profile = get_company_profile()
        self.name_input.setText(profile.name)
        self.address_input.setPlainText(profile.address)
        self.contact_input.setText(profile.contact)
        self.ntn_input.setText(profile.ntn)
        self.strn_input.setText(profile.strn)

        prefs = get_preferences()
        self.invoice_prefix_input.setText(prefs.invoice_prefix)
        self.invoice_sequence_input.setValue(prefs.invoice_sequence)
        self.pdf_dir_input.setText(os.path.abspath(prefs.default_pdf_dir))
        self.auto_open_checkbox.setChecked(prefs.auto_open_pdf)
        self._set_status("Loaded latest saved settings.")

    def _collect_company_data(self) -> CompanyProfile:
        return CompanyProfile(
            name=self.name_input.text().strip(),
            address=self.address_input.toPlainText().strip(),
            contact=self.contact_input.text().strip(),
            ntn=self.ntn_input.text().strip(),
            strn=self.strn_input.text().strip(),
        )

    def _collect_preferences(self) -> Preferences:
        return Preferences(
            invoice_prefix=self.invoice_prefix_input.text().strip() or "INV-",
            invoice_sequence=self.invoice_sequence_input.value(),
            default_pdf_dir=self.pdf_dir_input.text().strip(),
            auto_open_pdf=self.auto_open_checkbox.isChecked(),
        )

    def _on_save_company(self):
        try:
            profile = self._collect_company_data()
            save_company_profile(profile)
        except ValueError as exc:
            self._set_status(str(exc), error=True)
            QMessageBox.warning(self, "Validation Error", str(exc))
            return
        except Exception as exc:  # pragma: no cover - best effort messaging
            self._set_status("Failed to save company profile.", error=True)
            QMessageBox.critical(self, "Unexpected Error", str(exc))
            return

        self._set_status("Company profile saved.")
        QMessageBox.information(self, "Settings", "Company profile updated successfully.")

    def _on_save_preferences(self):
        try:
            prefs = self._collect_preferences()
            if not prefs.default_pdf_dir:
                raise ValueError("Please select a PDF output folder.")
            save_preferences(prefs)
        except ValueError as exc:
            self._set_status(str(exc), error=True)
            QMessageBox.warning(self, "Validation Error", str(exc))
            return
        except Exception as exc:  # pragma: no cover - best effort messaging
            self._set_status("Failed to save preferences.", error=True)
            QMessageBox.critical(self, "Unexpected Error", str(exc))
            return

        self._set_status("Preferences saved.")
        QMessageBox.information(self, "Settings", "Preferences updated successfully.")

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #
    def _browse_pdf_dir(self):
        start_dir = self.pdf_dir_input.text() or os.getcwd()
        selected = QFileDialog.getExistingDirectory(
            self,
            "Select PDF output folder",
            os.path.abspath(start_dir),
        )
        if selected:
            self.pdf_dir_input.setText(os.path.abspath(selected))

    def _set_status(self, message: str, error: bool = False):
        color = "#c62828" if error else "#2e7d32"
        self.status_label.setStyleSheet(f"color: {color}; font-weight: 500;")
        self.status_label.setText(message)

    # ------------------------------------------------------------------ #
    # Data maintenance actions
    # ------------------------------------------------------------------ #
    def _on_backup_database(self):
        try:
            backup_path = backup_database()
        except Exception as exc:  # pragma: no cover - I/O heavy
            QMessageBox.critical(self, "Backup Failed", str(exc))
            self._set_status("Backup failed.", error=True)
            return

        self._set_status("Database backup completed.")
        QMessageBox.information(
            self,
            "Backup Ready",
            f"A backup was saved to:\n{backup_path}",
        )

    def _on_restore_database(self):
        start_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data", "backups"))
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select backup file",
            start_dir,
            "SQLite database (*.db);;All files (*)",
        )
        if not path:
            return

        confirm = QMessageBox.question(
            self,
            "Restore Database",
            "Restoring will overwrite the current database. Continue?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if confirm != QMessageBox.Yes:
            return

        try:
            restore_database(path)
        except Exception as exc:  # pragma: no cover - I/O heavy
            QMessageBox.critical(self, "Restore Failed", str(exc))
            self._set_status("Restore failed.", error=True)
            return

        self._set_status("Database restored from backup.")
        QMessageBox.information(
            self,
            "Restore Complete",
            "Database restored successfully. Please restart the application to ensure all data is reloaded.",
        )

    def _on_regenerate_pdfs(self):
        start_dir = self.pdf_dir_input.text().strip() or os.getcwd()
        output_dir = QFileDialog.getExistingDirectory(
            self,
            "Select folder for regenerated PDFs",
            os.path.abspath(start_dir),
        )
        if not output_dir:
            return

        try:
            pdf_paths = regenerate_all_pdfs(output_dir)
        except Exception as exc:  # pragma: no cover - heavy I/O
            QMessageBox.critical(self, "Regeneration Failed", str(exc))
            self._set_status("PDF regeneration failed.", error=True)
            return

        self._set_status("PDF regeneration complete.")
        QMessageBox.information(
            self,
            "PDFs Ready",
            f"Regenerated {len(pdf_paths)} invoices into:\n{output_dir}",
        )

    # ------------------------------------------------------------------ #
    # Security actions
    # ------------------------------------------------------------------ #
    def _update_password_status(self):
        if is_password_protected():
            self.password_status_label.setText("Status: Password Protected 🔒")
            self.password_status_label.setStyleSheet("color: green; font-weight: bold;")
        else:
            self.password_status_label.setText("Status: No Password Set 🔓")
            self.password_status_label.setStyleSheet("color: orange; font-weight: bold;")

    def _on_change_password(self):
        # If currently protected, ask for old password
        if is_password_protected():
            old_pw, ok = QInputDialog.getText(self, "Security", "Enter current password:", QLineEdit.Password)
            if not ok:
                return
            if not verify_app_password(old_pw):
                QMessageBox.warning(self, "Security", "Incorrect password.")
                return

        new_pw, ok = QInputDialog.getText(self, "Security", "Enter new password (leave empty to remove):", QLineEdit.Password)
        if not ok:
            return
        
        if new_pw:
            confirm_pw, ok = QInputDialog.getText(self, "Security", "Confirm new password:", QLineEdit.Password)
            if not ok:
                return
            if new_pw != confirm_pw:
                QMessageBox.warning(self, "Security", "Passwords do not match.")
                return
        
        set_app_password(new_pw)
        self._update_password_status()
        msg = "Password updated." if new_pw else "Password removed."
        self._set_status(msg)
        QMessageBox.information(self, "Security", msg)

    # ------------------------------------------------------------------ #
    # Import / Export actions
    # ------------------------------------------------------------------ #
    def _on_export_data(self, table_name: str):
        path, _ = QFileDialog.getSaveFileName(
            self,
            f"Export {table_name.capitalize()}",
            f"{table_name}.csv",
            "CSV Files (*.csv);;All Files (*)"
        )
        if not path:
            return
            
        try:
            export_to_csv(table_name, path)
            self._set_status(f"Exported {table_name} successfully.")
            QMessageBox.information(self, "Export", f"Successfully exported {table_name} to {path}")
        except Exception as e:
            self._set_status(f"Export failed: {e}", error=True)
            QMessageBox.critical(self, "Export Failed", str(e))

    def _on_import_customers(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Import Customers CSV",
            "",
            "CSV Files (*.csv);;All Files (*)"
        )
        if not path:
            return
            
        try:
            count = import_customers_from_csv(path)
            self._set_status(f"Imported {count} customers.")
            QMessageBox.information(self, "Import", f"Successfully imported/updated {count} customers.")
        except Exception as e:
            self._set_status(f"Import failed: {e}", error=True)
            QMessageBox.critical(self, "Import Failed", str(e))

    def _on_import_products(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Import Products CSV",
            "",
            "CSV Files (*.csv);;All Files (*)"
        )
        if not path:
            return
            
        try:
            count = import_products_from_csv(path)
            self._set_status(f"Imported {count} products.")
            QMessageBox.information(self, "Import", f"Successfully imported/updated {count} products.")
        except Exception as e:
            self._set_status(f"Import failed: {e}", error=True)
            QMessageBox.critical(self, "Import Failed", str(e))


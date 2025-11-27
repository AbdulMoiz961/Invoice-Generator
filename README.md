# Invoice Generator

A modern, desktop-based Invoice Generator application built with Python and PySide6.

## Features

- **Dashboard**: View key metrics like total sales, monthly revenue, and recent invoices.
- **Invoice Management**: Create, view, and delete invoices. Generates professional PDFs.
- **Customer Management**: Manage customer details (Name, Address, NTN, STRN).
- **Product Management**: Manage products/services with SKU, Barcode, and Tax rates.
- **Reports**: View sales reports by date range and export data.
- **Settings**: Configure company profile, invoice numbering, and application security.
- **Data Portability**: Import/Export customers and products via CSV. Backup/Restore database.
- **Security**: Optional password protection for settings.

## Installation

### Running from Source

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/yourusername/invoice-generator.git
    cd invoice-generator
    ```

2.  **Create a virtual environment**:
    ```bash
    python -m venv .venv
    # Windows
    .venv\Scripts\activate
    # Linux/Mac
    source .venv/bin/activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

4.  **Run the application**:
    ```bash
    python src/main.py
    ```

### Building the Executable

To build a standalone `.exe` file:

```bash
pip install pyinstaller
python build_exe.py
```

The executable will be located in `dist/InvoiceGenerator/InvoiceGenerator.exe`.

## Project Structure

- `src/`: Source code.
  - `ui/`: UI components (PySide6 widgets).
  - `db.py`: Database access layer (SQLite).
  - `pdfgen.py`: PDF generation logic (ReportLab).
  - `settings_manager.py`: Settings and configuration management.
- `data/`: Database and generated PDFs (ignored in git).
- `tests/`: Unit tests.

## Contributing

1.  Fork the repository.
2.  Create a feature branch (`git checkout -b feature/AmazingFeature`).
3.  Commit your changes (`git commit -m 'Add some AmazingFeature'`).
4.  Push to the branch (`git push origin feature/AmazingFeature`).
5.  Open a Pull Request.

## License

Distributed under the MIT License. See `LICENSE` for more information.

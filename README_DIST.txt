DISTRIBUTION INSTRUCTIONS
=========================

1. Executable Application
-------------------------
The standalone application has been built and is located in:
  dist/InvoiceGenerator/InvoiceGenerator.exe

You can zip the 'dist/InvoiceGenerator' folder and distribute it as a portable application.

2. Installer (Optional)
-----------------------
To create a professional Windows installer (.exe setup file):
1. Download and install Inno Setup (https://jrsoftware.org/isdl.php).
2. Open the 'setup.iss' file located in the project root with Inno Setup.
3. Click "Compile".
4. The installer will be generated in the 'installer' directory.

3. Data Portability
-------------------
- The application supports exporting Customers, Products, and Invoices to CSV.
- It supports importing Customers and Products from CSV.
- Database backups can be created and restored from the Settings tab.

4. Security
-----------
- You can set an application password in the Settings tab.
- If set, the password will be required to access the Settings tab.

5. Logging
----------
- Logs are stored in 'data/logs/app.log'.

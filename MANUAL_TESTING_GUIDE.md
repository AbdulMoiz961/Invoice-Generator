# Invoice Generator - Manual Testing Guide

This guide provides a step-by-step approach to manually testing the Invoice Generator application to ensure all features work as intended.

## 1. Setup and Launch
*   **Objective**: Verify the application starts correctly.
*   **Steps**:
    1.  Open your terminal.
    2.  Navigate to the project directory: `e:\CS\PROJECTS\Invoice Generator\inv-gen`.
    3.  Run the application: `python -m src.main`.
*   **Expected Result**: The application window opens, displaying the Dashboard by default. The sidebar navigation is visible on the left.

## 2. Settings & Company Profile (CRITICAL FIRST STEP)
*   **Objective**: Ensure company details can be saved, as they are required for generating invoices.
*   **Steps**:
    1.  Click on **Settings** in the sidebar.
    2.  **Company Profile**:
        *   Enter "Test Company" in **Legal Name**.
        *   Enter an address in **Mailing Address**.
        *   Enter contact info, NTN, and STRN.
        *   Click **Save Company Profile**.
    3.  **Preferences**:
        *   Set **Invoice Prefix** (e.g., "INV-").
        *   Set **Next Number** (e.g., 1001).
        *   Select a **PDF Output Folder** (create a temporary folder if needed).
        *   Check **Open PDF after saving invoice**.
        *   Click **Save Preferences**.
*   **Expected Result**: Success messages appear. Data persists if you navigate away and come back.

## 3. Customer Management
*   **Objective**: Verify adding and managing customers.
*   **Steps**:
    1.  Click on **Customers** in the sidebar.
    2.  **Add Customer**:
        *   Fill in Name (e.g., "John Doe"), Email, Phone, Address.
        *   Click **Add Customer**.
    3.  **Verify List**: The new customer should appear in the table on the right.
    4.  **Edit Customer**:
        *   Select "John Doe" from the table.
        *   Change the Phone number.
        *   Click **Update Customer**.
        *   Verify the change in the table.
    5.  **Search**: Type "John" in the search bar. Verify the list filters correctly.

## 4. Product Management
*   **Objective**: Verify adding and managing products.
*   **Steps**:
    1.  Click on **Products** in the sidebar.
    2.  **Add Product**:
        *   Fill in Name (e.g., "Widget A").
        *   Set Unit Price (e.g., 100).
        *   Set Tax Rate (e.g., 10).
        *   Click **Add Product**.
    3.  **Verify List**: The new product should appear in the table.
    4.  **Edit Product**:
        *   Select "Widget A".
        *   Change Price to 150.
        *   Click **Update Product**.
        *   Verify the change in the table.

## 5. Invoice Generation (Core Feature)
*   **Objective**: Create an invoice and verify calculations and PDF generation.
*   **Steps**:
    1.  Click on **New Invoice** in the sidebar.
    2.  **Header**:
        *   Check if **Invoice No** is auto-populated (based on Settings).
        *   Select "John Doe" from the **Customer** dropdown.
        *   Verify that customer details (NTN/STRN) appear below the dropdown.
        *   Enter "New York" in **Shipped To**.
    3.  **Add Items**:
        *   Select "Widget A" from the **Product** dropdown.
        *   Enter Qty: 2.
        *   Click **Add Item**.
    4.  **Verify Calculations** (in the table row):
        *   Unit Price: 150
        *   Value: 300 (2 * 150)
        *   Sales Tax: 30 (10% of 300)
        *   Advance Tax: 1.5 (0.5% of 300 - default rate)
        *   Total: 331.5
    5.  **Totals Panel**: Verify the Grand Total matches the sum of the table rows.
    6.  **Save**:
        *   Click **Save Invoice**.
        *   A confirmation popup should appear.
        *   If "Open PDF" was checked in settings, the PDF should open automatically.
    7.  **PDF Check**:
        *   Inspect the generated PDF.
        *   Ensure Company Name, Customer Name, Items, and Totals are correct.

## 6. Reports & Analytics
*   **Objective**: Verify data visualization.
*   **Steps**:
    1.  Click on **Reports** in the sidebar.
    2.  Check if the charts (Sales over time, Top products) reflect the invoice you just created.
    3.  Use the **Date Range** filter (if available) to test filtering.

## 7. Dashboard
*   **Objective**: Verify the overview.
*   **Steps**:
    1.  Click on **Dashboard**.
    2.  Verify that **Total Sales**, **Total Invoices**, etc., have updated to reflect the new invoice.

## 8. Security (Optional)
*   **Objective**: Test password protection for Settings.
*   **Steps**:
    1.  Go to **Settings**.
    2.  Click **Change Password**.
    3.  Set a password.
    4.  Navigate to Dashboard and back to Settings.
    5.  **Expected Result**: You should be prompted for a password to enter Settings.

## 9. Data Persistence & Backup
*   **Objective**: Ensure data is safe.
*   **Steps**:
    1.  Close the application.
    2.  Relaunch it.
    3.  Check **Customers**, **Products**, and **Reports** to ensure data is still there.
    4.  **Backup**:
        *   Go to **Settings**.
        *   Click **Backup Database**.
        *   Save the file.
    5.  **Restore** (Caution: this overwrites current data):
        *   Click **Restore Database** and select the backup file.
        *   Restart app and verify data.

## 10. UI Responsiveness
*   **Objective**: Test the fix for the window overflow issue.
*   **Steps**:
    1.  Maximize the window.
    2.  Resize the window to be smaller than the content.
    3.  **Expected Result**: Scrollbars should appear, allowing you to view all content.

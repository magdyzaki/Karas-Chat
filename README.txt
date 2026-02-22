Smart CRM - Generated Project
============================

How to use:
1. Install dependencies:
   pip install PyQt5 pandas fpdf openpyxl

2. (Optional) Place Arabic font Amiri in:
   ./fonts/Amiri-Regular.ttf
   The export PDF will use it if available.

3. Initialize the database (creates database and tables):
   python setup_db.py

4. Run the app:
   python MainWindow.py

Notes:
- This is a functional baseline scaffold implementing the pages we agreed on:
  Customers, Products, Sales, Invoices, Reports, Settings, SmartFriend.
- The Sales page stores sale_date automatically and uses a manual exchange rate field.
- Export to PDF will ask where to save the file (file dialog).

# pages/InvoicesPage.py
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QHBoxLayout, QLineEdit, QPushButton,
    QComboBox, QTableWidget, QTableWidgetItem, QMessageBox, QFileDialog,
    QDialog, QScrollArea, QInputDialog
)
from PyQt5.QtGui import QFont, QPixmap, QPainter, QColor
from PyQt5.QtCore import Qt, QDateTime
import sqlite3, os
import pandas as pd
from fpdf import FPDF

# ==================== المسارات ====================
DB = os.path.join(os.path.dirname(__file__), "..", "database", "crm.db")
FONTS_FOLDER = os.path.join(os.path.dirname(__file__), "..", "fonts")
LETTERHEAD_PATH = os.path.join(os.path.dirname(__file__), "..", "assets", "letterhead.png")
DEJAVU_TTF = os.path.join(FONTS_FOLDER, "DejaVuSans.ttf")
AMIRI_TTF = os.path.join(FONTS_FOLDER, "Amiri-Regular.ttf")

# ==================== نافذة المعاينة ====================
class InvoicePreviewDialog(QDialog):
    def __init__(self, pixmap, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Invoice Preview")
        # نافذة قابلة للتكبير، حجم افتراضي مناسب
        self.resize(850, 1100)
        layout = QVBoxLayout(self)
        scroll = QScrollArea(self)
        label = QLabel()
        label.setPixmap(pixmap)
        label.setAlignment(Qt.AlignCenter)
        scroll.setWidget(label)
        scroll.setWidgetResizable(True)
        layout.addWidget(scroll)
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn, alignment=Qt.AlignCenter)

# ==================== صفحة الفواتير ====================
class InvoicesPage(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("background-color: #FFFDF5;")
        self.invoice_items = []
        self.save_folder = os.path.join(os.path.dirname(__file__), "..", "exports", "invoices")
        os.makedirs(self.save_folder, exist_ok=True)
        self.init_ui()
        self.load_settings()

    def init_ui(self):
        main = QVBoxLayout()

        title = QLabel("🧾 Invoices / إدارة الفواتير")
        title.setFont(QFont("Amiri", 18, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        main.addWidget(title)

        # 🔹 الحقول العلوية
        top_row = QHBoxLayout()
        self.invoice_number_input = QLineEdit()
        self.invoice_number_input.setPlaceholderText("Invoice No (manual)")
        self.currency_combo = QComboBox(); self.currency_combo.addItems(["EGP", "USD"])
        self.language_combo = QComboBox(); self.language_combo.addItems(["English", "العربية"])
        self.save_folder_btn = QPushButton("Choose save folder")
        self.save_folder_btn.clicked.connect(self.choose_save_folder)
        for lbl, widget in [("Invoice No:", self.invoice_number_input),
                            ("Currency:", self.currency_combo),
                            ("Language:", self.language_combo),
                            ("", self.save_folder_btn)]:
            if lbl:
                top_row.addWidget(QLabel(lbl))
            top_row.addWidget(widget)
        main.addLayout(top_row)

        # 🔹 استيراد المبيعات
        import_row = QHBoxLayout()
        self.sales_combo = QComboBox()
        self.reload_sales_button = QPushButton("Load sales")
        self.reload_sales_button.clicked.connect(self.load_sales_list)
        self.add_sale_btn = QPushButton("Add sale to invoice")
        self.add_sale_btn.clicked.connect(self.add_selected_sale_to_invoice)
        import_row.addWidget(QLabel("Import from sales:"))
        import_row.addWidget(self.sales_combo)
        import_row.addWidget(self.reload_sales_button)
        import_row.addWidget(self.add_sale_btn)
        main.addLayout(import_row)

        # 🔹 جدول الفاتورة
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "Sale ID", "Customer", "Code", "Product", "Unit", "Qty", "Price", "Total"
        ])
        self.table.horizontalHeader().setStretchLastSection(True)
        main.addWidget(self.table)

        # 🔹 أزرار التحكم (ملونة كما طلبت)
        buttons_row = QHBoxLayout()
        self.remove_item_btn = QPushButton("Remove item")
        self.remove_item_btn.clicked.connect(self.remove_selected_item)
        self.clear_items_btn = QPushButton("Clear items")
        self.clear_items_btn.clicked.connect(self.clear_items)
        self.preview_btn = QPushButton("Preview invoice")
        self.preview_btn.clicked.connect(self.preview_invoice)
        self.export_pdf_btn = QPushButton("Export PDF")
        self.export_pdf_btn.clicked.connect(self.export_pdf)
        self.export_excel_btn = QPushButton("Export Excel")
        self.export_excel_btn.clicked.connect(self.export_excel)

        # ألوان الأزرار
        self.remove_item_btn.setStyleSheet("background-color:#E53935;color:white;")
        self.clear_items_btn.setStyleSheet("background-color:#9C27B0;color:white;")
        self.preview_btn.setStyleSheet("background-color:#03A9F4;color:white;")
        self.export_pdf_btn.setStyleSheet("background-color:#4CAF50;color:white;")
        self.export_excel_btn.setStyleSheet("background-color:#FF9800;color:white;")

        for b in [self.remove_item_btn, self.clear_items_btn, self.preview_btn,
                  self.export_pdf_btn, self.export_excel_btn]:
            b.setFont(QFont("Amiri", 12, QFont.Bold))
            b.setFixedHeight(40)
            buttons_row.addWidget(b)
        main.addLayout(buttons_row)

        # 🔹 الإجمالي
        summary_row = QHBoxLayout()
        self.total_label = QLabel("Total: 0.00")
        self.total_label.setFont(QFont("Amiri", 14, QFont.Bold))
        summary_row.addStretch()
        summary_row.addWidget(self.total_label)
        main.addLayout(summary_row)

        # 🔹 أزرار الإعدادات (شروط الدفع ومعلومات البنك)
        settings_row = QHBoxLayout()
        self.payment_terms_btn = QPushButton("Payment Terms (edit)")
        self.payment_terms_btn.clicked.connect(self.edit_payment_terms)
        self.bank_details_btn = QPushButton("Bank Details (edit)")
        self.bank_details_btn.clicked.connect(self.edit_bank_details)
        settings_row.addWidget(self.payment_terms_btn)
        settings_row.addWidget(self.bank_details_btn)
        main.addLayout(settings_row)

        self.setLayout(main)
        self.load_sales_list()

    # ========= قواعد البيانات =========
    def db_conn(self): return sqlite3.connect(DB)

    def choose_save_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Choose save folder", self.save_folder)
        if folder: self.save_folder = folder

    def load_sales_list(self):
        try:
            self.sales_combo.clear()
            conn = self.db_conn(); cur = conn.cursor()
            cur.execute("SELECT id, customer_name, product_name, sale_date FROM sales ORDER BY id DESC")
            rows = cur.fetchall()
            if not rows: self.sales_combo.addItem("No sales", None)
            else:
                for r in rows:
                    self.sales_combo.addItem(f"{r[0]} | {r[1]} | {r[2]} | {r[3]}", r[0])
            conn.close()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load sales:\n{e}")

    # ========= إدارة الفاتورة =========
    def add_selected_sale_to_invoice(self):
        sale_id = self.sales_combo.currentData()
        if not sale_id:
            QMessageBox.warning(self, "Warning", "Choose a sale first.")
            return
        try:
            conn = self.db_conn(); cur = conn.cursor()
            cur.execute("""
                SELECT id, customer_name, product_code, product_name, unit, quantity,
                       price_egp, price_usd FROM sales WHERE id=?
            """, (sale_id,))
            row = cur.fetchone(); conn.close()
            if not row: return
            sid, cust_name, code, pname, unit, qty, pegp, pusd = row
            curr = self.currency_combo.currentText()
            price = float(pegp) if curr == "EGP" else float(pusd)
            total = round(float(qty) * price, 2)
            self.invoice_items.append({
                "sale_id": sid, "customer_name": cust_name, "product_code": code,
                "product_name": pname, "unit": unit, "quantity": float(qty),
                "price": price, "total": total
            })
            self.refresh_invoice_table()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Add failed:\n{e}")

    def refresh_invoice_table(self):
        self.table.setRowCount(0)
        for it in self.invoice_items:
            r = self.table.rowCount(); self.table.insertRow(r)
            for i, val in enumerate([
                it.get("sale_id"), it.get("customer_name"), it.get("product_code"),
                it.get("product_name"), it.get("unit"), it.get("quantity"),
                self.format_money(it.get("price")), self.format_money(it.get("total"))
            ]):
                item = QTableWidgetItem(str(val))
                item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(r, i, item)
        self.update_totals()

    def remove_selected_item(self):
        row = self.table.currentRow()
        if row >= 0:
            del self.invoice_items[row]
            self.refresh_invoice_table()

    def clear_items(self):
        self.invoice_items = []
        self.refresh_invoice_table()

    def update_totals(self):
        total = sum(it["total"] for it in self.invoice_items)
        self.total_label.setText(f"Total: {total:.2f} {self.currency_combo.currentText()}")

    def format_money(self, val):
        try:
            return f"{float(val):.2f}"
        except:
            return str(val)

    # ========= إعدادات الحفظ =========
    def load_settings(self):
        try:
            conn = self.db_conn(); cur = conn.cursor()
            cur.execute("SELECT value FROM settings WHERE key='payment_terms'")
            row = cur.fetchone()
            self.payment_terms = row[0] if row else ""
            cur.execute("SELECT value FROM settings WHERE key='bank_details'")
            row2 = cur.fetchone()
            self.bank_details = row2[0] if row2 else ""
            conn.close()
        except:
            self.payment_terms = ""
            self.bank_details = ""

    def save_setting(self, key, val):
        conn = self.db_conn(); cur = conn.cursor()
        cur.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, val))
        conn.commit(); conn.close()

    def edit_payment_terms(self):
        txt, ok = QInputDialog.getMultiLineText(self, "Edit Payment Terms", "Enter payment terms:", self.payment_terms)
        if ok:
            self.payment_terms = txt; self.save_setting("payment_terms", txt)

    def edit_bank_details(self):
        txt, ok = QInputDialog.getMultiLineText(self, "Edit Bank Details", "Enter bank details:", self.bank_details)
        if ok:
            self.bank_details = txt; self.save_setting("bank_details", txt)

    # ========= المعاينة =========
    def render_invoice_pixmap(self):
        # حجم A4 افتراضي بالبيكسل تقريبي (لتصوير المعاينة)
        base_w, base_h = 1240, 1754
        base = QPixmap(LETTERHEAD_PATH) if os.path.exists(LETTERHEAD_PATH) else QPixmap(base_w, base_h)
        base = base.scaled(base_w, base_h, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
        if base.isNull(): base.fill(QColor("white"))
        painter = QPainter(base)
        painter.setPen(QColor("#000000"))
        painter.setFont(QFont("Times New Roman", 12))

        x, y = 80, 140
        painter.setFont(QFont("Arial Black", 14))
        painter.drawText(x, y, f"Invoice No: {self.invoice_number_input.text() or ''}")
        y += 30
        painter.setFont(QFont("Times New Roman", 12))
        painter.drawText(x, y, f"Date: {QDateTime.currentDateTime().toString('yyyy-MM-dd hh:mm')}")
        y += 30
        if self.invoice_items:
            painter.drawText(x, y, f"Customer: {self.invoice_items[0]['customer_name']}")
            y += 40

        # جدول (رسم رؤوس وخط أفقي)
        painter.setFont(QFont("Times New Roman", 12, QFont.Bold))
        headers = ["Description", "Qty", "Price", "USD"]
        col_x = [x, x + 300, x + 450, x + 600]
        for i, h in enumerate(headers):
            painter.drawText(col_x[i], y, h)
        y += 10
        painter.drawLine(x, y, x + 700, y)
        y += 25
        painter.setFont(QFont("Times New Roman", 12))
        for it in self.invoice_items:
            painter.drawText(col_x[0], y, it["product_name"])
            painter.drawText(col_x[1], y, str(it["quantity"]))
            painter.drawText(col_x[2], y, self.format_money(it["price"]))
            painter.drawText(col_x[3], y, self.format_money(it["total"]))
            y += 20
        painter.end()
        return base

    def preview_invoice(self):
        if not self.invoice_items:
            QMessageBox.warning(self, "Warning", "No items to preview.")
            return
        pix = self.render_invoice_pixmap()
        dlg = InvoicePreviewDialog(pix, self)
        dlg.exec_()

    # ========= التصدير =========
    def export_pdf(self):
        if not self.invoice_items:
            QMessageBox.warning(self, "Warning", "No items to export.")
            return
        invoice_no = self.invoice_number_input.text() or QDateTime.currentDateTime().toString("yyyyMMddHHmmss")
        path, _ = QFileDialog.getSaveFileName(self, "Save PDF", os.path.join(self.save_folder, f"invoice_{invoice_no}.pdf"), "PDF Files (*.pdf)")
        if not path: return

        try:
            pdf = FPDF(unit='mm', format='A4')
            pdf.set_auto_page_break(auto=True, margin=15)
            pdf.add_page()

            # إذا وُجد letterhead، نطبعه كخلفية
            if os.path.exists(LETTERHEAD_PATH):
                try:
                    pdf.image(LETTERHEAD_PATH, x=0, y=0, w=210)
                except Exception:
                    # بعض الصيغ أو أحجام الصور قد تسبب مشاكل — لكن نتابع بدون فشل
                    pass

            # خطوط افتراضية (FPDF يحتاج خطوط مُثبتة لتدعم العربية؛ هنا نستخدم واجهة بسيطة)
            pdf.set_font("Arial", size=12)
            pdf.cell(0, 8, f"Invoice No: {invoice_no}", ln=True)
            pdf.cell(0, 8, f"Date: {QDateTime.currentDateTime().toString('yyyy-MM-dd hh:mm')}", ln=True)
            pdf.ln(6)

            # رأس الجدول
            pdf.set_font("Arial", size=11, style='B')
            pdf.cell(90, 8, "Description", 1)
            pdf.cell(30, 8, "Qty", 1)
            pdf.cell(35, 8, "Price", 1)
            pdf.cell(35, 8, "USD", 1, ln=True)

            pdf.set_font("Arial", size=11)
            for it in self.invoice_items:
                pdf.cell(90, 8, str(it["product_name"])[:40], 1)
                pdf.cell(30, 8, str(it["quantity"]), 1)
                pdf.cell(35, 8, self.format_money(it["price"]), 1)
                pdf.cell(35, 8, self.format_money(it["total"]), 1, ln=True)

            pdf.ln(4)
            total = sum(it["total"] for it in self.invoice_items)
            pdf.set_font("Arial", size=12, style='B')
            pdf.cell(0, 8, f"Total: {self.format_money(total)} {self.currency_combo.currentText()}", ln=True)

            pdf.output(path)
            QMessageBox.information(self, "Done", f"Saved PDF: {os.path.basename(path)}")
        except Exception as e:
            # أشهر سبب: أحرف عربية مع خط غير داعم -> نبلّغ المستخدم بوضوح
            QMessageBox.critical(self, "Failed To create PDF", f"{e}\n\nIf Arabic text causes errors, ensure a Unicode font (e.g. DejaVu or Amiri) is available in fonts/ and the fpdf add_font used.")

    def export_excel(self):
        if not self.invoice_items:
            QMessageBox.warning(self, "Warning", "No items to export.")
            return
        df = pd.DataFrame([{
            "sale_id": it.get("sale_id"),
            "customer": it.get("customer_name"),
            "product_code": it.get("product_code"),
            "product": it.get("product_name"),
            "unit": it.get("unit"),
            "quantity": it.get("quantity"),
            "price": it.get("price"),
            "total": it.get("total"),
        } for it in self.invoice_items])
        default_name = f"invoice_{self.invoice_number_input.text() or QDateTime.currentDateTime().toString('yyyyMMdd_HHmmss')}.xlsx"
        path, _ = QFileDialog.getSaveFileName(self, "Save Excel", os.path.join(self.save_folder, default_name), "Excel Files (*.xlsx)")
        if not path: return
        if not path.lower().endswith(".xlsx"):
            path += ".xlsx"
        try:
            df.to_excel(path, index=False)
            QMessageBox.information(self, "Done", f"Saved Excel: {os.path.basename(path)}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Export failed:\n{e}")
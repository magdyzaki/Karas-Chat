# pages/StockPage.py
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem,
    QHeaderView, QHBoxLayout, QLineEdit, QPushButton, QComboBox
)
from PyQt5.QtGui import QFont, QColor
from PyQt5.QtCore import Qt
import sqlite3, os
from fpdf import FPDF

DB = os.path.join(os.path.dirname(__file__), "..", "database", "crm.db")


class StockPage(QWidget):
    """ صفحة المخزون النهائية — تعمل 100% بدون فراغ """

    def __init__(self):
        super().__init__()
        # إزالة الستايل الثابت للسماح بتطبيق الستايل من MainWindow
        # self.setStyleSheet("background-color: #FFFBEA;")  # تم إزالة الستايل الثابت
        self.setFont(QFont("Amiri", 10))

        self.display_unit = "ton"  # افتراضي

        self.init_ui()
        self.load_stock()

    def db_conn(self):
        return sqlite3.connect(DB)

    def _table_columns(self, table_name):
        conn = self.db_conn()
        cur = conn.cursor()
        cur.execute(f"PRAGMA table_info({table_name})")
        rows = cur.fetchall()
        conn.close()
        return [r[1] for r in rows]

    # ======================================================================
    #                         واجهة المستخدم
    # ======================================================================
    def init_ui(self):
        layout = QVBoxLayout()

        title = QLabel("📦 صفحة المخزون — الكميات المتبقية")
        title.setFont(QFont("Amiri", 18, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # ---------------- شريط التحكم ----------------
        row = QHBoxLayout()

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("بحث باسم المنتج أو الكود…")
        self.search_input.textChanged.connect(self.filter_table)

        refresh_btn = QPushButton("🔄 تحديث")
        refresh_btn.clicked.connect(self.load_stock)

        pdf_btn = QPushButton("📄 PDF")
        pdf_btn.clicked.connect(self.export_pdf)

        # اختيار الوحدة
        self.unit_selector = QComboBox()
        self.unit_selector.addItems(["عرض بالطن", "عرض بالكيلو"])
        self.unit_selector.currentIndexChanged.connect(self.on_unit_change)

        row.addWidget(self.search_input)
        row.addWidget(refresh_btn)
        row.addWidget(pdf_btn)
        row.addWidget(self.unit_selector)

        layout.addLayout(row)

        # ---------------- جدول المخزون ----------------
        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels([
            "ID", "Product", "Unit", "Initial Qty",
            "Sold Qty", "Remaining", "Sold %"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setDefaultSectionSize(38)

        layout.addWidget(self.table)
        self.setLayout(layout)

    # ======================================================================
    #                 تغيير وحدة العرض (طن/كيلو)
    # ======================================================================
    def on_unit_change(self):
        self.display_unit = "ton" if self.unit_selector.currentIndex() == 0 else "kg"
        self.load_stock()

    # ======================================================================
    #                 دوال التحويل الذكي
    # ======================================================================
    def normalize_to_ton(self, qty, unit):
        try:
            qty = float(qty)
        except:
            return 0

        u = str(unit).lower()
        if u in ["طن", "ton", "tons"]:
            return qty
        if u in ["كم", "كجم", "كيلو", "kg"]:
            return qty / 1000
        return qty

    def normalize_to_kg(self, qty, unit):
        try:
            qty = float(qty)
        except:
            return 0

        u = str(unit).lower()
        if u in ["طن", "ton", "tons"]:
            return qty * 1000
        if u in ["كم", "كجم", "كيلو", "kg"]:
            return qty
        return qty

    # ======================================================================
    #                   حساب المباع من جدول Sales
    # ======================================================================
    def get_sold(self, pid, name):
        conn = self.db_conn()
        cur = conn.cursor()
        cur.execute("SELECT quantity, unit, product_id, product_name FROM sales")
        rows = cur.fetchall()
        conn.close()

        total = 0
        for q, u, pid2, pname in rows:
            if str(pid2) == str(pid) or pname == name:
                total += self.normalize_to_kg(q, u)  # نخزن بالكيلو دائماً

        return total

    # ======================================================================
    #                       تحميل البيانات الأساسية
    # ======================================================================
    def load_stock(self):
        self.table.setRowCount(0)

        prod_cols = self._table_columns("products")
        sales_cols = self._table_columns("sales")

        unit_col = next((u for u in ("unit", "unit_type", "uom") if u in prod_cols), None)
        name_col = "name" if "name" in prod_cols else "product_name"
        qty_col = next((c for c in ["quantity", "qty", "initial_qty"] if c in prod_cols), None)

        conn = self.db_conn()
        cur = conn.cursor()
        cur.execute(f"SELECT id, {name_col}, {qty_col} {', ' + unit_col if unit_col else ''} FROM products")
        products = cur.fetchall()
        conn.close()

        for row in products:
            if unit_col:
                pid, name, qty_raw, punit = row
            else:
                pid, name, qty_raw = row
                punit = ""

            initial_raw = float(qty_raw or 0)
            sold_raw = self.get_sold(pid, name)

            # التحويل الذكي
            initial_ton = self.normalize_to_ton(initial_raw, punit)
            sold_ton = sold_raw / 1000
            remaining_ton = initial_ton - sold_ton

            if self.display_unit == "ton":
                initial_c = initial_ton
                sold_c = sold_ton
                remaining = remaining_ton
            else:
                initial_c = initial_ton * 1000
                sold_c = sold_ton * 1000
                remaining = remaining_ton * 1000

            percent = (sold_c / initial_c * 100) if initial_c > 0 else 0

            self.add_row(pid, name, punit, initial_c, sold_c, remaining, percent)

    # ======================================================================
    #                       إضافة صف للجدول
    # ======================================================================
    def add_row(self, pid, name, unit, initial, sold, remaining, percent):
        r = self.table.rowCount()
        self.table.insertRow(r)

        values = [
            pid,
            name,
            unit,
            f"{initial:.2f}",
            f"{sold:.2f}",
            f"{remaining:.2f}",
            f"{percent:.1f}%"
        ]

        for c in range(7):
            item = QTableWidgetItem(str(values[c]))
            item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(r, c, item)

    # ======================================================================
    #                        الفلترة
    # ======================================================================
    def filter_table(self):
        q = self.search_input.text().lower()
        for r in range(self.table.rowCount()):
            name = self.table.item(r, 1).text().lower()
            pid = self.table.item(r, 0).text().lower()
            self.table.setRowHidden(r, q not in name and q not in pid)

    # ======================================================================
    #                        تصدير PDF
    # ======================================================================
    def export_pdf(self):
        try:
            from PyQt5.QtWidgets import QFileDialog, QMessageBox
            from PyQt5.QtCore import Qt
            
            # اختيار مكان الحفظ
            file_path, _ = QFileDialog.getSaveFileName(
                self, 
                "حفظ تقرير PDF", 
                "Stock_Report.pdf", 
                "PDF Files (*.pdf)"
            )
            
            if not file_path:
                return
            
            pdf = FPDF()
            pdf.add_page()
            # محاولة استخدام خط Amiri من مجلدات مختلفة
            font_paths = [
                os.path.join(os.path.dirname(__file__), "..", "fonts", "Amiri-Regular.ttf"),
                os.path.join(os.path.dirname(__file__), "..", "assets", "Amiri-Regular.ttf"),
                "Amiri-Regular.ttf"
            ]
            font_loaded = False
            for font_path in font_paths:
                if os.path.exists(font_path):
                    try:
                        pdf.add_font("Amiri", "", fname=font_path, uni=True)
                        pdf.set_font("Amiri", size=14)
                        font_loaded = True
                        break
                    except:
                        pass
            if not font_loaded:
                pdf.set_font("Arial", size=14)

            pdf.cell(0, 10, "تقرير المخزون", ln=1, align="C")

            for r in range(self.table.rowCount()):
                row_data = []
                for c in range(7):
                    item = self.table.item(r, c)
                    if item:
                        row_data.append(item.text())
                    else:
                        row_data.append("")
                pdf.cell(0, 8, " | ".join(row_data), ln=1)

            pdf.output(file_path)
            QMessageBox.information(self, "نجاح", f"تم حفظ التقرير بنجاح:\n{file_path}")
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"حدث خطأ أثناء تصدير PDF:\n{str(e)}")

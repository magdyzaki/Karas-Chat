from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QMessageBox
)
from PyQt5.QtGui import QFont, QColor
from PyQt5.QtCore import Qt
import sqlite3, os
from fpdf import FPDF

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "database", "crm.db")

class InventoryPage(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("background-color: #FFFBEA;")
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignTop)

        # 🔹 العنوان
        title = QLabel("📦 إدارة المخزون")
        title.setFont(QFont("Amiri", 20, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #444; margin: 10px;")
        layout.addWidget(title)

        # 🔹 الأزرار
        btn_layout = QHBoxLayout()
        self.refresh_btn = QPushButton("🔄 تحديث")
        self.refresh_btn.setStyleSheet("background-color:#FFD700;color:black;")
        self.refresh_btn.setFont(QFont("Amiri", 12, QFont.Bold))
        self.refresh_btn.setFixedHeight(40)
        self.refresh_btn.clicked.connect(self.load_data)

        self.export_btn = QPushButton("📄 تصدير PDF")
        self.export_btn.setStyleSheet("background-color:#BA68C8;color:white;")
        self.export_btn.setFont(QFont("Amiri", 12, QFont.Bold))
        self.export_btn.setFixedHeight(40)
        self.export_btn.clicked.connect(self.export_to_pdf)

        btn_layout.addWidget(self.refresh_btn)
        btn_layout.addWidget(self.export_btn)
        layout.addLayout(btn_layout)

        # 🔹 الجدول
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "ID", "اسم المنتج", "الوصف", "الكمية المتبقية", "الوحدة", "حالة المخزون"
        ])
        self.table.setStyleSheet("""
            QHeaderView::section {
                background-color: #E0E0E0;
                color: #000;
                font-weight: bold;
                padding: 6px;
                border: none;
            }
            QTableWidget {
                background-color: #FFFFFF;
                gridline-color: #CCC;
                font-family: 'Amiri';
            }
            QTableWidget::item:selected {
                background-color: #FFF176;
                color: #000;
            }
        """)
        layout.addWidget(self.table)
        self.setLayout(layout)

        # تحميل البيانات
        self.load_data()

    # =============================
    # 🔹 تحميل بيانات المخزون
    # =============================
    def load_data(self):
        self.table.setRowCount(0)
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT id, name, description, quantity, unit FROM products")
        rows = c.fetchall()
        conn.close()

        for row_data in rows:
            row = self.table.rowCount()
            self.table.insertRow(row)
            for col, data in enumerate(row_data):
                item = QTableWidgetItem(str(data))
                item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(row, col, item)

            # 🔹 حالة المخزون بالألوان
            qty = float(row_data[3]) if row_data[3] else 0
            status_item = QTableWidgetItem()
            if qty <= 5:
                status_item.setText("⚠️ منخفض جدًا")
                status_item.setBackground(QColor("#F44336"))  # أحمر
                status_item.setForeground(QColor("#FFF"))
            elif qty <= 20:
                status_item.setText("🟡 متوسط")
                status_item.setBackground(QColor("#FFEB3B"))  # أصفر
            else:
                status_item.setText("🟢 جيد")
                status_item.setBackground(QColor("#4CAF50"))  # أخضر
                status_item.setForeground(QColor("#FFF"))

            self.table.setItem(row, 5, status_item)

        # 🔔 تنبيه تلقائي عند وجود كميات منخفضة
        low_items = [r[1] for r in rows if float(r[3]) <= 5]
        if low_items:
            QMessageBox.warning(
                self, "تنبيه المخزون",
                f"⚠️ المنتجات التالية منخفضة الكمية:\n" + "\n".join(low_items)
            )

    # =============================
    # 📄 تصدير تقرير PDF
    # =============================
    def export_to_pdf(self):
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT name, description, quantity, unit FROM products")
        rows = c.fetchall()
        conn.close()

        if not rows:
            QMessageBox.information(self, "تنبيه", "لا توجد بيانات لتصديرها.")
            return

        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", "B", 16)
        pdf.cell(200, 10, "تقرير المخزون - KARAS CRM", ln=True, align="C")
        pdf.set_font("Arial", "", 12)
        pdf.cell(200, 10, "", ln=True)

        for name, desc, qty, unit in rows:
            status = "⚠️ منخفض" if float(qty) <= 5 else ("🟡 متوسط" if float(qty) <= 20 else "🟢 جيد")
            pdf.cell(0, 8, f"اسم المنتج: {name} | الكمية: {qty} {unit} | الحالة: {status}", ln=True)

        file_path = os.path.join(os.path.dirname(__file__), "..", "reports", "inventory_report.pdf")
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        pdf.output(file_path)
        QMessageBox.information(self, "تم", f"📄 تم إنشاء التقرير بنجاح:\n{file_path}")
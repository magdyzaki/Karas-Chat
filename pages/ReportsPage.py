from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QComboBox
)
from PyQt5.QtGui import QFont, QColor
from PyQt5.QtCore import Qt
import sqlite3, os

DB = os.path.join(os.path.dirname(__file__), "..", "database", "crm.db")


class ReportsPage(QWidget):
    def __init__(self):
        super().__init__()

        # إزالة الستايل الثابت للسماح بتطبيق الستايل من MainWindow
        # self.setStyleSheet("...")  # تم إزالة الستايل الثابت

        main_layout = QVBoxLayout()
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(15, 15, 15, 15)

        # ================== العنوان ==================
        title = QLabel("📊 صفحة التقارير")
        title.setFont(QFont("Amiri", 22, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title)

        # ================== شريط الفلاتر ==================
        filter_layout = QHBoxLayout()
        filter_layout.setSpacing(10)

        self.report_type = QComboBox()
        self.report_type.addItems([
            "تقرير المبيعات",
            "تقرير العملاء",
            "تقرير المخزون"
        ])
        self.report_type.setFont(QFont("Amiri", 12))

        self.refresh_btn = QPushButton("🔄 تحديث التقرير")
        self.refresh_btn.setFont(QFont("Amiri", 12, QFont.Bold))
        self.refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                padding: 8px 16px;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #1E88E5;
            }
        """)

        filter_layout.addWidget(self.report_type)
        filter_layout.addWidget(self.refresh_btn)
        filter_layout.addStretch()

        main_layout.addLayout(filter_layout)

        # ================== الجدول ==================
        self.table = QTableWidget()
        self.table.setFont(QFont("Amiri", 11))
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setStyleSheet("""
            QHeaderView::section {
                background-color: #444;
                color: white;
                padding: 6px;
                font-weight: bold;
            }
            QTableWidget {
                gridline-color: #ddd;
                margin-top: 10px;
            }
        """)

        main_layout.addWidget(self.table)
        self.setLayout(main_layout)

        # ================== ربط الأحداث ==================
        self.refresh_btn.clicked.connect(self.load_report)
        self.report_type.currentIndexChanged.connect(self.load_report)

        # تحميل مبدئي
        self.load_report()

    # ================== DB ==================
    def connect_db(self):
        return sqlite3.connect(DB)

    # ================== تحميل التقرير ==================
    def load_report(self):
        try:
            report = self.report_type.currentText()

            if report == "تقرير المبيعات":
                self.load_sales_report()
            elif report == "تقرير العملاء":
                self.load_customers_report()
            elif report == "تقرير المخزون":
                self.load_stock_report()
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"حدث خطأ أثناء تحميل التقرير:\n{str(e)}")

    # ================== تقرير المبيعات ==================
    def load_sales_report(self):
        try:
            self.table.setColumnCount(6)
            self.table.setHorizontalHeaderLabels([
                "ID", "العميل", "المنتج",
                "الكمية", "الإجمالي جنيه", "التاريخ"
            ])
            self.table.setRowCount(0)

            conn = self.connect_db()
            cur = conn.cursor()
            cur.execute("""
                SELECT id, customer_name, product_name,
                       quantity, total_egp, sale_date
                FROM sales
                ORDER BY sale_date DESC
            """)
            rows = cur.fetchall()
            conn.close()

            for row_data in rows:
                r = self.table.rowCount()
                self.table.insertRow(r)
                for c, val in enumerate(row_data):
                    item = QTableWidgetItem(str(val))
                    item.setTextAlignment(Qt.AlignCenter)
                    self.table.setItem(r, c, item)
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"حدث خطأ أثناء تحميل تقرير المبيعات:\n{str(e)}")

    # ================== تقرير العملاء ==================
    def load_customers_report(self):
        try:
            self.table.setColumnCount(6)
            self.table.setHorizontalHeaderLabels([
                "ID", "الاسم", "الدولة",
                "الشركة", "التقييم", "تاريخ الإضافة"
            ])
            self.table.setRowCount(0)

            conn = self.connect_db()
            cur = conn.cursor()
            cur.execute("""
                SELECT id, name, country, company, rating, created_at
                FROM customers
                ORDER BY created_at DESC
            """)
            rows = cur.fetchall()
            conn.close()

            for row_data in rows:
                r = self.table.rowCount()
                self.table.insertRow(r)
                for c, val in enumerate(row_data):
                    item = QTableWidgetItem(str(val))
                    item.setTextAlignment(Qt.AlignCenter)

                    # ألوان حسب التقييم
                    if c == 4:
                        rating = str(val).lower()
                        if rating == "hot":
                            item.setBackground(QColor("#C8E6C9"))
                        elif rating == "warm":
                            item.setBackground(QColor("#FFF9C4"))
                        elif rating == "cold":
                            item.setBackground(QColor("#BBDEFB"))
                        else:
                            item.setBackground(QColor("#FFCDD2"))

                    self.table.setItem(r, c, item)
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"حدث خطأ أثناء تحميل تقرير العملاء:\n{str(e)}")

    # ================== تقرير المخزون ==================
    def load_stock_report(self):
        try:
            self.table.setColumnCount(4)
            self.table.setHorizontalHeaderLabels([
                "ID", "المنتج", "الكمية", "الوحدة"
            ])
            self.table.setRowCount(0)

            conn = self.connect_db()
            cur = conn.cursor()
            cur.execute("""
                SELECT id, name, quantity, unit
                FROM products
                ORDER BY name
            """)
            rows = cur.fetchall()
            conn.close()

            for row_data in rows:
                r = self.table.rowCount()
                self.table.insertRow(r)
                for c, val in enumerate(row_data):
                    item = QTableWidgetItem(str(val))
                    item.setTextAlignment(Qt.AlignCenter)
                    self.table.setItem(r, c, item)
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"حدث خطأ أثناء تحميل تقرير المخزون:\n{str(e)}")

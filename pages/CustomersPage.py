from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem,
    QMessageBox, QHeaderView, QComboBox
)
from PyQt5.QtGui import QFont, QColor
from PyQt5.QtCore import Qt
import sqlite3
import os
from datetime import datetime


DB = os.path.join(os.path.dirname(__file__), "..", "database", "crm.db")


class CustomersPage(QWidget):
    def __init__(self):
        super().__init__()

        # ==================== Layout الأساسي ====================
        # إزالة الستايل الثابت للسماح بتطبيق الستايل من MainWindow
        # self.setStyleSheet("background-color:#FFFDF5;")  # تم إزالة الستايل الثابت
        main_layout = QVBoxLayout()
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(15, 15, 15, 15)

        title = QLabel("👥 إدارة العملاء")
        title.setFont(QFont("Amiri", 20, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title)

        # ==================== حقول الإدخال ====================
        form_layout = QHBoxLayout()
        form_layout.setSpacing(10)

        # إزالة الستايل الثابت للسماح بتطبيق الستايل من MainWindow
        input_style = """
        QLineEdit, QComboBox {
            padding: 8px 10px;
            margin: 4px;
            border-radius: 8px;
        }
        """

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("اسم العميل")

        self.country_input = QLineEdit()
        self.country_input.setPlaceholderText("الدولة")

        self.company_input = QLineEdit()
        self.company_input.setPlaceholderText("الشركة")

        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("الإيميل")

        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText("الهاتف")

        self.rating_combo = QComboBox()
        self.rating_combo.addItems(["Hot", "Warm", "Cold", "Not Suitable"])

        for widget in [
            self.name_input, self.country_input, self.company_input,
            self.email_input, self.phone_input, self.rating_combo
        ]:
            widget.setFont(QFont("Amiri", 12))
            widget.setStyleSheet(input_style)
            form_layout.addWidget(widget)

        main_layout.addLayout(form_layout)

        # ==================== الأزرار ====================
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(12)

        base_btn_style = """
        QPushButton {
            padding: 10px 18px;
            margin: 6px;
            border-radius: 10px;
            font-weight: bold;
            color: white;
        }
        """

        self.add_btn = QPushButton("➕ إضافة")
        self.add_btn.setStyleSheet(base_btn_style + """
            QPushButton { background-color:#4CAF50; }
            QPushButton:hover { background-color:#43A047; }
            QPushButton:pressed { background-color:#2E7D32; }
        """)

        self.edit_btn = QPushButton("✏️ تعديل")
        self.edit_btn.setStyleSheet(base_btn_style + """
            QPushButton { background-color:#2196F3; }
            QPushButton:hover { background-color:#1E88E5; }
            QPushButton:pressed { background-color:#1565C0; }
        """)

        self.delete_btn = QPushButton("🗑️ حذف")
        self.delete_btn.setStyleSheet(base_btn_style + """
            QPushButton { background-color:#F44336; }
            QPushButton:hover { background-color:#E53935; }
            QPushButton:pressed { background-color:#C62828; }
        """)

        self.clear_btn = QPushButton("♻️ مسح")
        self.clear_btn.setStyleSheet(base_btn_style + """
            QPushButton { background-color:#9C27B0; }
            QPushButton:hover { background-color:#8E24AA; }
            QPushButton:pressed { background-color:#6A1B9A; }
        """)

        for btn in [self.add_btn, self.edit_btn, self.delete_btn, self.clear_btn]:
            btn.setMinimumHeight(42)
            buttons_layout.addWidget(btn)

        main_layout.addLayout(buttons_layout)

        # ==================== الجدول ====================
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "ID", "الاسم", "الدولة", "الشركة",
            "الإيميل", "الهاتف", "التقييم", "تاريخ الإضافة"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setStyleSheet("""
            QTableWidget {
                margin-top: 10px;
                gridline-color: #ddd;
            }
        """)

        main_layout.addWidget(self.table)
        self.setLayout(main_layout)

        # ==================== الإشارات ====================
        self.add_btn.clicked.connect(self.add_customer)
        self.edit_btn.clicked.connect(self.edit_customer)
        self.delete_btn.clicked.connect(self.delete_customer)
        self.clear_btn.clicked.connect(self.clear_fields)
        self.table.itemSelectionChanged.connect(self.fill_inputs)

        self.load_data()

    # ==================== Database ====================
    def connect_db(self):
        return sqlite3.connect(DB)

    # ==================== تحميل البيانات ====================
    def load_data(self):
        self.table.setRowCount(0)
        conn = self.connect_db()
        cur = conn.cursor()
        cur.execute("""
            SELECT id, name, country, company, email, phone, rating, created_at
            FROM customers
            ORDER BY id DESC
        """)
        rows = cur.fetchall()
        conn.close()

        for row_data in rows:
            row = self.table.rowCount()
            self.table.insertRow(row)

            for col, value in enumerate(row_data):
                item = QTableWidgetItem(str(value))
                item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(row, col, item)

            rating = str(row_data[6]).lower()
            if rating == "hot":
                bg = QColor("#C8E6C9")
            elif rating == "warm":
                bg = QColor("#FFF9C4")
            elif rating == "cold":
                bg = QColor("#BBDEFB")
            else:
                bg = QColor("#FFCDD2")

            for col in range(8):
                self.table.item(row, col).setBackground(bg)

    # ==================== إضافة عميل ====================
    def add_customer(self):
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "تنبيه", "اسم العميل مطلوب")
            return

        conn = self.connect_db()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO customers
            (name, country, company, email, phone, rating, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            name,
            self.country_input.text(),
            self.company_input.text(),
            self.email_input.text(),
            self.phone_input.text(),
            self.rating_combo.currentText(),
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ))
        conn.commit()
        conn.close()

        self.load_data()
        self.clear_fields()

    # ==================== تعديل عميل ====================
    def edit_customer(self):
        row = self.table.currentRow()
        if row < 0:
            return

        customer_id = int(self.table.item(row, 0).text())

        conn = self.connect_db()
        cur = conn.cursor()
        cur.execute("""
            UPDATE customers SET
                name=?, country=?, company=?, email=?, phone=?, rating=?
            WHERE id=?
        """, (
            self.name_input.text(),
            self.country_input.text(),
            self.company_input.text(),
            self.email_input.text(),
            self.phone_input.text(),
            self.rating_combo.currentText(),
            customer_id
        ))
        conn.commit()
        conn.close()

        self.load_data()

    # ==================== حذف عميل ====================
    def delete_customer(self):
        row = self.table.currentRow()
        if row < 0:
            return

        customer_id = int(self.table.item(row, 0).text())
        confirm = QMessageBox.question(self, "تأكيد", "هل تريد حذف العميل؟")
        if confirm != QMessageBox.Yes:
            return

        conn = self.connect_db()
        cur = conn.cursor()
        cur.execute("DELETE FROM customers WHERE id=?", (customer_id,))
        conn.commit()
        conn.close()

        self.load_data()

    # ==================== تعبئة الحقول ====================
    def fill_inputs(self):
        row = self.table.currentRow()
        if row < 0:
            return

        self.name_input.setText(self.table.item(row, 1).text())
        self.country_input.setText(self.table.item(row, 2).text())
        self.company_input.setText(self.table.item(row, 3).text())
        self.email_input.setText(self.table.item(row, 4).text())
        self.phone_input.setText(self.table.item(row, 5).text())
        self.rating_combo.setCurrentText(self.table.item(row, 6).text())

    # ==================== مسح الحقول ====================
    def clear_fields(self):
        self.name_input.clear()
        self.country_input.clear()
        self.company_input.clear()
        self.email_input.clear()
        self.phone_input.clear()
        self.rating_combo.setCurrentIndex(0)

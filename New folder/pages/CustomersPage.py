from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QMessageBox, QComboBox, QHeaderView
)
from PyQt5.QtGui import QFont, QColor, QBrush
from PyQt5.QtCore import Qt
import sqlite3, os

DB = os.path.join(os.path.dirname(__file__), "..", "database", "crm.db")


class CustomersPage(QWidget):
    def __init__(self):
        super().__init__()

        self.setStyleSheet("""
            QWidget {
                background-color: #FFFDF5;
            }
            QLabel {
                color: #333;
            }
            QLineEdit, QComboBox {
                border: 1px solid #bbb;
                border-radius: 6px;
                padding: 4px;
                background: #fff;
            }
            QPushButton {
                font-weight: bold;
                border-radius: 8px;
                padding: 6px 10px;
            }
            QPushButton:hover {
                opacity: 0.9;
            }
        """)

        layout = QVBoxLayout()
        title = QLabel("👥 إدارة العملاء")
        title.setFont(QFont("Amiri", 20, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)

        # 🔹 البحث
        search_layout = QHBoxLayout()
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("ابحث باسم العميل أو الهاتف...")
        self.search_box.textChanged.connect(self.search_customer)
        search_layout.addWidget(self.search_box)

        # 🔹 الحقول
        form_layout = QHBoxLayout()
        self.name_input = QLineEdit(); self.name_input.setPlaceholderText("اسم العميل")
        self.phone_input = QLineEdit(); self.phone_input.setPlaceholderText("رقم الهاتف")
        self.email_input = QLineEdit(); self.email_input.setPlaceholderText("البريد الإلكتروني")
        self.company_input = QLineEdit(); self.company_input.setPlaceholderText("اسم الشركة")
        self.address_input = QLineEdit(); self.address_input.setPlaceholderText("العنوان")

        # 🔹 تقييم العميل (1-5)
        self.rating_combo = QComboBox()
        self.rating_combo.addItems(["1", "2", "3", "4", "5"])

        for w in [self.name_input, self.phone_input, self.email_input, self.company_input, self.address_input, self.rating_combo]:
            form_layout.addWidget(w)

        # 🔹 الأزرار
        btn_layout = QHBoxLayout()
        self.add_btn = QPushButton("➕ إضافة"); self.add_btn.setStyleSheet("background-color: #4CAF50; color: white;")
        self.update_btn = QPushButton("✏️ تعديل"); self.update_btn.setStyleSheet("background-color: #2196F3; color: white;")
        self.delete_btn = QPushButton("🗑️ حذف"); self.delete_btn.setStyleSheet("background-color: #F44336; color: white;")
        self.clear_btn = QPushButton("♻️ مسح"); self.clear_btn.setStyleSheet("background-color: #9C27B0; color: white;")

        btn_layout.addWidget(self.add_btn)
        btn_layout.addWidget(self.update_btn)
        btn_layout.addWidget(self.delete_btn)
        btn_layout.addWidget(self.clear_btn)

        # 🔹 جدول العملاء
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(["ID", "اسم العميل", "رقم الهاتف", "البريد الإلكتروني", "اسم الشركة", "العنوان", "تقييم"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet("""
            QHeaderView::section {
                background-color: #444;
                color: white;
                padding: 5px;
                font-weight: bold;
            }
            QTableWidget {
                gridline-color: #ccc;
                alternate-background-color: #FAFAFA;
            }
        """)

        self.table.cellClicked.connect(self.load_selected_row)

        # 🔹 قائمة "الترتيب حسب"
        sort_layout = QHBoxLayout()
        sort_label = QLabel("🔽 ترتيب حسب:")
        sort_label.setFont(QFont("Amiri", 12))
        self.sort_combo = QComboBox()
        self.sort_combo.addItems(["رقم العميل", "تقييم العميل"])
        self.sort_combo.currentIndexChanged.connect(self.sort_table)

        sort_layout.addWidget(sort_label)
        sort_layout.addWidget(self.sort_combo)
        sort_layout.addStretch()

        # ✅ ترتيب المكونات
        layout.addWidget(title)
        layout.addLayout(search_layout)
        layout.addLayout(form_layout)
        layout.addLayout(btn_layout)
        layout.addLayout(sort_layout)
        layout.addWidget(self.table)

        self.setLayout(layout)

        # 🔹 توصيل الأزرار بالوظائف
        self.add_btn.clicked.connect(self.add_customer)
        self.update_btn.clicked.connect(self.update_customer)
        self.delete_btn.clicked.connect(self.delete_customer)
        self.clear_btn.clicked.connect(self.clear_fields)

        self.load_data()

    # ===================== الوظائف =====================

    def connect_db(self):
        return sqlite3.connect(DB)

    def load_data(self):
        self.table.setRowCount(0)
        conn = self.connect_db()
        cur = conn.cursor()
        cur.execute("SELECT * FROM customers")
        for row_data in cur.fetchall():
            row = self.table.rowCount()
            self.table.insertRow(row)
            for col, data in enumerate(row_data):
                item = QTableWidgetItem(str(data))
                item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(row, col, item)

            # ⭐ تلوين الصف حسب التقييم
            rating = int(row_data[6])
            if rating == 5:
                for col in range(self.table.columnCount()):
                    self.table.item(row, col).setBackground(QBrush(QColor("#FFF8DC")))
            elif rating >= 4:
                for col in range(self.table.columnCount()):
                    self.table.item(row, col).setBackground(QBrush(QColor("#E8F5E9")))

        conn.close()

    def add_customer(self):
        name = self.name_input.text()
        phone = self.phone_input.text()
        email = self.email_input.text()
        company = self.company_input.text()
        address = self.address_input.text()
        rating = self.rating_combo.currentText()

        if not name or not phone:
            QMessageBox.warning(self, "خطأ", "يرجى إدخال اسم العميل ورقم الهاتف على الأقل.")
            return

        conn = self.connect_db()
        cur = conn.cursor()

        # 🔹 التأكد من وجود العمود ID كـ INTEGER PRIMARY KEY
        cur.execute("SELECT id FROM customers ORDER BY id ASC")
        existing_ids = [row[0] for row in cur.fetchall()]

        # 🔹 البحث عن أول رقم ناقص
        new_id = 1
        for i in range(1, len(existing_ids) + 2):
            if i not in existing_ids:
                new_id = i
                break

        # 🔹 إدخال العميل الجديد برقم مخصص
        cur.execute(
            "INSERT INTO customers (id, name, phone, email, company, address, rating) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (new_id, name, phone, email, company, address, rating)
        )

        conn.commit()
        conn.close()

        self.load_data()
        self.clear_fields()
        QMessageBox.information(self, "تم", f"تمت إضافة العميل بنجاح ✅ (رقم العميل: {new_id})")

    def update_customer(self):
        selected = self.table.currentRow()
        if selected < 0:
            QMessageBox.warning(self, "تنبيه", "يرجى اختيار العميل المراد تعديله.")
            return

        cid = int(self.table.item(selected, 0).text())
        name = self.name_input.text()
        phone = self.phone_input.text()
        email = self.email_input.text()
        company = self.company_input.text()
        address = self.address_input.text()
        rating = self.rating_combo.currentText()

        conn = self.connect_db()
        cur = conn.cursor()
        cur.execute("UPDATE customers SET name=?, phone=?, email=?, company=?, address=?, rating=? WHERE id=?",
                    (name, phone, email, company, address, rating, cid))
        conn.commit()
        conn.close()

        self.load_data()
        QMessageBox.information(self, "تم", "تم تعديل بيانات العميل بنجاح ✏️")

    def delete_customer(self):
        selected = self.table.currentRow()
        if selected < 0:
            QMessageBox.warning(self, "تنبيه", "يرجى اختيار العميل المراد حذفه.")
            return

        cid = int(self.table.item(selected, 0).text())
        confirm = QMessageBox.question(self, "تأكيد", "هل أنت متأكد من حذف هذا العميل؟", QMessageBox.Yes | QMessageBox.No)
        if confirm == QMessageBox.Yes:
            conn = self.connect_db()
            cur = conn.cursor()
            cur.execute("DELETE FROM customers WHERE id=?", (cid,))
            conn.commit()
            conn.close()
            self.load_data()
            QMessageBox.information(self, "تم", "تم حذف العميل 🗑️")

    def load_selected_row(self, row, _):
        self.name_input.setText(self.table.item(row, 1).text())
        self.phone_input.setText(self.table.item(row, 2).text())
        self.email_input.setText(self.table.item(row, 3).text())
        self.company_input.setText(self.table.item(row, 4).text())
        self.address_input.setText(self.table.item(row, 5).text())
        self.rating_combo.setCurrentText(self.table.item(row, 6).text())

    def clear_fields(self):
        for field in [self.name_input, self.phone_input, self.email_input, self.company_input, self.address_input]:
            field.clear()
        self.rating_combo.setCurrentIndex(0)
        self.table.clearSelection()

    def search_customer(self):
        text = self.search_box.text().lower()
        for row in range(self.table.rowCount()):
            visible = any(text in self.table.item(row, col).text().lower() for col in range(1, 6))
            self.table.setRowHidden(row, not visible)

    def sort_table(self):
        sort_by = self.sort_combo.currentText()
        if sort_by == "رقم العميل":
            self.table.sortItems(0, Qt.AscendingOrder)
        elif sort_by == "تقييم العميل":
            self.table.sortItems(6, Qt.DescendingOrder)
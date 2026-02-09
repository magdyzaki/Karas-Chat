# pages/SuppliersPage.py
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox, QTextEdit
)
from PyQt5.QtGui import QFont, QColor
from PyQt5.QtCore import Qt
import sqlite3, os

DB = os.path.join(os.path.dirname(__file__), "..", "database", "crm.db")


class SuppliersPage(QWidget):
    """ صفحة الموردين — إضافة / تعديل / حذف / بحث """

    def __init__(self):
        super().__init__()

        # إزالة الستايل الثابت للسماح بتطبيق الستايل من MainWindow
        # self.setStyleSheet("background-color: #FFFBEA;")  # تم إزالة الستايل الثابت
        self.setFont(QFont("Amiri", 11))

        self.create_table_if_not_exists()
        self.init_ui()
        self.load_suppliers()

    # --------------------------------------------------------
    #   إنشاء جدول الموردين لو مش موجود
    # --------------------------------------------------------
    def create_table_if_not_exists(self):
        conn = sqlite3.connect(DB)
        cur = conn.cursor()

        cur.execute("""
            CREATE TABLE IF NOT EXISTS suppliers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                phone TEXT,
                address TEXT,
                notes TEXT
            )
        """)

        conn.commit()
        conn.close()

    def db_conn(self):
        return sqlite3.connect(DB)

    # --------------------------------------------------------
    #                  واجهة المستخدم
    # --------------------------------------------------------
    def init_ui(self):
        layout = QVBoxLayout()

        title = QLabel("📦 إدارة الموردين")
        title.setFont(QFont("Amiri", 20, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # ---------------- شريط البحث ----------------
        search_row = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("بحث بالاسم أو رقم الهاتف…")
        self.search_input.textChanged.connect(self.filter_table)
        search_row.addWidget(self.search_input)

        layout.addLayout(search_row)

        # ---------------- استمارة الإدخال ----------------
        form_row = QHBoxLayout()

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("اسم المورد")

        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText("رقم الهاتف")

        self.addr_input = QLineEdit()
        self.addr_input.setPlaceholderText("العنوان")

        self.notes_input = QTextEdit()
        self.notes_input.setPlaceholderText("ملاحظات")
        self.notes_input.setFixedHeight(60)

        form_row.addWidget(self.name_input)
        form_row.addWidget(self.phone_input)
        form_row.addWidget(self.addr_input)
        form_row.addWidget(self.notes_input)

        layout.addLayout(form_row)

        # ---------------- أزرار التحكم ----------------
        btn_row = QHBoxLayout()

        add_btn = QPushButton("➕ إضافة")
        add_btn.setStyleSheet("background:#4CAF50;color:white;font-weight:bold;")
        add_btn.clicked.connect(self.add_supplier)

        edit_btn = QPushButton("✏️ تعديل")
        edit_btn.setStyleSheet("background:#FF9800;color:white;font-weight:bold;")
        edit_btn.clicked.connect(self.edit_supplier)

        delete_btn = QPushButton("🗑️ حذف")
        delete_btn.setStyleSheet("background:#E53935;color:white;font-weight:bold;")
        delete_btn.clicked.connect(self.delete_supplier)

        btn_row.addWidget(add_btn)
        btn_row.addWidget(edit_btn)
        btn_row.addWidget(delete_btn)

        layout.addLayout(btn_row)

        # ---------------- جدول الموردين ----------------
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["ID", "Name", "Phone", "Address", "Notes"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setDefaultSectionSize(36)
        self.table.setFont(QFont("Amiri", 12))
        self.table.itemSelectionChanged.connect(self.fill_fields)

        # لون الهيدر
        self.table.horizontalHeader().setStyleSheet(
            "::section {background-color: #E0E0E0; font-weight:bold;}"
        )

        layout.addWidget(self.table)

        self.setLayout(layout)

    # --------------------------------------------------------
    #                تحميل جدول الموردين
    # --------------------------------------------------------
    def load_suppliers(self):
        self.table.setRowCount(0)

        conn = self.db_conn()
        cur = conn.cursor()
        cur.execute("SELECT id, name, phone, address, notes FROM suppliers ORDER BY id DESC")
        rows = cur.fetchall()
        conn.close()

        for row in rows:
            self.add_row_to_table(row)

    # --------------------------------------------------------
    #                إضافة صف للجدول
    # --------------------------------------------------------
    def add_row_to_table(self, row):
        r = self.table.rowCount()
        self.table.insertRow(r)

        for c, value in enumerate(row):
            item = QTableWidgetItem(str(value))
            item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(r, c, item)

    # --------------------------------------------------------
    #                ملء الحقول عند اختيار صف
    # --------------------------------------------------------
    def fill_fields(self):
        items = self.table.selectedItems()
        if not items:
            return

        row = items[0].row()

        self.selected_id = self.table.item(row, 0).text()
        self.name_input.setText(self.table.item(row, 1).text())
        self.phone_input.setText(self.table.item(row, 2).text())
        self.addr_input.setText(self.table.item(row, 3).text())
        self.notes_input.setText(self.table.item(row, 4).text())

    # --------------------------------------------------------
    #                      إضافة مورد
    # --------------------------------------------------------
    def add_supplier(self):
        name = self.name_input.text().strip()
        phone = self.phone_input.text().strip()
        addr = self.addr_input.text().strip()
        notes = self.notes_input.toPlainText().strip()

        if not name:
            QMessageBox.warning(self, "خطأ", "لا يمكن ترك اسم المورد فارغاً.")
            return

        conn = self.db_conn()
        cur = conn.cursor()
        cur.execute("INSERT INTO suppliers (name, phone, address, notes) VALUES (?, ?, ?, ?)",
                    (name, phone, addr, notes))
        conn.commit()
        conn.close()

        self.load_suppliers()
        self.clear_fields()
        QMessageBox.information(self, "نجاح", "تمت إضافة المورد.")

    # --------------------------------------------------------
    #                      تعديل مورد
    # --------------------------------------------------------
    def edit_supplier(self):
        try:
            sid = self.selected_id
        except:
            QMessageBox.warning(self, "تنبيه", "اختر مورداً لتعديله.")
            return

        name = self.name_input.text().strip()
        phone = self.phone_input.text().strip()
        addr = self.addr_input.text().strip()
        notes = self.notes_input.toPlainText().strip()

        conn = self.db_conn()
        cur = conn.cursor()
        cur.execute("""
            UPDATE suppliers
            SET name=?, phone=?, address=?, notes=?
            WHERE id=?
        """, (name, phone, addr, notes, sid))
        conn.commit()
        conn.close()

        self.load_suppliers()
        QMessageBox.information(self, "تم", "تم تعديل بيانات المورد.")

    # --------------------------------------------------------
    #                      حذف مورد
    # --------------------------------------------------------
    def delete_supplier(self):
        try:
            sid = self.selected_id
        except:
            QMessageBox.warning(self, "تنبيه", "اختر مورداً لحذفه.")
            return

        answer = QMessageBox.question(
            self, "تأكيد", f"هل تريد حذف المورد رقم {sid}؟",
            QMessageBox.Yes | QMessageBox.No
        )

        if answer != QMessageBox.Yes:
            return

        conn = self.db_conn()
        cur = conn.cursor()
        cur.execute("DELETE FROM suppliers WHERE id=?", (sid,))
        conn.commit()
        conn.close()

        self.load_suppliers()
        self.clear_fields()
        QMessageBox.information(self, "تم", "تم حذف المورد.")

    # --------------------------------------------------------
    #                     مسح الحقول
    # --------------------------------------------------------
    def clear_fields(self):
        self.name_input.clear()
        self.phone_input.clear()
        self.addr_input.clear()
        self.notes_input.clear()

    # --------------------------------------------------------
    #                     فلترة البحث
    # --------------------------------------------------------
    def filter_table(self):
        q = self.search_input.text().lower()

        for r in range(self.table.rowCount()):
            name = self.table.item(r, 1).text().lower()
            phone = self.table.item(r, 2).text().lower()

            self.table.setRowHidden(r, q not in name and q not in phone)
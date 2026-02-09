# pages/FollowUpPage.py
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QMessageBox, QHeaderView, QComboBox,
    QDateEdit, QTextEdit, QFileDialog, QGroupBox, QFormLayout, QMainWindow,
    QScrollArea, QSplitter
)
from PyQt5.QtGui import QFont, QColor, QBrush
from PyQt5.QtCore import Qt, QDate
import sqlite3
import os
from datetime import datetime

DB = os.path.join(os.path.dirname(__file__), "..", "database", "crm.db")


class FollowUpManagerWindow(QMainWindow):
    """نافذة مستقلة لبرنامج Export Follow-Up Manager"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("📦 Export Follow-Up Manager - متابعة الصادرات")
        self.setMinimumSize(1400, 900)
        self.setGeometry(100, 100, 1400, 900)
        
        # تطبيق الستايل من الوالد إذا كان موجوداً
        if parent:
            try:
                self.setStyleSheet(parent.styleSheet())
            except:
                pass
        
        self.init_ui()
        self.load_data()

    def ensure_db(self):
        """التأكد من وجود جدول متابعة الصادرات"""
        conn = sqlite3.connect(DB)
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS export_followup (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_name TEXT NOT NULL,
                invoice_number TEXT,
                product_name TEXT,
                quantity REAL DEFAULT 0,
                unit TEXT DEFAULT '',
                export_date TEXT,
                shipping_date TEXT,
                expected_arrival TEXT,
                actual_arrival TEXT,
                status TEXT DEFAULT 'قيد المعالجة',
                port TEXT DEFAULT '',
                container_number TEXT DEFAULT '',
                shipping_line TEXT DEFAULT '',
                bl_number TEXT DEFAULT '',
                payment_status TEXT DEFAULT 'غير مدفوع',
                notes TEXT DEFAULT '',
                created_at TEXT DEFAULT '',
                updated_at TEXT DEFAULT ''
            )
        """)
        conn.commit()
        conn.close()

    def init_ui(self):
        # Widget مركزي
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # العنوان
        title = QLabel("📦 Export Follow-Up Manager - متابعة الصادرات")
        title.setFont(QFont("Amiri", 24, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("padding: 15px; margin-bottom: 10px;")
        main_layout.addWidget(title)

        # استخدام Splitter لتقسيم الشاشة
        splitter = QSplitter(Qt.Horizontal)
        
        # ==================== الجانب الأيسر: النموذج ====================
        form_widget = QWidget()
        form_layout = QVBoxLayout(form_widget)
        form_layout.setSpacing(10)
        
        # ScrollArea للنموذج
        form_scroll = QScrollArea()
        form_scroll.setWidget(form_widget)
        form_scroll.setWidgetResizable(True)
        form_scroll.setMinimumWidth(500)
        
        # ==================== معلومات أساسية ====================
        basic_group = QGroupBox("معلومات أساسية")
        basic_group.setFont(QFont("Amiri", 14, QFont.Bold))
        basic_layout = QFormLayout()

        self.customer_combo = QComboBox()
        self.customer_combo.setEditable(True)
        self.customer_combo.setMinimumWidth(200)
        basic_layout.addRow("اسم العميل:", self.customer_combo)

        self.invoice_input = QLineEdit()
        self.invoice_input.setPlaceholderText("رقم الفاتورة")
        basic_layout.addRow("رقم الفاتورة:", self.invoice_input)

        self.product_input = QLineEdit()
        self.product_input.setPlaceholderText("اسم المنتج")
        basic_layout.addRow("اسم المنتج:", self.product_input)

        qty_layout = QHBoxLayout()
        self.quantity_input = QLineEdit()
        self.quantity_input.setPlaceholderText("الكمية")
        self.unit_combo = QComboBox()
        self.unit_combo.addItems(["طن", "كيلو", "طرد", "صندوق", "حاوية"])
        qty_layout.addWidget(self.quantity_input)
        qty_layout.addWidget(self.unit_combo)
        basic_layout.addRow("الكمية:", qty_layout)

        basic_group.setLayout(basic_layout)
        form_layout.addWidget(basic_group)

        # ==================== تواريخ الشحن ====================
        dates_group = QGroupBox("تواريخ الشحن")
        dates_group.setFont(QFont("Amiri", 14, QFont.Bold))
        dates_layout = QFormLayout()

        self.export_date = QDateEdit()
        self.export_date.setDate(QDate.currentDate())
        self.export_date.setCalendarPopup(True)
        dates_layout.addRow("تاريخ التصدير:", self.export_date)

        self.shipping_date = QDateEdit()
        self.shipping_date.setDate(QDate.currentDate())
        self.shipping_date.setCalendarPopup(True)
        dates_layout.addRow("تاريخ الشحن:", self.shipping_date)

        self.expected_arrival = QDateEdit()
        self.expected_arrival.setDate(QDate.currentDate())
        self.expected_arrival.setCalendarPopup(True)
        dates_layout.addRow("تاريخ الوصول المتوقع:", self.expected_arrival)

        self.actual_arrival = QDateEdit()
        self.actual_arrival.setDate(QDate.currentDate())
        self.actual_arrival.setCalendarPopup(True)
        dates_layout.addRow("تاريخ الوصول الفعلي:", self.actual_arrival)

        dates_group.setLayout(dates_layout)
        form_layout.addWidget(dates_group)

        # ==================== معلومات الشحن ====================
        shipping_group = QGroupBox("معلومات الشحن")
        shipping_group.setFont(QFont("Amiri", 14, QFont.Bold))
        shipping_layout = QFormLayout()

        self.status_combo = QComboBox()
        self.status_combo.addItems([
            "قيد المعالجة",
            "جاهز للشحن",
            "في الميناء",
            "في الطريق",
            "وصل الميناء",
            "تم التسليم",
            "ملغى"
        ])
        shipping_layout.addRow("حالة الشحنة:", self.status_combo)

        self.port_input = QLineEdit()
        self.port_input.setPlaceholderText("اسم الميناء")
        shipping_layout.addRow("الميناء:", self.port_input)

        self.container_input = QLineEdit()
        self.container_input.setPlaceholderText("رقم الحاوية")
        shipping_layout.addRow("رقم الحاوية:", self.container_input)

        self.shipping_line_input = QLineEdit()
        self.shipping_line_input.setPlaceholderText("خط الشحن")
        shipping_layout.addRow("خط الشحن:", self.shipping_line_input)

        self.bl_number_input = QLineEdit()
        self.bl_number_input.setPlaceholderText("رقم B/L")
        shipping_layout.addRow("رقم B/L:", self.bl_number_input)

        self.payment_status_combo = QComboBox()
        self.payment_status_combo.addItems([
            "غير مدفوع",
            "مدفوع جزئياً",
            "مدفوع بالكامل"
        ])
        shipping_layout.addRow("حالة الدفع:", self.payment_status_combo)

        shipping_group.setLayout(shipping_layout)
        form_layout.addWidget(shipping_group)

        # ==================== ملاحظات ====================
        notes_group = QGroupBox("ملاحظات")
        notes_group.setFont(QFont("Amiri", 14, QFont.Bold))
        notes_layout = QVBoxLayout()

        self.notes_input = QTextEdit()
        self.notes_input.setPlaceholderText("أضف أي ملاحظات هنا...")
        self.notes_input.setMaximumHeight(120)
        notes_layout.addWidget(self.notes_input)

        notes_group.setLayout(notes_layout)
        form_layout.addWidget(notes_group)

        # ==================== الأزرار ====================
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(10)

        self.add_btn = QPushButton("➕ إضافة")
        self.add_btn.setMinimumHeight(45)
        self.add_btn.setMinimumWidth(120)
        self.add_btn.clicked.connect(self.add_record)

        self.update_btn = QPushButton("✏️ تعديل")
        self.update_btn.setMinimumHeight(45)
        self.update_btn.setMinimumWidth(120)
        self.update_btn.clicked.connect(self.update_record)

        self.delete_btn = QPushButton("🗑️ حذف")
        self.delete_btn.setMinimumHeight(45)
        self.delete_btn.setMinimumWidth(120)
        self.delete_btn.clicked.connect(self.delete_record)

        self.clear_btn = QPushButton("♻️ مسح")
        self.clear_btn.setMinimumHeight(45)
        self.clear_btn.setMinimumWidth(120)
        self.clear_btn.clicked.connect(self.clear_fields)

        self.export_btn = QPushButton("📄 تصدير Excel")
        self.export_btn.setMinimumHeight(45)
        self.export_btn.setMinimumWidth(150)
        self.export_btn.clicked.connect(self.export_to_excel)

        buttons_layout.addWidget(self.add_btn)
        buttons_layout.addWidget(self.update_btn)
        buttons_layout.addWidget(self.delete_btn)
        buttons_layout.addWidget(self.clear_btn)
        buttons_layout.addWidget(self.export_btn)
        buttons_layout.addStretch()

        form_layout.addLayout(buttons_layout)
        form_layout.addStretch()

        # ==================== الجانب الأيمن: الجدول ====================
        table_widget = QWidget()
        table_layout = QVBoxLayout(table_widget)
        
        table_label = QLabel("📊 قائمة الشحنات")
        table_label.setFont(QFont("Amiri", 16, QFont.Bold))
        table_label.setAlignment(Qt.AlignCenter)
        table_layout.addWidget(table_label)

        self.table = QTableWidget()
        self.table.setColumnCount(12)
        self.table.setHorizontalHeaderLabels([
            "ID", "العميل", "رقم الفاتورة", "المنتج", "الكمية",
            "حالة الشحنة", "تاريخ الشحن", "تاريخ الوصول المتوقع",
            "تاريخ الوصول الفعلي", "الميناء", "رقم الحاوية", "حالة الدفع"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.itemSelectionChanged.connect(self.fill_fields)

        table_layout.addWidget(self.table)

        # إضافة الاثنين إلى Splitter
        splitter.addWidget(form_scroll)
        splitter.addWidget(table_widget)
        splitter.setSizes([500, 900])  # توزيع المساحة

        main_layout.addWidget(splitter)

        # تحميل العملاء
        self.load_customers()
        self.ensure_db()

    def load_customers(self):
        """تحميل قائمة العملاء"""
        self.customer_combo.clear()
        try:
            conn = sqlite3.connect(DB)
            cur = conn.cursor()
            cur.execute("SELECT DISTINCT name FROM customers ORDER BY name")
            rows = cur.fetchall()
            conn.close()
            for row in rows:
                self.customer_combo.addItem(row[0])
        except Exception as e:
            print(f"خطأ في تحميل العملاء: {e}")

    def connect_db(self):
        return sqlite3.connect(DB)

    def load_data(self):
        """تحميل البيانات"""
        self.table.setRowCount(0)
        conn = self.connect_db()
        cur = conn.cursor()
        cur.execute("""
            SELECT id, customer_name, invoice_number, product_name, quantity,
                   status, shipping_date, expected_arrival, actual_arrival,
                   port, container_number, payment_status
            FROM export_followup
            ORDER BY id DESC
        """)
        rows = cur.fetchall()
        conn.close()

        for row_data in rows:
            row = self.table.rowCount()
            self.table.insertRow(row)

            for col, value in enumerate(row_data):
                item = QTableWidgetItem(str(value) if value else "")
                item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(row, col, item)

            # تلوين حسب الحالة
            status = str(row_data[5]).lower() if row_data[5] else ""
            if "تم التسليم" in status or "تم" in status:
                bg = QColor("#C8E6C9")  # أخضر فاتح
            elif "في الطريق" in status or "في الميناء" in status:
                bg = QColor("#BBDEFB")  # أزرق فاتح
            elif "جاهز" in status:
                bg = QColor("#FFF9C4")  # أصفر فاتح
            elif "ملغى" in status:
                bg = QColor("#FFCDD2")  # أحمر فاتح
            else:
                bg = QColor("#F5F5F5")  # رمادي فاتح

            for col in range(12):
                if self.table.item(row, col):
                    self.table.item(row, col).setBackground(bg)

    def add_record(self):
        """إضافة سجل جديد"""
        if not self.customer_combo.currentText().strip():
            QMessageBox.warning(self, "تنبيه", "اسم العميل مطلوب")
            return

        conn = self.connect_db()
        cur = conn.cursor()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cur.execute("""
            INSERT INTO export_followup (
                customer_name, invoice_number, product_name, quantity, unit,
                export_date, shipping_date, expected_arrival, actual_arrival,
                status, port, container_number, shipping_line, bl_number,
                payment_status, notes, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            self.customer_combo.currentText(),
            self.invoice_input.text(),
            self.product_input.text(),
            float(self.quantity_input.text() or 0),
            self.unit_combo.currentText(),
            self.export_date.date().toString("yyyy-MM-dd"),
            self.shipping_date.date().toString("yyyy-MM-dd"),
            self.expected_arrival.date().toString("yyyy-MM-dd"),
            self.actual_arrival.date().toString("yyyy-MM-dd"),
            self.status_combo.currentText(),
            self.port_input.text(),
            self.container_input.text(),
            self.shipping_line_input.text(),
            self.bl_number_input.text(),
            self.payment_status_combo.currentText(),
            self.notes_input.toPlainText(),
            now,
            now
        ))
        conn.commit()
        conn.close()

        QMessageBox.information(self, "تم", "تمت إضافة السجل بنجاح ✅")
        self.load_data()
        self.clear_fields()

    def update_record(self):
        """تعديل سجل"""
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "تنبيه", "اختر سجلاً لتعديله")
            return

        record_id = int(self.table.item(row, 0).text())
        conn = self.connect_db()
        cur = conn.cursor()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cur.execute("""
            UPDATE export_followup SET
                customer_name=?, invoice_number=?, product_name=?, quantity=?, unit=?,
                export_date=?, shipping_date=?, expected_arrival=?, actual_arrival=?,
                status=?, port=?, container_number=?, shipping_line=?, bl_number=?,
                payment_status=?, notes=?, updated_at=?
            WHERE id=?
        """, (
            self.customer_combo.currentText(),
            self.invoice_input.text(),
            self.product_input.text(),
            float(self.quantity_input.text() or 0),
            self.unit_combo.currentText(),
            self.export_date.date().toString("yyyy-MM-dd"),
            self.shipping_date.date().toString("yyyy-MM-dd"),
            self.expected_arrival.date().toString("yyyy-MM-dd"),
            self.actual_arrival.date().toString("yyyy-MM-dd"),
            self.status_combo.currentText(),
            self.port_input.text(),
            self.container_input.text(),
            self.shipping_line_input.text(),
            self.bl_number_input.text(),
            self.payment_status_combo.currentText(),
            self.notes_input.toPlainText(),
            now,
            record_id
        ))
        conn.commit()
        conn.close()

        QMessageBox.information(self, "تم", "تم تعديل السجل بنجاح ✏️")
        self.load_data()
        self.clear_fields()

    def delete_record(self):
        """حذف سجل"""
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "تنبيه", "اختر سجلاً لحذفه")
            return

        record_id = int(self.table.item(row, 0).text())
        reply = QMessageBox.question(
            self, "تأكيد", "هل تريد حذف هذا السجل؟",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return

        conn = self.connect_db()
        cur = conn.cursor()
        cur.execute("DELETE FROM export_followup WHERE id=?", (record_id,))
        conn.commit()
        conn.close()

        QMessageBox.information(self, "تم", "تم حذف السجل بنجاح 🗑️")
        self.load_data()
        self.clear_fields()

    def fill_fields(self):
        """تعبئة الحقول من الجدول"""
        row = self.table.currentRow()
        if row < 0:
            return

        try:
            # تحميل البيانات الكاملة من قاعدة البيانات
            record_id = int(self.table.item(row, 0).text())
            conn = self.connect_db()
            cur = conn.cursor()
            cur.execute("SELECT * FROM export_followup WHERE id=?", (record_id,))
            data = cur.fetchone()
            conn.close()

            if not data:
                return

            # تعبئة الحقول
            customer_name = data[1] or ""
            index = self.customer_combo.findText(customer_name)
            if index >= 0:
                self.customer_combo.setCurrentIndex(index)
            else:
                self.customer_combo.setCurrentText(customer_name)

            self.invoice_input.setText(str(data[2] or ""))
            self.product_input.setText(str(data[3] or ""))
            self.quantity_input.setText(str(data[4] or ""))
            
            unit = str(data[5] or "")
            unit_index = self.unit_combo.findText(unit)
            if unit_index >= 0:
                self.unit_combo.setCurrentIndex(unit_index)

            if data[6]:  # export_date
                self.export_date.setDate(QDate.fromString(data[6], "yyyy-MM-dd"))
            if data[7]:  # shipping_date
                self.shipping_date.setDate(QDate.fromString(data[7], "yyyy-MM-dd"))
            if data[8]:  # expected_arrival
                self.expected_arrival.setDate(QDate.fromString(data[8], "yyyy-MM-dd"))
            if data[9]:  # actual_arrival
                self.actual_arrival.setDate(QDate.fromString(data[9], "yyyy-MM-dd"))

            status = str(data[10] or "")
            status_index = self.status_combo.findText(status)
            if status_index >= 0:
                self.status_combo.setCurrentIndex(status_index)

            self.port_input.setText(str(data[11] or ""))
            self.container_input.setText(str(data[12] or ""))
            self.shipping_line_input.setText(str(data[13] or ""))
            self.bl_number_input.setText(str(data[14] or ""))

            payment_status = str(data[15] or "")
            payment_index = self.payment_status_combo.findText(payment_status)
            if payment_index >= 0:
                self.payment_status_combo.setCurrentIndex(payment_index)

            self.notes_input.setPlainText(str(data[16] or ""))
        except Exception as e:
            QMessageBox.warning(self, "خطأ", f"فشل تحميل البيانات: {str(e)}")

    def clear_fields(self):
        """مسح الحقول"""
        self.customer_combo.setCurrentIndex(-1)
        self.customer_combo.setCurrentText("")
        self.invoice_input.clear()
        self.product_input.clear()
        self.quantity_input.clear()
        self.unit_combo.setCurrentIndex(0)
        self.export_date.setDate(QDate.currentDate())
        self.shipping_date.setDate(QDate.currentDate())
        self.expected_arrival.setDate(QDate.currentDate())
        self.actual_arrival.setDate(QDate.currentDate())
        self.status_combo.setCurrentIndex(0)
        self.port_input.clear()
        self.container_input.clear()
        self.shipping_line_input.clear()
        self.bl_number_input.clear()
        self.payment_status_combo.setCurrentIndex(0)
        self.notes_input.clear()
        self.table.clearSelection()

    def export_to_excel(self):
        """تصدير البيانات إلى Excel"""
        try:
            import pandas as pd
            from openpyxl import load_workbook
        except ImportError:
            QMessageBox.warning(
                self, "مكتبة غير مثبتة",
                "يجب تثبيت pandas و openpyxl:\npip install pandas openpyxl"
            )
            return

        if self.table.rowCount() == 0:
            QMessageBox.warning(self, "تنبيه", "لا توجد بيانات للتصدير")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, "حفظ ملف Excel", "", "Excel Files (*.xlsx)"
        )
        if not file_path:
            return

        try:
            conn = self.connect_db()
            df = pd.read_sql_query("""
                SELECT 
                    id, customer_name, invoice_number, product_name, quantity, unit,
                    export_date, shipping_date, expected_arrival, actual_arrival,
                    status, port, container_number, shipping_line, bl_number,
                    payment_status, notes, created_at, updated_at
                FROM export_followup
                ORDER BY id DESC
            """, conn)
            conn.close()

            df.to_excel(file_path, index=False, engine='openpyxl')
            QMessageBox.information(self, "تم", f"تم تصدير البيانات إلى:\n{file_path}")
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل التصدير:\n{str(e)}")


class FollowUpPage(QWidget):
    """صفحة بسيطة تفتح النافذة المستقلة"""
    def __init__(self):
        super().__init__()
        self.followup_window = None
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)
        
        title = QLabel("📦 Export Follow-Up Manager")
        title.setFont(QFont("Amiri", 24, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        desc = QLabel("برنامج متابعة الصادرات - إدارة شاملة لعمليات التصدير")
        desc.setFont(QFont("Amiri", 14))
        desc.setAlignment(Qt.AlignCenter)
        layout.addWidget(desc)
        
        open_btn = QPushButton("🚀 فتح برنامج متابعة الصادرات")
        open_btn.setFont(QFont("Amiri", 16, QFont.Bold))
        open_btn.setMinimumHeight(60)
        open_btn.setMinimumWidth(400)
        open_btn.clicked.connect(self.open_followup_manager)
        layout.addWidget(open_btn, alignment=Qt.AlignCenter)
        
        layout.addStretch()
        self.setLayout(layout)
    
    def open_followup_manager(self):
        """فتح نافذة برنامج متابعة الصادرات"""
        if self.followup_window is None or not self.followup_window.isVisible():
            self.followup_window = FollowUpManagerWindow(self)
            self.followup_window.show()
        else:
            self.followup_window.raise_()
            self.followup_window.activateWindow()
    def __init__(self):
        super().__init__()
        # إزالة الستايل الثابت للسماح بتطبيق الستايل من MainWindow
        self.ensure_db()
        self.init_ui()
        self.load_data()

    def ensure_db(self):
        """التأكد من وجود جدول متابعة الصادرات"""
        conn = sqlite3.connect(DB)
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS export_followup (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_name TEXT NOT NULL,
                invoice_number TEXT,
                product_name TEXT,
                quantity REAL DEFAULT 0,
                unit TEXT DEFAULT '',
                export_date TEXT,
                shipping_date TEXT,
                expected_arrival TEXT,
                actual_arrival TEXT,
                status TEXT DEFAULT 'قيد المعالجة',
                port TEXT DEFAULT '',
                container_number TEXT DEFAULT '',
                shipping_line TEXT DEFAULT '',
                bl_number TEXT DEFAULT '',
                payment_status TEXT DEFAULT 'غير مدفوع',
                notes TEXT DEFAULT '',
                created_at TEXT DEFAULT '',
                updated_at TEXT DEFAULT ''
            )
        """)
        conn.commit()
        conn.close()

    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(15, 15, 15, 15)

        # العنوان
        title = QLabel("📦 متابعة الصادرات (Export Follow-Up)")
        title.setFont(QFont("Amiri", 20, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title)

        # ==================== معلومات أساسية ====================
        basic_group = QGroupBox("معلومات أساسية")
        basic_group.setFont(QFont("Amiri", 14, QFont.Bold))
        basic_layout = QFormLayout()

        self.customer_combo = QComboBox()
        self.customer_combo.setEditable(True)
        self.customer_combo.setMinimumWidth(200)
        basic_layout.addRow("اسم العميل:", self.customer_combo)

        self.invoice_input = QLineEdit()
        self.invoice_input.setPlaceholderText("رقم الفاتورة")
        basic_layout.addRow("رقم الفاتورة:", self.invoice_input)

        self.product_input = QLineEdit()
        self.product_input.setPlaceholderText("اسم المنتج")
        basic_layout.addRow("اسم المنتج:", self.product_input)

        qty_layout = QHBoxLayout()
        self.quantity_input = QLineEdit()
        self.quantity_input.setPlaceholderText("الكمية")
        self.unit_combo = QComboBox()
        self.unit_combo.addItems(["طن", "كيلو", "طرد", "صندوق", "حاوية"])
        qty_layout.addWidget(self.quantity_input)
        qty_layout.addWidget(self.unit_combo)
        basic_layout.addRow("الكمية:", qty_layout)

        basic_group.setLayout(basic_layout)
        main_layout.addWidget(basic_group)

        # ==================== تواريخ الشحن ====================
        dates_group = QGroupBox("تواريخ الشحن")
        dates_group.setFont(QFont("Amiri", 14, QFont.Bold))
        dates_layout = QFormLayout()

        self.export_date = QDateEdit()
        self.export_date.setDate(QDate.currentDate())
        self.export_date.setCalendarPopup(True)
        dates_layout.addRow("تاريخ التصدير:", self.export_date)

        self.shipping_date = QDateEdit()
        self.shipping_date.setDate(QDate.currentDate())
        self.shipping_date.setCalendarPopup(True)
        dates_layout.addRow("تاريخ الشحن:", self.shipping_date)

        self.expected_arrival = QDateEdit()
        self.expected_arrival.setDate(QDate.currentDate())
        self.expected_arrival.setCalendarPopup(True)
        dates_layout.addRow("تاريخ الوصول المتوقع:", self.expected_arrival)

        self.actual_arrival = QDateEdit()
        self.actual_arrival.setDate(QDate.currentDate())
        self.actual_arrival.setCalendarPopup(True)
        dates_layout.addRow("تاريخ الوصول الفعلي:", self.actual_arrival)

        dates_group.setLayout(dates_layout)
        main_layout.addWidget(dates_group)

        # ==================== معلومات الشحن ====================
        shipping_group = QGroupBox("معلومات الشحن")
        shipping_group.setFont(QFont("Amiri", 14, QFont.Bold))
        shipping_layout = QFormLayout()

        self.status_combo = QComboBox()
        self.status_combo.addItems([
            "قيد المعالجة",
            "جاهز للشحن",
            "في الميناء",
            "في الطريق",
            "وصل الميناء",
            "تم التسليم",
            "ملغى"
        ])
        shipping_layout.addRow("حالة الشحنة:", self.status_combo)

        self.port_input = QLineEdit()
        self.port_input.setPlaceholderText("اسم الميناء")
        shipping_layout.addRow("الميناء:", self.port_input)

        self.container_input = QLineEdit()
        self.container_input.setPlaceholderText("رقم الحاوية")
        shipping_layout.addRow("رقم الحاوية:", self.container_input)

        self.shipping_line_input = QLineEdit()
        self.shipping_line_input.setPlaceholderText("خط الشحن")
        shipping_layout.addRow("خط الشحن:", self.shipping_line_input)

        self.bl_number_input = QLineEdit()
        self.bl_number_input.setPlaceholderText("رقم B/L")
        shipping_layout.addRow("رقم B/L:", self.bl_number_input)

        self.payment_status_combo = QComboBox()
        self.payment_status_combo.addItems([
            "غير مدفوع",
            "مدفوع جزئياً",
            "مدفوع بالكامل"
        ])
        shipping_layout.addRow("حالة الدفع:", self.payment_status_combo)

        shipping_group.setLayout(shipping_layout)
        main_layout.addWidget(shipping_group)

        # ==================== ملاحظات ====================
        notes_group = QGroupBox("ملاحظات")
        notes_group.setFont(QFont("Amiri", 14, QFont.Bold))
        notes_layout = QVBoxLayout()

        self.notes_input = QTextEdit()
        self.notes_input.setPlaceholderText("أضف أي ملاحظات هنا...")
        self.notes_input.setMaximumHeight(100)
        notes_layout.addWidget(self.notes_input)

        notes_group.setLayout(notes_layout)
        main_layout.addWidget(notes_group)

        # ==================== الأزرار ====================
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(10)

        self.add_btn = QPushButton("➕ إضافة")
        self.add_btn.setMinimumHeight(40)
        self.add_btn.clicked.connect(self.add_record)

        self.update_btn = QPushButton("✏️ تعديل")
        self.update_btn.setMinimumHeight(40)
        self.update_btn.clicked.connect(self.update_record)

        self.delete_btn = QPushButton("🗑️ حذف")
        self.delete_btn.setMinimumHeight(40)
        self.delete_btn.clicked.connect(self.delete_record)

        self.clear_btn = QPushButton("♻️ مسح")
        self.clear_btn.setMinimumHeight(40)
        self.clear_btn.clicked.connect(self.clear_fields)

        self.export_btn = QPushButton("📄 تصدير Excel")
        self.export_btn.setMinimumHeight(40)
        self.export_btn.clicked.connect(self.export_to_excel)

        buttons_layout.addWidget(self.add_btn)
        buttons_layout.addWidget(self.update_btn)
        buttons_layout.addWidget(self.delete_btn)
        buttons_layout.addWidget(self.clear_btn)
        buttons_layout.addWidget(self.export_btn)
        buttons_layout.addStretch()

        main_layout.addLayout(buttons_layout)

        # ==================== الجدول ====================
        self.table = QTableWidget()
        self.table.setColumnCount(12)
        self.table.setHorizontalHeaderLabels([
            "ID", "العميل", "رقم الفاتورة", "المنتج", "الكمية",
            "حالة الشحنة", "تاريخ الشحن", "تاريخ الوصول المتوقع",
            "تاريخ الوصول الفعلي", "الميناء", "رقم الحاوية", "حالة الدفع"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.itemSelectionChanged.connect(self.fill_fields)

        main_layout.addWidget(self.table)
        self.setLayout(main_layout)

        # تحميل العملاء
        self.load_customers()

    def load_customers(self):
        """تحميل قائمة العملاء"""
        self.customer_combo.clear()
        try:
            conn = sqlite3.connect(DB)
            cur = conn.cursor()
            cur.execute("SELECT DISTINCT name FROM customers ORDER BY name")
            rows = cur.fetchall()
            conn.close()
            for row in rows:
                self.customer_combo.addItem(row[0])
        except Exception as e:
            print(f"خطأ في تحميل العملاء: {e}")

    def connect_db(self):
        return sqlite3.connect(DB)

    def load_data(self):
        """تحميل البيانات"""
        self.table.setRowCount(0)
        conn = self.connect_db()
        cur = conn.cursor()
        cur.execute("""
            SELECT id, customer_name, invoice_number, product_name, quantity,
                   status, shipping_date, expected_arrival, actual_arrival,
                   port, container_number, payment_status
            FROM export_followup
            ORDER BY id DESC
        """)
        rows = cur.fetchall()
        conn.close()

        for row_data in rows:
            row = self.table.rowCount()
            self.table.insertRow(row)

            for col, value in enumerate(row_data):
                item = QTableWidgetItem(str(value) if value else "")
                item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(row, col, item)

            # تلوين حسب الحالة
            status = str(row_data[5]).lower() if row_data[5] else ""
            if "تم التسليم" in status or "تم" in status:
                bg = QColor("#C8E6C9")  # أخضر فاتح
            elif "في الطريق" in status or "في الميناء" in status:
                bg = QColor("#BBDEFB")  # أزرق فاتح
            elif "جاهز" in status:
                bg = QColor("#FFF9C4")  # أصفر فاتح
            elif "ملغى" in status:
                bg = QColor("#FFCDD2")  # أحمر فاتح
            else:
                bg = QColor("#F5F5F5")  # رمادي فاتح

            for col in range(12):
                if self.table.item(row, col):
                    self.table.item(row, col).setBackground(bg)

    def add_record(self):
        """إضافة سجل جديد"""
        if not self.customer_combo.currentText().strip():
            QMessageBox.warning(self, "تنبيه", "اسم العميل مطلوب")
            return

        conn = self.connect_db()
        cur = conn.cursor()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cur.execute("""
            INSERT INTO export_followup (
                customer_name, invoice_number, product_name, quantity, unit,
                export_date, shipping_date, expected_arrival, actual_arrival,
                status, port, container_number, shipping_line, bl_number,
                payment_status, notes, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            self.customer_combo.currentText(),
            self.invoice_input.text(),
            self.product_input.text(),
            float(self.quantity_input.text() or 0),
            self.unit_combo.currentText(),
            self.export_date.date().toString("yyyy-MM-dd"),
            self.shipping_date.date().toString("yyyy-MM-dd"),
            self.expected_arrival.date().toString("yyyy-MM-dd"),
            self.actual_arrival.date().toString("yyyy-MM-dd"),
            self.status_combo.currentText(),
            self.port_input.text(),
            self.container_input.text(),
            self.shipping_line_input.text(),
            self.bl_number_input.text(),
            self.payment_status_combo.currentText(),
            self.notes_input.toPlainText(),
            now,
            now
        ))
        conn.commit()
        conn.close()

        QMessageBox.information(self, "تم", "تمت إضافة السجل بنجاح ✅")
        self.load_data()
        self.clear_fields()

    def update_record(self):
        """تعديل سجل"""
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "تنبيه", "اختر سجلاً لتعديله")
            return

        record_id = int(self.table.item(row, 0).text())
        conn = self.connect_db()
        cur = conn.cursor()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cur.execute("""
            UPDATE export_followup SET
                customer_name=?, invoice_number=?, product_name=?, quantity=?, unit=?,
                export_date=?, shipping_date=?, expected_arrival=?, actual_arrival=?,
                status=?, port=?, container_number=?, shipping_line=?, bl_number=?,
                payment_status=?, notes=?, updated_at=?
            WHERE id=?
        """, (
            self.customer_combo.currentText(),
            self.invoice_input.text(),
            self.product_input.text(),
            float(self.quantity_input.text() or 0),
            self.unit_combo.currentText(),
            self.export_date.date().toString("yyyy-MM-dd"),
            self.shipping_date.date().toString("yyyy-MM-dd"),
            self.expected_arrival.date().toString("yyyy-MM-dd"),
            self.actual_arrival.date().toString("yyyy-MM-dd"),
            self.status_combo.currentText(),
            self.port_input.text(),
            self.container_input.text(),
            self.shipping_line_input.text(),
            self.bl_number_input.text(),
            self.payment_status_combo.currentText(),
            self.notes_input.toPlainText(),
            now,
            record_id
        ))
        conn.commit()
        conn.close()

        QMessageBox.information(self, "تم", "تم تعديل السجل بنجاح ✏️")
        self.load_data()
        self.clear_fields()

    def delete_record(self):
        """حذف سجل"""
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "تنبيه", "اختر سجلاً لحذفه")
            return

        record_id = int(self.table.item(row, 0).text())
        reply = QMessageBox.question(
            self, "تأكيد", "هل تريد حذف هذا السجل؟",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return

        conn = self.connect_db()
        cur = conn.cursor()
        cur.execute("DELETE FROM export_followup WHERE id=?", (record_id,))
        conn.commit()
        conn.close()

        QMessageBox.information(self, "تم", "تم حذف السجل بنجاح 🗑️")
        self.load_data()
        self.clear_fields()

    def fill_fields(self):
        """تعبئة الحقول من الجدول"""
        row = self.table.currentRow()
        if row < 0:
            return

        try:
            # تحميل البيانات الكاملة من قاعدة البيانات
            record_id = int(self.table.item(row, 0).text())
            conn = self.connect_db()
            cur = conn.cursor()
            cur.execute("SELECT * FROM export_followup WHERE id=?", (record_id,))
            data = cur.fetchone()
            conn.close()

            if not data:
                return

            # تعبئة الحقول
            customer_name = data[1] or ""
            index = self.customer_combo.findText(customer_name)
            if index >= 0:
                self.customer_combo.setCurrentIndex(index)
            else:
                self.customer_combo.setCurrentText(customer_name)

            self.invoice_input.setText(str(data[2] or ""))
            self.product_input.setText(str(data[3] or ""))
            self.quantity_input.setText(str(data[4] or ""))
            
            unit = str(data[5] or "")
            unit_index = self.unit_combo.findText(unit)
            if unit_index >= 0:
                self.unit_combo.setCurrentIndex(unit_index)

            if data[6]:  # export_date
                self.export_date.setDate(QDate.fromString(data[6], "yyyy-MM-dd"))
            if data[7]:  # shipping_date
                self.shipping_date.setDate(QDate.fromString(data[7], "yyyy-MM-dd"))
            if data[8]:  # expected_arrival
                self.expected_arrival.setDate(QDate.fromString(data[8], "yyyy-MM-dd"))
            if data[9]:  # actual_arrival
                self.actual_arrival.setDate(QDate.fromString(data[9], "yyyy-MM-dd"))

            status = str(data[10] or "")
            status_index = self.status_combo.findText(status)
            if status_index >= 0:
                self.status_combo.setCurrentIndex(status_index)

            self.port_input.setText(str(data[11] or ""))
            self.container_input.setText(str(data[12] or ""))
            self.shipping_line_input.setText(str(data[13] or ""))
            self.bl_number_input.setText(str(data[14] or ""))

            payment_status = str(data[15] or "")
            payment_index = self.payment_status_combo.findText(payment_status)
            if payment_index >= 0:
                self.payment_status_combo.setCurrentIndex(payment_index)

            self.notes_input.setPlainText(str(data[16] or ""))
        except Exception as e:
            QMessageBox.warning(self, "خطأ", f"فشل تحميل البيانات: {str(e)}")

    def clear_fields(self):
        """مسح الحقول"""
        self.customer_combo.setCurrentIndex(-1)
        self.customer_combo.setCurrentText("")
        self.invoice_input.clear()
        self.product_input.clear()
        self.quantity_input.clear()
        self.unit_combo.setCurrentIndex(0)
        self.export_date.setDate(QDate.currentDate())
        self.shipping_date.setDate(QDate.currentDate())
        self.expected_arrival.setDate(QDate.currentDate())
        self.actual_arrival.setDate(QDate.currentDate())
        self.status_combo.setCurrentIndex(0)
        self.port_input.clear()
        self.container_input.clear()
        self.shipping_line_input.clear()
        self.bl_number_input.clear()
        self.payment_status_combo.setCurrentIndex(0)
        self.notes_input.clear()
        self.table.clearSelection()

    def export_to_excel(self):
        """تصدير البيانات إلى Excel"""
        try:
            import pandas as pd
            from openpyxl import load_workbook
        except ImportError:
            QMessageBox.warning(
                self, "مكتبة غير مثبتة",
                "يجب تثبيت pandas و openpyxl:\npip install pandas openpyxl"
            )
            return

        if self.table.rowCount() == 0:
            QMessageBox.warning(self, "تنبيه", "لا توجد بيانات للتصدير")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, "حفظ ملف Excel", "", "Excel Files (*.xlsx)"
        )
        if not file_path:
            return

        try:
            conn = self.connect_db()
            df = pd.read_sql_query("""
                SELECT 
                    id, customer_name, invoice_number, product_name, quantity, unit,
                    export_date, shipping_date, expected_arrival, actual_arrival,
                    status, port, container_number, shipping_line, bl_number,
                    payment_status, notes, created_at, updated_at
                FROM export_followup
                ORDER BY id DESC
            """, conn)
            conn.close()

            df.to_excel(file_path, index=False, engine='openpyxl')
            QMessageBox.information(self, "تم", f"تم تصدير البيانات إلى:\n{file_path}")
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل التصدير:\n{str(e)}")

# pages/AddProductDialog.py
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QLineEdit, QComboBox, QHBoxLayout,
    QPushButton, QMessageBox
)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt
import sqlite3, os
from datetime import datetime

DB = os.path.join(os.path.dirname(__file__), "..", "database", "crm.db")


class AddProductDialog(QDialog):
    """
    نافذة إضافة منتج جديد — تخزين مباشر في قاعدة البيانات
    الحقول:
    - كود المنتج
    - اسم المنتج
    - الوحدة (طن / كيلو)
    - الكمية الابتدائية
    - سعر الشراء
    - العملة
    """

    def __init__(self):
        super().__init__()
        self.setWindowTitle("➕ إضافة منتج جديد")
        self.setMinimumWidth(420)
        # إزالة الستايل الثابت للسماح بتطبيق الستايل من MainWindow
        # self.setStyleSheet("background-color:#FFFBEA;")  # تم إزالة الستايل الثابت
        self.setFont(QFont("Amiri", 11))

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        title = QLabel("إضافة منتج جديد")
        title.setFont(QFont("Amiri", 16, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # ===== الكود =====
        layout.addWidget(QLabel("كود المنتج:"))
        self.code_input = QLineEdit()
        self.code_input.setPlaceholderText("مثل: P-1001")
        layout.addWidget(self.code_input)

        # ===== الاسم =====
        layout.addWidget(QLabel("اسم المنتج:"))
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("اسم المنتج…")
        layout.addWidget(self.name_input)

        # ===== الوحدة =====
        layout.addWidget(QLabel("الوحدة:"))
        self.unit_combo = QComboBox()
        self.unit_combo.addItems(["طن", "كيلو", "وحدة"])
        layout.addWidget(self.unit_combo)

        # ===== الكمية =====
        layout.addWidget(QLabel("الكمية الابتدائية:"))
        self.qty_input = QLineEdit()
        self.qty_input.setPlaceholderText("مثال: 10 أو 5000")
        layout.addWidget(self.qty_input)

        # ===== سعر الشراء =====
        layout.addWidget(QLabel("سعر الشراء (لكل وحدة):"))
        self.buy_price_input = QLineEdit()
        self.buy_price_input.setPlaceholderText("سعر شراء الوحدة")
        layout.addWidget(self.buy_price_input)

        # ===== العملة =====
        layout.addWidget(QLabel("العملة:"))
        self.currency_combo = QComboBox()
        self.currency_combo.addItems(["جنيه مصري - EGP", "دولار - USD"])
        layout.addWidget(self.currency_combo)

        # ===== الأزرار =====
        btns = QHBoxLayout()
        save_btn = QPushButton("💾 حفظ المنتج")
        save_btn.setStyleSheet("background:#4CAF50;color:white;font-weight:bold;")
        save_btn.clicked.connect(self.save_product)

        cancel_btn = QPushButton("إلغاء")
        cancel_btn.setStyleSheet("background:#E53935;color:white;font-weight:bold;")
        cancel_btn.clicked.connect(self.reject)

        btns.addWidget(save_btn)
        btns.addWidget(cancel_btn)

        layout.addLayout(btns)

        self.setLayout(layout)

    def save_product(self):
        code = self.code_input.text().strip()
        name = self.name_input.text().strip()
        unit = self.unit_combo.currentText()
        qty = self.qty_input.text().strip()
        buy_price = self.buy_price_input.text().strip()
        currency = self.currency_combo.currentText()

        # تحقق أساسي
        if not code or not name or not qty or not buy_price:
            QMessageBox.warning(self, "تنبيه", "يجب ملء جميع الحقول.")
            return

        try:
            qty_val = float(qty)
            price_val = float(buy_price)
        except:
            QMessageBox.warning(self, "خطأ", "الكمية أو السعر غير صحيح (ادخل أرقام).")
            return

        try:
            conn = sqlite3.connect(DB)
            cur = conn.cursor()

            # استخدام نفس مخطط جدول المنتجات الموجود
            # نستخدم product_code و code (كلاهما نفس القيمة)
            # إذا كانت العملة EGP نضعها في price_egp، وإذا كانت USD نضعها في price_usd
            price_egp = price_val if "جنيه" in currency or "EGP" in currency else 0
            price_usd = price_val if "دولار" in currency or "USD" in currency else 0
            
            # محاولة إدراج مع product_code أولاً
            try:
                cur.execute("""
                    INSERT INTO products (product_code, code, name, unit, quantity, buy_price, price_egp, price_usd)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (code, code, name, unit, qty_val, price_val, price_egp, price_usd))
            except:
                # إذا فشل، نستخدم code فقط
                try:
                    cur.execute("""
                        INSERT INTO products (code, name, unit, quantity, buy_price, price_egp, price_usd)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (code, name, unit, qty_val, price_val, price_egp, price_usd))
                except:
                    # إذا فشل أيضاً، نستخدم product_code فقط
                    cur.execute("""
                        INSERT INTO products (product_code, name, unit, quantity, price_egp, price_usd)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (code, name, unit, qty_val, price_egp, price_usd))

            conn.commit()
            conn.close()

            QMessageBox.information(self, "تم", "تم حفظ المنتج بنجاح.")
            # نريد أن النافذة تغلق وتعيد قبول حتى يستدعي المستدعي load_products() أو يقوم بتنزيل السطر مباشرة.
            self.accept()

        except Exception as e:
            QMessageBox.critical(self, "DB Error", str(e))

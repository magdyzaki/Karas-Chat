from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QMessageBox, QComboBox, QHeaderView
)
from PyQt5.QtGui import QFont, QColor, QBrush
from PyQt5.QtCore import Qt
import sqlite3, os

DB = os.path.join(os.path.dirname(__file__), "..", "database", "crm.db")


class ProductsPage(QWidget):
    def __init__(self):
        super().__init__()

        # إزالة الستايل الثابت للسماح بتطبيق الستايل من MainWindow
        # self.setStyleSheet("...")  # تم إزالة الستايل الثابت

        layout = QVBoxLayout()
        title = QLabel("📦 إدارة المنتجات")
        title.setFont(QFont("Amiri", 20, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)

        # 🔹 البحث
        search_layout = QHBoxLayout()
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("ابحث باسم المنتج أو الكود...")
        self.search_box.textChanged.connect(self.search_product)
        search_layout.addWidget(self.search_box)

        # 🔹 الحقول
        form_layout = QHBoxLayout()
        self.code_input = QLineEdit(); self.code_input.setPlaceholderText("كود المنتج")
        self.name_input = QLineEdit(); self.name_input.setPlaceholderText("اسم المنتج")
        self.desc_input = QLineEdit(); self.desc_input.setPlaceholderText("الوصف")
        self.qty_input = QLineEdit(); self.qty_input.setPlaceholderText("الكمية")

        # 🔹 قائمة للوحدة
        self.unit_combo = QComboBox()
        self.unit_combo.addItems(["طن", "كجم", "جم", "قطعة", "كرتونة"])

        self.price_egp_input = QLineEdit(); self.price_egp_input.setPlaceholderText("السعر بالجنيه")
        self.price_usd_input = QLineEdit(); self.price_usd_input.setPlaceholderText("السعر بالدولار")
        self.category_input = QLineEdit(); self.category_input.setPlaceholderText("الفئة")

        for w in [
            self.code_input, self.name_input, self.desc_input, self.qty_input,
            self.unit_combo, self.price_egp_input, self.price_usd_input, self.category_input
        ]:
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

        # 🔹 جدول المنتجات
        self.table = QTableWidget()
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels([
            "ID", "كود المنتج", "اسم المنتج", "الوصف", "الكمية", "الوحدة",
            "السعر بالجنيه", "السعر بالدولار", "الفئة"
        ])
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

        # 🔹 قائمة "الترتيب حسب الفئة"
        sort_layout = QHBoxLayout()
        sort_label = QLabel("🔽 ترتيب حسب:")
        sort_label.setFont(QFont("Amiri", 12))
        self.sort_combo = QComboBox()
        self.sort_combo.addItems(["رقم المنتج", "الفئة"])
        self.sort_combo.currentIndexChanged.connect(self.sort_table)

        sort_layout.addWidget(sort_label)
        sort_layout.addWidget(self.sort_combo)
        sort_layout.addStretch()

        # ✅ ترتيب الصفحة
        layout.addWidget(title)
        layout.addLayout(search_layout)
        layout.addLayout(form_layout)
        layout.addLayout(btn_layout)
        layout.addLayout(sort_layout)
        layout.addWidget(self.table)
        self.setLayout(layout)

        # 🔹 توصيل الأزرار
        self.add_btn.clicked.connect(self.add_product)
        self.update_btn.clicked.connect(self.update_product)
        self.delete_btn.clicked.connect(self.delete_product)
        self.clear_btn.clicked.connect(self.clear_fields)

        # التأكد من وجود الأعمدة قبل التحميل
        self.ensure_columns()
        self.load_data()

    # ===================== الوظائف =====================

    def connect_db(self):
        return sqlite3.connect(DB)
    
    def ensure_columns(self):
        """التأكد من وجود جميع الأعمدة المطلوبة"""
        conn = self.connect_db()
        cur = conn.cursor()
        
        # الحصول على الأعمدة الموجودة
        cur.execute("PRAGMA table_info(products)")
        existing_columns = [row[1] for row in cur.fetchall()]
        
        # إضافة الأعمدة المفقودة
        columns_to_add = {
            "description": "TEXT DEFAULT ''",
            "product_code": "TEXT",
            "code": "TEXT DEFAULT ''",
            "category": "TEXT DEFAULT ''",
            "price_egp": "REAL DEFAULT 0",
            "price_usd": "REAL DEFAULT 0",
            "buy_price": "REAL DEFAULT 0"
        }
        
        for col_name, col_type in columns_to_add.items():
            if col_name not in existing_columns:
                try:
                    cur.execute(f"ALTER TABLE products ADD COLUMN {col_name} {col_type}")
                except:
                    pass
        
        conn.commit()
        conn.close()

    def load_data(self):
        self.ensure_columns()  # التأكد من وجود الأعمدة
        self.table.setRowCount(0)
        conn = self.connect_db()
        cur = conn.cursor()
        
        # استخدام SELECT محدد بدلاً من SELECT *
        try:
            cur.execute("""
                SELECT id, product_code, name, description, quantity, unit, 
                       price_egp, price_usd, category
                FROM products
            """)
        except:
            # إذا فشل، نستخدم الأعمدة الأساسية فقط
            try:
                cur.execute("SELECT id, name, quantity, unit FROM products")
            except:
                conn.close()
                return
        
        for row_data in cur.fetchall():
            row = self.table.rowCount()
            self.table.insertRow(row)
            # ملء الأعمدة المتاحة
            for col in range(min(len(row_data), self.table.columnCount())):
                item = QTableWidgetItem(str(row_data[col] if col < len(row_data) else ""))
                item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(row, col, item)
        conn.close()

    def add_product(self):
        try:
            self.ensure_columns()  # التأكد من وجود الأعمدة
            
            code = self.code_input.text()
            name = self.name_input.text()
            desc = self.desc_input.text()
            qty = self.qty_input.text()
            unit = self.unit_combo.currentText()
            price_egp = self.price_egp_input.text()
            price_usd = self.price_usd_input.text()
            category = self.category_input.text()

            if not name or not qty:
                QMessageBox.warning(self, "خطأ", "يرجى إدخال اسم المنتج والكمية على الأقل.")
                return

            conn = self.connect_db()
            cur = conn.cursor()
            
            # محاولة إدراج مع جميع الأعمدة
            try:
                cur.execute("""
                    INSERT INTO products (product_code, name, description, quantity, unit, price_egp, price_usd, category)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (code, name, desc, qty, unit, price_egp, price_usd, category))
            except:
                # إذا فشل، نستخدم الأعمدة الأساسية فقط
                try:
                    cur.execute("""
                        INSERT INTO products (name, quantity, unit, price_egp, price_usd)
                        VALUES (?, ?, ?, ?, ?)
                    """, (name, qty, unit, price_egp or 0, price_usd or 0))
                except:
                    cur.execute("""
                        INSERT INTO products (name, quantity, unit)
                        VALUES (?, ?, ?)
                    """, (name, qty, unit))
            
            conn.commit()
            conn.close()

            self.load_data()
            self.clear_fields()
            QMessageBox.information(self, "تم", "تمت إضافة المنتج بنجاح ✅")
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"حدث خطأ أثناء إضافة المنتج:\n{str(e)}")

    def update_product(self):
        try:
            self.ensure_columns()  # التأكد من وجود الأعمدة
            
            selected = self.table.currentRow()
            if selected < 0:
                QMessageBox.warning(self, "تنبيه", "يرجى اختيار المنتج المراد تعديله.")
                return

            pid_item = self.table.item(selected, 0)
            if not pid_item:
                QMessageBox.warning(self, "تنبيه", "لا يمكن قراءة رقم المنتج.")
                return
                
            pid = int(pid_item.text())
            code = self.code_input.text()
            name = self.name_input.text()
            desc = self.desc_input.text()
            qty = self.qty_input.text()
            unit = self.unit_combo.currentText()
            price_egp = self.price_egp_input.text()
            price_usd = self.price_usd_input.text()
            category = self.category_input.text()

            conn = self.connect_db()
            cur = conn.cursor()
            
            # محاولة التحديث مع جميع الأعمدة
            try:
                cur.execute("""
                    UPDATE products SET
                    product_code=?, name=?, description=?, quantity=?, unit=?, price_egp=?, price_usd=?, category=?
                    WHERE id=?
                """, (code, name, desc, qty, unit, price_egp, price_usd, category, pid))
            except:
                # إذا فشل، نستخدم الأعمدة الأساسية فقط
                try:
                    cur.execute("""
                        UPDATE products SET
                        name=?, quantity=?, unit=?, price_egp=?, price_usd=?
                        WHERE id=?
                    """, (name, qty, unit, price_egp or 0, price_usd or 0, pid))
                except:
                    cur.execute("""
                        UPDATE products SET
                        name=?, quantity=?, unit=?
                        WHERE id=?
                    """, (name, qty, unit, pid))
            
            conn.commit()
            conn.close()

            self.load_data()
            QMessageBox.information(self, "تم", "تم تعديل المنتج بنجاح ✏️")
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"حدث خطأ أثناء تعديل المنتج:\n{str(e)}")

    def delete_product(self):
        selected = self.table.currentRow()
        if selected < 0:
            QMessageBox.warning(self, "تنبيه", "يرجى اختيار المنتج المراد حذفه.")
            return

        pid = int(self.table.item(selected, 0).text())
        confirm = QMessageBox.question(self, "تأكيد", "هل أنت متأكد من حذف هذا المنتج؟", QMessageBox.Yes | QMessageBox.No)
        if confirm == QMessageBox.Yes:
            conn = self.connect_db()
            cur = conn.cursor()
            cur.execute("DELETE FROM products WHERE id=?", (pid,))
            conn.commit()
            conn.close()
            self.load_data()
            QMessageBox.information(self, "تم", "تم حذف المنتج 🗑️")

    def load_selected_row(self, row, _):
        try:
            if row < 0 or row >= self.table.rowCount():
                return
            
            # التحقق من وجود العناصر قبل القراءة
            items = []
            for col in range(9):
                item = self.table.item(row, col)
                items.append(item.text() if item else "")
            
            self.code_input.setText(items[1] if len(items) > 1 else "")
            self.name_input.setText(items[2] if len(items) > 2 else "")
            self.desc_input.setText(items[3] if len(items) > 3 else "")
            self.qty_input.setText(items[4] if len(items) > 4 else "")
            if len(items) > 5 and items[5]:
                self.unit_combo.setCurrentText(items[5])
            self.price_egp_input.setText(items[6] if len(items) > 6 else "")
            self.price_usd_input.setText(items[7] if len(items) > 7 else "")
            self.category_input.setText(items[8] if len(items) > 8 else "")
        except Exception as e:
            # لا نعرض رسالة خطأ هنا لأن هذه دالة يتم استدعاؤها تلقائياً
            pass

    def clear_fields(self):
        for field in [
            self.code_input, self.name_input, self.desc_input,
            self.qty_input, self.price_egp_input, self.price_usd_input, self.category_input
        ]:
            field.clear()
        self.unit_combo.setCurrentIndex(0)
        self.table.clearSelection()

    def search_product(self):
        text = self.search_box.text().lower()
        for row in range(self.table.rowCount()):
            visible = any(text in self.table.item(row, col).text().lower() for col in range(1, 4))
            self.table.setRowHidden(row, not visible)

    def sort_table(self):
        sort_by = self.sort_combo.currentText()
        if sort_by == "رقم المنتج":
            self.table.sortItems(0, Qt.AscendingOrder)
        elif sort_by == "الفئة":
            self.table.sortItems(8, Qt.AscendingOrder)
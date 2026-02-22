# pages/PurchasesPage.py
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton,
    QTableWidget, QTableWidgetItem, QLineEdit, QMessageBox, QHeaderView
)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt
import sqlite3, os
from datetime import datetime
from pages.AddProductDialog import AddProductDialog

DB = os.path.join(os.path.dirname(__file__), "..", "database", "crm.db")


class PurchasesPage(QWidget):

    def __init__(self):
        super().__init__()
        # إزالة الستايل الثابت للسماح بتطبيق الستايل من MainWindow
        # self.setStyleSheet("background-color:#FFFBEA;")  # تم إزالة الستايل الثابت
        self.setFont(QFont("Amiri", 10))

        self.current_purchase_id = None
        # list of products loaded from DB
        self.products = []

        # used to suppress cellChanged recursion
        self._suppress_cell_change = False

        self._ensure_db()
        self.init_ui()
        self.load_suppliers()
        self.load_products()
        self.load_purchases()

    # ===================================================================
    #                      Database Ensure
    # ===================================================================
    def db_conn(self):
        return sqlite3.connect(DB)

    def _ensure_db(self):
        conn = self.db_conn()
        cur = conn.cursor()

        cur.execute("""
            CREATE TABLE IF NOT EXISTS purchases (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                supplier TEXT,
                invoice_no TEXT,
                date TEXT,
                subtotal REAL,
                total REAL,
                note TEXT,
                created_at TEXT
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS purchase_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                purchase_id INTEGER,
                product_id TEXT,
                product_code TEXT,
                product_name TEXT,
                unit TEXT,
                quantity REAL,
                unit_price REAL,
                line_total REAL,
                FOREIGN KEY(purchase_id) REFERENCES purchases(id)
            )
        """)

        # ensure suppliers table exists
        cur.execute("CREATE TABLE IF NOT EXISTS suppliers (id INTEGER PRIMARY KEY, name TEXT)")

        conn.commit()
        conn.close()

    # ===================================================================
    #                            UI
    # ===================================================================
    def init_ui(self):
        layout = QVBoxLayout()

        title = QLabel("📥 صفحة المشتريات")
        title.setFont(QFont("Amiri", 18, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # ---------- الصف العلوي ----------
        top = QHBoxLayout()

        top.addWidget(QLabel("المورد:"))
        self.supplier_combo = QComboBox()
        top.addWidget(self.supplier_combo)

        top.addWidget(QLabel("رقم الفاتورة:"))
        self.invoice_no_input = QLineEdit()
        self.invoice_no_input.setMaximumWidth(150)
        top.addWidget(self.invoice_no_input)

        top.addWidget(QLabel("التاريخ:"))
        self.date_input = QLineEdit(datetime.now().strftime("%Y-%m-%d"))
        self.date_input.setMaximumWidth(120)
        top.addWidget(self.date_input)

        # زر إضافة منتج جديد
        self.add_product_btn = QPushButton("➕ إضافة منتج")
        self.add_product_btn.setStyleSheet("background:#6A1B9A;color:white;")
        self.add_product_btn.clicked.connect(self.open_add_product)
        top.addWidget(self.add_product_btn)

        layout.addLayout(top)

        # ===================================================================
        #                         جدول إضافة المشتريات
        # ===================================================================
        self.items_table = QTableWidget(0, 7)
        self.items_table.setHorizontalHeaderLabels(
            ["كود", "المنتج", "الوحدة", "الكمية", "السعر", "الإجمالي", "حذف"]
        )
        self.items_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.items_table.verticalHeader().setDefaultSectionSize(38)
        self.items_table.setFont(QFont("Amiri", 12))

        # نربط حدث التغيير في الخلايا
        self.items_table.cellChanged.connect(self.on_cell_changed)

        layout.addWidget(self.items_table)

        # ---------- أزرار ----------
        row_btns = QHBoxLayout()

        add_row_btn = QPushButton("＋ أضف سطر")
        add_row_btn.setStyleSheet("background:#4CAF50;color:white;")
        add_row_btn.clicked.connect(self.add_item_row)
        row_btns.addWidget(add_row_btn)

        edit_btn = QPushButton("✏ تعديل الشراء")
        edit_btn.setStyleSheet("background:#FF9800;color:white;")
        # يمكنك لاحقًا ربط وظيفة التعديل هنا
        row_btns.addWidget(edit_btn)

        row_btns.addStretch()
        layout.addLayout(row_btns)

        # ===================================================================
        #                            الإجماليات
        # ===================================================================
        totals_row = QHBoxLayout()

        form = QVBoxLayout()

        self.subtotal_label = QLabel("0.00")
        self.total_label = QLabel("0.00")
        self.note_input = QLineEdit()

        lbl1 = QLabel("Subtotal:")
        lbl1.setAlignment(Qt.AlignCenter)
        form.addWidget(lbl1)
        form.addWidget(self.subtotal_label)

        lbl2 = QLabel("TOTAL:")
        lbl2.setAlignment(Qt.AlignCenter)
        form.addWidget(lbl2)
        form.addWidget(self.total_label)

        lbl3 = QLabel("ملاحظة:")
        lbl3.setAlignment(Qt.AlignCenter)
        form.addWidget(lbl3)
        form.addWidget(self.note_input)

        totals_row.addLayout(form)

        # أزرار الحفظ
        actions = QVBoxLayout()

        save_btn = QPushButton("💾 حفظ الفاتورة")
        save_btn.setStyleSheet("background:#1976D2;color:white;")
        save_btn.clicked.connect(self.save_purchase)
        actions.addWidget(save_btn)

        del_btn = QPushButton("🗑 حذف الفاتورة")
        del_btn.setStyleSheet("background:#E53935;color:white;")
        del_btn.clicked.connect(self.delete_purchase)
        actions.addWidget(del_btn)

        actions.addStretch()
        totals_row.addLayout(actions)

        layout.addLayout(totals_row)

        # ===================================================================
        #                            سجل المشتريات
        # ===================================================================
        layout.addWidget(QLabel("📄 سجل المشتريات"))

        self.purchases_table = QTableWidget(0, 8)
        self.purchases_table.setHorizontalHeaderLabels([
            "ID", "المورد", "رقم الفاتورة", "التاريخ",
            "الإجمالي", "ملاحظة", "تاريخ الإدخال", "عرض"
        ])
        self.purchases_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.purchases_table.verticalHeader().setDefaultSectionSize(34)
        self.purchases_table.setFont(QFont("Amiri", 11))
        layout.addWidget(self.purchases_table)

        self.setLayout(layout)

    # ===================================================================
    #                      إضافة منتج جديد عبر نافذة
    # ===================================================================
    def open_add_product(self):
        try:
            dlg = AddProductDialog()
            if dlg.exec_():
                # حدثنا قائمة المنتجات
                self.load_products()

                # نأخذ آخر منتج تم إدخاله وننزل سطرًا له
                if self.products:
                    last = self.products[-1]
                    # products = list of tuples (code, name, unit, buy_price)
                    try:
                        code, name, unit, buy_price = last
                    except:
                        QMessageBox.warning(self, "تنبيه", "خطأ في قراءة بيانات المنتج.")
                        return

                # نستخدم الكمية والسعر من الديالوج لو كانت موجودة (لكن AddProductDialog أغلق بـ accept)
                # بصراحة هنا لا نملك قيم dlg بعد الإغلاق، فسننزل السطر مع qty=0 كي يمكن للمستخدم تعديلها يدوياً،
                # ولكن لو أردت تخزين qty من dialog يجب إعادة تصميم ليعيد القيم أو حفظها في مكان مشترك.
                r = self.items_table.rowCount()
                self.items_table.insertRow(r)

                # الكود
                it0 = QTableWidgetItem(str(code))
                it0.setTextAlignment(Qt.AlignCenter)
                it0.setFlags(it0.flags() & ~Qt.ItemIsEditable)  # اجعل الكود غير قابل للتعديل
                self.items_table.setItem(r, 0, it0)

                # الاسم
                it1 = QTableWidgetItem(str(name))
                it1.setTextAlignment(Qt.AlignCenter)
                it1.setFlags(it1.flags() & ~Qt.ItemIsEditable)
                self.items_table.setItem(r, 1, it1)

                # الوحدة
                it2 = QTableWidgetItem(str(unit))
                it2.setTextAlignment(Qt.AlignCenter)
                it2.setFlags(it2.flags() & ~Qt.ItemIsEditable)
                self.items_table.setItem(r, 2, it2)

                # الكمية (قابلة للتحرير)
                it3 = QTableWidgetItem("0")
                it3.setTextAlignment(Qt.AlignCenter)
                self.items_table.setItem(r, 3, it3)

                # السعر (قابلة للتحرير)
                it4 = QTableWidgetItem(str(buy_price))
                it4.setTextAlignment(Qt.AlignCenter)
                self.items_table.setItem(r, 4, it4)

                # الإجمالي (غير قابل للتحرير)
                it5 = QTableWidgetItem("0.00")
                it5.setFlags(it5.flags() & ~Qt.ItemIsEditable)
                it5.setTextAlignment(Qt.AlignCenter)
                self.items_table.setItem(r, 5, it5)

                # زر حذف
                btn = QPushButton("✖")
                btn.setStyleSheet("background:#C62828;color:white;")
                btn.clicked.connect(lambda _, row=r: self.remove_row(row))
                self.items_table.setCellWidget(r, 6, btn)

                # حدث حساب الاجمالى
                self.update_totals()

                QMessageBox.information(self, "✔", "تمت إضافة المنتج إلى جدول المشتريات.")
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"حدث خطأ أثناء فتح نافذة إضافة المنتج:\n{str(e)}")

    # ===================================================================
    #                      تحميل الموردين
    # ===================================================================
    def load_suppliers(self):
        self.supplier_combo.clear()
        try:
            conn = self.db_conn()
            cur = conn.cursor()
            cur.execute("SELECT DISTINCT name FROM suppliers ORDER BY name")
            rows = cur.fetchall()
            conn.close()

            if rows:
                for r in rows:
                    self.supplier_combo.addItem(r[0])
            else:
                self.supplier_combo.addItem("— لا موردين —")

        except:
            self.supplier_combo.addItem("— خطأ —")

    # ===================================================================
    #                  تحميل المنتجات
    # ===================================================================
    def load_products(self):
        try:
            conn = self.db_conn()
            cur = conn.cursor()
            # محاولة استخدام code أولاً، وإذا لم يكن موجوداً نستخدم product_code
            try:
                cur.execute("SELECT code, name, unit, buy_price FROM products ORDER BY name")
                self.products = cur.fetchall()
            except:
                # إذا لم يكن عمود code موجوداً، نستخدم product_code
                cur.execute("SELECT product_code, name, unit, buy_price FROM products ORDER BY name")
                self.products = cur.fetchall()
            conn.close()
        except:
            self.products = []

    # ===================================================================
    #                         إضافة سطر فارغ
    # ===================================================================
    def add_item_row(self):
        r = self.items_table.rowCount()
        self.items_table.insertRow(r)

        # نملأ الأعمدة افتراضياً — الخلايا 3 و4 قابلة للتحرير
        for c in range(7):
            if c == 6:
                btn = QPushButton("✖")
                btn.setStyleSheet("background:#C62828;color:white;")
                btn.clicked.connect(lambda _, row=r: self.remove_row(row))
                self.items_table.setCellWidget(r, 6, btn)
            elif c == 3:  # quantity
                item = QTableWidgetItem("0")
                item.setTextAlignment(Qt.AlignCenter)
                self.items_table.setItem(r, c, item)
            elif c == 4:  # price
                item = QTableWidgetItem("0")
                item.setTextAlignment(Qt.AlignCenter)
                self.items_table.setItem(r, c, item)
            elif c == 5:  # line total
                item = QTableWidgetItem("0.00")
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                item.setTextAlignment(Qt.AlignCenter)
                self.items_table.setItem(r, c, item)
            else:
                item = QTableWidgetItem("")
                item.setTextAlignment(Qt.AlignCenter)
                # أول عمود الكود نجعله قابل للكتابة في حال أردت لصق كود
                self.items_table.setItem(r, c, item)

    def remove_row(self, row):
        try:
            # إزالة صف وتحديث الإجماليات
            if row >= 0 and row < self.items_table.rowCount():
                self.items_table.removeRow(row)
                self.update_totals()
        except Exception as e:
            QMessageBox.warning(self, "تنبيه", f"حدث خطأ أثناء حذف الصف:\n{str(e)}")

    # ===================================================================
    #                     حساب الإجماليات (محمي ضد recursion)
    # ===================================================================
    def update_totals(self):
        subtotal = 0.0

        # قمع إشعارات التغيير أثناء التحديث
        self._suppress_cell_change = True
        try:
            for r in range(self.items_table.rowCount()):
                try:
                    qty_item = self.items_table.item(r, 3)
                    price_item = self.items_table.item(r, 4)
                    total_item = self.items_table.item(r, 5)

                    qty = float(qty_item.text()) if qty_item and qty_item.text() else 0.0
                    price = float(price_item.text()) if price_item and price_item.text() else 0.0
                    line = qty * price
                    subtotal += line

                    # تحديث النص في عمود الإجمالي
                    if total_item is None:
                        total_item = QTableWidgetItem(f"{line:.2f}")
                        total_item.setFlags(total_item.flags() & ~Qt.ItemIsEditable)
                        total_item.setTextAlignment(Qt.AlignCenter)
                        self.items_table.setItem(r, 5, total_item)
                    else:
                        total_item.setText(f"{line:.2f}")

                except Exception:
                    # تجاهل صفوف غير صالحة مؤقتاً
                    pass

            self.subtotal_label.setText(f"{subtotal:.2f}")
            self.total_label.setText(f"{subtotal:.2f}")

        finally:
            # إعادة تفعيل إشعارات التغيير
            self._suppress_cell_change = False

    # ===================================================================
    #                 استجابة لتغيير خلية في الجدول
    # ===================================================================
    def on_cell_changed(self, row, column):
        # إذا كان القمع مفعل فلا نفعل شيء
        if getattr(self, "_suppress_cell_change", False):
            return

        # نريد أن التغيير في عمود الكمية أو السعر يسبب إعادة حساب
        try:
            if column in (3, 4):  # qty or price changed
                # نقرأ القيم ونحدث الإجمالي لذلك الصف
                qty_item = self.items_table.item(row, 3)
                price_item = self.items_table.item(row, 4)
                total_item = self.items_table.item(row, 5)

                try:
                    qty = float(qty_item.text()) if qty_item and qty_item.text() else 0.0
                except:
                    qty = 0.0
                try:
                    price = float(price_item.text()) if price_item and price_item.text() else 0.0
                except:
                    price = 0.0

                line = qty * price

                # منع إعادة استدعاء أثناء الكتابة
                self._suppress_cell_change = True
                if total_item is None:
                    total_item = QTableWidgetItem(f"{line:.2f}")
                    total_item.setFlags(total_item.flags() & ~Qt.ItemIsEditable)
                    total_item.setTextAlignment(Qt.AlignCenter)
                    self.items_table.setItem(row, 5, total_item)
                else:
                    total_item.setText(f"{line:.2f}")
                self._suppress_cell_change = False

                # وأخيراً نحدث الإجماليات الكلية
                self.update_totals()

        except Exception:
            pass

    # ===================================================================
    #                         حفظ الفاتورة
    # ===================================================================
    def save_purchase(self):
        supplier = self.supplier_combo.currentText()
        invoice_no = self.invoice_no_input.text().strip()
        date = self.date_input.text().strip()
        note = self.note_input.text().strip()

        try:
            subtotal = float(self.subtotal_label.text())
        except:
            subtotal = 0.0
        total = subtotal

        if self.items_table.rowCount() == 0:
            QMessageBox.warning(self, "تنبيه", "أضف سطوراً قبل الحفظ.")
            return

        try:
            conn = self.db_conn()
            cur = conn.cursor()

            cur.execute("""
                INSERT INTO purchases (supplier, invoice_no, date, subtotal, total, note, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (supplier, invoice_no, date, subtotal, total, note, datetime.now().isoformat()))

            purchase_id = cur.lastrowid

            # حفظ السطور — نستخدم product_id = NULL لأنه قد لا يكون معرفًا
            for r in range(self.items_table.rowCount()):
                code = self.items_table.item(r, 0).text() if self.items_table.item(r, 0) else ""
                name = self.items_table.item(r, 1).text() if self.items_table.item(r, 1) else ""
                unit = self.items_table.item(r, 2).text() if self.items_table.item(r, 2) else ""
                try:
                    qty = float(self.items_table.item(r, 3).text() or 0)
                except:
                    qty = 0.0
                try:
                    price = float(self.items_table.item(r, 4).text() or 0)
                except:
                    price = 0.0
                line_total = qty * price

                # نحاول ملاءمة أسماء الأعمدة الموجودة عندك في DB
                cur.execute("""
                    INSERT INTO purchase_items (
                        purchase_id, product_id, product_code, product_name, unit, quantity, unit_price, line_total
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (purchase_id, None, code, name, unit, qty, price, line_total))

            conn.commit()
            conn.close()

            QMessageBox.information(self, "تم", f"تم حفظ الفاتورة رقم {purchase_id}")
            # بعد الحفظ نفرغ الجدول الحالي ونحدث سجل المشتريات
            self.items_table.setRowCount(0)
            self.subtotal_label.setText("0.00")
            self.total_label.setText("0.00")
            self.load_purchases()

        except Exception as e:
            QMessageBox.critical(self, "DB Error", str(e))

    # ===================================================================
    #                      سجل المشتريات
    # ===================================================================
    def load_purchases(self):
        self.purchases_table.setRowCount(0)

        conn = self.db_conn()
        cur = conn.cursor()
        cur.execute("SELECT id, supplier, invoice_no, date, total, note, created_at FROM purchases ORDER BY id DESC")
        rows = cur.fetchall()
        conn.close()

        for r_data in rows:
            r = self.purchases_table.rowCount()
            self.purchases_table.insertRow(r)

            for c, val in enumerate(r_data):
                item = QTableWidgetItem(str(val))
                item.setTextAlignment(Qt.AlignCenter)
                self.purchases_table.setItem(r, c, item)

            # زر عرض
            btn = QPushButton("عرض")
            btn.setStyleSheet("background:#1E88E5;color:white;")
            self.purchases_table.setCellWidget(r, 7, btn)

    # ===================================================================
    #                      حذف مشتريات
    # ===================================================================
    def delete_purchase(self):
        try:
            items = self.purchases_table.selectedItems()
            if not items:
                QMessageBox.warning(self, "تنبيه", "اختر فاتورة.")
                return

            row = items[0].row()
            if row < 0 or row >= self.purchases_table.rowCount():
                QMessageBox.warning(self, "تنبيه", "الصف المحدد غير صحيح.")
                return
                
            pid_item = self.purchases_table.item(row, 0)
            if not pid_item:
                QMessageBox.warning(self, "تنبيه", "لا يمكن قراءة رقم الفاتورة.")
                return
                
            pid = pid_item.text()

            confirm = QMessageBox.question(self, "تأكيد", f"هل تريد حذف الفاتورة رقم {pid}؟",
                                           QMessageBox.Yes | QMessageBox.No)
            if confirm != QMessageBox.Yes:
                return

            conn = self.db_conn()
            cur = conn.cursor()
            cur.execute("DELETE FROM purchase_items WHERE purchase_id=?", (pid,))
            cur.execute("DELETE FROM purchases WHERE id=?", (pid,))
            conn.commit()
            conn.close()

            QMessageBox.information(self, "تم", "تم حذف الفاتورة.")
            self.load_purchases()
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"حدث خطأ أثناء حذف الفاتورة:\n{str(e)}")

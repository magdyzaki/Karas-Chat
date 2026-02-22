from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QComboBox, QTableWidget, QTableWidgetItem, QMessageBox, QHeaderView
)
from PyQt5.QtGui import QFont, QColor, QBrush
from PyQt5.QtCore import Qt, QDateTime
import sqlite3, os

DB = os.path.join(os.path.dirname(__file__), "..", "database", "crm.db")


class SalesPage(QWidget):
    def __init__(self):
        super().__init__()

        # إزالة الستايل الثابت للسماح بتطبيق الستايل من MainWindow
        # self.setStyleSheet("...")  # تم إزالة الستايل الثابت

        layout = QVBoxLayout()

        title = QLabel("💰 إدارة المبيعات")
        title.setFont(QFont("Amiri", 20, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # ================== الحقول ==================
        form_layout = QHBoxLayout()

        self.customer_combo = QComboBox()
        self.customer_combo.setFont(QFont("Amiri", 12))

        self.product_combo = QComboBox()
        self.product_combo.setFont(QFont("Amiri", 12))

        self.qty_input = QLineEdit()
        self.qty_input.setPlaceholderText("الكمية")

        self.unit_combo = QComboBox()
        self.unit_combo.addItems(["طن", "كجم", "جم"])

        self.return_input = QLineEdit()
        self.return_input.setPlaceholderText("المرتجع")

        self.exchange_input = QLineEdit()
        self.exchange_input.setPlaceholderText("سعر الصرف")

        for w in [
            self.customer_combo, self.product_combo, self.qty_input,
            self.unit_combo, self.return_input, self.exchange_input
        ]:
            form_layout.addWidget(w)

        layout.addLayout(form_layout)

        # ================== الأزرار ==================
        btn_layout = QHBoxLayout()

        self.add_btn = QPushButton("➕ إضافة")
        self.add_btn.setStyleSheet("background:#4CAF50;color:white;")

        self.edit_btn = QPushButton("✏️ تعديل")
        self.edit_btn.setStyleSheet("background:#2196F3;color:white;")

        self.delete_btn = QPushButton("🗑️ حذف")
        self.delete_btn.setStyleSheet("background:#F44336;color:white;")

        self.refresh_btn = QPushButton("🔄 تحديث")
        self.refresh_btn.setStyleSheet("background:#FFD700;color:black;")

        self.clear_btn = QPushButton("♻️ مسح")
        self.clear_btn.setStyleSheet("background:#9C27B0;color:white;")

        for b in [self.add_btn, self.edit_btn, self.delete_btn, self.refresh_btn, self.clear_btn]:
            b.setFont(QFont("Amiri", 12, QFont.Bold))
            b.setFixedHeight(40)
            btn_layout.addWidget(b)

        layout.addLayout(btn_layout)

        # ================== الجدول ==================
        self.table = QTableWidget()
        self.table.setColumnCount(14)
        self.table.setHorizontalHeaderLabels([
            "ID", "كود العميل", "اسم العميل", "كود المنتج", "اسم المنتج",
            "الوحدة", "الكمية", "سعر جنيه", "سعر دولار",
            "سعر الصرف", "إجمالي جنيه", "إجمالي دولار", "مرتجع", "التاريخ"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table)

        self.setLayout(layout)

        # ================== ربط الأحداث ==================
        self.add_btn.clicked.connect(self.add_sale)
        self.edit_btn.clicked.connect(self.edit_sale)
        self.delete_btn.clicked.connect(self.delete_sale)
        self.refresh_btn.clicked.connect(self.refresh_all)
        self.clear_btn.clicked.connect(self.clear_fields)
        self.table.itemSelectionChanged.connect(self.fill_inputs_from_table)

        # تحميل مبدئي
        self.refresh_all()

    # ================== DB ==================
    def connect_db(self):
        return sqlite3.connect(DB)

    # ================== تحميل العملاء ==================
    def load_customers(self):
        conn = self.connect_db()
        cur = conn.cursor()
        cur.execute("SELECT id, name FROM customers")
        rows = cur.fetchall()
        conn.close()

        self.customer_combo.blockSignals(True)
        self.customer_combo.clear()
        for cid, name in rows:
            self.customer_combo.addItem(f"{name} (ID:{cid})", cid)
        self.customer_combo.blockSignals(False)

    # ================== تحميل المنتجات ==================
    def load_products(self):
        conn = self.connect_db()
        cur = conn.cursor()
        cur.execute("""
            SELECT id, name, product_code, price_egp, price_usd, unit
            FROM products
        """)
        rows = cur.fetchall()
        conn.close()

        self.product_combo.blockSignals(True)
        self.product_combo.clear()
        for pid, name, code, egp, usd, unit in rows:
            self.product_combo.addItem(
                f"{name} (Code:{code})",
                (pid, code, egp or 0, usd or 0, unit)
            )
        self.product_combo.blockSignals(False)

    # ================== تحديث شامل ==================
    def refresh_all(self):
        self.load_customers()
        self.load_products()
        self.load_sales()

    # ================== تحميل المبيعات ==================
    def load_sales(self):
        self.table.setRowCount(0)
        conn = self.connect_db()
        cur = conn.cursor()
        cur.execute("""
            SELECT 
                id, customer_id, customer_name, product_code, product_name,
                unit, quantity, price_egp, price_usd, exchange_rate,
                total_egp, total_usd, return_qty, sale_date
            FROM sales
            ORDER BY id DESC
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

            if float(row_data[12] or 0) > 0:
                for c in range(len(row_data)):
                    self.table.item(r, c).setBackground(QBrush(QColor("#E8F5E9")))

    # ================== تعبئة الحقول ==================
    def fill_inputs_from_table(self):
        try:
            r = self.table.currentRow()
            if r < 0:
                return
            
            # التحقق من وجود العناصر
            if not all(self.table.item(r, col) for col in [5, 6, 9, 12]):
                return
            
            # تعبئة الحقول الأساسية
            self.qty_input.setText(self.table.item(r, 6).text() or "0")
            self.return_input.setText(self.table.item(r, 12).text() or "0")
            self.exchange_input.setText(self.table.item(r, 9).text() or "0")
            self.unit_combo.setCurrentText(self.table.item(r, 5).text() or "طن")
            
            # محاولة تحديد العميل في القائمة المنسدلة
            try:
                customer_id_item = self.table.item(r, 1)  # customer_id في العمود 1
                if customer_id_item and customer_id_item.text():
                    customer_id = int(customer_id_item.text())
                    for i in range(self.customer_combo.count()):
                        if self.customer_combo.itemData(i) == customer_id:
                            self.customer_combo.setCurrentIndex(i)
                            break
            except (ValueError, AttributeError):
                pass
                
            # محاولة تحديد المنتج في القائمة المنسدلة
            try:
                # نستخدم اسم المنتج أو كود المنتج
                product_name_item = self.table.item(r, 4)  # product_name في العمود 4
                if product_name_item and product_name_item.text():
                    product_name = product_name_item.text()
                    for i in range(self.product_combo.count()):
                        combo_text = self.product_combo.itemText(i)
                        if product_name in combo_text or combo_text.startswith(product_name):
                            self.product_combo.setCurrentIndex(i)
                            break
            except (ValueError, AttributeError):
                pass
        except Exception as e:
            # لا نعرض رسالة خطأ هنا لأن هذه دالة يتم استدعاؤها تلقائياً
            pass

    # ================== إضافة بيع ==================
    def add_sale(self):
        try:
            if self.customer_combo.currentIndex() < 0 or self.product_combo.currentIndex() < 0:
                QMessageBox.warning(self, "تنبيه", "اختر عميل ومنتج.")
                return

            customer_id = self.customer_combo.currentData()
            if customer_id is None:
                QMessageBox.warning(self, "تنبيه", "العميل المحدد غير صحيح.")
                return
            customer_name = self.customer_combo.currentText().split(" (")[0]

            product_data = self.product_combo.currentData()
            if product_data is None:
                QMessageBox.warning(self, "تنبيه", "المنتج المحدد غير صحيح.")
                return
            try:
                product_id, product_code, p_egp, p_usd, _ = product_data
            except (ValueError, TypeError):
                QMessageBox.warning(self, "تنبيه", "خطأ في قراءة بيانات المنتج.")
                return
            product_name = self.product_combo.currentText().split(" (")[0]

            qty = float(self.qty_input.text() or 0)
            return_qty = float(self.return_input.text() or 0)
            exchange_rate = float(self.exchange_input.text() or 0)
            unit = self.unit_combo.currentText()

            if unit == "كجم":
                p_egp /= 1000
                p_usd /= 1000
            elif unit == "جم":
                p_egp /= 1_000_000
                p_usd /= 1_000_000

            net_qty = max(qty - return_qty, 0)
            total_egp = round(net_qty * p_egp, 2)
            total_usd = round(net_qty * p_usd, 2)
            sale_date = QDateTime.currentDateTime().toString("yyyy-MM-dd HH:mm:ss")

            conn = self.connect_db()
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO sales (
                    customer_id, customer_name,
                    product_id, product_name, product_code,
                    unit, quantity,
                    price_egp, price_usd, exchange_rate,
                    total_egp, total_usd, return_qty, sale_date
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                customer_id, customer_name,
                product_id, product_name, product_code,
                unit, qty,
                p_egp, p_usd, exchange_rate,
                total_egp, total_usd, return_qty, sale_date
            ))
            conn.commit()
            conn.close()

            self.refresh_all()
            self.clear_fields()
            QMessageBox.information(self, "تم", "✅ تمت إضافة عملية البيع بنجاح")

        except Exception as e:
            QMessageBox.critical(self, "خطأ", str(e))

    # ================== تعديل ==================
    def edit_sale(self):
        try:
            r = self.table.currentRow()
            if r < 0:
                QMessageBox.warning(self, "تنبيه", "اختر عملية بيع لتعديلها.")
                return

            sale_id_item = self.table.item(r, 0)
            if not sale_id_item:
                QMessageBox.warning(self, "تنبيه", "لا يمكن قراءة رقم عملية البيع.")
                return
                
            sale_id = int(sale_id_item.text())

            if self.customer_combo.currentIndex() < 0 or self.product_combo.currentIndex() < 0:
                QMessageBox.warning(self, "تنبيه", "اختر عميل ومنتج.")
                return

            # التحقق من البيانات
            customer_data = self.customer_combo.currentData()
            product_data = self.product_combo.currentData()
            
            if customer_data is None:
                QMessageBox.warning(self, "تنبيه", "العميل المحدد غير صحيح.")
                return
                
            if product_data is None:
                QMessageBox.warning(self, "تنبيه", "المنتج المحدد غير صحيح.")
                return

            try:
                qty = float(self.qty_input.text() or 0)
                return_qty = float(self.return_input.text() or 0)
                exchange_rate = float(self.exchange_input.text() or 0)
            except ValueError:
                QMessageBox.warning(self, "تنبيه", "يرجى إدخال أرقام صحيحة في الحقول.")
                return
                
            unit = self.unit_combo.currentText()

            try:
                product_id, product_code, p_egp, p_usd, _ = product_data
                product_name = self.product_combo.currentText().split(" (")[0]
                customer_name = self.customer_combo.currentText().split(" (")[0]
            except (ValueError, TypeError) as e:
                QMessageBox.warning(self, "تنبيه", f"خطأ في قراءة بيانات المنتج أو العميل:\n{str(e)}")
                return

            if unit == "كجم":
                p_egp /= 1000
                p_usd /= 1000
            elif unit == "جم":
                p_egp /= 1_000_000
                p_usd /= 1_000_000

            net_qty = max(qty - return_qty, 0)
            total_egp = round(net_qty * p_egp, 2)
            total_usd = round(net_qty * p_usd, 2)

            conn = self.connect_db()
            cur = conn.cursor()
            cur.execute("""
                UPDATE sales SET
                    customer_name=?, product_name=?, product_code=?,
                    unit=?, quantity=?, price_egp=?, price_usd=?,
                    exchange_rate=?, total_egp=?, total_usd=?, return_qty=?
                WHERE id=?
            """, (
                customer_name, product_name, product_code,
                unit, qty, p_egp, p_usd,
                exchange_rate, total_egp, total_usd, return_qty,
                sale_id
            ))
            conn.commit()
            conn.close()

            self.refresh_all()
            QMessageBox.information(self, "تم", "✅ تم تعديل عملية البيع بنجاح")
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"حدث خطأ أثناء تعديل عملية البيع:\n{str(e)}")

    # ================== حذف ==================
    def delete_sale(self):
        try:
            r = self.table.currentRow()
            if r < 0:
                QMessageBox.warning(self, "تنبيه", "اختر عملية بيع لحذفها.")
                return
                
            sale_id_item = self.table.item(r, 0)
            if not sale_id_item:
                QMessageBox.warning(self, "تنبيه", "لا يمكن قراءة رقم عملية البيع.")
                return
                
            sale_id = int(sale_id_item.text())
            
            if QMessageBox.question(self, "تأكيد", f"هل تريد حذف عملية البيع رقم {sale_id}؟",
                                   QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
                conn = self.connect_db()
                cur = conn.cursor()
                cur.execute("DELETE FROM sales WHERE id=?", (sale_id,))
                conn.commit()
                conn.close()
                self.refresh_all()
                QMessageBox.information(self, "تم", "✅ تم حذف عملية البيع بنجاح")
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"حدث خطأ أثناء حذف عملية البيع:\n{str(e)}")

    # ================== مسح الحقول ==================
    def clear_fields(self):
        self.qty_input.clear()
        self.return_input.clear()
        self.exchange_input.clear()
        self.unit_combo.setCurrentIndex(0)

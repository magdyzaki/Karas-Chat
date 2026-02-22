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

        # 🎨 ستايل موحد مثل العملاء
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
        title = QLabel("💰 إدارة المبيعات")
        title.setFont(QFont("Amiri", 20, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)

        # 🔹 الحقول العليا
        form_layout = QHBoxLayout()

        self.customer_combo = QComboBox()
        self.customer_combo.setPlaceholderText("اسم العميل")
        self.load_customers()

        self.product_combo = QComboBox()
        self.product_combo.setPlaceholderText("اسم المنتج")
        self.load_products()

        self.qty_input = QLineEdit()
        self.qty_input.setPlaceholderText("الكمية")

        self.unit_combo = QComboBox()
        self.unit_combo.addItems(["طن", "كجم", "جم", "قطعة", "كرتونة"])

        self.return_input = QLineEdit()
        self.return_input.setPlaceholderText("المرتجع")

        self.exchange_input = QLineEdit()
        self.exchange_input.setPlaceholderText("سعر صرف الدولار")

        for w in [self.customer_combo, self.product_combo, self.qty_input,
                  self.unit_combo, self.return_input, self.exchange_input]:
            w.setFont(QFont("Amiri", 12))
            form_layout.addWidget(w)

        layout.addWidget(title)
        layout.addLayout(form_layout)

        # 🔹 الأزرار
        btn_layout = QHBoxLayout()
        self.add_btn = QPushButton("➕ إضافة")
        self.add_btn.setStyleSheet("background-color:#4CAF50;color:white;")

        self.edit_btn = QPushButton("✏️ تعديل")
        self.edit_btn.setStyleSheet("background-color:#2196F3;color:white;")

        self.delete_btn = QPushButton("🗑️ حذف")
        self.delete_btn.setStyleSheet("background-color:#F44336;color:white;")

        self.refresh_btn = QPushButton("🔄 تحديث")
        self.refresh_btn.setStyleSheet("background-color:#FFD700;color:black;")

        self.clear_btn = QPushButton("♻️ مسح")
        self.clear_btn.setStyleSheet("background-color:#9C27B0;color:white;")

        for btn in [self.add_btn, self.edit_btn, self.delete_btn, self.refresh_btn, self.clear_btn]:
            btn.setFont(QFont("Amiri", 12, QFont.Bold))
            btn.setFixedHeight(40)
            btn_layout.addWidget(btn)

        layout.addLayout(btn_layout)

        # 🔹 الجدول
        self.table = QTableWidget()
        self.table.setColumnCount(14)
        self.table.setHorizontalHeaderLabels([
            "ID", "كود العميل", "اسم العميل", "كود المنتج", "اسم المنتج",
            "الوحدة", "الكمية", "السعر بالجنيه", "السعر بالدولار",
            "سعر الصرف", "إجمالي بالجنيه", "إجمالي بالدولار", "المرتجع", "تاريخ البيع"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
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

        layout.addWidget(self.table)
        self.setLayout(layout)

        # 🔹 ربط الأحداث
        self.add_btn.clicked.connect(self.add_sale)
        self.edit_btn.clicked.connect(self.edit_sale)
        self.delete_btn.clicked.connect(self.delete_sale)
        self.refresh_btn.clicked.connect(self.load_sales)
        self.clear_btn.clicked.connect(self.clear_fields)
        self.table.itemSelectionChanged.connect(self.fill_inputs_from_table)

        self.load_sales()

    # ==================== قواعد البيانات ====================
    def connect_db(self):
        return sqlite3.connect(DB)

    def load_customers(self):
        conn = self.connect_db()
        cur = conn.cursor()
        cur.execute("SELECT id, name FROM customers")
        self.customer_combo.clear()
        for cid, name in cur.fetchall():
            self.customer_combo.addItem(f"{name} (ID:{cid})", cid)
        conn.close()

    def load_products(self):
        conn = self.connect_db()
        cur = conn.cursor()
        cur.execute("SELECT id, name, product_code, price_egp, price_usd, unit FROM products")
        self.product_combo.clear()
        for pid, name, code, egp, usd, unit in cur.fetchall():
            self.product_combo.addItem(f"{name} (Code:{code})", (pid, code, egp, usd, unit))
        conn.close()

    # ==================== تحميل المبيعات ====================
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
        """)
        for row_data in cur.fetchall():
            row = self.table.rowCount()
            self.table.insertRow(row)
            for col, data in enumerate(row_data):
                item = QTableWidgetItem(str(data))
                item.setTextAlignment(Qt.AlignCenter)

                if col == 12 and float(row_data[12]) > 0:
                    for i in range(len(row_data)):
                        self.table.setItem(row, i, QTableWidgetItem(str(row_data[i])))
                        self.table.item(row, i).setBackground(QBrush(QColor("#DFFFD6")))
                else:
                    self.table.setItem(row, col, item)
        conn.close()

    # ==================== تعبئة الحقول عند اختيار صف ====================
    def fill_inputs_from_table(self):
        row = self.table.currentRow()
        if row < 0:
            return
        self.customer_combo.setCurrentText(self.table.item(row, 2).text())
        self.product_combo.setCurrentText(self.table.item(row, 4).text())
        self.unit_combo.setCurrentText(self.table.item(row, 5).text())
        self.qty_input.setText(self.table.item(row, 6).text())
        self.return_input.setText(self.table.item(row, 12).text())
        self.exchange_input.setText(self.table.item(row, 9).text())

    # ==================== إضافة عملية بيع ====================
    def add_sale(self):
        try:
            customer_data = self.customer_combo.currentData()
            product_data = self.product_combo.currentData()
            qty = float(self.qty_input.text().strip() or 0)
            return_qty = float(self.return_input.text().strip() or 0)
            exchange_rate = float(self.exchange_input.text().strip() or 0)
            unit_selected = self.unit_combo.currentText()

            if not customer_data or not product_data:
                QMessageBox.warning(self, "خطأ", "يجب اختيار عميل ومنتج.")
                return

            customer_id = customer_data
            customer_name = self.customer_combo.currentText().split(" (")[0]
            product_id, product_code, p_egp, p_usd, unit = product_data
            product_name = self.product_combo.currentText().split(" (")[0]

            p_egp = float(p_egp or 0)
            p_usd = float(p_usd or 0)

            # ✅ تعديل السعر بناءً على الوحدة
            if unit_selected == "كجم":
                p_egp /= 1000
                p_usd /= 1000
                QMessageBox.information(self, "تحويل السعر", "💡 تم تعديل السعر تلقائيًا بناءً على الوحدة (كجم).")
            elif unit_selected == "جم":
                p_egp /= 1000000
                p_usd /= 1000000
                QMessageBox.information(self, "تحويل السعر", "💡 تم تعديل السعر تلقائيًا بناءً على الوحدة (جم).")

            net_qty = max(qty - return_qty, 0)
            total_egp = round(net_qty * p_egp, 2)
            total_usd = round(net_qty * p_usd, 2)
            sale_date = QDateTime.currentDateTime().toString("yyyy-MM-dd hh:mm:ss")

            conn = self.connect_db()
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO sales (
                    customer_id, customer_name, product_id, product_name,
                    product_code, unit, quantity, price_egp, price_usd,
                    exchange_rate, total_egp, total_usd, return_qty, sale_date
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                customer_id, customer_name, product_id, product_name, product_code,
                unit_selected, qty, p_egp, p_usd, exchange_rate,
                total_egp, total_usd, return_qty, sale_date
            ))
            conn.commit()
            conn.close()
            self.load_sales()
            self.clear_fields()
            QMessageBox.information(self, "تم", "✅ تمت إضافة عملية البيع وتحديث الوحدة بنجاح.")
        except Exception as e:
            QMessageBox.critical(self, "خطأ أثناء الإضافة", str(e))

    # ==================== تعديل عملية بيع ====================
    def edit_sale(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "تنبيه", "يرجى اختيار عملية بيع لتعديلها.")
            return

        sale_id = int(self.table.item(row, 0).text())
        qty = float(self.qty_input.text().strip() or 0)
        return_qty = float(self.return_input.text().strip() or 0)
        exchange_rate = float(self.exchange_input.text().strip() or 0)
        unit_selected = self.unit_combo.currentText()
        customer_name = self.customer_combo.currentText().split(" (")[0]
        product_name = self.product_combo.currentText().split(" (")[0]
        product_data = self.product_combo.currentData()

        if not product_data:
            QMessageBox.warning(self, "خطأ", "حدث خطأ في بيانات المنتج.")
            return

        product_id, product_code, p_egp, p_usd, _ = product_data
        p_egp = float(p_egp or 0)
        p_usd = float(p_usd or 0)

        if unit_selected == "كجم":
            p_egp /= 1000
            p_usd /= 1000
            QMessageBox.information(self, "تحويل السعر", "💡 تم تعديل السعر تلقائيًا بناءً على الوحدة (كجم).")
        elif unit_selected == "جم":
            p_egp /= 1000000
            p_usd /= 1000000
            QMessageBox.information(self, "تحويل السعر", "💡 تم تعديل السعر تلقائيًا بناءً على الوحدة (جم).")

        total_egp = round((qty - return_qty) * p_egp, 2)
        total_usd = round((qty - return_qty) * p_usd, 2)

        conn = self.connect_db()
        cur = conn.cursor()
        cur.execute("""
            UPDATE sales SET
                customer_name=?, product_name=?, product_code=?, unit=?, quantity=?,
                price_egp=?, price_usd=?, exchange_rate=?, total_egp=?, total_usd=?, return_qty=?
            WHERE id=?
        """, (
            customer_name, product_name, product_code, unit_selected, qty,
            p_egp, p_usd, exchange_rate, total_egp, total_usd, return_qty, sale_id
        ))
        conn.commit()
        conn.close()
        self.load_sales()
        QMessageBox.information(self, "تم", "تم تعديل عملية البيع بنجاح ✏️")

    # ==================== حذف عملية بيع ====================
    def delete_sale(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "تنبيه", "يرجى اختيار عملية بيع لحذفها.")
            return

        sale_id = int(self.table.item(row, 0).text())
        confirm = QMessageBox.question(self, "تأكيد", f"هل تريد حذف عملية البيع رقم {sale_id}؟",
                                       QMessageBox.Yes | QMessageBox.No)
        if confirm == QMessageBox.Yes:
            conn = self.connect_db()
            cur = conn.cursor()
            cur.execute("DELETE FROM sales WHERE id=?", (sale_id,))
            conn.commit()
            conn.close()
            self.load_sales()
            QMessageBox.information(self, "تم", "تم حذف عملية البيع بنجاح 🗑️")

    def clear_fields(self):
        self.qty_input.clear()
        self.return_input.clear()
        self.exchange_input.clear()
        self.unit_combo.setCurrentIndex(0)
        self.customer_combo.setCurrentIndex(0)
        self.product_combo.setCurrentIndex(0)
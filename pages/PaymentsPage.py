# PaymentsPage.py
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton,
    QTableWidget, QTableWidgetItem, QLineEdit, QMessageBox, QHeaderView,
    QCheckBox, QDateEdit, QTextEdit, QFormLayout, QSizePolicy, QAbstractItemView
)
from PyQt5.QtGui import QFont, QColor, QBrush
from PyQt5.QtCore import Qt, QDate
import sqlite3
import os

DB = os.path.join(os.path.dirname(__file__), "..", "database", "crm.db")


class PaymentsPage(QWidget):
    """
    صفحة تحصيل المدفوعات مع تحسين عرض جدول "سجل الدفعات" ليشمل
    شريط تمرير أفقي، وحجم مبدئي مناسب، ومرونة في أعمدة الجدول.
    """

    def __init__(self):
        super().__init__()
        # إزالة الستايل الثابت للسماح بتطبيق الستايل من MainWindow
        # self.setStyleSheet("background-color: #FFFBEA;")  # تم إزالة الستايل الثابت
        self.setFont(QFont("Amiri", 10))

        self.selected_sale_ids = []
        self._ensure_db()
        self.init_ui()
        self.load_customers()
        self.load_payments()

    def db_conn(self):
        return sqlite3.connect(DB)

    def _ensure_db(self):
        os.makedirs(os.path.join(os.path.dirname(__file__), "..", "database"), exist_ok=True)
        conn = sqlite3.connect(DB)
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_name TEXT,
                sale_ids TEXT,
                sale_id TEXT,
                amount REAL,
                remaining REAL,
                receipt TEXT,
                method TEXT,
                created_at TEXT,
                note TEXT
            )
        """)
        conn.commit()
        conn.close()

    def _table_columns(self, table_name):
        try:
            conn = self.db_conn()
            cur = conn.cursor()
            cur.execute(f"PRAGMA table_info({table_name})")
            rows = cur.fetchall()
            conn.close()
            return [r[1] for r in rows]
        except Exception:
            return []

    def init_ui(self):
        main = QVBoxLayout()
        title = QLabel("📥 تحصيل المدفوعات")
        title.setFont(QFont("Amiri", 18, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        main.addWidget(title)

        # top: اختيار العميل والبحث
        top = QHBoxLayout()
        top.addWidget(QLabel("العميل:"))
        self.customer_combo = QComboBox()
        self.customer_combo.currentIndexChanged.connect(self.on_customer_changed)
        top.addWidget(self.customer_combo)

        self.reload_sales_btn = QPushButton("عرض مبيعات العميل")
        self.reload_sales_btn.clicked.connect(self.load_sales_for_selected_customer)
        self.reload_sales_btn.setStyleSheet("background:#03A9F4;color:white;border-radius:6px;")
        top.addWidget(self.reload_sales_btn)

        top.addStretch()
        top.addWidget(QLabel("بحث في السجل:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("بحث بالعميل، رقم الإيصال، أو id")
        self.search_input.textChanged.connect(self.load_payments)
        top.addWidget(self.search_input)

        main.addLayout(top)

        # middle: left = مبيعات، right = فورم + سجل الدفعات
        middle = QHBoxLayout()

        # left column (مبيعات)
        left_col = QVBoxLayout()
        left_col.addWidget(QLabel("قائمة المبيعات (اختار أكثر من بيع):"))
        self.sales_table = QTableWidget(0, 5)
        self.sales_table.setHorizontalHeaderLabels(["اختيار", "Sale ID", "Product", "Qty", "Total (USD)"])
        self.sales_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.sales_table.verticalHeader().setDefaultSectionSize(36)
        self.sales_table.setFont(QFont("Amiri", 12))
        left_col.addWidget(self.sales_table)

        btns = QHBoxLayout()
        self.add_selected_btn = QPushButton("أضف المحدد كمجموع لاستخدامه")
        self.add_selected_btn.clicked.connect(self.on_add_selected_sales)
        self.add_selected_btn.setStyleSheet("background:#4CAF50;color:white;border-radius:6px;")
        btns.addWidget(self.add_selected_btn)

        self.clear_selection_btn = QPushButton("مسح الاختيارات")
        self.clear_selection_btn.clicked.connect(self.clear_sales_selection)
        self.clear_selection_btn.setStyleSheet("background:#9E9E9E;color:white;border-radius:6px;")
        btns.addWidget(self.clear_selection_btn)

        left_col.addLayout(btns)
        middle.addLayout(left_col, 2)

        # right column (فورم + سجل)
        right_col = QVBoxLayout()
        right_col.addWidget(QLabel("تسجيل دفعة"))

        form = QFormLayout()
        self.selected_total_label = QLabel("0.00")
        self.selected_total_label.setFont(QFont("Amiri", 12, QFont.Bold))
        form.addRow("مجموع المبيعات المختارة (USD):", self.selected_total_label)

        self.pay_amount_input = QLineEdit()
        self.pay_amount_input.setPlaceholderText("مثال: 1500")
        self.pay_amount_input.textChanged.connect(self.update_selected_total_label_after_input)
        form.addRow("قيمة الدفعة:", self.pay_amount_input)

        self.receipt_input = QLineEdit()
        form.addRow("رقم الإيصال:", self.receipt_input)

        self.method_input = QComboBox()
        self.method_input.addItems(["Bank Transfer", "Cash", "Cheque", "Other"])
        form.addRow("طريقة الدفع:", self.method_input)

        self.date_input = QDateEdit()
        self.date_input.setDate(QDate.currentDate())
        self.date_input.setDisplayFormat("yyyy-MM-dd")
        form.addRow("التاريخ:", self.date_input)

        self.note_input = QTextEdit()
        self.note_input.setFixedHeight(70)
        form.addRow("ملاحظة:", self.note_input)

        right_col.addLayout(form)

        actions = QHBoxLayout()
        self.save_payment_btn = QPushButton("تسجيل الدفعة")
        self.save_payment_btn.setStyleSheet("background:#1976D2;color:white;border-radius:6px;")
        self.save_payment_btn.clicked.connect(self.save_payment)
        actions.addWidget(self.save_payment_btn)

        self.edit_payment_btn = QPushButton("تعديل الدفعة المحددة")
        self.edit_payment_btn.setStyleSheet("background:#FF9800;color:white;border-radius:6px;")
        self.edit_payment_btn.clicked.connect(self.edit_selected_payment)
        actions.addWidget(self.edit_payment_btn)

        self.delete_payment_btn = QPushButton("حذف الدفعة المحددة")
        self.delete_payment_btn.setStyleSheet("background:#E53935;color:white;border-radius:6px;")
        self.delete_payment_btn.clicked.connect(self.delete_selected_payment)
        actions.addWidget(self.delete_payment_btn)

        right_col.addLayout(actions)
        right_col.addSpacing(8)
        right_col.addWidget(QLabel("سجل الدفعات"))

        # ---------- جدول سجل الدفعات مع تحسينات العرض ----------
        self.payments_table = QTableWidget(0, 8)
        self.payments_table.setHorizontalHeaderLabels(
            ["ID", "Customer", "Sale IDs", "Amount", "Remaining", "Receipt", "Date", "Note"]
        )

        # مهم جداً: لا نجعل جميع الأعمدة تمتد دائماً (لإظهار scrollbar أفقي عند الحاجة)
        # سنعطي الجدول سياسة حجم تسمح له بأن يكون واسعاً، ونضع ScrollBar عند الحاجة
        self.payments_table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.payments_table.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.payments_table.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.payments_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.payments_table.setMinimumHeight(320)   # اجعل الجدول أعلى قليلاً
        self.payments_table.setMinimumWidth(780)    # عرض مبدئي كافٍ للعرض السليم
        self.payments_table.verticalHeader().setDefaultSectionSize(36)
        self.payments_table.setFont(QFont("Amiri", 11))
        self.payments_table.itemSelectionChanged.connect(self.on_payments_selection_changed)

        # اجعل آخر عمود قابل للتمدد أقل من بقية الأعمدة لكي تظهر المسطرة بشكل أفضل
        try:
            self.payments_table.horizontalHeader().setStretchLastSection(False)
        except Exception:
            pass

        right_col.addWidget(self.payments_table)

        middle.addLayout(right_col, 1)
        main.addLayout(middle)
        self.setLayout(main)

    # ---------------- تحميل العملاء والمبيعات ----------------
    def load_customers(self):
        self.customer_combo.clear()
        try:
            conn = self.db_conn()
            cur = conn.cursor()
            cur.execute("SELECT DISTINCT name FROM customers ORDER BY name COLLATE NOCASE")
            rows = cur.fetchall()
            conn.close()
            if not rows:
                self.customer_combo.addItem("(لا عملاء)")
            else:
                for r in rows:
                    self.customer_combo.addItem(r[0])
        except Exception as e:
            QMessageBox.critical(self, "DB Error", str(e))

    def on_customer_changed(self, idx):
        self.clear_sales_table()

    def load_sales_for_selected_customer(self):
        cust = self.customer_combo.currentText()
        if not cust or cust == '(لا عملاء)':
            return
        self.clear_sales_table()
        try:
            conn = self.db_conn()
            cur = conn.cursor()
            cur.execute("SELECT id, product_name, COALESCE(quantity,0), COALESCE(price_usd,0) FROM sales WHERE customer_name=? ORDER BY id DESC", (cust,))
            rows = cur.fetchall()
            conn.close()
            for r in rows:
                self._append_sale_row(r)
        except Exception as e:
            QMessageBox.critical(self, "DB Error", str(e))

    def clear_sales_table(self):
        self.sales_table.setRowCount(0)
        self.selected_sale_ids = []
        self.selected_total_label.setText("0.00")
        self.update_selected_total_label_after_input()

    def _append_sale_row(self, sale_row):
        r_id, pname, qty, price = sale_row
        r = self.sales_table.rowCount()
        self.sales_table.insertRow(r)

        chk = QCheckBox()
        chk.stateChanged.connect(lambda st, sale_id=r_id: self.on_sale_checkbox_changed(st, sale_id))
        self.sales_table.setCellWidget(r, 0, chk)

        self.sales_table.setItem(r, 1, QTableWidgetItem(str(r_id)))
        self.sales_table.setItem(r, 2, QTableWidgetItem(str(pname)))

        try:
            qv = float(qty)
            qty_text = str(int(qv)) if qv.is_integer() else f"{qv:.2f}".rstrip('0').rstrip('.')
        except:
            qty_text = str(qty)
        self.sales_table.setItem(r, 3, QTableWidgetItem(qty_text))

        total = float(price or 0) * float(qty or 0)
        total_text = self._format_numeric_display(total)
        self.sales_table.setItem(r, 4, QTableWidgetItem(total_text))

        for c in range(1, 5):
            it = self.sales_table.item(r, c)
            if it:
                it.setTextAlignment(Qt.AlignCenter)

    def on_sale_checkbox_changed(self, state, sale_id):
        if state == Qt.Checked:
            if sale_id not in self.selected_sale_ids:
                self.selected_sale_ids.append(sale_id)
        else:
            if sale_id in self.selected_sale_ids:
                self.selected_sale_ids.remove(sale_id)
        self.update_selected_total_label_after_input()

    def update_selected_total_label_after_input(self):
        total = 0.0
        for r in range(self.sales_table.rowCount()):
            sid_item = self.sales_table.item(r, 1)
            if not sid_item:
                continue
            try:
                sid = int(sid_item.text())
            except:
                continue
            if sid in self.selected_sale_ids:
                cell = self.sales_table.item(r, 4)
                if cell:
                    val = str(cell.text()).replace(',', '').strip()
                    try:
                        total += float(val)
                    except:
                        pass
        self.selected_total_label.setText(self._format_numeric_display(total))

    def _format_numeric_display(self, v):
        try:
            fv = float(v)
            if fv.is_integer():
                return str(int(fv))
            else:
                s = f"{fv:.2f}"
                s = s.rstrip('0').rstrip('.')
                return s
        except:
            return str(v)

    def on_add_selected_sales(self):
        if not self.selected_sale_ids:
            QMessageBox.warning(self, "تحذير", "اختار مبيعات أولا.")
            return
        QMessageBox.information(self, "مجموع المبيعات",
                                f"مجموع المبيعات المحددة: {self.selected_total_label.text()} USD\nيمكنك الآن تسجيل دفعة لهذه المبيعات.")

    # ---------------- حفظ دفعة ----------------
    def save_payment(self):
        cust = self.customer_combo.currentText()
        if not cust or cust == '(لا عملاء)':
            QMessageBox.warning(self, "تحذير", "اختار عميلًا أولاً.")
            return
        if not self.selected_sale_ids:
            QMessageBox.warning(self, "تحذير", "اختار مبيعات مرتبطة بهذه الدفعة.")
            return
        amount_text = self.pay_amount_input.text().strip()
        try:
            amount = float(amount_text)
        except:
            QMessageBox.warning(self, "خطأ", "ادخل قيمة صحيحة للدفع.")
            return

        receipt = self.receipt_input.text().strip()
        method = self.method_input.currentText()
        created_at = self.date_input.date().toString("yyyy-MM-dd")
        note = self.note_input.toPlainText().strip()
        sale_ids_str = ','.join(str(x) for x in self.selected_sale_ids)

        total_sales_val = self._sum_sales_value_by_ids(sale_ids_str)
        remaining = max(0.0, total_sales_val - amount)

        cols = self._table_columns("payments")
        try:
            conn = self.db_conn()
            cur = conn.cursor()
            if "sale_ids" in cols and "sale_id" in cols:
                cur.execute("""INSERT INTO payments
                    (customer_name, sale_ids, sale_id, amount, remaining, receipt, method, created_at, note)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                            (cust, sale_ids_str, sale_ids_str, amount, remaining, receipt, method, created_at, note))
            elif "sale_ids" in cols:
                cur.execute("""INSERT INTO payments
                    (customer_name, sale_ids, amount, remaining, receipt, method, created_at, note)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                            (cust, sale_ids_str, amount, remaining, receipt, method, created_at, note))
            elif "sale_id" in cols:
                cur.execute("""INSERT INTO payments
                    (customer_name, sale_id, amount, remaining, receipt, method, created_at, note)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                            (cust, sale_ids_str, amount, remaining, receipt, method, created_at, note))
            else:
                cur.execute("""INSERT INTO payments
                    (customer_name, amount, remaining, receipt, method, created_at, note)
                    VALUES (?, ?, ?, ?, ?, ?, ?)""",
                            (cust, amount, remaining, receipt, method, created_at, note))
            conn.commit()
            conn.close()
        except sqlite3.IntegrityError as e:
            QMessageBox.critical(self, "DB Error", f"خطأ في قيود القاعدة:\n{e}")
            return
        except Exception as e:
            QMessageBox.critical(self, "DB Error", str(e))
            return

        self.pay_amount_input.clear()
        self.receipt_input.clear()
        self.note_input.clear()
        self.selected_sale_ids = []
        self.clear_sales_table()
        self.load_payments()
        QMessageBox.information(self, "نجاح", "تم تسجيل الدفعة بنجاح.")

    # ---------------- سجل الدفعات ----------------
    def load_payments(self):
        query = self.search_input.text().strip() if hasattr(self, 'search_input') else ""
        self.payments_table.setRowCount(0)
        try:
            conn = self.db_conn()
            cur = conn.cursor()
            cols = self._table_columns("payments")
            select_cols = []
            for c in ["id", "customer_name", "sale_ids", "sale_id", "amount", "remaining", "receipt", "created_at", "note"]:
                if c in cols:
                    select_cols.append(c)
            if not select_cols:
                conn.close()
                return
            select_clause = ", ".join(select_cols)
            if query:
                q = f"%{query}%"
                where_parts = []
                params = []
                if "customer_name" in select_cols:
                    where_parts.append("customer_name LIKE ?"); params.append(q)
                if "receipt" in select_cols:
                    where_parts.append("receipt LIKE ?"); params.append(q)
                if "sale_ids" in select_cols:
                    where_parts.append("sale_ids LIKE ?"); params.append(q)
                if "sale_id" in select_cols:
                    where_parts.append("sale_id LIKE ?"); params.append(q)
                where_clause = " OR ".join(where_parts) if where_parts else "1=1"
                cur.execute(f"SELECT {select_clause} FROM payments WHERE {where_clause} ORDER BY id DESC", params)
            else:
                cur.execute(f"SELECT {select_clause} FROM payments ORDER BY id DESC")
            rows = cur.fetchall()
            conn.close()

            for r in rows:
                data = dict(zip(select_cols, r))
                pid = str(data.get("id", ""))
                cust = data.get("customer_name", "")
                sale_ids = data.get("sale_ids", data.get("sale_id", ""))
                amount = data.get("amount", 0.0)
                remaining = data.get("remaining", "")
                receipt = data.get("receipt", "")
                created_at = data.get("created_at", "")
                note = data.get("note", "")
                self._append_payment_row((pid, cust, sale_ids, amount, remaining, receipt, created_at, note))
        except Exception as e:
            QMessageBox.critical(self, "DB Error", str(e))

    def _append_payment_row(self, payment_row):
        pid, cust, sale_ids, amount, remaining, receipt, created_at, note = payment_row
        r = self.payments_table.rowCount()
        self.payments_table.insertRow(r)

        self.payments_table.setItem(r, 0, QTableWidgetItem(str(pid)))
        self.payments_table.setItem(r, 1, QTableWidgetItem(str(cust)))
        self.payments_table.setItem(r, 2, QTableWidgetItem(str(sale_ids)))
        self.payments_table.setItem(r, 3, QTableWidgetItem(self._format_numeric_display(amount)))
        self.payments_table.setItem(r, 4, QTableWidgetItem(self._format_numeric_display(remaining) if remaining != "" else ""))
        self.payments_table.setItem(r, 5, QTableWidgetItem(receipt or ""))
        self.payments_table.setItem(r, 6, QTableWidgetItem(created_at or ""))
        self.payments_table.setItem(r, 7, QTableWidgetItem(note or ""))

        for c in range(self.payments_table.columnCount()):
            it = self.payments_table.item(r, c)
            if it:
                it.setTextAlignment(Qt.AlignCenter)

        total_sales_value = self._sum_sales_value_by_ids(sale_ids)
        try:
            paid_value = float(amount or 0)
        except:
            paid_value = 0.0
        self._color_payment_row(r, paid_value, total_sales_value)

    def _sum_sales_value_by_ids(self, sale_ids_str):
        if not sale_ids_str or str(sale_ids_str).strip() == "":
            return 0.0
        try:
            ids = [int(x.strip()) for x in str(sale_ids_str).split(',') if x.strip()]
        except:
            return 0.0
        if not ids:
            return 0.0
        try:
            conn = self.db_conn()
            cur = conn.cursor()
            placeholders = ','.join('?' for _ in ids)
            cur.execute(f"SELECT COALESCE(quantity,0), COALESCE(price_usd,0) FROM sales WHERE id IN ({placeholders})", ids)
            rows = cur.fetchall()
            conn.close()
            s = 0.0
            for q, p in rows:
                try:
                    s += float(q or 0) * float(p or 0)
                except:
                    pass
            return s
        except:
            return 0.0

    def _color_payment_row(self, row_index, paid, total):
        try:
            paid = float(paid)
            total = float(total)
        except:
            return
        if total <= 0:
            color = QColor(200, 200, 200, 40)
        elif paid >= total:
            color = QColor(0, 180, 0, 60)
        elif paid > 0:
            color = QColor(255, 215, 0, 80)
        else:
            color = QColor(255, 0, 0, 40)
        for col in range(self.payments_table.columnCount()):
            it = self.payments_table.item(row_index, col)
            if it:
                it.setBackground(QBrush(color))

    def on_payments_selection_changed(self):
        items = self.payments_table.selectedItems()
        if not items:
            return
        row = items[0].row()
        pid_item = self.payments_table.item(row, 0)
        if pid_item:
            pid = pid_item.text()
            try:
                conn = self.db_conn()
                cur = conn.cursor()
                cur.execute("SELECT customer_name, COALESCE(sale_ids, sale_id), amount, remaining, receipt, method, created_at, note FROM payments WHERE id=?", (pid,))
                r = cur.fetchone()
                conn.close()
                if r:
                    cust, sale_ids, amount, remaining, receipt, method, created_at, note = r
                    self.customer_combo.setCurrentText(cust)
                    self.pay_amount_input.setText(self._format_numeric_display(amount))
                    try:
                        ids = [int(x.strip()) for x in str(sale_ids).split(',') if x.strip()]
                        self.selected_sale_ids = ids
                        for r_idx in range(self.sales_table.rowCount()):
                            sid_item = self.sales_table.item(r_idx, 1)
                            if sid_item:
                                try:
                                    sid_val = int(sid_item.text())
                                except:
                                    continue
                                w = self.sales_table.cellWidget(r_idx, 0)
                                if isinstance(w, QCheckBox):
                                    w.blockSignals(True)
                                    w.setChecked(sid_val in self.selected_sale_ids)
                                    w.blockSignals(False)
                    except:
                        pass
                    self.receipt_input.setText(receipt or "")
                    try:
                        idx = self.method_input.findText(method)
                        if idx >= 0:
                            self.method_input.setCurrentIndex(idx)
                    except:
                        pass
                    try:
                        dt = QDate.fromString(created_at, "yyyy-MM-dd")
                        if dt.isValid():
                            self.date_input.setDate(dt)
                    except:
                        pass
                    self.note_input.setPlainText(note or "")
                    self.update_selected_total_label_after_input()
            except Exception:
                pass

    def edit_selected_payment(self):
        items = self.payments_table.selectedItems()
        if not items:
            QMessageBox.warning(self, "تنبيه", "اختر دفعة من السجل لتعديلها.")
            return
        row = items[0].row()
        pid = self.payments_table.item(row, 0).text()
        try:
            amount = float(self.pay_amount_input.text().strip())
        except:
            QMessageBox.warning(self, "خطأ", "ادخل قيمة صحيحة للمبلغ قبل التعديل.")
            return
        receipt = self.receipt_input.text().strip()
        method = self.method_input.currentText()
        date_str = self.date_input.date().toString("yyyy-MM-dd")
        note = self.note_input.toPlainText().strip()

        sale_ids_str = ','.join(str(x) for x in self.selected_sale_ids)
        total_sales_val = self._sum_sales_value_by_ids(sale_ids_str)
        remaining = max(0.0, total_sales_val - amount)

        try:
            conn = self.db_conn()
            cur = conn.cursor()
            cols = self._table_columns("payments")
            if "sale_ids" in cols and "sale_id" in cols:
                cur.execute("""UPDATE payments SET amount=?, remaining=?, receipt=?, method=?, created_at=?, note=?, sale_ids=?, sale_id=? WHERE id=?""",
                            (amount, remaining, receipt, method, date_str, note, sale_ids_str, sale_ids_str, pid))
            elif "sale_ids" in cols:
                cur.execute("""UPDATE payments SET amount=?, remaining=?, receipt=?, method=?, created_at=?, note=?, sale_ids=? WHERE id=?""",
                            (amount, remaining, receipt, method, date_str, note, sale_ids_str, pid))
            elif "sale_id" in cols:
                cur.execute("""UPDATE payments SET amount=?, remaining=?, receipt=?, method=?, created_at=?, note=?, sale_id=? WHERE id=?""",
                            (amount, remaining, receipt, method, date_str, note, sale_ids_str, pid))
            else:
                cur.execute("""UPDATE payments SET amount=?, remaining=?, receipt=?, method=?, created_at=?, note=? WHERE id=?""",
                            (amount, remaining, receipt, method, date_str, note, pid))
            conn.commit()
            conn.close()
            QMessageBox.information(self, "تم", "تم تحديث الدفعة.")
            self.load_payments()
        except Exception as e:
            QMessageBox.critical(self, "خطأ", str(e))

    def delete_selected_payment(self):
        items = self.payments_table.selectedItems()
        if not items:
            QMessageBox.warning(self, "تنبيه", "اختر دفعة من السجل لحذفها.")
            return
        row = items[0].row()
        pid = self.payments_table.item(row, 0).text()
        confirm = QMessageBox.question(self, "تأكيد حذف", f"هل تريد حذف الدفعة رقم {pid}؟", QMessageBox.Yes | QMessageBox.No)
        if confirm != QMessageBox.Yes:
            return
        try:
            conn = self.db_conn()
            cur = conn.cursor()
            cur.execute("DELETE FROM payments WHERE id=?", (pid,))
            conn.commit()
            conn.close()
            QMessageBox.information(self, "تم", "تم حذف الدفعة.")
            self.load_payments()
        except Exception as e:
            QMessageBox.critical(self, "خطأ", str(e))

    def clear_sales_selection(self):
        for r in range(self.sales_table.rowCount()):
            w = self.sales_table.cellWidget(r, 0)
            if isinstance(w, QCheckBox):
                w.blockSignals(True)
                w.setChecked(False)
                w.blockSignals(False)
        self.selected_sale_ids = []
        self.selected_total_label.setText("0.00")
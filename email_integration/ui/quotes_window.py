"""
نافذة إدارة العروض والاقتباسات
Quotes/Offers Management Window
"""
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QMessageBox, QTableWidget, QTableWidgetItem, QLineEdit,
    QGroupBox, QComboBox, QDoubleSpinBox, QDateEdit, QTextEdit
)
from PyQt5.QtGui import QFont, QColor
from PyQt5.QtCore import Qt, QDate
from datetime import datetime, timedelta
import tempfile
import os

from core.db import (
    get_all_quotes, add_quote, get_quote_by_id,
    update_quote_status, delete_quote, get_client_quotes,
    calculate_quote_profitability, get_all_clients, get_all_products
)


class QuotesWindow(QDialog):
    def __init__(self, parent=None, client_id=None):
        super().__init__(parent)
        
        self.client_id = client_id
        self.setWindowTitle("💼 إدارة العروض - Quotes Management")
        self.setMinimumSize(1200, 700)
        
        main_layout = QVBoxLayout(self)
        
        # العنوان
        title = QLabel("💼 إدارة العروض والاقتباسات - Quotes Management")
        title.setFont(QFont("Segoe UI", 14, QFont.Bold))
        main_layout.addWidget(title)
        
        # معلومات العميل
        if client_id:
            clients = get_all_clients()
            client = next((c for c in clients if c[0] == client_id), None)
            if client:
                client_info = QLabel(f"العميل: {client[1]} | {client[4] or 'بدون بريد إلكتروني'}")
                client_info.setStyleSheet("font-weight: bold; color: #4ECDC4; padding: 5px;")
                main_layout.addWidget(client_info)
        
        # الفلاتر
        filter_group = QGroupBox("فلترة - Filters")
        filter_layout = QHBoxLayout()
        
        self.status_filter = QComboBox()
        self.status_filter.addItems([
            "جميع الحالات",
            "draft",
            "sent",
            "under_review",
            "accepted",
            "rejected",
            "expired"
        ])
        self.status_filter.currentTextChanged.connect(self.load_quotes)
        filter_layout.addWidget(QLabel("الحالة:"))
        filter_layout.addWidget(self.status_filter)
        
        filter_layout.addStretch()
        
        filter_group.setLayout(filter_layout)
        main_layout.addWidget(filter_group)
        
        # جدول العروض
        self.quotes_table = QTableWidget()
        self.quotes_table.setColumnCount(8)
        self.quotes_table.setHorizontalHeaderLabels([
            "رقم العرض", "العميل", "التاريخ", "صالح حتى", "الحالة", "المبلغ الإجمالي", "الربحية", "الهامش الربحي"
        ])
        self.quotes_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.quotes_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.quotes_table.setSortingEnabled(True)
        self.quotes_table.horizontalHeader().setStretchLastSection(True)
        self.quotes_table.cellDoubleClicked.connect(self.view_quote)
        main_layout.addWidget(self.quotes_table)
        
        # مربع نص الرسالة للإرسال
        self.message_input = QTextEdit()
        self.message_input.setPlaceholderText("اكتب رسالة للعميل عند إرسال العرض (اختياري)...")
        self.message_input.setMaximumHeight(80)
        main_layout.addWidget(QLabel("رسالة الإرسال:"))
        main_layout.addWidget(self.message_input)
        
        # الأزرار
        buttons_layout = QHBoxLayout()
        
        self.add_btn = QPushButton("➕ عرض جديد")
        self.add_btn.clicked.connect(self.add_quote)
        self.add_btn.setStyleSheet("background-color: #4ECDC4; color: white; font-weight: bold; border-radius: 5px; padding: 8px;")
        buttons_layout.addWidget(self.add_btn)
        
        self.view_btn = QPushButton("👁 عرض التفاصيل")
        self.view_btn.clicked.connect(self.view_quote)
        buttons_layout.addWidget(self.view_btn)
        
        self.update_status_btn = QPushButton("🔄 تحديث الحالة")
        self.update_status_btn.clicked.connect(self.update_status)
        buttons_layout.addWidget(self.update_status_btn)
        
        self.send_btn = QPushButton("📧 إرسال عبر Outlook")
        self.send_btn.clicked.connect(self.send_quote_via_outlook)
        self.send_btn.setStyleSheet("background-color: #0078D4; color: white; font-weight: bold; border-radius: 5px; padding: 8px;")
        buttons_layout.addWidget(self.send_btn)
        
        self.delete_btn = QPushButton("🗑 حذف")
        self.delete_btn.clicked.connect(self.delete_selected_quote)
        self.delete_btn.setStyleSheet("background-color: #FF6B6B; color: white; font-weight: bold; border-radius: 5px; padding: 8px;")
        buttons_layout.addWidget(self.delete_btn)
        
        buttons_layout.addStretch()
        
        self.close_btn = QPushButton("❌ إغلاق")
        self.close_btn.clicked.connect(self.accept)
        buttons_layout.addWidget(self.close_btn)
        
        main_layout.addLayout(buttons_layout)
        
        # تحميل العروض
        self.load_quotes()
    
    def load_quotes(self):
        """تحميل العروض"""
        status_filter = self.status_filter.currentText()
        
        if self.client_id:
            quotes = get_client_quotes(self.client_id)
        else:
            if status_filter == "جميع الحالات":
                quotes = get_all_quotes()
            else:
                quotes = get_all_quotes(status_filter=status_filter)
        
        # عرض في الجدول
        self.quotes_table.setRowCount(len(quotes))
        
        clients = get_all_clients()
        client_dict = {c[0]: c[1] for c in clients}
        
        for row, quote in enumerate(quotes):
            (
                quote_id, quote_number, client_id, quote_date,
                valid_until, status, total_amount, currency,
                discount, tax_rate, notes, terms_conditions,
                created_date, created_by
            ) = quote
            
            # حساب الربحية
            try:
                profit_data = calculate_quote_profitability(quote_id)
                profit = profit_data["profit"]
                profit_margin = profit_data["profit_margin"]
            except:
                profit = 0
                profit_margin = 0
            
            # تنسيق الحالة
            status_arabic = {
                "draft": "مسودة",
                "sent": "مرسلة",
                "under_review": "قيد المراجعة",
                "accepted": "مقبولة",
                "rejected": "مرفوضة",
                "expired": "منتهية"
            }.get(status, status)
            
            client_name = client_dict.get(client_id, f"Client {client_id}")
            
            values = [
                quote_number or f"QT-{quote_id}",
                client_name,
                quote_date or "",
                valid_until or "",
                status_arabic,
                f"{currency or 'USD'} {total_amount:.2f}",
                f"${profit:.2f}",
                f"{profit_margin:.1f}%"
            ]
            
            for col, val in enumerate(values):
                item = QTableWidgetItem(str(val))
                item.setData(Qt.UserRole, quote_id)
                self.quotes_table.setItem(row, col, item)
                
                # تلوين حسب الحالة
                if col == 4:  # الحالة
                    if status == "accepted":
                        item.setForeground(QColor(0, 128, 0))
                    elif status == "rejected":
                        item.setForeground(QColor(255, 0, 0))
                    elif status == "under_review":
                        item.setForeground(QColor(255, 165, 0))
                    elif status == "sent":
                        item.setForeground(QColor(0, 0, 255))
                
                # تلوين الربحية
                if col == 6:  # الربحية
                    if profit < 0:
                        item.setForeground(QColor(255, 0, 0))
                    elif profit_margin < 10:
                        item.setForeground(QColor(255, 165, 0))
                    else:
                        item.setForeground(QColor(0, 128, 0))
    
    def get_selected_quote_id(self):
        """الحصول على معرف العرض المحدد"""
        row = self.quotes_table.currentRow()
        if row < 0:
            return None
        
        item = self.quotes_table.item(row, 0)
        if item:
            return item.data(Qt.UserRole)
        return None
    
    def add_quote(self):
        """إضافة عرض جديد"""
        dialog = QuoteEditDialog(self, client_id=self.client_id)
        if dialog.exec_() == QDialog.Accepted:
            data = dialog.get_data()
            try:
                quote_id = add_quote(data)
                QMessageBox.information(self, "نجح", "تم إضافة العرض بنجاح")
                self.load_quotes()
            except Exception as e:
                QMessageBox.critical(self, "خطأ", f"حدث خطأ أثناء الإضافة:\n{str(e)}")
    
    def view_quote(self):
        """عرض تفاصيل العرض"""
        quote_id = self.get_selected_quote_id()
        if not quote_id:
            QMessageBox.warning(self, "تنبيه", "الرجاء تحديد عرض أولاً")
            return
        
        quote, items = get_quote_by_id(quote_id)
        if not quote:
            return
        
        dialog = QuoteViewDialog(self, quote, items)
        dialog.exec_()
    
    def update_status(self):
        """تحديث حالة العرض"""
        quote_id = self.get_selected_quote_id()
        if not quote_id:
            QMessageBox.warning(self, "تنبيه", "الرجاء تحديد عرض أولاً")
            return
        
        statuses = ["draft", "sent", "under_review", "accepted", "rejected", "expired"]
        status_arabic = {
            "draft": "مسودة",
            "sent": "مرسلة",
            "under_review": "قيد المراجعة",
            "accepted": "مقبولة",
            "rejected": "مرفوضة",
            "expired": "منتهية"
        }
        
        status, ok = QMessageBox.getItem(
            self,
            "تحديث الحالة",
            "اختر الحالة الجديدة:",
            [status_arabic[s] for s in statuses],
            0,
            False
        )
        
        if ok:
            selected_status = statuses[[status_arabic[s] for s in statuses].index(status)]
            try:
                update_quote_status(quote_id, selected_status)
                QMessageBox.information(self, "نجح", "تم تحديث الحالة بنجاح")
                self.load_quotes()
            except Exception as e:
                QMessageBox.critical(self, "خطأ", f"حدث خطأ أثناء التحديث:\n{str(e)}")
    
    def send_quote_via_outlook(self):
        """إرسال العرض عبر Outlook"""
        quote_id = self.get_selected_quote_id()
        if not quote_id:
            QMessageBox.warning(self, "تنبيه", "الرجاء تحديد عرض أولاً")
            return
        
        quote, items = get_quote_by_id(quote_id)
        if not quote:
            return
        
        # الحصول على معلومات العميل
        client_id = quote[2]
        clients = get_all_clients()
        client = next((c for c in clients if c[0] == client_id), None)
        if not client:
            QMessageBox.warning(self, "تنبيه", "العميل غير موجود")
            return
        
        client_email = client[4]
        if not client_email:
            QMessageBox.warning(self, "تنبيه", "العميل لا يمتلك بريد إلكتروني")
            return
        
        # الحصول على token من الوالد
        graph_token = None
        parent = self.parent()
        while parent:
            if hasattr(parent, "graph_token") and parent.graph_token:
                graph_token = parent.graph_token
                break
            parent = parent.parent()
        
        if not graph_token:
            QMessageBox.warning(self, "تنبيه", "الرجاء توصيل Outlook أولاً")
            return
        
        try:
            from core.ms_document_sender import create_draft_with_attachment
            
            quote_number = quote[1]
            client_name = client[1]
            total_amount = quote[6]
            currency = quote[7] or "USD"
            
            # إنشاء نص العرض
            quote_text = f"<h3>Quote: {quote_number}</h3>"
            quote_text += f"<p><b>Date:</b> {quote[3]}</p>"
            if quote[4]:
                quote_text += f"<p><b>Valid Until:</b> {quote[4]}</p>"
            quote_text += f"<p><b>Total Amount:</b> {currency} {total_amount:.2f}</p>"
            quote_text += "<hr><h4>Items:</h4><table border='1' style='border-collapse: collapse; width: 100%;'>"
            quote_text += "<tr><th>Product</th><th>Quantity</th><th>Unit Price</th><th>Total</th></tr>"
            
            for item in items:
                product_name = item[2] or ""
                quantity = item[3] or 0
                unit_price = item[4] or 0
                total_price = item[6] or 0
                quote_text += f"<tr><td>{product_name}</td><td>{quantity}</td><td>${unit_price:.2f}</td><td>${total_price:.2f}</td></tr>"
            
            quote_text += "</table>"
            
            # استخدام الرسالة من مربع النص إذا كانت موجودة
            message_text = self.message_input.toPlainText().strip()
            if message_text:
                body = f"Dear {client_name},<br><br>{message_text.replace(chr(10), '<br>')}<br><br>{quote_text}"
            else:
                body = f"Dear {client_name},<br><br>Please find our quote details below:<br><br>{quote_text}"
            
            subject = f"Quote: {quote_number}"
            
            # إنشاء ملف نصي مؤقت للعرض
            temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8')
            temp_file.write(f"Quote: {quote_number}\n")
            temp_file.write(f"Date: {quote[3]}\n")
            if quote[4]:
                temp_file.write(f"Valid Until: {quote[4]}\n")
            temp_file.write(f"Total: {currency} {total_amount:.2f}\n\n")
            temp_file.write("Items:\n")
            for item in items:
                temp_file.write(f"- {item[2]}: {item[3]} x ${item[4]:.2f} = ${item[6]:.2f}\n")
            temp_file.close()
            
            try:
                draft_id = create_draft_with_attachment(
                    graph_token=graph_token,
                    to_email=client_email,
                    subject=subject,
                    body=body,
                    attachment_path=temp_file.name
                )
                
                QMessageBox.information(
                    self,
                    "نجح",
                    f"تم إنشاء مسودة رسالة مع تفاصيل العرض.\nافتح Outlook لمراجعة وإرسال الرسالة."
                )
                
                # تحديث حالة العرض إلى "sent"
                update_quote_status(quote_id, "sent")
                self.load_quotes()
            finally:
                # حذف الملف المؤقت
                try:
                    os.unlink(temp_file.name)
                except:
                    pass
            
        except Exception as e:
            error_msg = str(e)
            QMessageBox.critical(self, "خطأ", f"حدث خطأ أثناء الإرسال:\n{error_msg}")
    
    def delete_selected_quote(self):
        """حذف العرض المحدد"""
        quote_id = self.get_selected_quote_id()
        if not quote_id:
            QMessageBox.warning(self, "تنبيه", "الرجاء تحديد عرض أولاً")
            return
        
        quote, _ = get_quote_by_id(quote_id)
        if not quote:
            return
        
        quote_number = quote[1]
        
        reply = QMessageBox.question(
            self,
            "تأكيد الحذف",
            f"هل تريد حذف العرض '{quote_number}'؟",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                delete_quote(quote_id)
                QMessageBox.information(self, "نجح", "تم حذف العرض بنجاح")
                self.load_quotes()
            except Exception as e:
                QMessageBox.critical(self, "خطأ", f"حدث خطأ أثناء الحذف:\n{str(e)}")


class QuoteEditDialog(QDialog):
    def __init__(self, parent=None, client_id=None):
        super().__init__(parent)
        
        self.client_id = client_id
        self.items = []
        
        self.setWindowTitle("عرض جديد")
        self.setMinimumSize(800, 600)
        
        layout = QVBoxLayout(self)
        
        # معلومات أساسية
        info_layout = QHBoxLayout()
        
        info_layout.addWidget(QLabel("العميل *:"))
        self.client_combo = QComboBox()
        clients = get_all_clients()
        for client in clients:
            self.client_combo.addItem(f"{client[1]} ({client[4] or 'no email'})", client[0])
        if client_id:
            for i in range(self.client_combo.count()):
                if self.client_combo.itemData(i) == client_id:
                    self.client_combo.setCurrentIndex(i)
                    break
        info_layout.addWidget(self.client_combo)
        
        info_layout.addWidget(QLabel("العملة:"))
        self.currency_combo = QComboBox()
        self.currency_combo.addItems(["USD", "EUR", "GBP", "EGP"])
        info_layout.addWidget(self.currency_combo)
        
        layout.addLayout(info_layout)
        
        date_layout = QHBoxLayout()
        
        date_layout.addWidget(QLabel("تاريخ العرض:"))
        self.date_input = QDateEdit()
        self.date_input.setDate(QDate.currentDate())
        self.date_input.setCalendarPopup(True)
        date_layout.addWidget(self.date_input)
        
        date_layout.addWidget(QLabel("صالح حتى:"))
        self.valid_until_input = QDateEdit()
        self.valid_until_input.setDate(QDate.currentDate().addDays(30))
        self.valid_until_input.setCalendarPopup(True)
        date_layout.addWidget(self.valid_until_input)
        
        layout.addLayout(date_layout)
        
        # المنتجات
        products_group = QGroupBox("المنتجات")
        products_layout = QVBoxLayout()
        
        # جدول المنتجات
        self.items_table = QTableWidget()
        self.items_table.setColumnCount(6)
        self.items_table.setHorizontalHeaderLabels([
            "اسم المنتج", "الكمية", "سعر الوحدة", "الخصم %", "السعر الإجمالي", ""
        ])
        self.items_table.horizontalHeader().setStretchLastSection(True)
        products_layout.addWidget(self.items_table)
        
        # أزرار إضافة/حذف المنتجات
        items_buttons = QHBoxLayout()
        
        add_item_btn = QPushButton("➕ إضافة منتج")
        add_item_btn.clicked.connect(self.add_item)
        items_buttons.addWidget(add_item_btn)
        
        remove_item_btn = QPushButton("➖ حذف منتج")
        remove_item_btn.clicked.connect(self.remove_item)
        items_buttons.addWidget(remove_item_btn)
        
        items_buttons.addStretch()
        products_layout.addLayout(items_buttons)
        
        products_group.setLayout(products_layout)
        layout.addWidget(products_group)
        
        # الملخص
        summary_group = QGroupBox("الملخص")
        summary_layout = QVBoxLayout()
        
        summary_row1 = QHBoxLayout()
        summary_row1.addWidget(QLabel("المجموع الفرعي:"))
        self.subtotal_label = QLabel("$0.00")
        summary_row1.addWidget(self.subtotal_label)
        summary_row1.addStretch()
        summary_layout.addLayout(summary_row1)
        
        summary_row2 = QHBoxLayout()
        summary_row2.addWidget(QLabel("الخصم:"))
        self.discount_input = QDoubleSpinBox()
        self.discount_input.setMaximum(999999.99)
        self.discount_input.setPrefix("$ ")
        self.discount_input.valueChanged.connect(self.calculate_totals)
        summary_row2.addWidget(self.discount_input)
        summary_row2.addStretch()
        summary_layout.addLayout(summary_row2)
        
        summary_row3 = QHBoxLayout()
        summary_row3.addWidget(QLabel("المبلغ الإجمالي:"))
        self.total_label = QLabel("$0.00")
        self.total_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        summary_row3.addWidget(self.total_label)
        summary_row3.addStretch()
        summary_layout.addLayout(summary_row3)
        
        summary_group.setLayout(summary_layout)
        layout.addWidget(summary_group)
        
        # الملاحظات
        layout.addWidget(QLabel("ملاحظات:"))
        self.notes_input = QTextEdit()
        self.notes_input.setMaximumHeight(80)
        layout.addWidget(self.notes_input)
        
        # الأزرار
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        
        save_btn = QPushButton("💾 حفظ")
        save_btn.clicked.connect(self.accept)
        save_btn.setStyleSheet("background-color: #4ECDC4; color: white; font-weight: bold; border-radius: 5px; padding: 8px;")
        buttons_layout.addWidget(save_btn)
        
        cancel_btn = QPushButton("إلغاء")
        cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_btn)
        
        layout.addLayout(buttons_layout)
    
    def add_item(self):
        """إضافة منتج إلى العرض"""
        dialog = QuoteItemDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            item_data = dialog.get_data()
            self.items.append(item_data)
            self.update_items_table()
            self.calculate_totals()
    
    def remove_item(self):
        """حذف منتج من العرض"""
        row = self.items_table.currentRow()
        if row >= 0:
            self.items.pop(row)
            self.update_items_table()
            self.calculate_totals()
    
    def update_items_table(self):
        """تحديث جدول المنتجات"""
        self.items_table.setRowCount(len(self.items))
        
        for row, item in enumerate(self.items):
            product_name = item["product_name"]
            quantity = item["quantity"]
            unit_price = item["unit_price"]
            discount = item.get("discount", 0)
            total_price = item["total_price"]
            
            self.items_table.setItem(row, 0, QTableWidgetItem(product_name))
            self.items_table.setItem(row, 1, QTableWidgetItem(str(quantity)))
            self.items_table.setItem(row, 2, QTableWidgetItem(f"${unit_price:.2f}"))
            self.items_table.setItem(row, 3, QTableWidgetItem(f"{discount:.1f}%"))
            self.items_table.setItem(row, 4, QTableWidgetItem(f"${total_price:.2f}"))
            
            remove_btn = QPushButton("🗑")
            remove_btn.clicked.connect(lambda checked, r=row: self.remove_item_at(r))
            self.items_table.setCellWidget(row, 5, remove_btn)
    
    def remove_item_at(self, row):
        """حذف منتج من موضع معين"""
        if 0 <= row < len(self.items):
            self.items.pop(row)
            self.update_items_table()
            self.calculate_totals()
    
    def calculate_totals(self):
        """حساب الإجماليات"""
        subtotal = sum(item["total_price"] for item in self.items)
        discount = self.discount_input.value()
        total = subtotal - discount
        
        currency = self.currency_combo.currentText()
        self.subtotal_label.setText(f"{currency} {subtotal:.2f}")
        self.total_label.setText(f"{currency} {total:.2f}")
    
    def get_data(self):
        """الحصول على البيانات"""
        client_id = self.client_combo.currentData()
        
        return {
            "client_id": client_id,
            "quote_date": self.date_input.date().toString("dd/MM/yyyy"),
            "valid_until": self.valid_until_input.date().toString("dd/MM/yyyy"),
            "status": "draft",
            "total_amount": float(self.total_label.text().split()[1]),
            "currency": self.currency_combo.currentText(),
            "discount": self.discount_input.value(),
            "tax_rate": 0,
            "notes": self.notes_input.toPlainText().strip() or None,
            "items": self.items
        }
    
    def accept(self):
        """التحقق من البيانات قبل الحفظ"""
        if self.client_combo.currentIndex() < 0:
            QMessageBox.warning(self, "تنبيه", "الرجاء اختيار عميل")
            return
        
        if len(self.items) == 0:
            QMessageBox.warning(self, "تنبيه", "الرجاء إضافة منتج واحد على الأقل")
            return
        
        super().accept()


class QuoteItemDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setWindowTitle("إضافة منتج")
        self.setMinimumWidth(400)
        
        layout = QVBoxLayout(self)
        
        # المنتج
        layout.addWidget(QLabel("المنتج *:"))
        self.product_combo = QComboBox()
        products = get_all_products()
        for product in products:
            self.product_combo.addItem(
                f"{product[1]} - ${product[5] or 0:.2f}",
                product[0]
            )
        self.product_combo.currentIndexChanged.connect(self.on_product_changed)
        layout.addWidget(self.product_combo)
        
        # الكمية
        layout.addWidget(QLabel("الكمية *:"))
        self.quantity_input = QDoubleSpinBox()
        self.quantity_input.setMinimum(0.01)
        self.quantity_input.setMaximum(999999.99)
        self.quantity_input.setValue(1.0)
        self.quantity_input.valueChanged.connect(self.calculate_item_total)
        layout.addWidget(self.quantity_input)
        
        # سعر الوحدة
        layout.addWidget(QLabel("سعر الوحدة *:"))
        self.unit_price_input = QDoubleSpinBox()
        self.unit_price_input.setMinimum(0)
        self.unit_price_input.setMaximum(999999.99)
        self.unit_price_input.setPrefix("$ ")
        self.unit_price_input.valueChanged.connect(self.calculate_item_total)
        layout.addWidget(self.unit_price_input)
        
        # الخصم
        layout.addWidget(QLabel("الخصم (%):"))
        self.discount_input = QDoubleSpinBox()
        self.discount_input.setMinimum(0)
        self.discount_input.setMaximum(100)
        self.discount_input.setSuffix(" %")
        self.discount_input.valueChanged.connect(self.calculate_item_total)
        layout.addWidget(self.discount_input)
        
        # السعر الإجمالي
        layout.addWidget(QLabel("السعر الإجمالي:"))
        self.total_label = QLabel("$0.00")
        self.total_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        layout.addWidget(self.total_label)
        
        # الأزرار
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        
        add_btn = QPushButton("➕ إضافة")
        add_btn.clicked.connect(self.accept)
        add_btn.setStyleSheet("background-color: #4ECDC4; color: white; font-weight: bold; border-radius: 5px; padding: 8px;")
        buttons_layout.addWidget(add_btn)
        
        cancel_btn = QPushButton("إلغاء")
        cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_btn)
        
        layout.addLayout(buttons_layout)
        
        # تحديث السعر عند اختيار منتج
        self.on_product_changed()
        self.calculate_item_total()
    
    def on_product_changed(self):
        """عند تغيير المنتج"""
        product_id = self.product_combo.currentData()
        if product_id:
            product = next((p for p in get_all_products() if p[0] == product_id), None)
            if product:
                self.unit_price_input.setValue(product[5] or 0)
                self.calculate_item_total()
    
    def calculate_item_total(self):
        """حساب السعر الإجمالي للمنتج"""
        quantity = self.quantity_input.value()
        unit_price = self.unit_price_input.value()
        discount_percent = self.discount_input.value()
        
        subtotal = quantity * unit_price
        discount_amount = subtotal * (discount_percent / 100)
        total = subtotal - discount_amount
        
        self.total_label.setText(f"${total:.2f}")
    
    def get_data(self):
        """الحصول على البيانات"""
        product_id = self.product_combo.currentData()
        product_name = self.product_combo.currentText().split(" - ")[0]
        quantity = self.quantity_input.value()
        unit_price = self.unit_price_input.value()
        discount_percent = self.discount_input.value()
        
        subtotal = quantity * unit_price
        discount_amount = subtotal * (discount_percent / 100)
        total = subtotal - discount_amount
        
        return {
            "product_id": product_id,
            "product_name": product_name,
            "quantity": quantity,
            "unit_price": unit_price,
            "discount": discount_percent,
            "total_price": total
        }


class QuoteViewDialog(QDialog):
    def __init__(self, parent=None, quote=None, items=None):
        super().__init__(parent)
        
        self.quote = quote
        self.items = items or []
        
        self.setWindowTitle(f"عرض تفاصيل: {quote[1] if quote else 'Unknown'}")
        self.setMinimumSize(800, 600)
        
        layout = QVBoxLayout(self)
        
        # معلومات العرض
        info_group = QGroupBox("معلومات العرض")
        info_layout = QVBoxLayout()
        
        info_layout.addWidget(QLabel(f"رقم العرض: {quote[1] if quote else ''}"))
        info_layout.addWidget(QLabel(f"التاريخ: {quote[3] if quote else ''}"))
        info_layout.addWidget(QLabel(f"صالح حتى: {quote[4] if quote else ''}"))
        info_layout.addWidget(QLabel(f"الحالة: {quote[5] if quote else ''}"))
        
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)
        
        # المنتجات
        items_group = QGroupBox("المنتجات")
        items_layout = QVBoxLayout()
        
        items_table = QTableWidget()
        items_table.setColumnCount(5)
        items_table.setHorizontalHeaderLabels([
            "اسم المنتج", "الكمية", "سعر الوحدة", "الخصم", "السعر الإجمالي"
        ])
        items_table.setRowCount(len(self.items))
        
        for row, item in enumerate(self.items):
            items_table.setItem(row, 0, QTableWidgetItem(str(item[2] or "")))  # product_name
            items_table.setItem(row, 1, QTableWidgetItem(str(item[3] or "")))  # quantity
            items_table.setItem(row, 2, QTableWidgetItem(f"${item[4] or 0:.2f}"))  # unit_price
            items_table.setItem(row, 3, QTableWidgetItem(f"{item[5] or 0:.1f}%"))  # discount
            items_table.setItem(row, 4, QTableWidgetItem(f"${item[6] or 0:.2f}"))  # total_price
        
        items_table.horizontalHeader().setStretchLastSection(True)
        items_layout.addWidget(items_table)
        items_group.setLayout(items_layout)
        layout.addWidget(items_group)
        
        # الربحية
        if quote:
            try:
                profit_data = calculate_quote_profitability(quote[0])
                profit_group = QGroupBox("الربحية")
                profit_layout = QVBoxLayout()
                
                profit_layout.addWidget(QLabel(f"الإيرادات: ${profit_data['total_revenue']:.2f}"))
                profit_layout.addWidget(QLabel(f"التكاليف: ${profit_data['total_cost']:.2f}"))
                profit_layout.addWidget(QLabel(f"الربح: ${profit_data['profit']:.2f}"))
                profit_layout.addWidget(QLabel(f"هامش الربح: {profit_data['profit_margin']:.1f}%"))
                
                profit_group.setLayout(profit_layout)
                layout.addWidget(profit_group)
            except:
                pass
        
        # الملاحظات
        if quote and quote[10]:
            notes_group = QGroupBox("ملاحظات")
            notes_layout = QVBoxLayout()
            notes_layout.addWidget(QLabel(quote[10]))
            notes_group.setLayout(notes_layout)
            layout.addWidget(notes_group)
        
        # الأزرار
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        
        close_btn = QPushButton("إغلاق")
        close_btn.clicked.connect(self.accept)
        buttons_layout.addWidget(close_btn)
        
        layout.addLayout(buttons_layout)

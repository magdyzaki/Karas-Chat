"""
نافذة البحث المتقدم
Advanced Search Window
"""
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QComboBox, QDateEdit, QCheckBox, QGroupBox,
    QTabWidget, QWidget, QTableWidget, QTableWidgetItem,
    QMessageBox, QSpinBox, QTextEdit, QRadioButton, QButtonGroup
)
from PyQt5.QtGui import QFont, QColor, QBrush
from PyQt5.QtCore import Qt, QDate
from datetime import datetime, timedelta

from core.advanced_search import (
    search_clients_advanced,
    search_messages_advanced,
    search_requests_advanced,
    search_all_advanced
)
from core.db import get_all_clients


class AdvancedSearchWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setWindowTitle("🔍 البحث المتقدم - Advanced Search")
        self.setMinimumSize(1000, 700)
        
        main_layout = QVBoxLayout(self)
        
        # العنوان
        title = QLabel("🔍 البحث المتقدم - Advanced Search")
        title.setFont(QFont("Segoe UI", 14, QFont.Bold))
        main_layout.addWidget(title)
        
        # التبويبات
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)
        
        # تبويب البحث في العملاء
        self.clients_tab = self.create_clients_search_tab()
        self.tabs.addTab(self.clients_tab, "👥 العملاء")
        
        # تبويب البحث في الرسائل
        self.messages_tab = self.create_messages_search_tab()
        self.tabs.addTab(self.messages_tab, "✉️ الرسائل")
        
        # تبويب البحث في الطلبات
        self.requests_tab = self.create_requests_search_tab()
        self.tabs.addTab(self.requests_tab, "📋 الطلبات")
        
        # تبويب البحث الشامل
        self.all_tab = self.create_all_search_tab()
        self.tabs.addTab(self.all_tab, "🔍 بحث شامل")
        
        # الأزرار
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        
        close_btn = QPushButton("إغلاق")
        close_btn.clicked.connect(self.accept)
        buttons_layout.addWidget(close_btn)
        
        main_layout.addLayout(buttons_layout)
    
    def create_clients_search_tab(self):
        """إنشاء تبويب البحث في العملاء"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # البحث النصي
        search_group = QGroupBox("البحث النصي")
        search_layout = QVBoxLayout()
        
        self.clients_search_input = QLineEdit()
        self.clients_search_input.setPlaceholderText("ابحث في اسم الشركة، البلد، البريد، الهاتف...")
        search_layout.addWidget(self.clients_search_input)
        
        search_group.setLayout(search_layout)
        layout.addWidget(search_group)
        
        # الفلاتر
        filters_group = QGroupBox("الفلاتر")
        filters_layout = QVBoxLayout()
        
        filters_row1 = QHBoxLayout()
        
        class_label = QLabel("التصنيف:")
        self.clients_class_combo = QComboBox()
        self.clients_class_combo.addItems([
            "All Classifications",
            "🔥 Serious Buyer",
            "👍 Potential",
            "❌ Not Serious"
        ])
        filters_row1.addWidget(class_label)
        filters_row1.addWidget(self.clients_class_combo)
        
        status_label = QLabel("الحالة:")
        self.clients_status_combo = QComboBox()
        self.clients_status_combo.addItems([
            "All Status",
            "New",
            "No Reply",
            "Requested Price",
            "Samples Requested",
            "Replied"
        ])
        filters_row1.addWidget(status_label)
        filters_row1.addWidget(self.clients_status_combo)
        
        filters_row1.addStretch()
        filters_layout.addLayout(filters_row1)
        
        filters_row2 = QHBoxLayout()
        
        country_label = QLabel("البلد:")
        self.clients_country_input = QLineEdit()
        self.clients_country_input.setPlaceholderText("اسم البلد...")
        filters_row2.addWidget(country_label)
        filters_row2.addWidget(self.clients_country_input)
        
        filters_row2.addStretch()
        filters_layout.addLayout(filters_row2)
        
        filters_row3 = QHBoxLayout()
        
        min_score_label = QLabel("النقاط من:")
        self.clients_min_score = QSpinBox()
        self.clients_min_score.setRange(-1000, 1000)
        self.clients_min_score.setValue(0)
        filters_row3.addWidget(min_score_label)
        filters_row3.addWidget(self.clients_min_score)
        
        max_score_label = QLabel("إلى:")
        self.clients_max_score = QSpinBox()
        self.clients_max_score.setRange(-1000, 1000)
        self.clients_max_score.setValue(1000)
        filters_row3.addWidget(max_score_label)
        filters_row3.addWidget(self.clients_max_score)
        
        self.clients_focus_check = QCheckBox("Focus فقط")
        filters_row3.addWidget(self.clients_focus_check)
        
        filters_row3.addStretch()
        filters_layout.addLayout(filters_row3)
        
        filters_group.setLayout(filters_layout)
        layout.addWidget(filters_group)
        
        # زر البحث
        search_btn = QPushButton("🔍 بحث")
        search_btn.clicked.connect(self.search_clients)
        search_btn.setStyleSheet("background-color: #4ECDC4; color: white; font-weight: bold; padding: 8px;")
        layout.addWidget(search_btn)
        
        # جدول النتائج
        self.clients_results_table = QTableWidget()
        self.clients_results_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.clients_results_table.setSelectionBehavior(QTableWidget.SelectRows)
        layout.addWidget(self.clients_results_table)
        
        return tab
    
    def create_messages_search_tab(self):
        """إنشاء تبويب البحث في الرسائل"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # البحث النصي
        search_group = QGroupBox("البحث النصي")
        search_layout = QVBoxLayout()
        
        self.messages_search_input = QLineEdit()
        self.messages_search_input.setPlaceholderText("ابحث في محتوى الرسالة أو الموضوع...")
        search_layout.addWidget(self.messages_search_input)
        
        search_group.setLayout(search_layout)
        layout.addWidget(search_group)
        
        # الفلاتر
        filters_group = QGroupBox("الفلاتر")
        filters_layout = QVBoxLayout()
        
        filters_row1 = QHBoxLayout()
        
        channel_label = QLabel("القناة:")
        self.messages_channel_combo = QComboBox()
        self.messages_channel_combo.addItems([
            "All Channels",
            "Email",
            "Outlook",
            "WhatsApp",
            "LinkedIn",
            "Telegram",
            "Phone",
            "SMS",
            "Other"
        ])
        filters_row1.addWidget(channel_label)
        filters_row1.addWidget(self.messages_channel_combo)
        
        type_label = QLabel("النوع:")
        self.messages_type_combo = QComboBox()
        self.messages_type_combo.addItems([
            "All Types",
            "Email",
            "Message",
            "Call",
            "Meeting",
            "Other"
        ])
        filters_row1.addWidget(type_label)
        filters_row1.addWidget(self.messages_type_combo)
        
        filters_row1.addStretch()
        filters_layout.addLayout(filters_row1)
        
        filters_row2 = QHBoxLayout()
        
        date_from_label = QLabel("من تاريخ:")
        self.messages_date_from = QDateEdit()
        self.messages_date_from.setCalendarPopup(True)
        self.messages_date_from.setDate(QDate.currentDate().addYears(-1))
        filters_row2.addWidget(date_from_label)
        filters_row2.addWidget(self.messages_date_from)
        
        date_to_label = QLabel("إلى تاريخ:")
        self.messages_date_to = QDateEdit()
        self.messages_date_to.setCalendarPopup(True)
        self.messages_date_to.setDate(QDate.currentDate())
        filters_row2.addWidget(date_to_label)
        filters_row2.addWidget(self.messages_date_to)
        
        filters_row2.addStretch()
        filters_layout.addLayout(filters_row2)
        
        filters_group.setLayout(filters_layout)
        layout.addWidget(filters_group)
        
        # زر البحث
        search_btn = QPushButton("🔍 بحث")
        search_btn.clicked.connect(self.search_messages)
        search_btn.setStyleSheet("background-color: #4ECDC4; color: white; font-weight: bold; padding: 8px;")
        layout.addWidget(search_btn)
        
        # جدول النتائج
        self.messages_results_table = QTableWidget()
        self.messages_results_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.messages_results_table.setSelectionBehavior(QTableWidget.SelectRows)
        layout.addWidget(self.messages_results_table)
        
        return tab
    
    def create_requests_search_tab(self):
        """إنشاء تبويب البحث في الطلبات"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # البحث النصي
        search_group = QGroupBox("البحث النصي")
        search_layout = QVBoxLayout()
        
        self.requests_search_input = QLineEdit()
        self.requests_search_input.setPlaceholderText("ابحث في نوع الطلب أو المحتوى...")
        search_layout.addWidget(self.requests_search_input)
        
        search_group.setLayout(search_layout)
        layout.addWidget(search_group)
        
        # الفلاتر
        filters_group = QGroupBox("الفلاتر")
        filters_layout = QVBoxLayout()
        
        filters_row1 = QHBoxLayout()
        
        type_label = QLabel("نوع الطلب:")
        self.requests_type_combo = QComboBox()
        self.requests_type_combo.addItems([
            "All Types",
            "Price Request",
            "Sample Request",
            "Specs Request",
            "MOQ / Quantity"
        ])
        filters_row1.addWidget(type_label)
        filters_row1.addWidget(self.requests_type_combo)
        
        status_label = QLabel("الحالة:")
        self.requests_status_combo = QComboBox()
        self.requests_status_combo.addItems([
            "All Status",
            "open",
            "closed"
        ])
        filters_row1.addWidget(status_label)
        filters_row1.addWidget(self.requests_status_combo)
        
        reply_status_label = QLabel("حالة الرد:")
        self.requests_reply_status_combo = QComboBox()
        self.requests_reply_status_combo.addItems([
            "All",
            "pending",
            "replied"
        ])
        filters_row1.addWidget(reply_status_label)
        filters_row1.addWidget(self.requests_reply_status_combo)
        
        filters_row1.addStretch()
        filters_layout.addLayout(filters_row1)
        
        filters_row2 = QHBoxLayout()
        
        date_from_label = QLabel("من تاريخ:")
        self.requests_date_from = QDateEdit()
        self.requests_date_from.setCalendarPopup(True)
        self.requests_date_from.setDate(QDate.currentDate().addYears(-1))
        filters_row2.addWidget(date_from_label)
        filters_row2.addWidget(self.requests_date_from)
        
        date_to_label = QLabel("إلى تاريخ:")
        self.requests_date_to = QDateEdit()
        self.requests_date_to.setCalendarPopup(True)
        self.requests_date_to.setDate(QDate.currentDate())
        filters_row2.addWidget(date_to_label)
        filters_row2.addWidget(self.requests_date_to)
        
        filters_row2.addStretch()
        filters_layout.addLayout(filters_row2)
        
        filters_group.setLayout(filters_layout)
        layout.addWidget(filters_group)
        
        # زر البحث
        search_btn = QPushButton("🔍 بحث")
        search_btn.clicked.connect(self.search_requests)
        search_btn.setStyleSheet("background-color: #4ECDC4; color: white; font-weight: bold; padding: 8px;")
        layout.addWidget(search_btn)
        
        # جدول النتائج
        self.requests_results_table = QTableWidget()
        self.requests_results_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.requests_results_table.setSelectionBehavior(QTableWidget.SelectRows)
        layout.addWidget(self.requests_results_table)
        
        return tab
    
    def create_all_search_tab(self):
        """إنشاء تبويب البحث الشامل"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # البحث النصي
        search_group = QGroupBox("البحث الشامل")
        search_layout = QVBoxLayout()
        
        self.all_search_input = QLineEdit()
        self.all_search_input.setPlaceholderText("ابحث في جميع البيانات...")
        search_layout.addWidget(self.all_search_input)
        
        # خيارات البحث
        search_options = QHBoxLayout()
        
        self.search_clients_check = QCheckBox("العملاء")
        self.search_clients_check.setChecked(True)
        search_options.addWidget(self.search_clients_check)
        
        self.search_messages_check = QCheckBox("الرسائل")
        self.search_messages_check.setChecked(True)
        search_options.addWidget(self.search_messages_check)
        
        self.search_requests_check = QCheckBox("الطلبات")
        self.search_requests_check.setChecked(True)
        search_options.addWidget(self.search_requests_check)
        
        search_options.addStretch()
        search_layout.addLayout(search_options)
        
        search_group.setLayout(search_layout)
        layout.addWidget(search_group)
        
        # زر البحث
        search_btn = QPushButton("🔍 بحث شامل")
        search_btn.clicked.connect(self.search_all)
        search_btn.setStyleSheet("background-color: #4ECDC4; color: white; font-weight: bold; padding: 8px;")
        layout.addWidget(search_btn)
        
        # عرض النتائج
        results_label = QLabel("النتائج:")
        results_label.setFont(QFont("Segoe UI", 10, QFont.Bold))
        layout.addWidget(results_label)
        
        # ملخص النتائج
        self.all_results_summary = QTextEdit()
        self.all_results_summary.setReadOnly(True)
        self.all_results_summary.setMaximumHeight(150)
        layout.addWidget(self.all_results_summary)
        
        # جدول النتائج (سيتم عرض العملاء فقط للبساطة)
        self.all_results_table = QTableWidget()
        self.all_results_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.all_results_table.setSelectionBehavior(QTableWidget.SelectRows)
        layout.addWidget(self.all_results_table)
        
        return tab
    
    def search_clients(self):
        """البحث في العملاء"""
        try:
            search_text = self.clients_search_input.text().strip()
            
            classification = self.clients_class_combo.currentText()
            if classification == "All Classifications":
                classification = None
            
            status = self.clients_status_combo.currentText()
            if status == "All Status":
                status = None
            
            country = self.clients_country_input.text().strip() or None
            
            min_score = self.clients_min_score.value() if self.clients_min_score.value() > -1000 else None
            max_score = self.clients_max_score.value() if self.clients_max_score.value() < 1000 else None
            
            has_focus = None
            if self.clients_focus_check.isChecked():
                has_focus = True
            
            results = search_clients_advanced(
                search_text=search_text,
                classification=classification,
                status=status,
                country=country,
                min_score=min_score,
                max_score=max_score,
                has_focus=has_focus
            )
            
            self.display_clients_results(results)
            
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"حدث خطأ أثناء البحث:\n\n{str(e)}")
    
    def search_messages(self):
        """البحث في الرسائل"""
        try:
            search_text = self.messages_search_input.text().strip()
            
            channel = self.messages_channel_combo.currentText()
            if channel == "All Channels":
                channel = None
            
            message_type = self.messages_type_combo.currentText()
            if message_type == "All Types":
                message_type = None
            
            date_from = self.messages_date_from.date().toString("dd/MM/yyyy")
            date_to = self.messages_date_to.date().toString("dd/MM/yyyy")
            
            results = search_messages_advanced(
                search_text=search_text,
                channel=channel,
                message_type=message_type,
                date_from=date_from,
                date_to=date_to
            )
            
            self.display_messages_results(results)
            
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"حدث خطأ أثناء البحث:\n\n{str(e)}")
    
    def search_requests(self):
        """البحث في الطلبات"""
        try:
            search_text = self.requests_search_input.text().strip()
            
            request_type = self.requests_type_combo.currentText()
            if request_type == "All Types":
                request_type = None
            
            status = self.requests_status_combo.currentText()
            if status == "All Status":
                status = None
            
            reply_status = self.requests_reply_status_combo.currentText()
            if reply_status == "All":
                reply_status = None
            
            date_from = self.requests_date_from.date().toString("dd/MM/yyyy")
            date_to = self.requests_date_to.date().toString("dd/MM/yyyy")
            
            results = search_requests_advanced(
                search_text=search_text,
                request_type=request_type,
                status=status,
                reply_status=reply_status,
                date_from=date_from,
                date_to=date_to
            )
            
            self.display_requests_results(results)
            
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"حدث خطأ أثناء البحث:\n\n{str(e)}")
    
    def search_all(self):
        """البحث الشامل"""
        try:
            search_text = self.all_search_input.text().strip()
            
            search_in = []
            if self.search_clients_check.isChecked():
                search_in.append('clients')
            if self.search_messages_check.isChecked():
                search_in.append('messages')
            if self.search_requests_check.isChecked():
                search_in.append('requests')
            
            if not search_in:
                QMessageBox.warning(self, "تنبيه", "يرجى اختيار نوع واحد على الأقل للبحث")
                return
            
            results = search_all_advanced(search_text=search_text, search_in=search_in)
            
            self.display_all_results(results)
            
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"حدث خطأ أثناء البحث:\n\n{str(e)}")
    
    def display_clients_results(self, results):
        """عرض نتائج البحث في العملاء"""
        headers = [
            "ID", "Company", "Country", "Contact", "Email",
            "Phone", "Status", "Score", "Classification", "Focus"
        ]
        
        self.clients_results_table.setColumnCount(len(headers))
        self.clients_results_table.setHorizontalHeaderLabels(headers)
        self.clients_results_table.setRowCount(len(results))
        
        for row, client in enumerate(results):
            for col, value in enumerate(client[:10]):  # أول 10 أعمدة
                item = QTableWidgetItem(str(value) if value is not None else "")
                item.setTextAlignment(Qt.AlignCenter)
                self.clients_results_table.setItem(row, col, item)
            
            # تخزين ID في UserRole
            self.clients_results_table.item(row, 0).setData(Qt.UserRole, client[0])
        
        self.clients_results_table.resizeColumnsToContents()
    
    def display_messages_results(self, results):
        """عرض نتائج البحث في الرسائل"""
        headers = [
            "ID", "Company", "Date", "Type", "Channel",
            "Subject", "Score Effect"
        ]
        
        self.messages_results_table.setColumnCount(len(headers))
        self.messages_results_table.setHorizontalHeaderLabels(headers)
        self.messages_results_table.setRowCount(len(results))
        
        for row, msg in enumerate(results):
            self.messages_results_table.setItem(row, 0, QTableWidgetItem(str(msg['id'])))
            self.messages_results_table.setItem(row, 1, QTableWidgetItem(msg['company_name'] or ""))
            self.messages_results_table.setItem(row, 2, QTableWidgetItem(msg['message_date'] or ""))
            self.messages_results_table.setItem(row, 3, QTableWidgetItem(msg['message_type'] or ""))
            self.messages_results_table.setItem(row, 4, QTableWidgetItem(msg['channel'] or ""))
            
            subject = (msg['client_response'] or "")[:50]  # أول 50 حرف
            self.messages_results_table.setItem(row, 5, QTableWidgetItem(subject))
            
            self.messages_results_table.setItem(row, 6, QTableWidgetItem(str(msg['score_effect'])))
        
        self.messages_results_table.resizeColumnsToContents()
    
    def display_requests_results(self, results):
        """عرض نتائج البحث في الطلبات"""
        headers = [
            "ID", "Company", "Email", "Type", "Status",
            "Reply Status", "Created At"
        ]
        
        self.requests_results_table.setColumnCount(len(headers))
        self.requests_results_table.setHorizontalHeaderLabels(headers)
        self.requests_results_table.setRowCount(len(results))
        
        for row, req in enumerate(results):
            self.requests_results_table.setItem(row, 0, QTableWidgetItem(str(req['id'])))
            self.requests_results_table.setItem(row, 1, QTableWidgetItem(req['company_name'] or ""))
            self.requests_results_table.setItem(row, 2, QTableWidgetItem(req['client_email'] or ""))
            self.requests_results_table.setItem(row, 3, QTableWidgetItem(req['request_type'] or ""))
            self.requests_results_table.setItem(row, 4, QTableWidgetItem(req['status'] or ""))
            self.requests_results_table.setItem(row, 5, QTableWidgetItem(req['reply_status'] or ""))
            self.requests_results_table.setItem(row, 6, QTableWidgetItem(req['created_at'] or ""))
        
        self.requests_results_table.resizeColumnsToContents()
    
    def display_all_results(self, results):
        """عرض نتائج البحث الشامل"""
        summary_lines = []
        
        if 'clients' in results:
            summary_lines.append(f"👥 العملاء: {len(results['clients'])} نتيجة")
        
        if 'messages' in results:
            summary_lines.append(f"✉️ الرسائل: {len(results['messages'])} نتيجة")
        
        if 'requests' in results:
            summary_lines.append(f"📋 الطلبات: {len(results['requests'])} نتيجة")
        
        self.all_results_summary.setText("\n".join(summary_lines))
        
        # عرض العملاء في الجدول (يمكن تحسينه لاحقاً لعرض جميع النتائج)
        if 'clients' in results and results['clients']:
            headers = [
                "ID", "Company", "Country", "Contact", "Email",
                "Phone", "Status", "Score", "Classification", "Focus"
            ]
            
            self.all_results_table.setColumnCount(len(headers))
            self.all_results_table.setHorizontalHeaderLabels(headers)
            self.all_results_table.setRowCount(len(results['clients']))
            
            for row, client in enumerate(results['clients']):
                for col, value in enumerate(client[:10]):  # أول 10 أعمدة
                    item = QTableWidgetItem(str(value) if value is not None else "")
                    item.setTextAlignment(Qt.AlignCenter)
                    self.all_results_table.setItem(row, col, item)
                
                # تخزين ID في UserRole
                if self.all_results_table.item(row, 0):
                    self.all_results_table.item(row, 0).setData(Qt.UserRole, client[0])
            
            self.all_results_table.resizeColumnsToContents()

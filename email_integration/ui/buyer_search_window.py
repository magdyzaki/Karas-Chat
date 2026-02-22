"""
نافذة البحث عن المشترين حسب المنتج والدول
Buyer Search Window by Product and Countries
"""
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QMessageBox, QGroupBox, QLineEdit, QTableWidget, QTableWidgetItem,
    QCheckBox, QScrollArea, QWidget, QGridLayout, QComboBox, QRadioButton,
    QButtonGroup, QSplitter
)
from PyQt5.QtGui import QFont, QBrush, QColor
from PyQt5.QtCore import Qt

from core.db import search_buyers_by_product, add_client
from core.buyer_api_search import search_buyers_via_api
from datetime import datetime
from ui.countries_selection_dialog import CountriesSelectionDialog


class BuyerSearchWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setWindowTitle("🔍 البحث عن المشترين - Buyer Search")
        self.setMinimumSize(1300, 1400)
        self.resize(1300, 1400)
        
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(8)  # تقليل المسافات بين العناصر
        
        # العنوان (تقليل حجم الخط)
        title = QLabel("🔍 البحث عن المشترين حسب المنتج والدول")
        title.setFont(QFont("Segoe UI", 11, QFont.Bold))
        main_layout.addWidget(title)
        
        # ===== نوع البحث =====
        search_type_group = QGroupBox("نوع البحث - Search Type")
        search_type_layout = QHBoxLayout()
        
        self.search_type_group = QButtonGroup()
        
        self.local_search_radio = QRadioButton("🔍 البحث المحلي")
        self.local_search_radio.setChecked(True)
        self.search_type_group.addButton(self.local_search_radio, 1)
        search_type_layout.addWidget(self.local_search_radio)
        
        self.api_search_radio = QRadioButton("🌐 البحث عبر API")
        self.search_type_group.addButton(self.api_search_radio, 2)
        search_type_layout.addWidget(self.api_search_radio)
        
        self.both_search_radio = QRadioButton("🔍🌐 كلا الخيارين")
        self.search_type_group.addButton(self.both_search_radio, 3)
        search_type_layout.addWidget(self.both_search_radio)
        
        search_type_layout.addStretch()
        search_type_group.setLayout(search_type_layout)
        main_layout.addWidget(search_type_group)
        
        # ===== إعدادات API =====
        api_group = QGroupBox("إعدادات API - API Settings")
        api_layout = QVBoxLayout()
        
        api_keys_layout = QHBoxLayout()
        api_keys_layout.addWidget(QLabel("مفتاح API:"))
        self.api_key_input = QLineEdit()
        self.api_key_input.setPlaceholderText("أدخل مفتاح API (اختياري)")
        self.api_key_input.setEchoMode(QLineEdit.Password)
        api_keys_layout.addWidget(self.api_key_input)
        
        show_key_btn = QPushButton("👁")
        show_key_btn.setMaximumWidth(40)
        show_key_btn.setCheckable(True)
        show_key_btn.toggled.connect(lambda checked: self.api_key_input.setEchoMode(QLineEdit.Normal if checked else QLineEdit.Password))
        api_keys_layout.addWidget(show_key_btn)
        
        api_layout.addLayout(api_keys_layout)
        
        api_type_layout = QHBoxLayout()
        api_type_layout.addWidget(QLabel("نوع API:"))
        self.api_type_combo = QComboBox()
        self.api_type_combo.addItems(["serpapi", "custom", "google", "company_db"])
        self.api_type_combo.setCurrentText("serpapi")
        api_type_layout.addWidget(self.api_type_combo)
        api_type_layout.addStretch()
        
        api_layout.addLayout(api_type_layout)
        api_group.setLayout(api_layout)
        api_group.setEnabled(False)  # معطل افتراضياً
        main_layout.addWidget(api_group)
        self.api_group = api_group
        
        # تفعيل/تعطيل API group حسب نوع البحث
        self.search_type_group.buttonClicked.connect(self.on_search_type_changed)
        
        # ===== منتج البحث =====
        product_group = QGroupBox("المنتج - Product")
        product_layout = QVBoxLayout()
        
        self.product_input = QLineEdit()
        self.product_input.setPlaceholderText("أدخل اسم المنتج (مثل: Dehydrated Onion)")
        self.product_input.setText("Dehydrated Onion")
        product_layout.addWidget(self.product_input)
        
        product_group.setLayout(product_layout)
        main_layout.addWidget(product_group)
        
        # ===== اختيار الدول =====
        countries_layout = QHBoxLayout()
        countries_layout.addWidget(QLabel("🌍 الدول - Countries:"))
        self.countries_btn = QPushButton("اختر الدول - Select Countries")
        self.countries_btn.clicked.connect(self.open_countries_dialog)
        self.countries_btn.setStyleSheet("background-color: #4ECDC4; color: white; font-weight: bold; border-radius: 5px; padding: 8px;")
        countries_layout.addWidget(self.countries_btn)
        countries_layout.addStretch()
        main_layout.addLayout(countries_layout)
        
        # ===== أزرار البحث =====
        buttons_layout = QHBoxLayout()
        
        self.search_btn = QPushButton("🔍 بحث - Search")
        self.search_btn.clicked.connect(self.perform_search)
        self.search_btn.setStyleSheet("background-color: #4ECDC4; color: white; font-weight: bold; border-radius: 5px; padding: 8px;")
        buttons_layout.addWidget(self.search_btn)
        
        self.export_btn = QPushButton("📤 تصدير النتائج - Export Results")
        self.export_btn.clicked.connect(self.export_results)
        self.export_btn.setEnabled(False)
        buttons_layout.addWidget(self.export_btn)
        
        buttons_layout.addStretch()
        main_layout.addLayout(buttons_layout)
        
        # ===== جدول النتائج =====
        results_label = QLabel("النتائج - Results:")
        results_label.setFont(QFont("Segoe UI", 10, QFont.Bold))
        main_layout.addWidget(results_label)
        
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(11)
        self.results_table.setHorizontalHeaderLabels([
            "ID", "🏢 Company Name", "🌍 Country", "👤 Contact Person", "📧 Email",
            "📞 Phone", "🌐 Website", "📅 Date Added", "📊 Status", "⭐ Score", "🏷️ Classification"
        ])
        self.results_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.results_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.results_table.setSortingEnabled(True)
        self.results_table.horizontalHeader().setStretchLastSection(True)
        # تحسين عرض الأعمدة - زيادة العرض
        self.results_table.setColumnWidth(0, 60)   # ID
        self.results_table.setColumnWidth(1, 250)  # Company Name
        self.results_table.setColumnWidth(2, 140)  # Country
        self.results_table.setColumnWidth(3, 180)  # Contact Person
        self.results_table.setColumnWidth(4, 220)  # Email
        self.results_table.setColumnWidth(5, 150)  # Phone
        self.results_table.setColumnWidth(6, 200)  # Website
        self.results_table.setColumnWidth(7, 120)  # Date Added
        self.results_table.setColumnWidth(8, 120)  # Status
        self.results_table.setColumnWidth(9, 80)   # Score
        self.results_table.setColumnWidth(10, 150) # Classification
        
        # زيادة ارتفاع الصفوف
        self.results_table.verticalHeader().setDefaultSectionSize(30)
        
        # جعل الجدول يأخذ المساحة المتبقية
        main_layout.addWidget(self.results_table, 1)  # stretch factor = 1
        
        # النتائج المحفوظة
        self.current_results = []
        
        # الدول المحددة (قائمة الدول المحددة حالياً)
        self.selected_countries = None  # سيتم تحديثها عند فتح النافذة المنبثقة
    
    def open_countries_dialog(self):
        """فتح نافذة اختيار الدول"""
        dialog = CountriesSelectionDialog(self, self.selected_countries)
        if dialog.exec_() == QDialog.Accepted:
            self.selected_countries = dialog.get_selected_countries()
            # تحديث نص الزر لعرض عدد الدول المحددة
            count = len(self.selected_countries)
            self.countries_btn.setText(f"🌍 الدول ({count} محددة) - Select Countries ({count} selected)")
    
    def get_selected_countries(self):
        """الحصول على قائمة الدول المحددة"""
        if self.selected_countries is None:
            # إذا لم يتم تحديد دول بعد، استخدم جميع الدول الافتراضية
            return [
                "Austria", "Belgium", "Bulgaria", "Croatia", "Cyprus", "Czech Republic",
                "Denmark", "Estonia", "Finland", "France", "Germany", "Greece", "Hungary",
                "Ireland", "Italy", "Latvia", "Lithuania", "Luxembourg", "Malta",
                "Netherlands", "Poland", "Portugal", "Romania", "Slovakia", "Slovenia",
                "Spain", "Sweden", "United Kingdom", "USA", "United States"
            ]
        return self.selected_countries
    
    def on_search_type_changed(self):
        """تفعيل/تعطيل إعدادات API حسب نوع البحث"""
        if self.api_search_radio.isChecked() or self.both_search_radio.isChecked():
            self.api_group.setEnabled(True)
        else:
            self.api_group.setEnabled(False)
    
    def perform_search(self):
        """تنفيذ البحث"""
        product_name = self.product_input.text().strip()
        
        if not product_name:
            QMessageBox.warning(self, "تنبيه", "الرجاء إدخال اسم المنتج")
            return
        
        selected_countries = self.get_selected_countries()
        
        if not selected_countries:
            QMessageBox.warning(self, "تنبيه", "الرجاء اختيار دولة واحدة على الأقل")
            return
        
        try:
            all_results = []
            
            # البحث المحلي
            if self.local_search_radio.isChecked() or self.both_search_radio.isChecked():
                local_results = search_buyers_by_product(product_name, selected_countries)
                all_results.extend(local_results)
            
            # البحث عبر API
            if self.api_search_radio.isChecked() or self.both_search_radio.isChecked():
                api_key = self.api_key_input.text().strip()
                api_type = self.api_type_combo.currentText()
                
                if api_key or api_type == "custom":
                    try:
                        api_results = search_buyers_via_api(product_name, selected_countries, api_key, api_type)
                        
                        # تحويل نتائج API إلى تنسيق موحد (إذا كانت dict)
                        if api_results:
                            for item in api_results:
                                if isinstance(item, dict):
                                    # تحويل dict إلى tuple للتوافق مع display_results
                                    all_results.append((
                                        None,  # id
                                        item.get("company_name", ""),
                                        item.get("country", ""),
                                        item.get("contact_person", ""),
                                        item.get("email", ""),
                                        item.get("phone", ""),
                                        item.get("website", ""),
                                        datetime.now().strftime("%d/%m/%Y"),  # date_added
                                        "New",  # status
                                        0,  # score
                                        "",  # classification
                                        0  # is_focus
                                    ))
                    except Exception as api_error:
                        QMessageBox.warning(
                            self,
                            "تحذير API",
                            f"حدث خطأ في البحث عبر API:\n{str(api_error)}\n\nسيتم عرض نتائج البحث المحلي فقط."
                        )
            
            # إزالة التكرارات
            seen = set()
            unique_results = []
            for result in all_results:
                # استخدام email أو company_name كمعرف فريد
                identifier = result[4] if result[4] else result[1]  # email or company_name
                if identifier and identifier not in seen:
                    seen.add(identifier)
                    unique_results.append(result)
            
            self.current_results = unique_results
            
            # عرض النتائج
            self.display_results(unique_results)
            
            # تفعيل زر التصدير
            self.export_btn.setEnabled(len(unique_results) > 0)
            
            QMessageBox.information(
                self,
                "اكتمل البحث",
                f"تم العثور على {len(unique_results)} عميل"
            )
        except Exception as e:
            QMessageBox.critical(
                self,
                "خطأ",
                f"حدث خطأ أثناء البحث:\n{str(e)}"
            )
    
    def display_results(self, results):
        """عرض النتائج في الجدول مع تحسين التنسيق"""
        self.results_table.setRowCount(len(results))
        
        for row, client in enumerate(results):
            # التعامل مع النتائج من API (dict) أو قاعدة البيانات (tuple)
            if isinstance(client, dict):
                client_id = None
                company = client.get("company_name", "").strip()
                country = client.get("country", "").strip()
                contact = client.get("contact_person", "").strip()
                email = client.get("email", "").strip()
                phone = client.get("phone", "").strip()
                website = client.get("website", "").strip()
                date_added = client.get("date_added", datetime.now().strftime("%d/%m/%Y"))
                status = client.get("status", "New")
                score = client.get("score", 0)
                classification = client.get("classification", "")
                is_focus = client.get("is_focus", 0)
            else:
                (
                    client_id, company, country, contact, email,
                    phone, website, date_added,
                    status, score, classification, is_focus
                ) = client
            
            # تنظيف البيانات
            company = (company or "").strip()
            country = (country or "").strip()
            contact = (contact or "").strip()
            email = (email or "").strip().lower()
            phone = (phone or "").strip()
            website = (website or "").strip()
            classification = (classification or "").strip()
            
            # تنظيف رقم الهاتف (إزالة المسافات الزائدة)
            if phone:
                phone = " ".join(phone.split())
            
            # تنظيف الموقع (إزالة http:// أو https:// إذا لم يكن موجوداً)
            if website and not website.startswith(("http://", "https://")):
                website = f"https://{website}"
            
            values = [
                str(client_id) if client_id else "API",
                company or "-",
                country or "-",
                contact or "-",
                email or "-",
                phone or "-",
                website or "-",
                date_added or "-",
                status or "New",
                str(score or 0),
                classification or "-"
            ]
            
            for col, val in enumerate(values):
                item = QTableWidgetItem(str(val))
                if client_id:
                    item.setData(Qt.UserRole, client_id)
                
                # تحسين التنسيق حسب العمود
                if col == 1:  # Company Name
                    item.setFont(QFont("Segoe UI", 9, QFont.Bold))
                    item.setForeground(QBrush(QColor("#1a1a1a")))
                elif col == 4:  # Email
                    if email and email != "-":
                        item.setForeground(QBrush(QColor("#0066cc")))
                        item.setToolTip(f"📧 {email}")
                elif col == 5:  # Phone
                    if phone and phone != "-":
                        item.setForeground(QBrush(QColor("#006600")))
                        item.setToolTip(f"📞 {phone}")
                elif col == 6:  # Website
                    if website and website != "-":
                        item.setForeground(QBrush(QColor("#0066cc")))
                        item.setToolTip(f"🌐 {website}")
                elif col == 9:  # Score
                    score_val = score or 0
                    if score_val >= 50:
                        item.setForeground(QBrush(QColor("#006600")))
                    elif score_val >= 20:
                        item.setForeground(QBrush(QColor("#FF8C00")))
                    else:
                        item.setForeground(QBrush(QColor("#CC0000")))
                
                self.results_table.setItem(row, col, item)
                
                # تلوين الصفوف
                if is_focus:
                    item.setBackground(QBrush(QColor("#FFF2CC")))
                elif classification and classification.startswith("🔥"):
                    item.setBackground(QBrush(QColor("#FFD6D6")))
                elif classification and classification.startswith("👍"):
                    item.setBackground(QBrush(QColor("#FFF4CC")))
                else:
                    item.setBackground(QBrush(QColor("#FFFFFF")))
    
    def export_results(self):
        """تصدير النتائج إلى ملف Excel أو CSV"""
        if not self.current_results:
            QMessageBox.warning(self, "تنبيه", "لا توجد نتائج للتصدير")
            return
        
        try:
            from PyQt5.QtWidgets import QFileDialog
            from core.export_data import export_clients_to_excel, export_clients_to_csv
            import os
            
            # اختيار الملف
            file_path, selected_filter = QFileDialog.getSaveFileName(
                self,
                "حفظ النتائج - Save Results",
                f"buyers_{self.product_input.text().strip().replace(' ', '_')}.xlsx",
                "Excel Files (*.xlsx);;CSV Files (*.csv)"
            )
            
            if not file_path:
                return
            
            # التصدير - البيانات بالفعل في تنسيق tuple الصحيح
            if file_path.endswith('.xlsx'):
                try:
                    export_clients_to_excel(file_path, self.current_results)
                    QMessageBox.information(self, "نجح", f"تم التصدير بنجاح إلى:\n{file_path}")
                except Exception as e:
                    # إذا فشل التصدير إلى Excel، حاول CSV
                    csv_path = file_path.replace('.xlsx', '.csv')
                    export_clients_to_csv(csv_path, self.current_results)
                    QMessageBox.information(self, "نجح", f"تم التصدير إلى CSV:\n{csv_path}")
            else:
                export_clients_to_csv(file_path, self.current_results)
                QMessageBox.information(self, "نجح", f"تم التصدير بنجاح إلى:\n{file_path}")
                
        except Exception as e:
            QMessageBox.critical(
                self,
                "خطأ",
                f"حدث خطأ أثناء التصدير:\n{str(e)}"
            )

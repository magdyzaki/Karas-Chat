"""
نافذة البحث عن المستوردين بناءً على اسم الشركة المصدرة
Importer Search Window based on Exporter Company Name
"""
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QMessageBox, QGroupBox, QLineEdit, QTableWidget, QTableWidgetItem,
    QCheckBox, QScrollArea, QWidget, QGridLayout, QComboBox, QRadioButton,
    QButtonGroup, QSplitter, QProgressDialog, QDesktopWidget
)
from PyQt5.QtGui import QFont, QBrush, QColor
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from datetime import datetime

from core.db import add_client
from core.importer_api_search import search_importers_by_exporter, search_importkey_style
from ui.countries_selection_dialog import CountriesSelectionDialog


class SearchThread(QThread):
    """Thread للبحث في الخلفية"""
    finished = pyqtSignal(list)
    error = pyqtSignal(str)
    progress = pyqtSignal(str)
    
    def __init__(self, exporter_name: str, product_name: str = None, countries: list = None, api_key: str = None, use_importkey_style: bool = False):
        super().__init__()
        self.exporter_name = exporter_name
        self.product_name = product_name
        self.countries = countries
        self.api_key = api_key
        self.use_importkey_style = use_importkey_style
    
    def run(self):
        try:
            self.progress.emit("جاري البحث عن المستوردين...")
            
            if self.use_importkey_style:
                results = search_importkey_style(self.exporter_name, self.countries, self.api_key, self.product_name)
            else:
                results = search_importers_by_exporter(self.exporter_name, self.product_name, self.countries, self.api_key)
            
            if len(results) > 0:
                self.progress.emit(f"تم العثور على {len(results)} مستورد")
            else:
                self.progress.emit("لم يتم العثور على نتائج")
            self.finished.emit(results)
            
        except Exception as e:
            import traceback
            error_msg = f"{str(e)}\n\n{traceback.format_exc()}"
            self.error.emit(error_msg)


class ImporterSearchWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setWindowTitle("🔍 البحث عن المستوردين - Importer Search")
        
        # حساب حجم النافذة بناءً على حجم الشاشة
        screen = QDesktopWidget().screenGeometry()
        screen_width = screen.width()
        screen_height = screen.height()
        
        # استخدام 85% من حجم الشاشة كحد أقصى
        window_width = min(1600, int(screen_width * 0.85))
        window_height = min(1000, int(screen_height * 0.85))
        
        # حد أدنى للحجم
        min_width = 1200
        min_height = 700
        
        self.setMinimumSize(min_width, min_height)
        self.resize(window_width, window_height)
        
        # السماح بتكبير النافذة
        self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint)
        
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(10)
        
        # العنوان
        title = QLabel("🔍 البحث عن المستوردين بناءً على اسم الشركة المصدرة")
        title.setFont(QFont("Segoe UI", 14, QFont.Bold))
        main_layout.addWidget(title)
        
        subtitle = QLabel("أدخل اسم الشركة المصدرة واسم المنتج للبحث عن شركات محتملة")
        subtitle.setFont(QFont("Segoe UI", 10))
        subtitle.setStyleSheet("color: #666;")
        main_layout.addWidget(subtitle)
        
        # تحذير مختصر (تم إزالته لتوسيع مساحة النتائج)
        # يمكن إضافة تحذير صغير في أسفل النافذة إذا لزم الأمر
        
        # ===== نوع البحث =====
        search_type_group = QGroupBox("نوع البحث - Search Type")
        search_type_layout = QHBoxLayout()
        
        self.search_type_group = QButtonGroup()
        
        self.standard_search_radio = QRadioButton("🔍 البحث القياسي")
        self.standard_search_radio.setChecked(True)
        self.search_type_group.addButton(self.standard_search_radio, 1)
        search_type_layout.addWidget(self.standard_search_radio)
        
        self.importkey_style_radio = QRadioButton("🌐 نمط ImportKey")
        self.search_type_group.addButton(self.importkey_style_radio, 2)
        search_type_layout.addWidget(self.importkey_style_radio)
        
        search_type_layout.addStretch()
        search_type_group.setLayout(search_type_layout)
        main_layout.addWidget(search_type_group)
        
        # ===== اسم الشركة المصدرة =====
        exporter_group = QGroupBox("اسم الشركة المصدرة - Exporter Company Name")
        exporter_layout = QVBoxLayout()
        
        self.exporter_input = QLineEdit()
        self.exporter_input.setPlaceholderText("أدخل اسم الشركة المصدرة (مثال: El-Raee for Dehydration)")
        self.exporter_input.setMinimumHeight(35)
        exporter_layout.addWidget(self.exporter_input)
        
        exporter_group.setLayout(exporter_layout)
        main_layout.addWidget(exporter_group)
        
        # ===== اسم المنتج =====
        product_group = QGroupBox("اسم المنتج (اختياري) - Product Name (Optional)")
        product_layout = QVBoxLayout()
        
        self.product_input = QLineEdit()
        self.product_input.setPlaceholderText("أدخل اسم المنتج (مثال: Dried Onions, Dehydrated Vegetables)")
        self.product_input.setMinimumHeight(35)
        product_layout.addWidget(self.product_input)
        
        product_group.setLayout(product_layout)
        main_layout.addWidget(product_group)
        
        # ===== اختيار الدول (اختياري) =====
        countries_layout = QHBoxLayout()
        countries_layout.addWidget(QLabel("🌍 الدول (اختياري) - Countries (Optional):"))
        self.countries_btn = QPushButton("اختر الدول - Select Countries")
        self.countries_btn.clicked.connect(self.open_countries_dialog)
        self.countries_btn.setStyleSheet("background-color: #4ECDC4; color: white; font-weight: bold; border-radius: 5px; padding: 8px;")
        countries_layout.addWidget(self.countries_btn)
        countries_layout.addStretch()
        main_layout.addLayout(countries_layout)
        
        # ===== إعدادات API (اختياري) =====
        api_group = QGroupBox("إعدادات API (اختياري) - API Settings (Optional)")
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
        api_group.setLayout(api_layout)
        main_layout.addWidget(api_group)
        
        # ===== أزرار البحث =====
        buttons_layout = QHBoxLayout()
        
        self.search_btn = QPushButton("🔍 بحث - Search")
        self.search_btn.clicked.connect(self.perform_search)
        self.search_btn.setStyleSheet("background-color: #4ECDC4; color: white; font-weight: bold; border-radius: 5px; padding: 10px 20px; font-size: 12px;")
        buttons_layout.addWidget(self.search_btn)
        
        self.add_to_clients_btn = QPushButton("➕ إضافة المحدد إلى العملاء")
        self.add_to_clients_btn.clicked.connect(self.add_selected_to_clients)
        self.add_to_clients_btn.setEnabled(False)
        self.add_to_clients_btn.setStyleSheet("background-color: #95E1D3; color: white; font-weight: bold; border-radius: 5px; padding: 10px 20px; font-size: 12px;")
        buttons_layout.addWidget(self.add_to_clients_btn)
        
        self.export_btn = QPushButton("📤 تصدير النتائج - Export Results")
        self.export_btn.clicked.connect(self.export_results)
        self.export_btn.setEnabled(False)
        self.export_btn.setStyleSheet("background-color: #F38181; color: white; font-weight: bold; border-radius: 5px; padding: 10px 20px; font-size: 12px;")
        buttons_layout.addWidget(self.export_btn)
        
        self.analyze_btn = QPushButton("📊 تحليل النتائج - Analyze Results")
        self.analyze_btn.clicked.connect(self.analyze_results)
        self.analyze_btn.setEnabled(False)
        self.analyze_btn.setStyleSheet("background-color: #95A5A6; color: white; font-weight: bold; border-radius: 5px; padding: 10px 20px; font-size: 12px;")
        buttons_layout.addWidget(self.analyze_btn)
        
        buttons_layout.addStretch()
        main_layout.addLayout(buttons_layout)
        
        # ===== جدول النتائج =====
        results_label = QLabel("النتائج - Results:")
        results_label.setFont(QFont("Segoe UI", 11, QFont.Bold))
        main_layout.addWidget(results_label)
        
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(9)
        self.results_table.setHorizontalHeaderLabels([
            "محدد", "🏢 اسم الشركة", "🌍 الدولة", "📧 البريد الإلكتروني",
            "📞 الهاتف", "🌐 الموقع", "📍 العنوان", "📅 تاريخ الإضافة", "🔗 المصدر"
        ])
        self.results_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.results_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.results_table.setSelectionMode(QTableWidget.MultiSelection)
        self.results_table.setSortingEnabled(True)
        self.results_table.horizontalHeader().setStretchLastSection(True)
        
        # تحسين عرض الأعمدة
        self.results_table.setColumnWidth(0, 60)   # محدد
        self.results_table.setColumnWidth(1, 250)  # اسم الشركة
        self.results_table.setColumnWidth(2, 140)  # الدولة
        self.results_table.setColumnWidth(3, 220)  # البريد
        self.results_table.setColumnWidth(4, 150)   # الهاتف
        self.results_table.setColumnWidth(5, 200)  # الموقع
        self.results_table.setColumnWidth(6, 250)  # العنوان
        self.results_table.setColumnWidth(7, 120)  # تاريخ الإضافة
        self.results_table.setColumnWidth(8, 150)  # المصدر
        
        # زيادة ارتفاع الصفوف
        self.results_table.verticalHeader().setDefaultSectionSize(35)
        
        # جعل الجدول يأخذ المساحة المتبقية
        main_layout.addWidget(self.results_table, 1)
        
        # النتائج المحفوظة
        self.current_results = []
        self.selected_countries = None
        
        # Thread للبحث
        self.search_thread = None
    
    def open_countries_dialog(self):
        """فتح نافذة اختيار الدول"""
        dialog = CountriesSelectionDialog(self, self.selected_countries)
        if dialog.exec_() == QDialog.Accepted:
            self.selected_countries = dialog.get_selected_countries()
            count = len(self.selected_countries)
            self.countries_btn.setText(f"🌍 الدول ({count} محددة) - Select Countries ({count} selected)")
    
    def get_selected_countries(self):
        """الحصول على قائمة الدول المحددة"""
        return self.selected_countries or []
    
    def perform_search(self):
        """تنفيذ البحث"""
        exporter_name = self.exporter_input.text().strip()
        
        if not exporter_name:
            QMessageBox.warning(self, "تنبيه", "الرجاء إدخال اسم الشركة المصدرة")
            return
        
        # تعطيل زر البحث أثناء البحث
        self.search_btn.setEnabled(False)
        self.search_btn.setText("جاري البحث...")
        
        # إنشاء progress dialog
        self.progress_dialog = QProgressDialog("جاري البحث عن المستوردين...", "إلغاء", 0, 0, self)
        self.progress_dialog.setWindowModality(Qt.WindowModal)
        self.progress_dialog.setCancelButton(None)  # لا يمكن إلغاء البحث
        self.progress_dialog.show()
        
        # الحصول على اسم المنتج (اختياري)
        product_name = self.product_input.text().strip() or None
        
        # الحصول على الإعدادات
        selected_countries = self.get_selected_countries()
        api_key = self.api_key_input.text().strip() or None
        use_importkey_style = self.importkey_style_radio.isChecked()
        
        # إنشاء thread للبحث
        self.search_thread = SearchThread(exporter_name, product_name, selected_countries, api_key, use_importkey_style)
        self.search_thread.finished.connect(self.on_search_finished)
        self.search_thread.error.connect(self.on_search_error)
        self.search_thread.progress.connect(self.on_search_progress)
        self.search_thread.start()
    
    def on_search_progress(self, message: str):
        """تحديث رسالة التقدم"""
        if hasattr(self, 'progress_dialog'):
            self.progress_dialog.setLabelText(message)
    
    def on_search_finished(self, results: list):
        """عند انتهاء البحث"""
        if hasattr(self, 'progress_dialog'):
            self.progress_dialog.close()
        
        self.search_btn.setEnabled(True)
        self.search_btn.setText("🔍 بحث - Search")
        
        self.current_results = results
        
        # عرض النتائج
        self.display_results(results)
        
        # تفعيل الأزرار
        self.export_btn.setEnabled(len(results) > 0)
        self.add_to_clients_btn.setEnabled(len(results) > 0)
        self.analyze_btn.setEnabled(len(results) > 0)
        
        if len(results) > 0:
            QMessageBox.information(
                self,
                "اكتمل البحث",
                f"تم العثور على {len(results)} مستورد"
            )
        else:
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Warning)
            msg.setWindowTitle("لا توجد نتائج")
            msg.setText("لم يتم العثور على أي مستوردين.")
            
            # التحقق من رسائل DEBUG لتحديد السبب
            informative_text = (
                "السبب المحتمل:\n"
            )
            
            # إذا كان هناك مفتاح API لكن SerpAPI يعيد 401
            if hasattr(self, 'api_key_input') and self.api_key_input.text().strip():
                informative_text += (
                    "⚠️ مفتاح SerpAPI غير صحيح أو منتهي الصلاحية (خطأ 401)\n"
                    "• تأكد من أن المفتاح صحيح من https://serpapi.com/\n"
                    "• تأكد من أن المفتاح نشط ولديه رصيد كافٍ\n"
                    "• جرب إنشاء مفتاح جديد\n\n"
                )
            
            informative_text += (
                "مشاكل أخرى محتملة:\n"
                "• Google يحظر web scraping ويستخدم JavaScript\n"
                "• BeautifulSoup لا يستطيع قراءة JavaScript\n\n"
                "الحلول المقترحة:\n"
                "1. استخدم مفتاح SerpAPI صحيح ونشط\n"
                "   (احصل عليه من: https://serpapi.com/)\n\n"
                "2. استخدم قواعد بيانات متخصصة:\n"
                "   - ImportKey.com (بيانات شحن فعلية)\n"
                "   - Panjiva (بيانات جمركية)\n"
                "   - ImportGenius (بيانات تجارية)\n\n"
                "3. جرب البحث بدون تحديد دول محددة\n"
                "4. أضف اسم المنتج لتحسين البحث"
            )
            
            msg.setInformativeText(informative_text)
            msg.setStandardButtons(QMessageBox.Ok)
            msg.exec_()
    
    def on_search_error(self, error_message: str):
        """عند حدوث خطأ في البحث"""
        if hasattr(self, 'progress_dialog'):
            self.progress_dialog.close()
        
        self.search_btn.setEnabled(True)
        self.search_btn.setText("🔍 بحث - Search")
        
        QMessageBox.critical(
            self,
            "خطأ",
            f"حدث خطأ أثناء البحث:\n{error_message}"
        )
    
    def display_results(self, results: list):
        """عرض النتائج في الجدول"""
        self.results_table.setRowCount(len(results))
        
        for row, importer in enumerate(results):
            # Checkbox للتحديد
            checkbox = QCheckBox()
            checkbox.setChecked(False)
            self.results_table.setCellWidget(row, 0, checkbox)
            
            # البيانات
            company = importer.get("company_name", "").strip() or "-"
            country = importer.get("country", "").strip() or "-"
            email = importer.get("email", "").strip() or "-"
            phone = importer.get("phone", "").strip() or "-"
            website = importer.get("website", "").strip() or "-"
            address = importer.get("address", "").strip() or "-"
            date_added = datetime.now().strftime("%d/%m/%Y")
            source = importer.get("source", "").strip() or "-"
            
            # تنظيف الموقع
            if website and website != "-" and not website.startswith(("http://", "https://")):
                website = f"https://{website}"
            
            values = [company, country, email, phone, website, address, date_added, source]
            
            for col, val in enumerate(values, start=1):
                item = QTableWidgetItem(str(val))
                
                # تحسين التنسيق
                if col == 1:  # اسم الشركة
                    item.setFont(QFont("Segoe UI", 9, QFont.Bold))
                    item.setForeground(QBrush(QColor("#1a1a1a")))
                elif col == 3:  # البريد
                    if email and email != "-":
                        item.setForeground(QBrush(QColor("#0066cc")))
                        item.setToolTip(f"📧 {email}")
                elif col == 4:  # الهاتف
                    if phone and phone != "-":
                        item.setForeground(QBrush(QColor("#006600")))
                        item.setToolTip(f"📞 {phone}")
                elif col == 5:  # الموقع
                    if website and website != "-":
                        item.setForeground(QBrush(QColor("#0066cc")))
                        item.setToolTip(f"🌐 {website}")
                
                self.results_table.setItem(row, col, item)
    
    def add_selected_to_clients(self):
        """إضافة المستوردين المحددين إلى قائمة العملاء"""
        selected_rows = []
        
        for row in range(self.results_table.rowCount()):
            checkbox = self.results_table.cellWidget(row, 0)
            if checkbox and checkbox.isChecked():
                selected_rows.append(row)
        
        if not selected_rows:
            QMessageBox.warning(self, "تنبيه", "الرجاء تحديد مستورد واحد على الأقل")
            return
        
        added_count = 0
        skipped_count = 0
        
        for row in selected_rows:
            try:
                company = self.results_table.item(row, 1).text()
                country = self.results_table.item(row, 2).text()
                email = self.results_table.item(row, 3).text()
                phone = self.results_table.item(row, 4).text()
                website = self.results_table.item(row, 5).text()
                
                if company == "-" or not company:
                    skipped_count += 1
                    continue
                
                # إضافة العميل
                client_data = {
                    "company_name": company,
                    "country": country if country != "-" else "",
                    "contact_person": "",
                    "email": email if email != "-" else "",
                    "phone": phone if phone != "-" else "",
                    "website": website if website != "-" else "",
                }
                
                add_client(client_data)
                added_count += 1
                
            except Exception as e:
                skipped_count += 1
                continue
        
        QMessageBox.information(
            self,
            "تم الإضافة",
            f"تم إضافة {added_count} عميل بنجاح\nتم تخطي {skipped_count} عميل"
        )
    
    def export_results(self):
        """تصدير النتائج إلى ملف Excel (مفضل) أو CSV"""
        if not self.current_results:
            QMessageBox.warning(self, "تنبيه", "لا توجد نتائج للتصدير")
            return
        
        try:
            from PyQt5.QtWidgets import QFileDialog
            import os
            
            exporter_name = self.exporter_input.text().strip().replace(' ', '_')
            if not exporter_name:
                exporter_name = "importers"
            
            # محاولة التصدير إلى Excel أولاً (تنسيق أفضل)
            file_path, selected_filter = QFileDialog.getSaveFileName(
                self,
                "حفظ النتائج - Save Results",
                f"importers_{exporter_name}.xlsx",
                "Excel Files (*.xlsx);;CSV Files (*.csv)"
            )
            
            if not file_path:
                return
            
            # تحويل النتائج إلى تنسيق مناسب للتصدير
            export_data = []
            for importer in self.current_results:
                export_data.append((
                    None,  # id
                    importer.get("company_name", ""),
                    importer.get("country", ""),
                    importer.get("contact_person", ""),
                    importer.get("email", ""),
                    importer.get("phone", ""),
                    importer.get("website", ""),
                    datetime.now().strftime("%d/%m/%Y"),
                    "New",
                    0,
                    "",
                    0
                ))
            
            if not export_data:
                QMessageBox.warning(self, "تنبيه", "لا توجد بيانات للتصدير")
                return
            
            success = False
            
            # محاولة التصدير إلى Excel أولاً (تنسيق أفضل)
            if file_path.endswith('.xlsx') or selected_filter.startswith('Excel'):
                try:
                    from core.export_data import export_clients_to_excel
                    success = export_clients_to_excel(file_path, export_data)
                    if success and os.path.exists(file_path):
                        file_size = os.path.getsize(file_path)
                        QMessageBox.information(
                            self, 
                            "نجح", 
                            f"تم التصدير بنجاح إلى:\n{file_path}\n\nحجم الملف: {file_size:,} بايت\nعدد الشركات: {len(export_data)}"
                        )
                    else:
                        raise Exception("فشل إنشاء ملف Excel")
                except Exception as e:
                    # إذا فشل Excel، حاول CSV
                    try:
                        csv_path = file_path.replace('.xlsx', '.csv') if file_path.endswith('.xlsx') else file_path
                        self._export_to_csv_improved(csv_path, export_data)
                        if os.path.exists(csv_path):
                            QMessageBox.information(
                                self, 
                                "نجح", 
                                f"تم التصدير إلى CSV:\n{csv_path}\n\nملاحظة: فشل التصدير إلى Excel بسبب:\n{str(e)}"
                            )
                        else:
                            raise Exception("فشل إنشاء ملف CSV")
                    except Exception as e2:
                        QMessageBox.critical(
                            self, 
                            "خطأ", 
                            f"فشل التصدير:\n{str(e)}\n\n{str(e2)}"
                        )
            else:
                # تصدير مباشر إلى CSV محسّن
                try:
                    self._export_to_csv_improved(file_path, export_data)
                    if os.path.exists(file_path):
                        file_size = os.path.getsize(file_path)
                        QMessageBox.information(
                            self, 
                            "نجح", 
                            f"تم التصدير بنجاح إلى:\n{file_path}\n\nحجم الملف: {file_size:,} بايت\nعدد الشركات: {len(export_data)}"
                        )
                    else:
                        QMessageBox.critical(self, "خطأ", "فشل إنشاء ملف CSV")
                except Exception as e:
                    QMessageBox.critical(self, "خطأ", f"حدث خطأ أثناء التصدير:\n{str(e)}")
                
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            QMessageBox.critical(
                self,
                "خطأ",
                f"حدث خطأ أثناء التصدير:\n{str(e)}\n\nالتفاصيل:\n{error_details[:500]}"
            )
    
    def _export_to_csv_improved(self, file_path: str, export_data: list):
        """تصدير محسّن إلى CSV بتنسيق متوافق مع Excel"""
        import csv
        
        # استخدام UTF-8-sig للتوافق مع Excel
        with open(file_path, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            
            # رأس الجدول
            writer.writerow([
                'ID', 'Company Name', 'Country', 'Contact Person',
                'Email', 'Phone', 'Website', 'Date Added',
                'Status', 'Score', 'Classification', 'Focus'
            ])
            
            # البيانات
            for client in export_data:
                (
                    client_id, company, country, contact, email,
                    phone, website, date_added, status, score,
                    classification, is_focus
                ) = client
                
                writer.writerow([
                    client_id or '',
                    company or '',
                    country or '',
                    contact or '',
                    email or '',
                    phone or '',
                    website or '',
                    date_added or '',
                    status or '',
                    score or 0,
                    classification or '',
                    'Yes' if is_focus else 'No'
                ])
    
    def analyze_results(self):
        """تحليل النتائج وفحص جودتها"""
        if not self.current_results:
            QMessageBox.warning(self, "تنبيه", "لا توجد نتائج للتحليل")
            return
        
        try:
            from core.analyze_export_results import analyze_export_file
            from PyQt5.QtWidgets import QFileDialog, QTextEdit, QDialog, QDialogButtonBox
            
            exporter_name = self.exporter_input.text().strip() or "Unknown"
            
            # إنشاء ملف مؤقت للتحليل
            import tempfile
            temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8')
            temp_file_path = temp_file.name
            
            # كتابة البيانات في الملف المؤقت
            import csv
            writer = csv.writer(temp_file)
            writer.writerow(['ID', 'Company Name', 'Country', 'Contact Person', 'Email', 'Phone', 'Website', 'Date Added', 'Status', 'Score', 'Classification', 'Focus'])
            
            for importer in self.current_results:
                writer.writerow([
                    None,
                    importer.get("company_name", ""),
                    importer.get("country", ""),
                    importer.get("contact_person", ""),
                    importer.get("email", ""),
                    importer.get("phone", ""),
                    importer.get("website", ""),
                    datetime.now().strftime("%d/%m/%Y"),
                    "New",
                    0,
                    "",
                    0
                ])
            
            temp_file.close()
            
            # تحليل الملف
            analysis = analyze_export_file(temp_file_path, exporter_name)
            
            # حذف الملف المؤقت
            try:
                os.unlink(temp_file_path)
            except:
                pass
            
            # عرض النتائج
            dialog = QDialog(self)
            dialog.setWindowTitle("📊 تحليل النتائج - Results Analysis")
            dialog.setMinimumSize(600, 500)
            
            layout = QVBoxLayout(dialog)
            
            title = QLabel("📊 تحليل جودة النتائج")
            title.setFont(QFont("Segoe UI", 12, QFont.Bold))
            layout.addWidget(title)
            
            text_edit = QTextEdit()
            text_edit.setReadOnly(True)
            text_edit.setFont(QFont("Courier New", 10))
            text_edit.setPlainText("\n".join(analysis.get("analysis", [])))
            layout.addWidget(text_edit)
            
            buttons = QDialogButtonBox(QDialogButtonBox.Ok)
            buttons.accepted.connect(dialog.accept)
            layout.addWidget(buttons)
            
            dialog.exec_()
            
        except Exception as e:
            import traceback
            QMessageBox.critical(
                self,
                "خطأ",
                f"حدث خطأ أثناء التحليل:\n{str(e)}\n\n{traceback.format_exc()[:500]}"
            )
"""
نافذة استيراد البيانات
Data Import Window
"""
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QMessageBox, QFileDialog, QGroupBox, QRadioButton,
    QButtonGroup, QTextEdit, QProgressBar, QTabWidget, QWidget
)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt
import os

from core.import_data import (
    import_clients_from_csv, import_clients_from_excel,
    import_messages_from_csv, import_deals_from_csv,
    EXCEL_AVAILABLE
)


class ImportWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setWindowTitle("📥 استيراد البيانات - Import Data")
        self.setMinimumSize(700, 600)
        
        main_layout = QVBoxLayout(self)
        
        # العنوان
        title = QLabel("📥 استيراد البيانات - Import Data")
        title.setFont(QFont("Segoe UI", 14, QFont.Bold))
        main_layout.addWidget(title)
        
        # نوع البيانات
        data_group = QGroupBox("اختر نوع البيانات - Select Data Type")
        data_layout = QVBoxLayout()
        
        self.data_button_group = QButtonGroup()
        
        self.clients_radio = QRadioButton("👥 العملاء - Clients")
        self.clients_radio.setChecked(True)
        self.data_button_group.addButton(self.clients_radio, 0)
        data_layout.addWidget(self.clients_radio)
        
        self.messages_radio = QRadioButton("✉️ الرسائل - Messages")
        self.data_button_group.addButton(self.messages_radio, 1)
        data_layout.addWidget(self.messages_radio)
        
        self.deals_radio = QRadioButton("💰 الصفقات - Deals")
        self.data_button_group.addButton(self.deals_radio, 2)
        data_layout.addWidget(self.deals_radio)
        
        data_group.setLayout(data_layout)
        main_layout.addWidget(data_group)
        
        # نوع الملف
        format_group = QGroupBox("اختر نوع الملف - Select File Format")
        format_layout = QVBoxLayout()
        
        self.format_button_group = QButtonGroup()
        
        self.csv_radio = QRadioButton("CSV (.csv)")
        self.csv_radio.setChecked(True)
        self.format_button_group.addButton(self.csv_radio, 0)
        format_layout.addWidget(self.csv_radio)
        
        self.excel_radio = QRadioButton("Excel (.xlsx)")
        self.excel_radio.setEnabled(EXCEL_AVAILABLE)
        if not EXCEL_AVAILABLE:
            self.excel_radio.setToolTip("openpyxl غير مثبت. قم بتثبيته باستخدام: pip install openpyxl")
        self.format_button_group.addButton(self.excel_radio, 1)
        format_layout.addWidget(self.excel_radio)
        
        format_group.setLayout(format_layout)
        main_layout.addWidget(format_group)
        
        # معلومات الملف
        file_group = QGroupBox("الملف - File")
        file_layout = QVBoxLayout()
        
        file_select_layout = QHBoxLayout()
        self.file_path_label = QLabel("لم يتم اختيار ملف")
        self.file_path_label.setWordWrap(True)
        file_select_layout.addWidget(self.file_path_label)
        
        browse_btn = QPushButton("📂 تصفح...")
        browse_btn.clicked.connect(self.browse_file)
        file_select_layout.addWidget(browse_btn)
        
        file_layout.addLayout(file_select_layout)
        file_group.setLayout(file_layout)
        main_layout.addWidget(file_group)
        
        # معلومات الاستيراد
        info_group = QGroupBox("معلومات الاستيراد - Import Information")
        info_layout = QVBoxLayout()
        
        info_text = QLabel("""
        <b>ملاحظات مهمة:</b><br>
        • يجب أن يحتوي الملف على رؤوس (Headers) في الصف الأول<br>
        • للعملاء: يجب أن يحتوي على عمود "Company Name" أو "اسم الشركة"<br>
        • للرسائل: يجب أن يحتوي على عمود "Client" أو "عميل" و "Subject" أو "موضوع"<br>
        • للصفقات: يجب أن يحتوي على عمود "Client" أو "عميل" و "Deal Name" أو "اسم الصفقة"<br>
        • سيتم تخطي السجلات المكررة تلقائياً<br>
        • سيتم التحقق من صحة البيانات قبل الاستيراد
        """)
        info_text.setWordWrap(True)
        info_layout.addWidget(info_text)
        
        info_group.setLayout(info_layout)
        main_layout.addWidget(info_group)
        
        # شريط التقدم
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)
        
        # نتائج الاستيراد
        results_group = QGroupBox("نتائج الاستيراد - Import Results")
        results_layout = QVBoxLayout()
        
        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        self.results_text.setMaximumHeight(150)
        results_layout.addWidget(self.results_text)
        
        results_group.setLayout(results_layout)
        main_layout.addWidget(results_group)
        
        # الأزرار
        btn_layout = QHBoxLayout()
        
        btn_layout.addStretch()
        
        cancel_btn = QPushButton("إلغاء")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        import_btn = QPushButton("📥 استيراد")
        import_btn.setStyleSheet("background-color: #4ECDC4; color: white; font-weight: bold; padding: 8px;")
        import_btn.clicked.connect(self.do_import)
        btn_layout.addWidget(import_btn)
        
        main_layout.addLayout(btn_layout)
        
        self.file_path = None
    
    def browse_file(self):
        """اختيار ملف للاستيراد"""
        data_type = self.data_button_group.checkedId()
        format_type = self.format_button_group.checkedId()
        
        # تحديد نوع الملف
        if format_type == 0:  # CSV
            file_filter = "CSV Files (*.csv);;All Files (*.*)"
            default_ext = ".csv"
        else:  # Excel
            if not EXCEL_AVAILABLE:
                QMessageBox.warning(
                    self,
                    "Excel غير متاح",
                    "openpyxl غير مثبت. قم بتثبيته باستخدام: pip install openpyxl"
                )
                return
            file_filter = "Excel Files (*.xlsx *.xls);;All Files (*.*)"
            default_ext = ".xlsx"
        
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "اختر ملف للاستيراد",
            "",
            file_filter
        )
        
        if file_path:
            self.file_path = file_path
            self.file_path_label.setText(f"📄 {os.path.basename(file_path)}")
            self.results_text.clear()
    
    def do_import(self):
        """تنفيذ الاستيراد"""
        if not self.file_path or not os.path.exists(self.file_path):
            QMessageBox.warning(
                self,
                "اختر ملف",
                "يرجى اختيار ملف للاستيراد أولاً"
            )
            return
        
        data_type = self.data_button_group.checkedId()
        format_type = self.format_button_group.checkedId()
        
        # إظهار شريط التقدم
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate
        self.results_text.clear()
        
        try:
            # استيراد حسب النوع
            if data_type == 0:  # Clients
                if format_type == 0:  # CSV
                    results = import_clients_from_csv(self.file_path)
                else:  # Excel
                    results = import_clients_from_excel(self.file_path)
                data_name = "العملاء"
            
            elif data_type == 1:  # Messages
                if format_type == 1:  # Excel not supported for messages yet
                    QMessageBox.warning(
                        self,
                        "غير مدعوم",
                        "استيراد الرسائل من Excel غير متاح حالياً. استخدم CSV."
                    )
                    self.progress_bar.setVisible(False)
                    return
                results = import_messages_from_csv(self.file_path)
                data_name = "الرسائل"
            
            else:  # Deals
                if format_type == 1:  # Excel not supported for deals yet
                    QMessageBox.warning(
                        self,
                        "غير مدعوم",
                        "استيراد الصفقات من Excel غير متاح حالياً. استخدم CSV."
                    )
                    self.progress_bar.setVisible(False)
                    return
                results = import_deals_from_csv(self.file_path)
                data_name = "الصفقات"
            
            # عرض النتائج
            self.progress_bar.setVisible(False)
            
            success_count = results.get('success', 0)
            failed_count = results.get('failed', 0)
            skipped_count = results.get('skipped', 0)
            errors = results.get('errors', [])
            
            # رسالة النجاح
            message = f"""
            <b>تم الانتهاء من استيراد {data_name}</b><br><br>
            ✅ نجح: {success_count}<br>
            ⚠️ تم التخطي: {skipped_count}<br>
            ❌ فشل: {failed_count}<br>
            """
            
            if errors:
                message += f"<br><b>الأخطاء ({min(len(errors), 10)} من {len(errors)}):</b><br>"
                for error in errors[:10]:  # عرض أول 10 أخطاء فقط
                    message += f"• {error}<br>"
                if len(errors) > 10:
                    message += f"<br>... و {len(errors) - 10} خطأ آخر"
            
            self.results_text.setHtml(message)
            
            # رسالة تأكيد
            if success_count > 0:
                QMessageBox.information(
                    self,
                    "نجح الاستيراد",
                    f"تم استيراد {success_count} {data_name} بنجاح!\n\n"
                    f"تم التخطي: {skipped_count}\n"
                    f"فشل: {failed_count}"
                )
            elif skipped_count > 0 or failed_count > 0:
                QMessageBox.warning(
                    self,
                    "استيراد جزئي",
                    f"تم التخطي: {skipped_count}\n"
                    f"فشل: {failed_count}\n\n"
                    "راجع نتائج الاستيراد أدناه للتفاصيل."
                )
            else:
                QMessageBox.warning(
                    self,
                    "لا توجد بيانات",
                    "لم يتم استيراد أي بيانات. راجع نتائج الاستيراد أدناه."
                )
        
        except Exception as e:
            self.progress_bar.setVisible(False)
            QMessageBox.critical(
                self,
                "خطأ في الاستيراد",
                f"حدث خطأ أثناء الاستيراد:\n{str(e)}"
            )
            self.results_text.setPlainText(f"خطأ: {str(e)}")

"""
نافذة تصدير البيانات
Data Export Window
"""
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QMessageBox, QFileDialog, QGroupBox, QRadioButton,
    QButtonGroup, QTextEdit
)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt
import os

from core.export_data import (
    export_clients_to_csv, export_clients_to_excel,
    export_messages_to_csv, export_messages_to_excel,
    export_requests_to_csv, export_requests_to_excel,
    export_full_report_to_excel,
    EXCEL_AVAILABLE
)
try:
    from core.pdf_reports import (
        export_client_report_to_pdf, export_full_report_to_pdf,
        PDF_AVAILABLE
    )
except ImportError:
    PDF_AVAILABLE = False


class ExportWindow(QDialog):
    def __init__(self, parent=None, selected_client_id=None):
        super().__init__(parent)
        
        self.selected_client_id = selected_client_id
        self.setWindowTitle("📤 تصدير البيانات - Export Data")
        self.setMinimumSize(600, 500)
        
        main_layout = QVBoxLayout(self)
        
        # العنوان
        title = QLabel("📤 تصدير البيانات - Export Data")
        title.setFont(QFont("Segoe UI", 14, QFont.Bold))
        main_layout.addWidget(title)
        
        # نوع البيانات
        data_group = QGroupBox("اختر نوع البيانات - Select Data Type")
        data_layout = QVBoxLayout()
        
        self.data_button_group = QButtonGroup()
        
        self.export_clients_radio = QRadioButton("📋 قائمة العملاء - Clients List")
        self.export_clients_radio.setChecked(True)
        self.data_button_group.addButton(self.export_clients_radio, 1)
        data_layout.addWidget(self.export_clients_radio)
        
        self.export_messages_radio = QRadioButton("✉️ الرسائل - Messages")
        if selected_client_id:
            self.export_messages_radio.setText("✉️ رسائل العميل المحدد - Selected Client Messages")
        self.data_button_group.addButton(self.export_messages_radio, 2)
        data_layout.addWidget(self.export_messages_radio)
        
        self.export_requests_radio = QRadioButton("📋 الطلبات - Requests")
        self.data_button_group.addButton(self.export_requests_radio, 3)
        data_layout.addWidget(self.export_requests_radio)
        
        self.export_full_report_radio = QRadioButton("📊 تقرير شامل - Full Report (Excel Only)")
        self.data_button_group.addButton(self.export_full_report_radio, 4)
        data_layout.addWidget(self.export_full_report_radio)
        
        data_group.setLayout(data_layout)
        main_layout.addWidget(data_group)
        
        # تنسيق الملف
        format_group = QGroupBox("اختر تنسيق الملف - Select File Format")
        format_layout = QVBoxLayout()
        
        self.format_button_group = QButtonGroup()
        
        self.csv_radio = QRadioButton("CSV (Comma Separated Values)")
        self.format_button_group.addButton(self.csv_radio, 1)
        format_layout.addWidget(self.csv_radio)
        
        self.excel_radio = QRadioButton("Excel (.xlsx)")
        self.excel_radio.setChecked(True)
        if not EXCEL_AVAILABLE:
            self.excel_radio.setEnabled(False)
            self.excel_radio.setText("Excel (.xlsx) - Requires openpyxl (pip install openpyxl)")
            self.csv_radio.setChecked(True)
        self.format_button_group.addButton(self.excel_radio, 2)
        format_layout.addWidget(self.excel_radio)
        
        # PDF option (only for client reports and full reports)
        self.pdf_radio = QRadioButton("PDF (.pdf)")
        if not PDF_AVAILABLE:
            self.pdf_radio.setEnabled(False)
            self.pdf_radio.setText("PDF (.pdf) - Requires reportlab (pip install reportlab)")
        self.format_button_group.addButton(self.pdf_radio, 3)
        format_layout.addWidget(self.pdf_radio)
        
        format_group.setLayout(format_layout)
        main_layout.addWidget(format_group)
        
        # معلومات
        info_text = QTextEdit()
        info_text.setReadOnly(True)
        info_text.setMaximumHeight(100)
        info_text.setPlainText(
            "ملاحظات:\n"
            "- CSV: ملف نصي بسيط، متوافق مع جميع البرامج\n"
            "- Excel: ملف Excel متقدم مع تنسيق وألوان\n"
            "- PDF: تقرير PDF احترافي (متوفر للعملاء والتقارير الشاملة)\n"
            "- سيتم حفظ الملف في المكان الذي تحدده"
        )
        main_layout.addWidget(info_text)
        
        # الأزرار
        btn_layout = QHBoxLayout()
        
        export_btn = QPushButton("📤 تصدير - Export")
        export_btn.clicked.connect(self.do_export)
        btn_layout.addWidget(export_btn)
        
        cancel_btn = QPushButton("إلغاء - Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        btn_layout.addStretch()
        main_layout.addLayout(btn_layout)
    
    def do_export(self):
        """تنفيذ عملية التصدير"""
        try:
            # تحديد نوع البيانات
            data_type = self.data_button_group.checkedId()
            
            # تحديد تنسيق الملف
            format_id = self.format_button_group.checkedId()
            is_excel = format_id == 2
            is_pdf = format_id == 3
            
            if is_excel and not EXCEL_AVAILABLE:
                QMessageBox.warning(
                    self,
                    "تحذير",
                    "مكتبة openpyxl غير متوفرة!\n"
                    "يرجى تثبيتها باستخدام:\n"
                    "pip install openpyxl\n\n"
                    "أو اختر تنسيق CSV"
                )
                return
            
            if is_pdf and not PDF_AVAILABLE:
                QMessageBox.warning(
                    self,
                    "تحذير",
                    "مكتبة reportlab غير متوفرة!\n"
                    "يرجى تثبيتها باستخدام:\n"
                    "pip install reportlab"
                )
                return
            
            # تحديد اسم الملف الافتراضي
            default_filename = self.get_default_filename(data_type, is_excel, is_pdf)
            default_path = os.path.join(os.path.expanduser("~"), "Desktop", default_filename)
            
            # اختيار المكان
            if is_pdf:
                file_filter = "PDF Files (*.pdf);;All Files (*.*)"
                extension = ".pdf"
            elif is_excel:
                file_filter = "Excel Files (*.xlsx);;All Files (*.*)"
                extension = ".xlsx"
            else:
                file_filter = "CSV Files (*.csv);;All Files (*.*)"
                extension = ".csv"
            
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "حفظ الملف - Save File",
                default_path,
                file_filter
            )
            
            if not file_path:
                return
            
            # التأكد من وجود الامتداد
            if not file_path.endswith(extension):
                file_path += extension
            
            # تنفيذ التصدير
            success = False
            message = ""
            
            if data_type == 1:  # العملاء
                if is_pdf:
                    if self.selected_client_id:
                        success = export_client_report_to_pdf(self.selected_client_id, file_path)
                        message = "تم تصدير تقرير العميل إلى PDF بنجاح!"
                    else:
                        QMessageBox.warning(
                            self,
                            "تحذير",
                            "التصدير إلى PDF يتطلب اختيار عميل محدد!\n"
                            "يرجى فتح تقرير عميل أولاً أو اختر تنسيق آخر."
                        )
                        return
                elif is_excel:
                    success = export_clients_to_excel(file_path)
                    message = "تم تصدير قائمة العملاء إلى Excel بنجاح!"
                else:
                    success = export_clients_to_csv(file_path)
                    message = "تم تصدير قائمة العملاء إلى CSV بنجاح!"
            
            elif data_type == 2:  # الرسائل
                if is_pdf:
                    if self.selected_client_id:
                        success = export_client_report_to_pdf(self.selected_client_id, file_path)
                        message = "تم تصدير تقرير العميل (مع الرسائل) إلى PDF بنجاح!"
                    else:
                        QMessageBox.warning(
                            self,
                            "تحذير",
                            "التصدير إلى PDF يتطلب اختيار عميل محدد!\n"
                            "يرجى فتح تقرير عميل أولاً أو اختر تنسيق آخر."
                        )
                        return
                elif is_excel:
                    success = export_messages_to_excel(file_path, self.selected_client_id)
                    message = "تم تصدير الرسائل إلى Excel بنجاح!"
                else:
                    success = export_messages_to_csv(file_path, self.selected_client_id)
                    message = "تم تصدير الرسائل إلى CSV بنجاح!"
            
            elif data_type == 3:  # الطلبات
                if is_pdf:
                    QMessageBox.warning(
                        self,
                        "تحذير",
                        "التصدير إلى PDF غير متوفر للطلبات!\n"
                        "يرجى استخدام Excel أو CSV."
                    )
                    return
                elif is_excel:
                    success = export_requests_to_excel(file_path)
                    message = "تم تصدير الطلبات إلى Excel بنجاح!"
                else:
                    success = export_requests_to_csv(file_path)
                    message = "تم تصدير الطلبات إلى CSV بنجاح!"
            
            elif data_type == 4:  # التقرير الشامل
                if is_pdf:
                    success = export_full_report_to_pdf(file_path)
                    message = "تم تصدير التقرير الشامل إلى PDF بنجاح!"
                elif is_excel:
                    success = export_full_report_to_excel(file_path)
                    message = "تم تصدير التقرير الشامل إلى Excel بنجاح!"
                else:
                    QMessageBox.warning(
                        self,
                        "تحذير",
                        "التقرير الشامل متوفر فقط بصيغة Excel أو PDF!"
                    )
                    return
            
            if success:
                QMessageBox.information(
                    self,
                    "نجح التصدير",
                    f"{message}\n\nالموقع: {file_path}"
                )
                self.accept()
            else:
                QMessageBox.critical(
                    self,
                    "فشل التصدير",
                    "حدث خطأ أثناء التصدير!\nيرجى المحاولة مرة أخرى."
                )
                
        except Exception as e:
            QMessageBox.critical(
                self,
                "خطأ",
                f"حدث خطأ أثناء التصدير:\n\n{str(e)}"
            )
    
    def get_default_filename(self, data_type, is_excel, is_pdf=False):
        """الحصول على اسم الملف الافتراضي"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if is_pdf:
            extension = ".pdf"
        else:
            extension = ".xlsx" if is_excel else ".csv"
        
        if data_type == 1:
            return f"EFM_Clients_{timestamp}{extension}"
        elif data_type == 2:
            if self.selected_client_id:
                return f"EFM_Messages_Client_{self.selected_client_id}_{timestamp}{extension}"
            return f"EFM_Messages_All_{timestamp}{extension}"
        elif data_type == 3:
            return f"EFM_Requests_{timestamp}{extension}"
        elif data_type == 4:
            return f"EFM_FullReport_{timestamp}{extension}"
        
        return f"EFM_Export_{timestamp}{extension}"

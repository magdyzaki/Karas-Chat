"""
نافذة إدارة المستندات
Documents Management Window
"""
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QMessageBox, QTableWidget, QTableWidgetItem, QLineEdit,
    QGroupBox, QComboBox, QFileDialog, QTextEdit
)
from PyQt5.QtGui import QFont, QIcon
from PyQt5.QtCore import Qt
import os
import subprocess
from datetime import datetime

from core.db import (
    get_client_documents, add_document, delete_document,
    get_document_by_id, search_documents, get_client_by_id
)
from core.documents import (
    save_document_file, get_file_type, format_file_size,
    get_file_size
)


class DocumentsWindow(QDialog):
    def __init__(self, parent=None, client_id=None):
        super().__init__(parent)
        
        self.client_id = client_id
        self.setWindowTitle("📄 إدارة المستندات - Documents Management")
        self.setMinimumSize(1000, 600)
        
        main_layout = QVBoxLayout(self)
        
        # العنوان
        title = QLabel("📄 إدارة المستندات - Documents Management")
        title.setFont(QFont("Segoe UI", 14, QFont.Bold))
        main_layout.addWidget(title)
        
        # معلومات العميل
        if client_id:
            client = get_client_by_id(client_id)
            if client:
                client_info = QLabel(f"العميل: {client[1]} | {client[4] or 'بدون بريد إلكتروني'}")
                client_info.setStyleSheet("font-weight: bold; color: #4ECDC4; padding: 5px;")
                main_layout.addWidget(client_info)
        
        # ===== البحث =====
        search_group = QGroupBox("بحث - Search")
        search_layout = QHBoxLayout()
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("ابحث في اسم الملف، النوع، الوصف...")
        self.search_input.textChanged.connect(self.load_documents)
        search_layout.addWidget(self.search_input)
        
        self.doc_type_filter = QComboBox()
        self.doc_type_filter.addItems([
            "جميع الأنواع",
            "عرض أسعار",
            "عينة",
            "عقد",
            "فاتورة",
            "شهادة",
            "أخرى"
        ])
        self.doc_type_filter.currentTextChanged.connect(self.load_documents)
        search_layout.addWidget(QLabel("نوع المستند:"))
        search_layout.addWidget(self.doc_type_filter)
        
        search_group.setLayout(search_layout)
        main_layout.addWidget(search_group)
        
        # ===== جدول المستندات =====
        self.documents_table = QTableWidget()
        self.documents_table.setColumnCount(7)
        self.documents_table.setHorizontalHeaderLabels([
            "ID", "اسم الملف", "النوع", "حجم الملف", "نوع المستند", "الوصف", "تاريخ الرفع"
        ])
        self.documents_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.documents_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.documents_table.setSortingEnabled(True)
        self.documents_table.horizontalHeader().setStretchLastSection(True)
        self.documents_table.cellDoubleClicked.connect(self.open_document)
        main_layout.addWidget(self.documents_table)
        
        # ===== الأزرار =====
        buttons_layout = QHBoxLayout()
        
        self.upload_btn = QPushButton("📤 رفع مستند")
        self.upload_btn.clicked.connect(self.upload_document)
        self.upload_btn.setStyleSheet("background-color: #4ECDC4; color: white; font-weight: bold; border-radius: 5px; padding: 8px;")
        buttons_layout.addWidget(self.upload_btn)
        
        self.view_btn = QPushButton("👁 فتح")
        self.view_btn.clicked.connect(self.open_document)
        buttons_layout.addWidget(self.view_btn)
        
        # مربع نص الرسالة
        self.message_input = QTextEdit()
        self.message_input.setPlaceholderText("اكتب رسالة للعميل (اختياري)...")
        self.message_input.setMaximumHeight(80)
        main_layout.addWidget(QLabel("رسالة الإرسال:"))
        main_layout.addWidget(self.message_input)
        
        self.send_btn = QPushButton("📧 إرسال عبر Outlook")
        self.send_btn.clicked.connect(self.send_via_outlook)
        self.send_btn.setStyleSheet("background-color: #0078D4; color: white; font-weight: bold; border-radius: 5px; padding: 8px;")
        buttons_layout.addWidget(self.send_btn)
        
        self.delete_btn = QPushButton("🗑 حذف")
        self.delete_btn.clicked.connect(self.delete_selected_document)
        self.delete_btn.setStyleSheet("background-color: #FF6B6B; color: white; font-weight: bold; border-radius: 5px; padding: 8px;")
        buttons_layout.addWidget(self.delete_btn)
        
        buttons_layout.addStretch()
        main_layout.addLayout(buttons_layout)
        
        # تحميل المستندات
        self.load_documents()
    
    def load_documents(self):
        """تحميل المستندات"""
        search_text = self.search_input.text().strip()
        doc_type_filter = self.doc_type_filter.currentText()
        
        if search_text:
            if self.client_id:
                documents = search_documents(search_text, self.client_id)
            else:
                documents = search_documents(search_text)
        elif self.client_id:
            documents = get_client_documents(self.client_id)
        else:
            documents = []
        
        # فلترة حسب نوع المستند
        if doc_type_filter != "جميع الأنواع":
            documents = [doc for doc in documents if doc[5] == doc_type_filter]
        
        # عرض في الجدول
        self.documents_table.setRowCount(len(documents))
        
        for row, doc in enumerate(documents):
            # doc structure: (id, client_id, file_name, file_path, file_type, file_size, document_type, description, uploaded_date, uploaded_by)
            doc_id = doc[0]
            file_name = doc[2]
            file_type = doc[4] if len(doc) > 4 else None
            file_size = doc[5] if len(doc) > 5 else 0
            document_type = doc[6] if len(doc) > 6 else None
            description = doc[7] if len(doc) > 7 else ""
            uploaded_date = doc[8] if len(doc) > 8 else ""
            
            values = [
                str(doc_id),
                file_name,
                file_type or "Unknown",
                format_file_size(file_size or 0),
                document_type or "غير محدد",
                description or "",
                uploaded_date or ""
            ]
            
            for col, val in enumerate(values):
                item = QTableWidgetItem(str(val))
                item.setData(Qt.UserRole, doc_id)
                self.documents_table.setItem(row, col, item)
    
    def upload_document(self):
        """رفع مستند جديد"""
        if not self.client_id:
            QMessageBox.warning(self, "تنبيه", "الرجاء تحديد عميل أولاً")
            return
        
        # اختيار الملف
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "اختر الملف - Select File",
            "",
            "All Files (*.*);;PDF Files (*.pdf);;Word Documents (*.doc *.docx);;Excel Files (*.xls *.xlsx);;Images (*.jpg *.jpeg *.png)"
        )
        
        if not file_path:
            return
        
        # نافذة إدخال معلومات المستند
        from PyQt5.QtWidgets import QDialog, QFormLayout, QDialogButtonBox
        
        info_dialog = QDialog(self)
        info_dialog.setWindowTitle("معلومات المستند")
        info_dialog.setMinimumWidth(400)
        
        layout = QFormLayout(info_dialog)
        
        doc_type_combo = QComboBox()
        doc_type_combo.addItems([
            "عرض أسعار",
            "عينة",
            "عقد",
            "فاتورة",
            "شهادة",
            "أخرى"
        ])
        layout.addRow("نوع المستند:", doc_type_combo)
        
        description_edit = QTextEdit()
        description_edit.setMaximumHeight(100)
        description_edit.setPlaceholderText("وصف المستند (اختياري)")
        layout.addRow("الوصف:", description_edit)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(info_dialog.accept)
        buttons.rejected.connect(info_dialog.reject)
        layout.addRow(buttons)
        
        if info_dialog.exec_() != QDialog.Accepted:
            return
        
        try:
            # حفظ الملف
            file_name = os.path.basename(file_path)
            saved_path = save_document_file(file_path, self.client_id, file_name)
            
            # إضافة إلى قاعدة البيانات
            doc_data = {
                "client_id": self.client_id,
                "file_name": file_name,
                "file_path": saved_path,
                "file_type": get_file_type(file_name),
                "file_size": get_file_size(saved_path),
                "document_type": doc_type_combo.currentText(),
                "description": description_edit.toPlainText().strip(),
                "uploaded_date": datetime.now().strftime("%d/%m/%Y %H:%M"),
                "uploaded_by": "User"
            }
            
            add_document(doc_data)
            
            QMessageBox.information(self, "نجح", "تم رفع المستند بنجاح")
            self.load_documents()
            
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"حدث خطأ أثناء رفع المستند:\n{str(e)}")
    
    def get_selected_document_id(self):
        """الحصول على معرف المستند المحدد"""
        row = self.documents_table.currentRow()
        if row < 0:
            return None
        
        item = self.documents_table.item(row, 0)
        if item:
            return item.data(Qt.UserRole)
        return None
    
    def open_document(self):
        """فتح المستند"""
        doc_id = self.get_selected_document_id()
        if not doc_id:
            QMessageBox.warning(self, "تنبيه", "الرجاء تحديد مستند أولاً")
            return
        
        doc = get_document_by_id(doc_id)
        if not doc:
            QMessageBox.warning(self, "خطأ", "المستند غير موجود")
            return
        
        file_path = doc[3]  # file_path
        
        if not os.path.exists(file_path):
            QMessageBox.warning(self, "خطأ", "الملف غير موجود على القرص")
            return
        
        try:
            # فتح الملف باستخدام البرنامج الافتراضي
            if os.name == 'nt':  # Windows
                os.startfile(file_path)
            elif os.name == 'posix':  # macOS/Linux
                subprocess.call(['open' if sys.platform == 'darwin' else 'xdg-open', file_path])
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"حدث خطأ أثناء فتح الملف:\n{str(e)}")
    
    def delete_selected_document(self):
        """حذف المستند المحدد"""
        doc_id = self.get_selected_document_id()
        if not doc_id:
            QMessageBox.warning(self, "تنبيه", "الرجاء تحديد مستند أولاً")
            return
        
        doc = get_document_by_id(doc_id)
        if not doc:
            return
        
        file_name = doc[2]  # file_name
        
        reply = QMessageBox.question(
            self,
            "تأكيد الحذف",
            f"هل تريد حذف المستند '{file_name}'؟\nسيتم حذف الملف من القرص أيضاً.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                delete_document(doc_id)
                QMessageBox.information(self, "نجح", "تم حذف المستند بنجاح")
                self.load_documents()
            except Exception as e:
                QMessageBox.critical(self, "خطأ", f"حدث خطأ أثناء الحذف:\n{str(e)}")
    
    def send_via_outlook(self):
        """إرسال المستند عبر Outlook"""
        doc_id = self.get_selected_document_id()
        if not doc_id:
            QMessageBox.warning(self, "تنبيه", "الرجاء تحديد مستند أولاً")
            return
        
        if not self.client_id:
            QMessageBox.warning(self, "تنبيه", "العميل غير محدد")
            return
        
        # الحصول على معلومات المستند والعميل
        doc = get_document_by_id(doc_id)
        if not doc:
            return
        
        client = get_client_by_id(self.client_id)
        if not client:
            return
        
        client_email = client[4]  # email
        if not client_email:
            QMessageBox.warning(self, "تنبيه", "العميل لا يمتلك بريد إلكتروني")
            return
        
        file_path = doc[3]  # file_path
        file_name = doc[2]  # file_name
        client_name = client[1]  # company_name
        
        if not os.path.exists(file_path):
            QMessageBox.warning(self, "خطأ", "الملف غير موجود على القرص")
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
            # استدعاء وظيفة الإرسال
            from core.ms_document_sender import create_draft_with_attachment
            
            subject = f"Document: {file_name}"
            body = f"Dear {client_name},<br><br>Please find attached: {file_name}"
            
            draft_id = create_draft_with_attachment(
                graph_token=graph_token,
                to_email=client_email,
                subject=subject,
                body=body,
                attachment_path=file_path
            )
            
            QMessageBox.information(
                self,
                "نجح",
                f"تم إنشاء مسودة رسالة مع المرفق.\nافتح Outlook لمراجعة وإرسال الرسالة."
            )
            
        except Exception as e:
            error_msg = str(e)
            if "يدوياً" in error_msg or "manually" in error_msg.lower():
                QMessageBox.warning(
                    self,
                    "تنبيه",
                    f"{error_msg}\n\nتم فتح Outlook. يرجى إضافة الملف يدوياً."
                )
            else:
                QMessageBox.critical(self, "خطأ", f"حدث خطأ أثناء الإرسال:\n{error_msg}")

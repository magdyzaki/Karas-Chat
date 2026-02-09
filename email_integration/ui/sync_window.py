"""
نافذة المزامنة المخصصة
Custom Sync Window
"""
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QMessageBox, QLineEdit,
    QGroupBox, QFormLayout, QComboBox, QCheckBox, QProgressDialog,
    QTextEdit, QScrollArea, QTabWidget, QWidget, QSplitter
)
from PyQt5.QtGui import QFont, QColor, QBrush
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtWidgets import QApplication

from core.db import (
    get_custom_sync_clients,
    add_custom_sync_client,
    delete_custom_sync_client,
    find_custom_sync_client_by_email,
    find_client_by_email,
    get_client_messages,
    remove_duplicate_messages,
)
from core.ms_mail_reader import read_messages_from_folder
from core.logging_system import log_error, log_info


class AddClientDialog(QDialog):
    """نافذة منبثقة لإضافة عميل جديد"""
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setWindowTitle("➕ إضافة عميل جديد")
        self.setMinimumSize(500, 400)
        
        # تطبيق الثيم
        try:
            from core.theme import get_theme_manager
            theme_manager = get_theme_manager()
            self.setStyleSheet(theme_manager.get_stylesheet())
        except:
            pass
        
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # العنوان
        title = QLabel("➕ إضافة عميل جديد")
        title.setFont(QFont("Segoe UI", 12, QFont.Bold))
        layout.addWidget(title)
        
        # حقول الإدخال
        form_group = QGroupBox("بيانات العميل")
        form_layout = QFormLayout()
        form_layout.setSpacing(10)
        
        self.company_input = QLineEdit()
        self.company_input.setPlaceholderText("اسم الشركة")
        form_layout.addRow("الشركة:", self.company_input)
        
        self.country_input = QLineEdit()
        self.country_input.setPlaceholderText("البلد")
        form_layout.addRow("البلد:", self.country_input)
        
        self.contact_input = QLineEdit()
        self.contact_input.setPlaceholderText("اسم جهة الاتصال")
        form_layout.addRow("جهة الاتصال:", self.contact_input)
        
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("البريد الإلكتروني")
        form_layout.addRow("البريد الإلكتروني:", self.email_input)
        
        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText("رقم الهاتف")
        form_layout.addRow("الهاتف:", self.phone_input)
        
        self.website_input = QLineEdit()
        self.website_input.setPlaceholderText("الموقع الإلكتروني")
        form_layout.addRow("الموقع:", self.website_input)
        
        form_group.setLayout(form_layout)
        layout.addWidget(form_group)
        
        # الأزرار
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        cancel_btn = QPushButton("إلغاء")
        cancel_btn.clicked.connect(self.reject)
        cancel_btn.setMinimumHeight(35)
        btn_layout.addWidget(cancel_btn)
        
        add_btn = QPushButton("➕ إضافة")
        add_btn.clicked.connect(self.add_client)
        add_btn.setMinimumHeight(35)
        add_btn.setDefault(True)
        btn_layout.addWidget(add_btn)
        
        layout.addLayout(btn_layout)
    
    def add_client(self):
        """إضافة العميل"""
        from core.db import add_custom_sync_client, find_custom_sync_client_by_email
        
        company = self.company_input.text().strip()
        country = self.country_input.text().strip()
        contact = self.contact_input.text().strip()
        email = self.email_input.text().strip()
        phone = self.phone_input.text().strip()
        website = self.website_input.text().strip()
        
        if not company and not email:
            QMessageBox.warning(self, "تحذير", "يرجى إدخال اسم الشركة أو البريد الإلكتروني على الأقل.")
            return
        
        if email:
            # التحقق من وجوده داخل "المزامنة الخاصة" فقط
            existing = find_custom_sync_client_by_email(email)
            if existing:
                QMessageBox.warning(
                    self,
                    "عميل موجود",
                    f"يوجد بالفعل عميل بهذا البريد الإلكتروني داخل المزامنة الخاصة:\n{email}"
                )
                return
        
        try:
            # إضافة العميل داخل جدول مستقل للمزامنة الخاصة
            add_custom_sync_client({
                "company_name": company or "غير محدد",
                "country": country or "",
                "contact_person": contact or "",
                "email": email or "",
                "phone": phone or "",
                "website": website or "",
                "date_added": __import__("datetime").datetime.now().strftime("%d/%m/%Y %H:%M"),
            })
            
            QMessageBox.information(self, "نجح", "تم إضافة العميل بنجاح!")
            
            # إغلاق النافذة
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"حدث خطأ أثناء إضافة العميل:\n{str(e)}")


class MessageDetailsDialog(QDialog):
    """نافذة عرض محتوى الرسالة الكامل"""
    def __init__(self, message_data, email=None, company=None, parent=None):
        super().__init__(parent)
        
        self.setWindowTitle("📧 تفاصيل الرسالة")
        self.setMinimumSize(800, 600)
        
        # تطبيق الثيم
        try:
            from core.theme import get_theme_manager
            theme_manager = get_theme_manager()
            self.setStyleSheet(theme_manager.get_stylesheet())
        except:
            pass
        
        layout = QVBoxLayout(self)
        
        # استخراج بيانات الرسالة
        (message_date, actual_date, message_type, channel, 
         client_response, notes, score_effect) = message_data
        
        date_str = actual_date or message_date or ""
        
        # العنوان
        title = QLabel("📧 تفاصيل الرسالة")
        title.setFont(QFont("Segoe UI", 14, QFont.Bold))
        layout.addWidget(title)
        
        # معلومات الرسالة
        info_group = QGroupBox("معلومات الرسالة")
        info_layout = QVBoxLayout()
        
        if company:
            info_layout.addWidget(QLabel(f"<b>العميل:</b> {company}"))
        if email:
            info_layout.addWidget(QLabel(f"<b>البريد الإلكتروني:</b> {email}"))
        info_layout.addWidget(QLabel(f"<b>التاريخ:</b> {date_str}"))
        info_layout.addWidget(QLabel(f"<b>النوع:</b> {message_type or 'غير محدد'}"))
        info_layout.addWidget(QLabel(f"<b>القناة:</b> {channel or 'غير محدد'}"))
        if score_effect:
            info_layout.addWidget(QLabel(f"<b>تأثير النقاط:</b> {score_effect}"))
        
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)
        
        # الموضوع
        if client_response:
            subject_group = QGroupBox("الموضوع")
            subject_layout = QVBoxLayout()
            subject_label = QLabel(client_response)
            subject_label.setWordWrap(True)
            subject_label.setStyleSheet("padding: 8px; background: #f5f5f5; border-radius: 4px;")
            subject_layout.addWidget(subject_label)
            subject_group.setLayout(subject_layout)
            layout.addWidget(subject_group)
        
        # المحتوى الكامل
        content_group = QGroupBox("المحتوى الكامل")
        content_layout = QVBoxLayout()
        
        notes_content = notes or "لا يوجد محتوى"
        
        # التحقق مما إذا كان المحتوى HTML
        is_html = False
        if notes_content.strip().lower().startswith('<html') or '<body' in notes_content.lower() or '<div' in notes_content.lower() or '<p' in notes_content.lower():
            is_html = True
        
        # إنشاء تبويبات للتبديل بين HTML والنص العادي
        if is_html:
            tabs = QTabWidget()
            
            # تبويب HTML (العرض المنسق)
            html_widget = QWidget()
            html_layout = QVBoxLayout(html_widget)
            html_text = QTextEdit()
            html_text.setReadOnly(True)
            html_text.setHtml(notes_content)
            html_text.setMinimumHeight(300)
            html_layout.addWidget(html_text)
            tabs.addTab(html_widget, "📄 عرض HTML (منسق)")
            
            # تبويب النص العادي (للمقارنة)
            plain_widget = QWidget()
            plain_layout = QVBoxLayout(plain_widget)
            plain_text = QTextEdit()
            plain_text.setReadOnly(True)
            # استخراج النص من HTML
            try:
                import re
                # إزالة tags HTML بسيطة
                plain_content = re.sub(r'<[^>]+>', '', notes_content)
                # تنظيف المسافات الزائدة
                plain_content = re.sub(r'\s+', ' ', plain_content).strip()
                plain_text.setPlainText(plain_content)
            except:
                plain_text.setPlainText(notes_content)
            plain_text.setMinimumHeight(300)
            plain_layout.addWidget(plain_text)
            tabs.addTab(plain_widget, "📝 نص عادي")
            
            # تطبيق الثيم
            try:
                from core.theme import get_theme_manager
                theme_manager = get_theme_manager()
                is_dark = theme_manager.get_theme() == "dark"
                if is_dark:
                    html_text.setStyleSheet("""
                        QTextEdit {
                            background-color: #1E1E1E;
                            color: #FFFFFF;
                            border: 1px solid #3E3E3E;
                            border-radius: 4px;
                            padding: 8px;
                        }
                    """)
                    plain_text.setStyleSheet("""
                        QTextEdit {
                            background-color: #1E1E1E;
                            color: #FFFFFF;
                            border: 1px solid #3E3E3E;
                            border-radius: 4px;
                            padding: 8px;
                        }
                    """)
                else:
                    html_text.setStyleSheet("""
                        QTextEdit {
                            background-color: #FFFFFF;
                            color: #000000;
                            border: 1px solid #E0E0E0;
                            border-radius: 4px;
                            padding: 8px;
                        }
                    """)
                    plain_text.setStyleSheet("""
                        QTextEdit {
                            background-color: #FFFFFF;
                            color: #000000;
                            border: 1px solid #E0E0E0;
                            border-radius: 4px;
                            padding: 8px;
                        }
                    """)
            except:
                pass
            
            content_layout.addWidget(tabs)
        else:
            # إذا لم يكن HTML، عرض نص عادي فقط
            content_text = QTextEdit()
            content_text.setReadOnly(True)
            content_text.setPlainText(notes_content)
            content_text.setMinimumHeight(300)
            
            # تطبيق الثيم
            try:
                from core.theme import get_theme_manager
                theme_manager = get_theme_manager()
                is_dark = theme_manager.get_theme() == "dark"
                if is_dark:
                    content_text.setStyleSheet("""
                        QTextEdit {
                            background-color: #1E1E1E;
                            color: #FFFFFF;
                            border: 1px solid #3E3E3E;
                            border-radius: 4px;
                            padding: 8px;
                        }
                    """)
                else:
                    content_text.setStyleSheet("""
                        QTextEdit {
                            background-color: #FFFFFF;
                            color: #000000;
                            border: 1px solid #E0E0E0;
                            border-radius: 4px;
                            padding: 8px;
                        }
                    """)
            except:
                pass
            
            content_layout.addWidget(content_text)
        
        content_group.setLayout(content_layout)
        layout.addWidget(content_group)
        
        # زر الإغلاق
        close_btn = QPushButton("إغلاق")
        close_btn.clicked.connect(self.accept)
        close_btn.setMinimumHeight(40)
        layout.addWidget(close_btn)


class SyncWorkerThread(QThread):
    """Thread للمزامنة في الخلفية"""
    progress = pyqtSignal(str)
    finished = pyqtSignal(bool, str)
    
    def __init__(self, graph_token, client_emails, account_id):
        super().__init__()
        self.graph_token = graph_token
        self.client_emails = client_emails
        self.account_id = account_id
    
    def run(self):
        try:
            from core.message_filter import should_import_message, detect_request_type
            from core.ai_reply_scoring import detect_positive_reply
            from core.db import (
                find_client_by_email, add_client, add_message, save_request,
                find_custom_sync_client_by_email
            )
            from datetime import datetime as dt
            
            total = len(self.client_emails)
            processed = 0
            total_messages = 0
            saved_messages = 0
            created_clients = 0
            linked_messages = 0
            
            for email in self.client_emails:
                self.progress.emit(f"⏳ جاري مزامنة {email}... ({processed + 1}/{total})")
                
                # قراءة الرسائل للعميل المحدد مع timeout
                try:
                    messages = read_messages_from_folder(
                        self.graph_token,
                        folder_name="Inbox",
                        sender_email=email,
                        top=50,
                        max_messages=50  # حد أقصى 50 رسالة لكل عميل
                    )
                    
                    if messages:
                        total_messages += len(messages)
                        log_info(f"Found {len(messages)} messages for {email}", "Sync")
                        
                        # حفظ الرسائل في قاعدة البيانات
                        for msg in messages:
                            try:
                                # استخراج معلومات المرسل
                                sender_info = msg.get("from", {}).get("emailAddress", {})
                                sender_email_addr = sender_info.get("address", "").lower()
                                sender_name = sender_info.get("name", "")
                                
                                # التحقق من أن المرسل أو المستلم هو العميل المطلوب
                                to_recipients = msg.get("toRecipients", [])
                                to_addresses = [r.get("emailAddress", {}).get("address", "").lower() for r in to_recipients]
                                
                                # تحديد البريد المستهدف (العميل)
                                target_email = email.lower().strip()
                                
                                # إذا كانت الرسالة من العميل أو إلى العميل
                                if sender_email_addr == target_email or target_email in to_addresses:
                                    # استخدام بريد المرسل الفعلي للبحث عن العميل
                                    search_email = sender_email_addr if sender_email_addr == target_email else target_email
                                    
                                    # البحث عن العميل في الجدول الرئيسي
                                    client = find_client_by_email(search_email)
                                    
                                    # إذا لم يوجد، إنشاء عميل جديد
                                    if not client:
                                        # محاولة الحصول على بيانات من custom_sync_clients
                                        custom_client = find_custom_sync_client_by_email(search_email)
                                        
                                        if custom_client:
                                            # استخدام بيانات من custom_sync_clients
                                            (_, company, country, contact, email_addr, phone, website, _) = custom_client
                                            add_client({
                                                "company_name": company or sender_name or search_email.split("@")[0],
                                                "country": country or None,
                                                "contact_person": contact or sender_name,
                                                "email": email_addr or search_email,
                                                "phone": phone or None,
                                                "website": website or None,
                                                "date_added": dt.now().strftime("%d/%m/%Y"),
                                                "status": "New",
                                                "seriousness_score": 0,
                                                "classification": None,
                                                "is_focus": 0
                                            })
                                            client = find_client_by_email(search_email)
                                            created_clients += 1
                                        else:
                                            # إنشاء عميل جديد بدون بيانات
                                            add_client({
                                                "company_name": sender_name or search_email.split("@")[0],
                                                "country": None,
                                                "contact_person": sender_name,
                                                "email": search_email,
                                                "phone": None,
                                                "website": None,
                                                "date_added": dt.now().strftime("%d/%m/%Y"),
                                                "status": "New",
                                                "seriousness_score": 0,
                                                "classification": None,
                                                "is_focus": 0
                                            })
                                            client = find_client_by_email(search_email)
                                            created_clients += 1
                                    
                                    if client:
                                        subject = msg.get("subject", "")
                                        body = msg.get("body", {}).get("content", "")
                                        
                                        # فلترة الرسائل
                                        should_import, _reason = should_import_message(subject, body, search_email)
                                        if not should_import:
                                            continue
                                        
                                        # استخراج التاريخ الفعلي
                                        actual_date = None
                                        received_date = msg.get("receivedDateTime") or msg.get("sentDateTime")
                                        if received_date:
                                            try:
                                                date_obj = dt.fromisoformat(received_date.replace('Z', '+00:00'))
                                                actual_date = date_obj.strftime("%d/%m/%Y")
                                            except Exception:
                                                pass
                                        
                                        # اكتشاف نوع الطلب
                                        request_type, score = detect_request_type(subject, body)
                                        if request_type != "General Inquiry":
                                            save_request(
                                                client_email=search_email,
                                                request_type=request_type,
                                                extracted_text=body
                                            )
                                        
                                        # حساب التأثير على النقاط
                                        score_effect = 0
                                        if len(body) > 50:
                                            try:
                                                score_effect = detect_positive_reply(body)
                                            except Exception:
                                                pass
                                        score_effect += score
                                        
                                        # حفظ الرسالة
                                        add_message({
                                            "client_id": client[0],
                                            "message_date": dt.now().strftime("%d/%m/%Y"),
                                            "actual_date": actual_date,
                                            "message_type": "Email",
                                            "channel": "Outlook",
                                            "client_response": subject,
                                            "notes": body,
                                            "score_effect": score_effect
                                        })
                                        
                                        saved_messages += 1
                                        linked_messages += 1
                                        
                            except Exception as e:
                                log_error(f"Error processing message for {email}: {str(e)}", "Sync")
                                continue
                    
                except Exception as e:
                    error_msg = str(e)
                    log_error(f"Error syncing {email}: {error_msg}", "Sync")
                    # لا نتوقف عند خطأ في عميل واحد، نكمل مع الباقي
                
                processed += 1
            
            result_msg = (
                f"تم مزامنة {total} عميل بنجاح!\n"
                f"تم العثور على {total_messages} رسالة.\n"
                f"تم حفظ {saved_messages} رسالة في قاعدة البيانات.\n"
                f"تم إنشاء {created_clients} عميل جديد.\n"
                f"تم ربط {linked_messages} رسالة بالعملاء."
            )
            
            self.finished.emit(True, result_msg)
            
        except Exception as e:
            error_msg = str(e)
            log_error(f"Sync thread error: {error_msg}", "Sync")
            self.finished.emit(False, f"خطأ في المزامنة: {error_msg}")


class SyncWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        self.graph_token = None
        self.current_account_id = None
        
        # حفظ بيانات الرسائل للوصول إليها عند النقر المزدوج
        self.current_messages_data = []  # قائمة بجميع بيانات الرسائل الحالية
        
        self.setWindowTitle("🔄 مزامنة مخصصة - Custom Sync")
        self.setMinimumSize(1200, 800)
        self.resize(1400, 900)  # حجم افتراضي أكبر
        
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # العنوان مع زر إضافة عميل
        title_layout = QHBoxLayout()
        title = QLabel("🔄 مزامنة مخصصة - Custom Sync")
        title.setFont(QFont("Segoe UI", 14, QFont.Bold))
        title.setStyleSheet("padding: 5px;")
        title_layout.addWidget(title)
        title_layout.addStretch()
        
        # زر إضافة عميل جديد
        add_client_btn = QPushButton("➕ إضافة عميل جديد")
        add_client_btn.clicked.connect(self.open_add_client_dialog)
        add_client_btn.setMinimumHeight(35)
        add_client_btn.setMinimumWidth(150)
        title_layout.addWidget(add_client_btn)
        
        main_layout.addLayout(title_layout)
        
        # === استخدام QSplitter لتقسيم النافذة بشكل مرن ===
        main_splitter = QSplitter(Qt.Vertical)
        main_splitter.setChildrenCollapsible(False)
        
        # === القسم العلوي: جدول العملاء ===
        table_group = QGroupBox("📋 قائمة عملاء المزامنة الخاصة")
        table_layout = QVBoxLayout()
        table_layout.setSpacing(5)
        table_layout.setContentsMargins(5, 5, 5, 5)
        
        # شريط البحث
        search_layout = QHBoxLayout()
        search_label = QLabel("🔍 بحث:")
        search_label.setMinimumWidth(60)
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("ابحث بالشركة، البلد، أو البريد الإلكتروني...")
        self.search_input.textChanged.connect(self.filter_table)
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_input)
        table_layout.addLayout(search_layout)
        
        # الجدول
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "الشركة", "البلد", "جهة الاتصال", "البريد الإلكتروني",
            "الهاتف", "الموقع", "محدد"
        ])
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.ExtendedSelection)
        self.table.setSortingEnabled(True)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setMinimumHeight(200)
        table_layout.addWidget(self.table)
        
        table_group.setLayout(table_layout)
        main_splitter.addWidget(table_group)
        main_splitter.setStretchFactor(0, 2)  # القسم العلوي يأخذ 2/3 من المساحة
        
        # === القسم السفلي: جدول الرسائل ===
        messages_group = QGroupBox("📧 رسائل العملاء المحددين")
        messages_layout = QVBoxLayout()
        messages_layout.setSpacing(5)
        messages_layout.setContentsMargins(5, 5, 5, 5)
        
        # زر عرض الرسائل
        view_messages_btn = QPushButton("👁️ عرض رسائل المحدد")
        view_messages_btn.clicked.connect(self.view_selected_messages)
        view_messages_btn.setMinimumHeight(35)
        messages_layout.addWidget(view_messages_btn)
        
        # جدول الرسائل
        self.messages_table = QTableWidget()
        self.messages_table.setColumnCount(6)
        self.messages_table.setHorizontalHeaderLabels([
            "التاريخ", "النوع", "القناة", "الموضوع", "المحتوى", "تأثير النقاط"
        ])
        self.messages_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.messages_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.messages_table.setSortingEnabled(True)
        self.messages_table.horizontalHeader().setStretchLastSection(True)
        self.messages_table.setMinimumHeight(200)
        messages_layout.addWidget(self.messages_table)
        
        messages_group.setLayout(messages_layout)
        main_splitter.addWidget(messages_group)
        main_splitter.setStretchFactor(1, 1)  # القسم السفلي يأخذ 1/3 من المساحة
        
        # إضافة الـ Splitter إلى التخطيط الرئيسي
        main_layout.addWidget(main_splitter, 1)  # stretch factor = 1
        
        # ربط النقر على جدول العملاء لعرض الرسائل
        self.table.itemSelectionChanged.connect(self.on_client_selection_changed)
        
        # ربط النقر المزدوج على جدول الرسائل لعرض المحتوى الكامل
        self.messages_table.itemDoubleClicked.connect(self.on_message_double_clicked)
        
        # === الأزرار ===
        btn_layout = QHBoxLayout()
        
        self.sync_selected_btn = QPushButton("🔄 مزامنة المحدد")
        self.sync_selected_btn.clicked.connect(self.sync_selected)
        self.sync_selected_btn.setMinimumHeight(40)
        btn_layout.addWidget(self.sync_selected_btn)
        
        self.delete_selected_btn = QPushButton("🗑️ حذف المحدد")
        self.delete_selected_btn.clicked.connect(self.delete_selected)
        self.delete_selected_btn.setMinimumHeight(40)
        btn_layout.addWidget(self.delete_selected_btn)
        
        refresh_btn = QPushButton("🔄 تحديث القائمة")
        refresh_btn.clicked.connect(self.load_clients)
        refresh_btn.setMinimumHeight(40)
        btn_layout.addWidget(refresh_btn)
        
        remove_duplicates_btn = QPushButton("🗑️ إزالة الرسائل المكررة")
        remove_duplicates_btn.clicked.connect(self.remove_duplicate_messages)
        remove_duplicates_btn.setMinimumHeight(40)
        remove_duplicates_btn.setToolTip("إزالة الرسائل المكررة للعملاء المحددين")
        btn_layout.addWidget(remove_duplicates_btn)
        
        btn_layout.addStretch()
        
        close_btn = QPushButton("إغلاق")
        close_btn.clicked.connect(self.accept)
        close_btn.setMinimumHeight(40)
        btn_layout.addWidget(close_btn)
        
        main_layout.addLayout(btn_layout)
        
        # تحميل البيانات
        self.load_clients()
        self.get_graph_token()
    
    def get_graph_token(self):
        """الحصول على token من النافذة الرئيسية"""
        if self.parent_window:
            if hasattr(self.parent_window, "graph_token"):
                self.graph_token = self.parent_window.graph_token
            if hasattr(self.parent_window, "current_account_id"):
                self.current_account_id = self.parent_window.current_account_id
    
    def open_add_client_dialog(self):
        """فتح نافذة إضافة عميل جديد"""
        dialog = AddClientDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            # تحديث الجدول بعد إضافة العميل
            self.load_clients()
    
    def load_clients(self):
        """تحميل قائمة العملاء"""
        try:
            clients = get_custom_sync_clients()
            
            # التحقق من الوضع الداكن
            from core.theme import get_theme_manager
            theme_manager = get_theme_manager()
            is_dark = theme_manager.get_theme() == "dark"
            
            self.table.setRowCount(len(clients))
            
            for row, client in enumerate(clients):
                (
                    client_id, company, country, contact, email,
                    phone, website, date_added
                ) = client
                
                values = [
                    company or "", country or "", contact or "",
                    email or "", phone or "", website or ""
                ]
                
                # إضافة عمود للاختيار
                checkbox_item = QTableWidgetItem()
                checkbox_item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
                checkbox_item.setCheckState(Qt.Unchecked)
                checkbox_item.setData(Qt.UserRole, client_id)
                values.append(checkbox_item)
                
                # تطبيق الألوان حسب الوضع الداكن
                if is_dark:
                    bg_color = QColor("#1E1E1E") if row % 2 == 0 else QColor("#252525")
                    fg_color = QColor("#FFFFFF")
                else:
                    bg_color = QColor("#FFFFFF") if row % 2 == 0 else QColor("#F5F5F5")
                    fg_color = QColor("#000000")
                
                for col, val in enumerate(values):
                    if col == 6:  # عمود الاختيار
                        self.table.setItem(row, col, val)
                    else:
                        item = QTableWidgetItem(str(val) if val else "")
                        item.setData(Qt.UserRole, client_id)
                        item.setBackground(QBrush(bg_color))
                        item.setForeground(QBrush(fg_color))
                        self.table.setItem(row, col, item)
            
            self.table.resizeColumnsToContents()
            
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"حدث خطأ أثناء تحميل العملاء:\n{str(e)}")
    
    def filter_table(self):
        """تصفية الجدول حسب البحث"""
        search_text = self.search_input.text().lower()
        
        for row in range(self.table.rowCount()):
            match = False
            for col in range(6):  # الأعمدة العادية (بدون عمود الاختيار)
                item = self.table.item(row, col)
                if item and search_text in item.text().lower():
                    match = True
                    break
            
            self.table.setRowHidden(row, not match)
    
    def get_selected_clients(self):
        """الحصول على قائمة العملاء المحددين"""
        selected_emails = []
        selected_ids = []
        
        for row in range(self.table.rowCount()):
            checkbox_item = self.table.item(row, 6)  # عمود الاختيار
            if checkbox_item and checkbox_item.checkState() == Qt.Checked:
                client_id = checkbox_item.data(Qt.UserRole)
                email_item = self.table.item(row, 3)  # عمود البريد الإلكتروني
                if email_item:
                    email = email_item.text().strip()
                    if email:
                        selected_emails.append(email)
                        selected_ids.append(client_id)
        
        return selected_emails, selected_ids
    
    def sync_selected(self):
        """مزامنة العملاء المحددين"""
        selected_emails, selected_ids = self.get_selected_clients()
        
        if not selected_emails:
            QMessageBox.warning(
                self,
                "لا يوجد محدد",
                "يرجى تحديد عميل واحد على الأقل للمزامنة."
            )
            return
        
        if not self.graph_token:
            QMessageBox.warning(
                self,
                "غير متصل",
                "يرجى الاتصال بحساب Outlook أولاً من الصفحة الرئيسية."
            )
            return
        
        # تأكيد
        reply = QMessageBox.question(
            self,
            "تأكيد المزامنة",
            f"هل تريد مزامنة {len(selected_emails)} عميل؟\n\n{', '.join(selected_emails[:5])}{'...' if len(selected_emails) > 5 else ''}",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes
        )
        
        if reply != QMessageBox.Yes:
            return
        
        # تعطيل الزر أثناء المزامنة
        self.sync_selected_btn.setEnabled(False)
        
        # إنشاء نافذة تقدم قابلة للإغلاق
        progress_dialog = QProgressDialog(self)
        progress_dialog.setWindowTitle("جاري المزامنة...")
        progress_dialog.setLabelText("⏳ جاري مزامنة الرسائل، الرجاء الانتظار...")
        progress_dialog.setRange(0, 0)  # indeterminate progress
        progress_dialog.setCancelButton(None)  # لا يمكن إلغاء العملية
        progress_dialog.setMinimumDuration(0)
        progress_dialog.show()
        QApplication.processEvents()
        
        # إنشاء Thread للمزامنة
        self.sync_thread = SyncWorkerThread(
            self.graph_token,
            selected_emails,
            self.current_account_id
        )
        
        # ربط الإشارات
        self.sync_thread.progress.connect(progress_dialog.setLabelText)
        self.sync_thread.finished.connect(
            lambda success, msg: self._on_sync_finished(success, msg, progress_dialog)
        )
        
        # بدء المزامنة في Thread
        self.sync_thread.start()
    
    def _on_sync_finished(self, success, message, progress_dialog):
        """معالج انتهاء المزامنة"""
        progress_dialog.close()
        self.sync_selected_btn.setEnabled(True)
        
        if success:
            QMessageBox.information(
                self,
                "اكتمل المزامنة",
                message
            )
            
            # تحديث جدول الرسائل تلقائياً إذا كان هناك عميل محدد
            selected_emails, _ = self.get_selected_clients()
            if selected_emails:
                if len(selected_emails) == 1:
                    # إذا كان عميل واحد، عرض رسائله مباشرة
                    self.load_messages_for_email(selected_emails[0])
                else:
                    # إذا كان أكثر من عميل، عرض جميع رسائلهم
                    self.load_messages_for_emails(selected_emails)
        else:
            QMessageBox.critical(
                self,
                "خطأ في المزامنة",
                message
            )
    
    def delete_selected(self):
        """حذف العملاء المحددين"""
        # دعم طريقتين للاختيار:
        # 1) تحديد الصفوف مباشرة من الجدول
        # 2) تحديد عمود "محدد" (checkbox)
        selected_rows = {item.row() for item in self.table.selectedItems()}

        selected_ids = []
        selected_names = []

        if selected_rows:
            # استخراج client_id من عمود الشركة (يحمل UserRole)
            for row in sorted(selected_rows):
                company_item = self.table.item(row, 0)
                if not company_item:
                    continue
                client_id = company_item.data(Qt.UserRole)
                if client_id:
                    selected_ids.append(client_id)
                    selected_names.append(company_item.text() or "")
        else:
            # fallback: الاعتماد على عمود "محدد"
            _, selected_ids = self.get_selected_clients()
            if selected_ids:
                # محاولة تجميع أسماء العملاء من الجدول
                for row in range(self.table.rowCount()):
                    checkbox_item = self.table.item(row, 6)
                    if checkbox_item and checkbox_item.checkState() == Qt.Checked:
                        company_item = self.table.item(row, 0)
                        if company_item:
                            selected_names.append(company_item.text() or "")

        if not selected_ids:
            QMessageBox.warning(
                self,
                "لا يوجد محدد",
                "يرجى تحديد عميل واحد على الأقل للحذف (حدد الصف أو فعّل مربع \"محدد\")."
            )
            return
        
        # تأكيد الحذف
        if selected_names:
            preview = ", ".join([n for n in selected_names if n][:5])
            if len(selected_names) > 5:
                preview += f" ... (+{len(selected_names) - 5})"
            confirm_msg = f"هل أنت متأكد من حذف {len(selected_ids)} عميل؟\n\n{preview}\n\nهذا الإجراء لا يمكن التراجع عنه!"
        else:
            confirm_msg = f"هل أنت متأكد من حذف {len(selected_ids)} عميل؟\n\nهذا الإجراء لا يمكن التراجع عنه!"

        reply = QMessageBox.question(
            self,
            "تأكيد الحذف",
            confirm_msg,
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return
        
        # حذف العملاء المحددين
        deleted_count = 0
        failed_count = 0
        
        for client_id in selected_ids:
            try:
                delete_custom_sync_client(client_id)
                deleted_count += 1
            except Exception as e:
                log_error(f"Error deleting client {client_id}: {str(e)}", "Delete")
                failed_count += 1
        
        # رسالة النتيجة
        if failed_count == 0:
            QMessageBox.information(
                self,
                "تم الحذف",
                f"تم حذف {deleted_count} عميل بنجاح!"
            )
        else:
            QMessageBox.warning(
                self,
                "حذف جزئي",
                f"تم حذف {deleted_count} عميل.\nفشل حذف {failed_count} عميل."
            )
        
        # تحديث الجدول
        self.load_clients()
        
        # لا نقوم بتحديث قائمة العملاء الرئيسية لأن المزامنة الخاصة مستقلة
    
    def remove_duplicate_messages(self):
        """إزالة الرسائل المكررة للعملاء المحددين"""
        selected_emails, _ = self.get_selected_clients()
        
        if not selected_emails:
            QMessageBox.warning(
                self,
                "لا يوجد محدد",
                "يرجى تحديد عميل واحد على الأقل لإزالة الرسائل المكررة."
            )
            return
        
        # تأكيد
        reply = QMessageBox.question(
            self,
            "تأكيد إزالة التكرارات",
            f"هل تريد إزالة الرسائل المكررة لـ {len(selected_emails)} عميل؟\n\n"
            f"سيتم الاحتفاظ بأحدث رسالة لكل مجموعة مكررة.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return
        
        try:
            total_deleted = 0
            
            for email in selected_emails:
                client = find_client_by_email(email)
                if client:
                    client_id = client[0]
                    deleted = remove_duplicate_messages(client_id)
                    total_deleted += deleted
            
            if total_deleted > 0:
                QMessageBox.information(
                    self,
                    "تم الإزالة",
                    f"تم إزالة {total_deleted} رسالة مكررة بنجاح!"
                )
                # تحديث جدول الرسائل إذا كان مفتوحاً
                if len(selected_emails) == 1:
                    self.load_messages_for_email(selected_emails[0])
            else:
                QMessageBox.information(
                    self,
                    "لا توجد تكرارات",
                    "لم يتم العثور على رسائل مكررة للعملاء المحددين."
                )
                
        except Exception as e:
            QMessageBox.critical(
                self,
                "خطأ",
                f"حدث خطأ أثناء إزالة التكرارات:\n{str(e)}"
            )
            log_error(f"Error removing duplicates: {str(e)}", "Remove Duplicates")
    
    def on_client_selection_changed(self):
        """عند تغيير اختيار العميل، عرض رسائله تلقائياً"""
        selected_rows = {item.row() for item in self.table.selectedItems()}
        if len(selected_rows) == 1:
            # إذا كان عميل واحد محدد، عرض رسائله تلقائياً
            row = list(selected_rows)[0]
            email_item = self.table.item(row, 3)  # عمود البريد الإلكتروني
            if email_item:
                email = email_item.text().strip()
                if email:
                    self.load_messages_for_email(email)
    
    def view_selected_messages(self):
        """عرض رسائل العملاء المحددين"""
        selected_emails, _ = self.get_selected_clients()
        
        if not selected_emails:
            QMessageBox.warning(
                self,
                "لا يوجد محدد",
                "يرجى تحديد عميل واحد على الأقل لعرض رسائله."
            )
            return
        
        # إذا كان عميل واحد فقط، عرض رسائله مباشرة
        if len(selected_emails) == 1:
            self.load_messages_for_email(selected_emails[0])
        else:
            # إذا كان أكثر من عميل، عرض جميع رسائلهم مجتمعة
            self.load_messages_for_emails(selected_emails)
    
    def load_messages_for_email(self, email: str):
        """تحميل وعرض رسائل عميل واحد"""
        try:
            # البحث عن العميل في الجدول الرئيسي
            client = find_client_by_email(email)
            if not client:
                self.messages_table.setRowCount(0)
                QMessageBox.information(
                    self,
                    "لا توجد رسائل",
                    f"لم يتم العثور على عميل بالبريد: {email}\n\nقد تحتاج إلى مزامنة هذا العميل أولاً."
                )
                return
            
            client_id = client[0]
            messages = get_client_messages(client_id)
            
            # حفظ بيانات الرسائل للوصول إليها عند النقر المزدوج
            self.current_messages_data = messages
            
            # إعادة تعيين عدد الأعمدة لعميل واحد
            self.messages_table.setColumnCount(6)
            self.messages_table.setHorizontalHeaderLabels([
                "التاريخ", "النوع", "القناة", "الموضوع", "المحتوى", "تأثير النقاط"
            ])
            
            # التحقق من الوضع الداكن
            from core.theme import get_theme_manager
            theme_manager = get_theme_manager()
            is_dark = theme_manager.get_theme() == "dark"
            
            # مسح الجدول أولاً
            self.messages_table.clearContents()
            self.messages_table.setRowCount(0)
            QApplication.processEvents()
            
            if not messages:
                QMessageBox.information(
                    self,
                    "لا توجد رسائل",
                    f"لا توجد رسائل للعميل: {email}\n\nقد تحتاج إلى مزامنة هذا العميل أولاً."
                )
                return
            
            # تعيين عدد الصفوف
            self.messages_table.setRowCount(len(messages))
            QApplication.processEvents()
            
            for row, msg in enumerate(messages):
                try:
                    (message_date, actual_date, message_type, channel, 
                     client_response, notes, score_effect) = msg
                    
                    # استخدام التاريخ الفعلي إن وجد
                    date_str = actual_date or message_date or ""
                    
                    values = [
                        date_str,
                        message_type or "",
                        channel or "",
                        client_response or "",
                        (notes or "")[:100] + ("..." if len(notes or "") > 100 else ""),  # تقصير المحتوى
                        str(score_effect) if score_effect else "0"
                    ]
                    
                    # تطبيق الألوان حسب الوضع الداكن
                    if is_dark:
                        bg_color = QColor("#1E1E1E") if row % 2 == 0 else QColor("#252525")
                        fg_color = QColor("#FFFFFF")
                    else:
                        bg_color = QColor("#FFFFFF") if row % 2 == 0 else QColor("#F5F5F5")
                        fg_color = QColor("#000000")
                    
                    for col, val in enumerate(values):
                        item = QTableWidgetItem(str(val) if val else "")
                        item.setBackground(QBrush(bg_color))
                        item.setForeground(QBrush(fg_color))
                        self.messages_table.setItem(row, col, item)
                except Exception as e:
                    log_error(f"Error displaying message row {row}: {str(e)}", "View Messages")
                    continue
            
            # تحديث الجدول
            self.messages_table.resizeColumnsToContents()
            self.messages_table.setVisible(True)  # التأكد من أن الجدول مرئي
            self.messages_table.show()  # عرض الجدول
            self.messages_table.update()
            self.messages_table.repaint()
            QApplication.processEvents()
            
            # التأكد من أن النافذة محدثة
            self.update()
            self.repaint()
            QApplication.processEvents()
            
            # رسالة تأكيد
            QMessageBox.information(
                self,
                "تم تحميل الرسائل",
                f"تم العثور على {len(messages)} رسالة للعميل: {email}\n\nتم عرضها في الجدول أدناه."
            )
        except Exception as e:
            QMessageBox.critical(
                self,
                "خطأ",
                f"حدث خطأ أثناء تحميل الرسائل:\n{str(e)}"
            )
            log_error(f"Error loading messages: {str(e)}", "View Messages")
    
    def on_message_double_clicked(self, item):
        """عند النقر المزدوج على رسالة، عرض محتواها الكامل"""
        row = item.row()
        
        if row < 0 or row >= len(self.current_messages_data):
            return
        
        # الحصول على بيانات الرسالة
        column_count = self.messages_table.columnCount()
        if column_count == 6:
            # عميل واحد - البيانات مباشرة
            msg_data = self.current_messages_data[row]
            email = None
            company = None
        else:
            # عدة عملاء - البيانات مع email و company
            email, company, msg_data = self.current_messages_data[row]
        
        # فتح نافذة عرض التفاصيل
        dialog = MessageDetailsDialog(msg_data, email, company, self)
        dialog.exec_()
    
    def load_messages_for_emails(self, emails: list):
        """تحميل وعرض رسائل عدة عملاء"""
        try:
            all_messages = []
            clients_found = []
            
            for email in emails:
                client = find_client_by_email(email)
                if client:
                    client_id = client[0]
                    messages = get_client_messages(client_id)
                    for msg in messages:
                        all_messages.append((email, client[1], msg))  # (email, company, message)
                    clients_found.append((email, client[1], len(messages)))
            
            if not all_messages:
                QMessageBox.information(
                    self,
                    "لا توجد رسائل",
                    "لم يتم العثور على رسائل للعملاء المحددين.\n\nقد تحتاج إلى مزامنة هؤلاء العملاء أولاً."
                )
                self.messages_table.clearContents()
                self.messages_table.setRowCount(0)
                self.current_messages_data = []
                return
            
            # حفظ بيانات الرسائل للوصول إليها عند النقر المزدوج
            # نحفظها كقائمة من tuples: (email, company, message_data)
            self.current_messages_data = all_messages
            
            # التحقق من الوضع الداكن
            from core.theme import get_theme_manager
            theme_manager = get_theme_manager()
            is_dark = theme_manager.get_theme() == "dark"
            
            # مسح الجدول أولاً
            self.messages_table.clearContents()
            self.messages_table.setRowCount(0)
            QApplication.processEvents()
            
            self.messages_table.setColumnCount(7)  # إضافة عمود للعميل
            self.messages_table.setHorizontalHeaderLabels([
                "العميل", "البريد", "التاريخ", "النوع", "القناة", "الموضوع", "تأثير النقاط"
            ])
            
            self.messages_table.setRowCount(len(all_messages))
            QApplication.processEvents()
            
            for row, (email, company, msg) in enumerate(all_messages):
                try:
                    (message_date, actual_date, message_type, channel, 
                     client_response, notes, score_effect) = msg
                    
                    date_str = actual_date or message_date or ""
                    
                    values = [
                        company or email,
                        email,
                        date_str,
                        message_type or "",
                        channel or "",
                        client_response or "",
                        str(score_effect) if score_effect else "0"
                    ]
                    
                    # تطبيق الألوان حسب الوضع الداكن
                    if is_dark:
                        bg_color = QColor("#1E1E1E") if row % 2 == 0 else QColor("#252525")
                        fg_color = QColor("#FFFFFF")
                    else:
                        bg_color = QColor("#FFFFFF") if row % 2 == 0 else QColor("#F5F5F5")
                        fg_color = QColor("#000000")
                    
                    for col, val in enumerate(values):
                        item = QTableWidgetItem(str(val) if val else "")
                        item.setBackground(QBrush(bg_color))
                        item.setForeground(QBrush(fg_color))
                        self.messages_table.setItem(row, col, item)
                except Exception as e:
                    log_error(f"Error displaying message row {row}: {str(e)}", "View Messages")
                    continue
            
            # تحديث الجدول
            self.messages_table.resizeColumnsToContents()
            self.messages_table.setVisible(True)  # التأكد من أن الجدول مرئي
            self.messages_table.show()  # عرض الجدول
            self.messages_table.update()
            self.messages_table.repaint()
            QApplication.processEvents()
            
            # التأكد من أن النافذة محدثة
            self.update()
            self.repaint()
            QApplication.processEvents()
            
            # رسالة تأكيد
            summary = "\n".join([f"- {email}: {count} رسالة" for email, _, count in clients_found])
            QMessageBox.information(
                self,
                "تم تحميل الرسائل",
                f"تم العثور على {len(all_messages)} رسالة إجمالاً:\n\n{summary}\n\nتم عرضها في الجدول أدناه."
            )
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "خطأ",
                f"حدث خطأ أثناء تحميل الرسائل:\n{str(e)}"
            )
            log_error(f"Error loading messages: {str(e)}", "View Messages")
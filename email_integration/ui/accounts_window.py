"""
نافذة إدارة حسابات Outlook
Outlook Accounts Management Window
"""
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QMessageBox, QLineEdit,
    QHeaderView, QGroupBox, QDialogButtonBox, QComboBox, QSpinBox, QCheckBox
)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt
from core.db import (
    get_all_outlook_accounts, add_outlook_account, update_outlook_account,
    delete_outlook_account, get_outlook_account_by_id
)
from core.ms_auth import acquire_token_for_account
import os


class AccountsWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("📧 إدارة حسابات Outlook - Outlook Accounts Management")
        self.setMinimumSize(900, 600)
        
        main_layout = QVBoxLayout(self)
        
        # العنوان
        title = QLabel("📧 إدارة حسابات Outlook - Outlook Accounts Management")
        title.setFont(QFont("Segoe UI", 14, QFont.Bold))
        main_layout.addWidget(title)
        
        # جدول الحسابات
        self.accounts_table = QTableWidget()
        self.accounts_table.setColumnCount(6)
        self.accounts_table.setHorizontalHeaderLabels([
            "ID", "اسم الحساب", "البريد الإلكتروني", "حالة", "تاريخ الإنشاء", "آخر مزامنة"
        ])
        self.accounts_table.horizontalHeader().setStretchLastSection(True)
        self.accounts_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.accounts_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.accounts_table.setAlternatingRowColors(True)
        main_layout.addWidget(self.accounts_table)
        
        # أزرار الإدارة
        buttons_layout = QHBoxLayout()
        
        self.add_btn = QPushButton("➕ إضافة حساب جديد")
        self.add_btn.clicked.connect(self.add_account)
        self.add_btn.setStyleSheet("background-color: #4ECDC4; color: white; font-weight: bold; padding: 8px; border-radius: 5px;")
        buttons_layout.addWidget(self.add_btn)
        
        self.edit_btn = QPushButton("✏️ تعديل")
        self.edit_btn.clicked.connect(self.edit_account)
        self.edit_btn.setStyleSheet("background-color: #3498db; color: white; font-weight: bold; padding: 8px; border-radius: 5px;")
        buttons_layout.addWidget(self.edit_btn)
        
        self.delete_btn = QPushButton("🗑️ حذف")
        self.delete_btn.clicked.connect(self.delete_account)
        self.delete_btn.setStyleSheet("background-color: #e74c3c; color: white; font-weight: bold; padding: 8px; border-radius: 5px;")
        buttons_layout.addWidget(self.delete_btn)
        
        self.connect_btn = QPushButton("🔗 ربط حساب")
        self.connect_btn.clicked.connect(self.connect_account)
        self.connect_btn.setStyleSheet("background-color: #2ecc71; color: white; font-weight: bold; padding: 8px; border-radius: 5px;")
        buttons_layout.addWidget(self.connect_btn)
        
        buttons_layout.addStretch()
        
        close_btn = QPushButton("إغلاق")
        close_btn.clicked.connect(self.accept)
        buttons_layout.addWidget(close_btn)
        
        main_layout.addLayout(buttons_layout)
        
        self.load_accounts()
    
    def load_accounts(self):
        """تحميل الحسابات في الجدول"""
        accounts = get_all_outlook_accounts()
        self.accounts_table.setRowCount(len(accounts))
        
        for row, account in enumerate(accounts):
            # الحسابات القديمة قد تحتوي على 7، 13، أو 17 عنصراً
            account_length = len(account)
            
            # الحقول الأساسية (7 حقول)
            account_id = account[0]
            account_name = account[1]
            email = account[2]
            token_cache_path = account[3] if account_length > 3 else None
            is_active = account[4] if account_length > 4 else 1
            created_at = account[5] if account_length > 5 else None
            last_sync = account[6] if account_length > 6 else None
            
            # الحقول الإضافية
            account_type = account[7] if account_length > 7 else "outlook"
            imap_server = account[8] if account_length > 8 else None
            imap_port = account[9] if account_length > 9 else None
            imap_username = account[10] if account_length > 10 else None
            imap_password = account[11] if account_length > 11 else None
            use_ssl = account[12] if account_length > 12 else None
            cpanel_host = account[13] if account_length > 13 else None
            cpanel_username = account[14] if account_length > 14 else None
            cpanel_api_token = account[15] if account_length > 15 else None
            use_cpanel_api = account[16] == 1 if account_length > 16 else False
            
            self.accounts_table.setItem(row, 0, QTableWidgetItem(str(account_id)))
            self.accounts_table.setItem(row, 1, QTableWidgetItem(account_name or ""))
            
            # تحديد نوع الحساب للعرض
            if use_cpanel_api:
                type_text = "cPanel API"
            elif account_type == "imap":
                type_text = "cPanel/IMAP"
            else:
                type_text = "Outlook"
            self.accounts_table.setItem(row, 2, QTableWidgetItem(type_text))
            
            self.accounts_table.setItem(row, 3, QTableWidgetItem(email or ""))
            
            status_text = "✅ نشط" if is_active else "❌ غير نشط"
            status_item = QTableWidgetItem(status_text)
            self.accounts_table.setItem(row, 4, status_item)
            
            self.accounts_table.setItem(row, 5, QTableWidgetItem(created_at or ""))
            self.accounts_table.setItem(row, 6, QTableWidgetItem(last_sync or "لم يتم"))
            
            # حفظ account_id في البيانات المخفية
            for col in range(7):
                item = self.accounts_table.item(row, col)
                if item:
                    item.setData(Qt.UserRole, account_id)
    
    def add_account(self):
        """إضافة حساب جديد"""
        dialog = AccountDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            try:
                data = dialog.get_data()
                if not data or not data.get('account_name'):
                    QMessageBox.warning(self, "تنبيه", "اسم الحساب مطلوب")
                    return
                
                account_name = data['account_name']
                account_type = data.get('account_type', 'outlook')
                use_cpanel_api = data.get('use_cpanel_api', 0)
                
                if account_type == 'outlook':
                    # حساب Outlook
                    token_cache_path = f"database/ms_token_cache_{account_name.replace(' ', '_')}.bin"
                    add_outlook_account(
                        account_name=account_name,
                        email=data.get('email'),
                        token_cache_path=token_cache_path,
                        account_type='outlook'
                    )
                elif use_cpanel_api:
                    # حساب cPanel API
                    add_outlook_account(
                        account_name=account_name,
                        email=data.get('email'),
                        account_type='imap',
                        cpanel_host=data.get('cpanel_host'),
                        cpanel_username=data.get('cpanel_username'),
                        cpanel_api_token=data.get('cpanel_api_token'),
                        use_cpanel_api=1,
                        imap_username=data.get('imap_username') or data.get('email')
                    )
                else:
                    # حساب IMAP (cPanel عادي)
                    add_outlook_account(
                        account_name=account_name,
                        email=data.get('email'),
                        account_type='imap',
                        imap_server=data.get('imap_server'),
                        imap_port=data.get('imap_port', 993),
                        imap_username=data.get('imap_username'),
                        imap_password=data.get('imap_password'),
                        use_ssl=data.get('use_ssl', 1)
                    )
                
                self.load_accounts()
                QMessageBox.information(self, "نجح", f"تم إضافة الحساب '{account_name}' بنجاح")
            except ValueError as e:
                QMessageBox.warning(self, "تنبيه", str(e))
            except Exception as e:
                QMessageBox.critical(self, "خطأ", f"حدث خطأ غير متوقع:\n{str(e)}")
    
    def edit_account(self):
        """تعديل حساب محدد"""
        row = self.accounts_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "تنبيه", "الرجاء تحديد حساب للتعديل")
            return
        
        account_id = self.accounts_table.item(row, 0).data(Qt.UserRole)
        account = get_outlook_account_by_id(account_id)
        
        if not account:
            QMessageBox.warning(self, "خطأ", "لم يتم العثور على الحساب")
            return
        
        dialog = AccountDialog(self, account)
        if dialog.exec_() == QDialog.Accepted:
            data = dialog.get_data()
            if data and data.get('account_name'):
                try:
                    update_params = {
                        'account_name': data['account_name'],
                        'email': data.get('email')
                    }
                    
                    use_cpanel_api = data.get('use_cpanel_api', 0)
                    
                    if data.get('account_type') == 'imap':
                        if use_cpanel_api:
                            # cPanel API
                            update_params.update({
                                'account_type': 'imap',
                                'cpanel_host': data.get('cpanel_host'),
                                'cpanel_username': data.get('cpanel_username'),
                                'cpanel_api_token': data.get('cpanel_api_token'),
                                'use_cpanel_api': 1
                            })
                        else:
                            # IMAP عادي
                            update_params.update({
                                'account_type': 'imap',
                                'imap_server': data.get('imap_server'),
                                'imap_port': data.get('imap_port'),
                                'imap_username': data.get('imap_username'),
                                'imap_password': data.get('imap_password'),
                                'use_ssl': data.get('use_ssl'),
                                'use_cpanel_api': 0
                            })
                    else:
                        update_params['account_type'] = 'outlook'
                        update_params['use_cpanel_api'] = 0
                    
                    update_outlook_account(account_id, **update_params)
                    self.load_accounts()
                    QMessageBox.information(self, "نجح", "تم تحديث الحساب بنجاح")
                except ValueError as e:
                    QMessageBox.warning(self, "تنبيه", str(e))
                except Exception as e:
                    QMessageBox.critical(self, "خطأ", f"حدث خطأ غير متوقع:\n{str(e)}")
    
    def delete_account(self):
        """حذف حساب محدد"""
        row = self.accounts_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "تنبيه", "الرجاء تحديد حساب للحذف")
            return
        
        account_id = self.accounts_table.item(row, 0).data(Qt.UserRole)
        account_name = self.accounts_table.item(row, 1).text()
        
        reply = QMessageBox.question(
            self,
            "تأكيد الحذف",
            f"هل أنت متأكد من حذف الحساب '{account_name}'؟",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                # حذف ملف token cache إذا كان موجوداً
                account = get_outlook_account_by_id(account_id)
                if account and account[3]:  # token_cache_path
                    token_path = account[3]
                    if os.path.exists(token_path):
                        try:
                            os.remove(token_path)
                        except:
                            pass
                
                delete_outlook_account(account_id)
                self.load_accounts()
                QMessageBox.information(self, "نجح", "تم حذف الحساب بنجاح")
            except Exception as e:
                QMessageBox.warning(self, "خطأ", f"حدث خطأ: {str(e)}")
    
    def connect_account(self):
        """ربط حساب (تسجيل دخول Microsoft - فقط لحسابات Outlook) أو اختبار الاتصال (cPanel API)"""
        row = self.accounts_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "تنبيه", "الرجاء تحديد حساب للربط/الاختبار")
            return
        
        account_id = self.accounts_table.item(row, 0).data(Qt.UserRole)
        account = get_outlook_account_by_id(account_id)
        
        if not account:
            QMessageBox.warning(self, "خطأ", "لم يتم العثور على الحساب")
            return
        
        account_length = len(account)
        account_type = account[7] if account_length >= 8 else "outlook"
        use_cpanel_api = account[16] == 1 if account_length >= 17 else False
        
        # إذا كان حساب cPanel API، قم باختبار الاتصال
        if use_cpanel_api:
            self.test_cpanel_connection(account)
            return
        
        # إذا كان حساب IMAP عادي
        if account_type != "outlook":
            QMessageBox.information(
                self,
                "معلومة",
                "حسابات cPanel/IMAP لا تحتاج إلى ربط.\n" +
                "يتم الاتصال بها مباشرة باستخدام معلومات الخادم.\n\n" +
                "يمكنك اختبار الاتصال من الصفحة الرئيسية عبر زر 'مزامنة'."
            )
            return
        
        # حساب Outlook - ربط عادي
        account_name = account[1]
        token_cache_path = account[3]
        
        try:
            # محاولة الحصول على token للحساب
            token = acquire_token_for_account(account_name, token_cache_path)
            if token:
                # تحديث البريد الإلكتروني إذا كان متاحاً
                from core.ms_auth import get_account_email
                email = get_account_email(token)
                if email:
                    update_outlook_account(account_id, email=email)
                
                QMessageBox.information(
                    self,
                    "نجح",
                    f"تم ربط الحساب '{account_name}' بنجاح!\nالبريد: {email or 'غير متاح'}"
                )
                self.load_accounts()
            else:
                QMessageBox.warning(self, "فشل", "فشل ربط الحساب. يرجى المحاولة مرة أخرى.")
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"حدث خطأ أثناء ربط الحساب:\n{str(e)}")
    
    def test_cpanel_connection(self, account):
        """اختبار الاتصال بـ cPanel API"""
        account_length = len(account)
        cpanel_host = account[13] if account_length >= 14 else None
        cpanel_username = account[14] if account_length >= 15 else None
        cpanel_api_token = account[15] if account_length >= 16 else None
        email_account = account[2] or (account[10] if account_length >= 11 else None)
        
        if not cpanel_host or not cpanel_username or not cpanel_api_token or not email_account:
            QMessageBox.warning(
                self,
                "تنبيه",
                "معلومات cPanel API غير مكتملة.\nالرجاء التحقق من إعدادات الحساب."
            )
            return
        
        try:
            from core.cpanel_api_reader import read_messages_from_cpanel_api
            
            # محاولة قراءة رسالة واحدة فقط للاختبار
            messages = read_messages_from_cpanel_api(
                cpanel_host=cpanel_host,
                cpanel_username=cpanel_username,
                api_token=cpanel_api_token,
                email_account=email_account,
                max_messages=1
            )
            
            QMessageBox.information(
                self,
                "نجح",
                f"تم الاتصال بنجاح! ✅\n\n" +
                f"الخادم: {cpanel_host}\n" +
                f"البريد: {email_account}\n" +
                f"عدد الرسائل المتاحة: {len(messages) if messages else 'غير محدد'}"
            )
        except Exception as e:
            QMessageBox.critical(
                self,
                "فشل الاتصال",
                f"فشل الاتصال بـ cPanel API:\n\n{str(e)}\n\n" +
                "الرجاء التحقق من:\n" +
                "- عنوان خادم cPanel\n" +
                "- اسم المستخدم و API Token\n" +
                "- أن API Token صالح وله صلاحيات الوصول للإيميلات"
            )


class AccountDialog(QDialog):
    def __init__(self, parent=None, account=None):
        super().__init__(parent)
        self.account = account
        self.setWindowTitle("حساب البريد الإلكتروني - Email Account")
        self.setMinimumWidth(500)
        
        layout = QVBoxLayout(self)
        
        # نوع الحساب
        layout.addWidget(QLabel("نوع الحساب *:"))
        self.type_combo = QComboBox()
        self.type_combo.addItems(["Outlook (Microsoft)", "cPanel / IMAP", "cPanel API (بدون كلمة مرور)"])
        
        # تحديد النوع الافتراضي قبل ربط الإشارة
        if account and len(account) >= 17:
            use_cpanel_api = account[16] == 1 if len(account) > 16 else False
            account_type = account[7] or "outlook"
            if use_cpanel_api:
                self.type_combo.setCurrentIndex(2)  # cPanel API
            elif account_type == "imap":
                self.type_combo.setCurrentIndex(1)  # cPanel IMAP
        else:
            account_type = "outlook"
        
        layout.addWidget(self.type_combo)
        
        # ربط الإشارة بعد إنشاء جميع العناصر
        self.type_combo.currentIndexChanged.connect(self.on_type_changed)
        
        # اسم الحساب
        layout.addWidget(QLabel("اسم الحساب *:"))
        self.name_input = QLineEdit()
        if account:
            self.name_input.setText(account[1] or "")
        self.name_input.setPlaceholderText("مثال: حساب المبيعات")
        layout.addWidget(self.name_input)
        
        # البريد الإلكتروني
        layout.addWidget(QLabel("البريد الإلكتروني (اختياري):"))
        self.email_input = QLineEdit()
        if account:
            self.email_input.setText(account[2] or "")
        self.email_input.setPlaceholderText("example@domain.com")
        layout.addWidget(self.email_input)
        
        # === حقول IMAP (تظهر فقط لـ cPanel IMAP) ===
        self.imap_group = QGroupBox("إعدادات IMAP")
        imap_layout = QVBoxLayout()
        
        # ملاحظة
        note_label = QLabel("💡 أدخل معلومات IMAP للاتصال المباشر")
        note_label.setStyleSheet("color: #666; font-size: 10px;")
        imap_layout.addWidget(note_label)
        
        # خادم IMAP
        imap_layout.addWidget(QLabel("خادم IMAP *:"))
        self.imap_server_input = QLineEdit()
        if account and len(account) >= 9:
            self.imap_server_input.setText(account[8] or "")
        self.imap_server_input.setPlaceholderText("mail.example.com")
        imap_layout.addWidget(self.imap_server_input)
        
        # منفذ IMAP
        port_layout = QHBoxLayout()
        port_layout.addWidget(QLabel("منفذ IMAP:"))
        self.imap_port_input = QSpinBox()
        self.imap_port_input.setMinimum(1)
        self.imap_port_input.setMaximum(65535)
        self.imap_port_input.setValue(993)
        if account and len(account) >= 10:
            self.imap_port_input.setValue(account[9] or 993)
        port_layout.addWidget(self.imap_port_input)
        port_layout.addStretch()
        imap_layout.addLayout(port_layout)
        
        # اسم المستخدم
        imap_layout.addWidget(QLabel("اسم المستخدم / البريد الإلكتروني *:"))
        self.imap_username_input = QLineEdit()
        if account and len(account) >= 11:
            self.imap_username_input.setText(account[10] or "")
        self.imap_username_input.setPlaceholderText("user@example.com")
        imap_layout.addWidget(self.imap_username_input)
        
        # كلمة المرور
        imap_layout.addWidget(QLabel("كلمة المرور *:"))
        self.imap_password_input = QLineEdit()
        self.imap_password_input.setEchoMode(QLineEdit.Password)
        if account and len(account) >= 12:
            self.imap_password_input.setText(account[11] or "")
        imap_layout.addWidget(self.imap_password_input)
        
        # استخدام SSL
        self.use_ssl_checkbox = QCheckBox("استخدام SSL (مُوصى به)")
        self.use_ssl_checkbox.setChecked(True)
        if account and len(account) >= 13:
            self.use_ssl_checkbox.setChecked(account[12] == 1)
        imap_layout.addWidget(self.use_ssl_checkbox)
        
        self.imap_group.setLayout(imap_layout)
        layout.addWidget(self.imap_group)
        
        # === حقول cPanel API (تظهر فقط لـ cPanel API) ===
        self.cpanel_api_group = QGroupBox("إعدادات cPanel API")
        cpanel_api_layout = QVBoxLayout()
        
        # ملاحظة رئيسية
        api_note_label = QLabel("💡 استخدم Application Password (App Password) من cPanel للوصول بدون كلمة مرور")
        api_note_label.setStyleSheet("color: #0078D4; font-size: 11px; font-weight: bold; padding: 5px;")
        api_note_label.setWordWrap(True)
        cpanel_api_layout.addWidget(api_note_label)
        
        # ملاحظة مهمة
        important_note = QLabel(
            "⚠️ مهم جداً:\n"
            "يجب استخدام Application Password (App Password) وليس API Token العادي!\n"
            "API Token العادي لا يعمل مع IMAP في معظم الاستضافات."
        )
        important_note.setStyleSheet("color: #FF6B6B; font-size: 10px; padding: 8px; background-color: #FFEBEE; border-radius: 4px; border: 1px solid #FFCDD2;")
        important_note.setWordWrap(True)
        cpanel_api_layout.addWidget(important_note)
        
        # عنوان خادم cPanel
        cpanel_api_layout.addWidget(QLabel("عنوان خادم cPanel *:"))
        self.cpanel_host_input = QLineEdit()
        if account and len(account) >= 13:
            self.cpanel_host_input.setText(account[13] or "")
        self.cpanel_host_input.setPlaceholderText("example.com أو 192.168.1.1")
        cpanel_api_layout.addWidget(self.cpanel_host_input)
        
        # اسم مستخدم cPanel
        cpanel_api_layout.addWidget(QLabel("اسم مستخدم cPanel *:"))
        self.cpanel_username_input = QLineEdit()
        if account and len(account) >= 14:
            self.cpanel_username_input.setText(account[14] or "")
        self.cpanel_username_input.setPlaceholderText("اسم المستخدم الرئيسي في cPanel")
        cpanel_api_layout.addWidget(self.cpanel_username_input)
        
        # Application Password / API Token
        token_label = QLabel("Application Password (App Password) *:")
        token_label.setToolTip("يجب استخدام Application Password من cPanel وليس API Token العادي")
        cpanel_api_layout.addWidget(token_label)
        self.cpanel_api_token_input = QLineEdit()
        self.cpanel_api_token_input.setEchoMode(QLineEdit.Password)
        if account and len(account) >= 15:
            self.cpanel_api_token_input.setText(account[15] or "")
        self.cpanel_api_token_input.setPlaceholderText("Application Password من cPanel → Email Accounts → Manage → App Passwords")
        cpanel_api_layout.addWidget(self.cpanel_api_token_input)
        
        # رابط مساعد - كيفية الحصول على Application Password
        help_label = QLabel(
            "📖 كيفية الحصول على Application Password (App Password):\n\n"
            "الطريقة الموصى بها:\n"
            "1. ادخل إلى cPanel\n"
            "2. اذهب إلى Email Accounts (حسابات البريد الإلكتروني)\n"
            "3. اختر البريد الإلكتروني المطلوب\n"
            "4. اضغط على 'Manage' أو 'إدارة'\n"
            "5. ابحث عن 'App Passwords' أو 'كلمات مرور التطبيقات'\n"
            "6. اضغط 'Create' أو 'إنشاء'\n"
            "7. أدخل اسم للتطبيق (مثل: Email Sync)\n"
            "8. انسخ كلمة المرور التي تم إنشاؤها\n"
            "9. استخدمها في حقل 'Application Password' أعلاه\n\n"
            "💡 ملاحظة:\n"
            "- Application Password مختلف عن API Token\n"
            "- Application Password يعمل مع IMAP مباشرة\n"
            "- إذا لم تجد App Passwords، قد لا تكون متاحة في إصدار cPanel الخاص بك\n"
            "- في هذه الحالة، استخدم نوع الحساب 'cPanel / IMAP' مع كلمة مرور البريد العادية"
        )
        help_label.setStyleSheet("color: #0078D4; font-size: 9px; padding: 10px; background-color: #E3F2FD; border-radius: 4px; border: 1px solid #90CAF9;")
        help_label.setWordWrap(True)
        cpanel_api_layout.addWidget(help_label)
        
        self.cpanel_api_group.setLayout(cpanel_api_layout)
        layout.addWidget(self.cpanel_api_group)
        
        # تحديث عرض الحقول بعد إنشاء جميع العناصر
        # استدعاء مباشر بدلاً من الإشارة لتجنب مشاكل التوقيت
        account_type_index = self.type_combo.currentIndex()
        is_imap = account_type_index == 1
        is_cpanel_api = account_type_index == 2
        
        self.imap_group.setVisible(is_imap)
        self.cpanel_api_group.setVisible(is_cpanel_api)
        
        # أزرار
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def on_type_changed(self):
        """تغيير عرض الحقول حسب نوع الحساب"""
        # التحقق من وجود العناصر قبل الوصول إليها
        if not hasattr(self, 'imap_group') or not hasattr(self, 'cpanel_api_group'):
            return
        
        account_type_index = self.type_combo.currentIndex()
        is_imap = account_type_index == 1
        is_cpanel_api = account_type_index == 2
        
        self.imap_group.setVisible(is_imap)
        self.cpanel_api_group.setVisible(is_cpanel_api)
    
    def get_data(self):
        """الحصول على البيانات والتحقق من صحتها"""
        account_type_index = self.type_combo.currentIndex()
        
        if account_type_index == 2:
            # cPanel API
            account_type = "imap"  # نفس النوع لكن مع use_cpanel_api = 1
            use_cpanel_api = 1
        elif account_type_index == 1:
            # cPanel IMAP
            account_type = "imap"
            use_cpanel_api = 0
        else:
            # Outlook
            account_type = "outlook"
            use_cpanel_api = 0
        
        account_name = self.name_input.text().strip()
        if not account_name:
            raise ValueError("اسم الحساب مطلوب")
        
        data = {
            'account_name': account_name,
            'email': self.email_input.text().strip() or None,
            'account_type': account_type,
            'use_cpanel_api': use_cpanel_api
        }
        
        if account_type == "imap":
            if use_cpanel_api:
                # cPanel API - التحقق من الحقول المطلوبة
                cpanel_host = self.cpanel_host_input.text().strip()
                cpanel_username = self.cpanel_username_input.text().strip()
                cpanel_api_token = self.cpanel_api_token_input.text().strip()
                email_account = self.email_input.text().strip() or None
                
                if not cpanel_host:
                    raise ValueError("عنوان خادم cPanel مطلوب")
                if not cpanel_username:
                    raise ValueError("اسم مستخدم cPanel مطلوب")
                if not cpanel_api_token:
                    raise ValueError("API Token مطلوب")
                if not email_account:
                    raise ValueError("البريد الإلكتروني المطلوب قراءته مطلوب")
                
                # تنظيف عنوان الخادم
                cpanel_host = cpanel_host.replace("https://", "").replace("http://", "").replace("cpanel:", "").replace("cPanel:", "").strip().strip('/')
                
                data.update({
                    'cpanel_host': cpanel_host,
                    'cpanel_username': cpanel_username,
                    'cpanel_api_token': cpanel_api_token,
                    'imap_username': email_account
                })
            else:
                # IMAP عادي - التحقق من الحقول المطلوبة
                imap_server = self.imap_server_input.text().strip()
                imap_username = self.imap_username_input.text().strip()
                imap_password = self.imap_password_input.text()
                
                if not imap_server:
                    raise ValueError("خادم IMAP مطلوب")
                if not imap_username:
                    raise ValueError("اسم المستخدم / البريد الإلكتروني مطلوب")
                if not imap_password:
                    raise ValueError("كلمة المرور مطلوبة")
                
                data.update({
                    'imap_server': imap_server,
                    'imap_port': self.imap_port_input.value(),
                    'imap_username': imap_username,
                    'imap_password': imap_password,
                    'use_ssl': 1 if self.use_ssl_checkbox.isChecked() else 0
                })
        
        return data
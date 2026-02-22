from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QTextEdit, QPushButton, QTabWidget, QWidget, 
    QLineEdit, QComboBox, QMessageBox, QGroupBox
)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt

from core.reply_templates import (
    get_template, get_all_templates, save_reply_as_template,
    get_saved_replies, increment_template_usage, detect_language
)
from core.db import get_client_by_id


class SuggestedReplyPopup(QDialog):
    def __init__(self, company, request_type=None, status=None, client_id=None, **kwargs):
        super().__init__()

        self.setWindowTitle(f"💡 Suggested Reply – {company}")
        self.setMinimumSize(850, 700)

        # =====================
        # Public outputs
        # =====================
        self.subject = ""
        self.body = ""
        self.client_id = client_id
        self.company = company
        self.request_type = request_type or status or "inquiry"
        self.current_language = "english"

        # الحصول على معلومات العميل
        self.client_info = self.get_client_info()

        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(10)

        # =====================
        # Title and Language Selector
        # =====================
        header_layout = QHBoxLayout()
        
        title = QLabel(f"💡 Suggested Replies for: {company}")
        title.setFont(QFont("Segoe UI", 12, QFont.Bold))
        header_layout.addWidget(title)
        header_layout.addStretch()
        
        # Language selector
        lang_label = QLabel("🌐 Language:")
        header_layout.addWidget(lang_label)
        
        self.language_combo = QComboBox()
        self.language_combo.addItems([
            "🇬🇧 English",
            "🇸🇦 Arabic",
            "🇪🇸 Spanish",
            "🇫🇷 French"
        ])
        self.language_combo.currentIndexChanged.connect(self.on_language_changed)
        header_layout.addWidget(self.language_combo)
        
        main_layout.addLayout(header_layout)

        # =====================
        # Subject editor
        # =====================
        subject_group = QGroupBox("📌 Email Subject")
        subject_layout = QVBoxLayout()
        
        self.subject_edit = QLineEdit()
        self.subject_edit.setPlaceholderText("Enter email subject...")
        subject_layout.addWidget(self.subject_edit)
        subject_group.setLayout(subject_layout)
        main_layout.addWidget(subject_group)

        # =====================
        # Template Tabs
        # =====================
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)

        # Generate replies with new template system
        self.generate_replies()

        # =====================
        # Final Editable Reply
        # =====================
        final_group = QGroupBox("✏️ Final Editable Reply")
        final_layout = QVBoxLayout()
        
        self.final_edit = QTextEdit()
        self.final_edit.setMinimumHeight(150)
        self.final_edit.setFont(QFont("Segoe UI", 10))
        final_layout.addWidget(self.final_edit)
        final_group.setLayout(final_layout)
        main_layout.addWidget(final_group)

        # =====================
        # Buttons
        # =====================
        btns = QHBoxLayout()

        save_template_btn = QPushButton("💾 Save as Template")
        save_template_btn.clicked.connect(self.save_as_template)
        save_template_btn.setStyleSheet("background-color: #5F9EA0; color: white; font-weight: bold; border-radius: 5px; padding: 8px;")
        btns.addWidget(save_template_btn)

        btns.addStretch()

        use_btn = QPushButton("✅ Use This Reply")
        use_btn.clicked.connect(self.use_reply)
        use_btn.setStyleSheet("background-color: #4ECDC4; color: white; font-weight: bold; border-radius: 5px; padding: 8px;")
        btns.addWidget(use_btn)

        cancel_btn = QPushButton("❌ Cancel")
        cancel_btn.clicked.connect(self.reject)
        cancel_btn.setStyleSheet("background-color: #95A5A6; color: white; border-radius: 5px; padding: 8px;")
        btns.addWidget(cancel_btn)

        main_layout.addLayout(btns)

        # =====================
        # Events
        # =====================
        self.tabs.currentChanged.connect(self.sync_tab_to_editor)
        
        # تحميل الرد الأولي
        self.sync_tab_to_editor()

    def get_client_info(self) -> dict:
        """الحصول على معلومات العميل من قاعدة البيانات"""
        info = {
            "company_name": self.company,
            "request_type": self.request_type,
            "status": self.request_type or "inquiry"
        }
        
        if self.client_id:
            try:
                from core.db import get_client_by_id
                client = get_client_by_id(self.client_id)
                if client:
                    info.update({
                        "company_name": client[1] or self.company,
                        "contact_person": client[3] or "",
                        "country": client[2] or "",
                        "email": client[4] or "",
                        "phone": client[5] or "",
                        "status": client[8] or self.request_type or "inquiry",
                        "classification": client[10] or "",
                    })
            except Exception:
                pass
        
        return info

    def on_language_changed(self):
        """عند تغيير اللغة"""
        index = self.language_combo.currentIndex()
        languages = ["english", "arabic", "spanish", "french"]
        self.current_language = languages[index] if index < len(languages) else "english"
        
        # إعادة توليد الردود
        self.generate_replies()
        self.sync_tab_to_editor()

    def generate_replies(self):
        """توليد الردود باستخدام نظام القوالب الجديد"""
        # مسح التبويبات الحالية
        self.tabs.clear()
        
        # تحديد نوع الطلب
        request_type = self.request_type.lower()
        if "price" in request_type or "quotation" in request_type:
            template_type = "price_request"
        elif "sample" in request_type:
            template_type = "samples_request"
        elif "follow" in request_type or "followup" in request_type:
            template_type = "followup_reply"
        else:
            template_type = "short_reply"
        
        # توليد الردود المختلفة
        templates_to_show = [
            ("short_reply", "✉️ Short Reply", "Quick reply"),
            ("full_reply", "📧 Professional Email", "Detailed response"),
            ("followup_reply", "🔁 Follow-Up", "Follow-up message"),
        ]
        
        # إضافة قالب خاص للطلب إذا كان مناسباً
        if template_type in ["price_request", "samples_request"]:
            templates_to_show.insert(1, (template_type, f"📋 {template_type.replace('_', ' ').title()}", f"{template_type} template"))
        
        # إنشاء التبويبات
        self.reply_data = {}
        for template_key, tab_title, subject_hint in templates_to_show:
            try:
                reply = get_template(
                    template_key, 
                    self.current_language, 
                    self.client_info
                )
                self.reply_data[template_key] = reply
                self.add_tab(tab_title, reply["body"], reply["subject"])
            except Exception as e:
                # في حالة الخطأ، استخدام قالب افتراضي
                default_reply = f"Dear {self.company},\n\nThank you for your {self.request_type or 'inquiry'}.\n\nBest regards,\nExport Sales Team"
                self.add_tab(tab_title, default_reply, subject_hint)
        
        # إضافة تبويب للقوالب المحفوظة
        saved_replies = get_saved_replies()
        if saved_replies:
            saved_tab = QWidget()
            saved_layout = QVBoxLayout(saved_tab)
            saved_layout.setContentsMargins(10, 10, 10, 10)
            
            saved_label = QLabel("📚 Saved Templates:")
            saved_label.setFont(QFont("Segoe UI", 10, QFont.Bold))
            saved_layout.addWidget(saved_label)
            
            saved_combo = QComboBox()
            saved_combo.addItem("-- Select a saved template --")
            for reply in saved_replies:
                usage_count = reply.get('usage_count', 0)
                saved_combo.addItem(f"{reply['name']} ({reply['language']}) - Used {usage_count} times")
            
            # حفظ مرجع saved_replies للاستخدام
            def load_template_by_index(idx):
                if idx > 0 and idx <= len(saved_replies):
                    self.load_saved_template(saved_replies[idx - 1])
            
            saved_combo.currentIndexChanged.connect(load_template_by_index)
            saved_layout.addWidget(saved_combo)
            saved_layout.addStretch()
            
            self.tabs.addTab(saved_tab, "📚 Saved Templates")

    # ==================================================
    # Tabs helpers
    # ==================================================
    def add_tab(self, title, text, subject):
        w = QWidget()
        l = QVBoxLayout(w)
        l.setContentsMargins(5, 5, 5, 5)

        preview = QTextEdit()
        preview.setReadOnly(True)
        preview.setPlainText(text)
        preview.setFont(QFont("Segoe UI", 10))
        l.addWidget(preview)

        w.preview = preview
        w.subject = subject
        w.body = text

        self.tabs.addTab(w, title)

    def sync_tab_to_editor(self):
        """مزامنة محتوى التبويب الحالي مع محرر النص النهائي"""
        tab = self.tabs.currentWidget()
        if not tab or not hasattr(tab, 'preview'):
            return

        try:
            body = tab.body if hasattr(tab, 'body') else tab.preview.toPlainText()
            subject = tab.subject if hasattr(tab, 'subject') else "Re: Your Inquiry"
            
            self.final_edit.setPlainText(body)
            self.subject_edit.setText(subject)
        except Exception:
            pass

    def load_saved_template(self, saved_reply):
        """تحميل قالب محفوظ"""
        if not saved_reply:
            return
        
        try:
            self.final_edit.setPlainText(saved_reply['body'])
            self.subject_edit.setText(saved_reply['subject'])
            self.current_language = saved_reply.get('language', 'english')
            
            # تحديث لغة القائمة
            languages = ["english", "arabic", "spanish", "french"]
            if self.current_language in languages:
                index = languages.index(self.current_language)
                self.language_combo.setCurrentIndex(index)
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to load template: {str(e)}")

    # ==================================================
    # Save and Use reply
    # ==================================================
    def save_as_template(self):
        """حفظ الرد الحالي كقالب"""
        subject = self.subject_edit.text().strip()
        body = self.final_edit.toPlainText().strip()
        
        if not body:
            QMessageBox.warning(self, "Warning", "Please enter a reply body first.")
            return
        
        from PyQt5.QtWidgets import QInputDialog
        name, ok = QInputDialog.getText(
            self,
            "Save Template",
            "Enter template name:",
            text=f"Custom Reply {self.current_language.title()}"
        )
        
        if ok and name:
            try:
                saved_reply = save_reply_as_template(
                    subject, 
                    body, 
                    template_name=name,
                    language=self.current_language
                )
                QMessageBox.information(
                    self, 
                    "Success", 
                    f"Template '{name}' saved successfully!"
                )
                
                # تحديث تبويب القوالب المحفوظة
                self.generate_replies()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save template: {str(e)}")

    def use_reply(self):
        """استخدام الرد الحالي"""
        self.body = self.final_edit.toPlainText().strip()
        self.subject = self.subject_edit.text().strip() or "Re: Your Inquiry"
        
        if not self.body:
            QMessageBox.warning(self, "Warning", "Please enter a reply body.")
            return
        
        # اكتشاف اللغة تلقائياً إذا لم يتم التحديد
        if not self.current_language or self.current_language == "english":
            detected_lang = detect_language(self.body)
            if detected_lang != "unknown":
                self.current_language = detected_lang
        
        # حفظ كقالب تلقائياً (اختياري - يمكن تعطيله)
        try:
            # يمكن إضافة خيار لتخزين تلقائي في الإعدادات
            pass
        except Exception:
            pass
        
        self.accept()

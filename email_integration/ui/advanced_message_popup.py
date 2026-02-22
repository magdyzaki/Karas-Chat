"""
نافذة إضافة رسالة من قناة متقدمة
Advanced Message Popup
"""
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QTextEdit, QLineEdit, QFormLayout, QMessageBox,
    QDateEdit, QSpinBox
)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt, QDate
from datetime import datetime

from core.communication import (
    CommunicationChannel, MessageStatus,
    add_unified_message,
    save_whatsapp_message,
    save_linkedin_message,
    save_telegram_message
)
from core.db import get_all_clients, get_client_by_id


class AdvancedMessagePopup(QDialog):
    def __init__(self, parent=None, client_id=None):
        super().__init__(parent)
        
        self.client_id = client_id
        self.setWindowTitle("💬 إضافة رسالة متقدمة - Advanced Message")
        self.setMinimumSize(600, 500)
        
        layout = QVBoxLayout(self)
        
        title = QLabel("💬 إضافة رسالة من قناة تواصل")
        title.setFont(QFont("Segoe UI", 12, QFont.Bold))
        layout.addWidget(title)
        
        form = QFormLayout()
        
        # Client
        self.client_combo = QComboBox()
        clients = get_all_clients()
        self.client_combo.addItem("-- Select Client --", None)
        for client in clients:
            client_id_val, company = client[0], client[1]
            self.client_combo.addItem(company or f"Client {client_id_val}", client_id_val)
        
        if self.client_id:
            index = self.client_combo.findData(self.client_id)
            if index >= 0:
                self.client_combo.setCurrentIndex(index)
        
        form.addRow("Client:", self.client_combo)
        
        # Channel
        self.channel_combo = QComboBox()
        self.channel_combo.addItems([
            CommunicationChannel.EMAIL.value,
            CommunicationChannel.OUTLOOK.value,
            CommunicationChannel.WHATSAPP.value,
            CommunicationChannel.LINKEDIN.value,
            CommunicationChannel.TELEGRAM.value,
            CommunicationChannel.PHONE.value,
            CommunicationChannel.SMS.value,
            CommunicationChannel.OTHER.value
        ])
        self.channel_combo.currentIndexChanged.connect(self.on_channel_changed)
        form.addRow("Channel:", self.channel_combo)
        
        # Message Type
        self.type_combo = QComboBox()
        self.type_combo.addItems(["Email", "Message", "Call", "Meeting", "Other"])
        form.addRow("Message Type:", self.type_combo)
        
        # Date
        self.date_edit = QDateEdit()
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)
        form.addRow("Date:", self.date_edit)
        
        # Subject (for Email/Outlook)
        self.subject_input = QLineEdit()
        self.subject_input.setPlaceholderText("Subject / Title")
        form.addRow("Subject:", self.subject_input)
        
        # External ID (for WhatsApp, LinkedIn, Telegram)
        self.external_id_input = QLineEdit()
        self.external_id_input.setPlaceholderText("Phone / Chat ID / Conversation ID")
        form.addRow("External ID:", self.external_id_input)
        
        # Status
        self.status_combo = QComboBox()
        self.status_combo.addItems([
            MessageStatus.SENT.value,
            MessageStatus.RECEIVED.value,
            MessageStatus.DRAFT.value,
            MessageStatus.PENDING.value,
            MessageStatus.FAILED.value
        ])
        self.status_combo.setCurrentText(MessageStatus.RECEIVED.value)
        form.addRow("Status:", self.status_combo)
        
        # Content
        self.content_text = QTextEdit()
        self.content_text.setPlaceholderText("Message content...")
        self.content_text.setMinimumHeight(150)
        form.addRow("Content:", self.content_text)
        
        # Score Effect
        self.score_spin = QSpinBox()
        self.score_spin.setRange(-100, 100)
        self.score_spin.setValue(0)
        form.addRow("Score Effect:", self.score_spin)
        
        layout.addLayout(form)
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        save_btn = QPushButton("💾 Save")
        save_btn.clicked.connect(self.save_message)
        btn_layout.addWidget(save_btn)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addStretch()
        btn_layout.addWidget(cancel_btn)
        
        layout.addLayout(btn_layout)
        
        self.on_channel_changed()
    
    def on_channel_changed(self):
        """عند تغيير القناة - تحديث الحقول"""
        channel = self.channel_combo.currentText()
        
        # تحديث External ID placeholder
        if channel == CommunicationChannel.WHATSAPP.value:
            self.external_id_input.setPlaceholderText("Phone Number (e.g., +201234567890)")
        elif channel == CommunicationChannel.LINKEDIN.value:
            self.external_id_input.setPlaceholderText("Conversation ID")
        elif channel == CommunicationChannel.TELEGRAM.value:
            self.external_id_input.setPlaceholderText("Chat ID")
        else:
            self.external_id_input.setPlaceholderText("External ID")
        
        # إظهار/إخفاء Subject حسب القناة
        if channel in [CommunicationChannel.EMAIL.value, CommunicationChannel.OUTLOOK.value]:
            self.subject_input.setVisible(True)
            # إخفاء label Subject من form معقد، لذا نتركه مرئياً
        else:
            # يمكن إخفاءه لكن FormLayout لا يدعم ذلك بسهولة
            pass
    
    def save_message(self):
        """حفظ الرسالة"""
        client_id = self.client_combo.currentData()
        if not client_id:
            QMessageBox.warning(self, "Error", "Please select a client!")
            return
        
        content = self.content_text.toPlainText().strip()
        if not content:
            QMessageBox.warning(self, "Error", "Please enter message content!")
            return
        
        channel = self.channel_combo.currentText()
        message_type = self.type_combo.currentText()
        subject = self.subject_input.text().strip()
        external_id = self.external_id_input.text().strip()
        status = self.status_combo.currentText()
        score_effect = self.score_spin.value()
        
        try:
            # استخدام الدوال الخاصة لكل قناة أو الدالة الموحدة
            if channel == CommunicationChannel.WHATSAPP.value:
                save_whatsapp_message(
                    client_id=client_id,
                    message_text=content,
                    phone_number=external_id if external_id else None,
                    status=status
                )
            elif channel == CommunicationChannel.LINKEDIN.value:
                save_linkedin_message(
                    client_id=client_id,
                    message_text=content,
                    conversation_id=external_id if external_id else None,
                    status=status
                )
            elif channel == CommunicationChannel.TELEGRAM.value:
                save_telegram_message(
                    client_id=client_id,
                    message_text=content,
                    chat_id=external_id if external_id else None,
                    status=status
                )
            else:
                # استخدام الدالة الموحدة للقنوات الأخرى
                add_unified_message(
                    client_id=client_id,
                    channel=channel,
                    message_type=message_type,
                    content=content,
                    subject=subject if subject else None,
                    external_message_id=external_id if external_id else None,
                    status=status,
                    score_effect=score_effect
                )
            
            QMessageBox.information(self, "Success", "Message added successfully!")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to add message:\n{str(e)}")

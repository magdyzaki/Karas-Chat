from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QTextEdit,
    QPushButton, QMessageBox
)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt

import requests
import webbrowser

from core.ms_auth import acquire_token_interactive


GRAPH_BASE = "https://graph.microsoft.com/v1.0"


class RequestDetailsDialog(QDialog):
    def __init__(self, client, client_email, request_type, date, status, text):
        super().__init__()

        self.client = client
        self.client_email = client_email
        self.request_type = request_type
        self.date = date
        self.status = status
        self.text = text

        self.setWindowTitle("📨 Request Details")
        self.setMinimumSize(720, 540)

        layout = QVBoxLayout(self)

        # ===== Title =====
        title = QLabel("📨 Request Details")
        title.setFont(QFont("Segoe UI", 12, QFont.Bold))
        layout.addWidget(title)

        # ===== Info =====
        info = QLabel(
            f"<b>Client:</b> {client or '—'}<br>"
            f"<b>Type:</b> {request_type.upper()}<br>"
            f"<b>Date:</b> {date}<br>"
            f"<b>Status:</b> {status}"
        )
        info.setTextFormat(Qt.RichText)
        layout.addWidget(info)

        # ===== Original Request =====
        layout.addWidget(QLabel("📄 Original Request:"))

        self.original_text = QTextEdit()
        self.original_text.setReadOnly(True)
        self.original_text.setPlainText(text or "")
        self.original_text.setMinimumHeight(140)
        layout.addWidget(self.original_text)

        # ===== Suggested Reply =====
        layout.addWidget(QLabel("✉ Suggested Reply:"))

        self.reply_text = QTextEdit()
        self.reply_text.setPlainText(self.default_reply())
        self.reply_text.setMinimumHeight(160)
        layout.addWidget(self.reply_text)

        # ===== Send Button =====
        self.send_btn = QPushButton("📤 Send via Outlook (Draft)")
        self.send_btn.setFixedHeight(36)
        self.send_btn.clicked.connect(self.create_outlook_draft)
        layout.addWidget(self.send_btn)

    # ===============================
    # Default Reply
    # ===============================
    def default_reply(self):
        if self.request_type.lower() == "price":
            return (
                "Dear Team,\n\n"
                "Thank you for your interest in our products.\n"
                "Kindly confirm the required specifications, packing details, "
                "quantity, and destination port so we can share our best quotation.\n\n"
                "Best regards,\n"
                "Elraee Export Team"
            )

        if self.request_type.lower() == "sample":
            return (
                "Dear Team,\n\n"
                "Thank you for your request.\n"
                "Please confirm the sample specifications, quantity required, "
                "and courier account details.\n\n"
                "Best regards,\n"
                "Elraee Export Team"
            )

        return (
            "Dear Team,\n\n"
            "Thank you for your message.\n"
            "Kindly provide further details so we can assist you accordingly.\n\n"
            "Best regards,\n"
            "Elraee Export Team"
        )

    # ===============================
    # Create Outlook Draft
    # ===============================
    def create_outlook_draft(self):
        try:
            if not self.client_email:
                QMessageBox.warning(
                    self,
                    "Missing Client Email",
                    "This request is not linked to a client email."
                )
                return

            access_token = acquire_token_interactive()

            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }

            payload = {
                "subject": f"Re: {self.request_type.capitalize()} Request",
                "body": {
                    "contentType": "Text",
                    "content": self.reply_text.toPlainText()
                },
                "toRecipients": [
                    {
                        "emailAddress": {
                            "address": self.client_email
                        }
                    }
                ]
            }

            resp = requests.post(
                f"{GRAPH_BASE}/me/messages",
                headers=headers,
                json=payload
            )

            if resp.status_code not in (200, 201):
                raise Exception(resp.text)

            message_id = resp.json().get("id")

            if message_id:
                outlook_url = f"https://outlook.office.com/mail/deeplink/compose/{message_id}"
                webbrowser.open(outlook_url)

            QMessageBox.information(
                self,
                "Success",
                "✔ Outlook draft opened successfully.\n"
                "You can complete & send it from Outlook."
            )

        except Exception as e:
            QMessageBox.critical(self, "Send Error", str(e))

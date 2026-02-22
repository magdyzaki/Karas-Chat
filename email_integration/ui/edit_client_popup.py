from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QLabel,
    QLineEdit, QPushButton, QHBoxLayout, QMessageBox
)
from PyQt5.QtGui import QFont

from core.db import get_client_by_id, update_client
from core.validation import (
    validate_email, validate_phone, validate_url, validate_text
)


class EditClientPopup(QDialog):
    def __init__(self, client_id, refresh_callback):
        super().__init__()

        self.client_id = client_id
        self.refresh_callback = refresh_callback

        self.setWindowTitle("✏️ Edit Client")
        self.setMinimumSize(420, 380)

        layout = QVBoxLayout(self)

        title = QLabel("✏️ Edit Client Information")
        title.setFont(QFont("Segoe UI", 11, QFont.Bold))
        layout.addWidget(title)

        client = get_client_by_id(client_id)
        if not client:
            QMessageBox.critical(self, "Error", "Client not found.")
            self.reject()
            return

        (
            _id, company, country, contact, email,
            phone, website, date_added,
            status, score, classification, is_focus
        ) = client

        # ===== Fields =====
        self.company_input = QLineEdit(company)
        self.country_input = QLineEdit(country or "")
        self.contact_input = QLineEdit(contact or "")
        self.email_input = QLineEdit(email or "")
        self.phone_input = QLineEdit(phone or "")
        self.website_input = QLineEdit(website or "")
        self.status_input = QLineEdit(status or "")
        self.class_input = QLineEdit(classification or "")

        for lbl, w in [
            ("Company", self.company_input),
            ("Country", self.country_input),
            ("Contact Person", self.contact_input),
            ("Email", self.email_input),
            ("Phone", self.phone_input),
            ("Website", self.website_input),
            ("Status", self.status_input),
            ("Classification", self.class_input),
        ]:
            layout.addWidget(QLabel(lbl))
            layout.addWidget(w)

        # ===== Buttons =====
        btns = QHBoxLayout()

        save_btn = QPushButton("💾 Save")
        save_btn.clicked.connect(self.save)
        btns.addWidget(save_btn)

        cancel_btn = QPushButton("❌ Cancel")
        cancel_btn.clicked.connect(self.reject)
        btns.addWidget(cancel_btn)

        layout.addLayout(btns)

    def save(self):
        company = self.company_input.text().strip()
        email = self.email_input.text().strip()
        phone = self.phone_input.text().strip()
        website = self.website_input.text().strip()

        # التحقق من صحة البيانات
        # 1. اسم الشركة (مطلوب)
        valid, error = validate_text(company, min_length=1, required=True)
        if not valid:
            QMessageBox.warning(self, "تحقق من البيانات", error or "اسم الشركة مطلوب.")
            self.company_input.setFocus()
            return

        # 2. البريد الإلكتروني
        if email:
            valid, error = validate_email(email)
            if not valid:
                QMessageBox.warning(self, "تحقق من البيانات", error or "البريد الإلكتروني غير صحيح.")
                self.email_input.setFocus()
                return

        # 3. رقم الهاتف
        if phone:
            valid, error = validate_phone(phone)
            if not valid:
                QMessageBox.warning(self, "تحقق من البيانات", error or "رقم الهاتف غير صحيح.")
                self.phone_input.setFocus()
                return

        # 4. رابط الموقع
        if website:
            valid, error = validate_url(website)
            if not valid:
                QMessageBox.warning(self, "تحقق من البيانات", error or "رابط الموقع غير صحيح.")
                self.website_input.setFocus()
                return

        update_client(self.client_id, {
            "company_name": company,
            "country": self.country_input.text().strip(),
            "contact_person": self.contact_input.text().strip(),
            "email": email,
            "phone": phone,
            "website": website if not website or website.startswith(('http://', 'https://')) else f"https://{website}",
            "status": self.status_input.text().strip(),
            "seriousness_score": 0,  # score محفوظ من الرسائل
            "classification": self.class_input.text().strip(),
            "is_focus": 0
        })

        self.refresh_callback()
        self.accept()

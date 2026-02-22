from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton,
    QComboBox, QMessageBox
)
from PyQt5.QtCore import Qt
from datetime import datetime

from core.db import (
    add_client,
    update_client,
    get_client_by_id
)
from core.validation import (
    validate_email, validate_phone, validate_url, validate_integer, validate_text
)


class AddClientPopup(QDialog):
    def __init__(self, refresh_callback, client_id=None):
        super().__init__()

        self.refresh_callback = refresh_callback
        self.client_id = client_id

        try:
            self.setWindowTitle("Add Client" if not client_id else "Edit Client")
            self.setMinimumWidth(420)

            layout = QVBoxLayout()

            # ===== Inputs =====
            self.company_input = QLineEdit()
            self.country_input = QLineEdit()
            self.contact_input = QLineEdit()
            self.email_input = QLineEdit()
            self.phone_input = QLineEdit()
            self.website_input = QLineEdit()

            self.status_combo = QComboBox()
            self.status_combo.addItems([
                "New",
                "No Reply",
                "Requested Price",
                "Samples Requested",
                "Replied"
            ])

            self.score_input = QLineEdit()
            self.score_input.setPlaceholderText("0")

            self.class_combo = QComboBox()
            self.class_combo.addItems([
                "🔥 Serious Buyer",
                "👍 Potential",
                "❌ Not Serious",
                "⭐ Focus"
            ])

            def add_row(label, widget):
                layout.addWidget(QLabel(label))
                layout.addWidget(widget)

            add_row("Company Name", self.company_input)
            add_row("Country", self.country_input)
            add_row("Contact Person", self.contact_input)
            add_row("Email", self.email_input)
            add_row("Phone", self.phone_input)
            add_row("Website", self.website_input)
            add_row("Status", self.status_combo)
            add_row("Seriousness Score", self.score_input)
            add_row("Classification", self.class_combo)

            # ===== Buttons =====
            btn_layout = QHBoxLayout()

            self.save_btn = QPushButton("💾 Save")
            self.save_btn.clicked.connect(self.save_client)

            self.cancel_btn = QPushButton("Cancel")
            self.cancel_btn.clicked.connect(self.close)

            btn_layout.addWidget(self.save_btn)
            btn_layout.addWidget(self.cancel_btn)

            layout.addLayout(btn_layout)
            self.setLayout(layout)

            # ===== Load data if Edit =====
            if self.client_id:
                self.load_client_data()

        except Exception as e:
            QMessageBox.critical(self, "Popup Init Error", str(e))

    # ==========================
    # Load client for edit
    # ==========================
    def load_client_data(self):
        try:
            client = get_client_by_id(self.client_id)
            if not client:
                QMessageBox.warning(self, "Error", "Client not found.")
                return

            (
                _id,
                company,
                country,
                contact,
                email,
                phone,
                website,
                date_added,
                status,
                score,
                classification,
                is_focus
            ) = client

            self.company_input.setText(company or "")
            self.country_input.setText(country or "")
            self.contact_input.setText(contact or "")
            self.email_input.setText(email or "")
            self.phone_input.setText(phone or "")
            self.website_input.setText(website or "")
            self.status_combo.setCurrentText(status or "New")
            self.score_input.setText(str(score or 0))
            self.class_combo.setCurrentText(classification or "❌ Not Serious")

        except Exception as e:
            QMessageBox.critical(self, "Load Client Error", str(e))

    # ==========================
    # Save (Add / Update)
    # ==========================
    def save_client(self):
        try:
            company = self.company_input.text().strip()
            email = self.email_input.text().strip()
            phone = self.phone_input.text().strip()
            website = self.website_input.text().strip()
            score_text = self.score_input.text().strip()

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

            # 5. النقاط (Score)
            if score_text:
                valid, error = validate_integer(score_text, min_value=0, max_value=1000)
                if not valid:
                    QMessageBox.warning(self, "تحقق من البيانات", error or "النقاط يجب أن تكون رقماً صحيحاً بين 0 و 1000.")
                    self.score_input.setFocus()
                    return
                score = int(score_text)
            else:
                score = 0

            data = {
                "company_name": company,
                "country": self.country_input.text().strip(),
                "contact_person": self.contact_input.text().strip(),
                "email": email,
                "phone": phone,
                "website": website if not website or website.startswith(('http://', 'https://')) else f"https://{website}",
                "date_added": datetime.now().strftime("%d/%m/%Y"),
                "status": self.status_combo.currentText(),
                "seriousness_score": score,
                "classification": self.class_combo.currentText()
            }

            if self.client_id:
                update_client(self.client_id, data)
            else:
                add_client(data)

            if callable(self.refresh_callback):
                self.refresh_callback()

            self.close()

        except Exception as e:
            QMessageBox.critical(self, "Save Error", str(e))

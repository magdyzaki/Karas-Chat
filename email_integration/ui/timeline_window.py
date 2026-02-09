from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit,
    QScrollArea, QWidget, QPushButton, QMessageBox
)
from PyQt5.QtGui import QFont, QColor
from PyQt5.QtCore import Qt

from core.db import get_client_messages, save_request  # ← (1) إضافة فقط

import re
from html import unescape


# ===============================
# === EFM ADDITION – Detection ===
# ===============================
PRICE_PATTERNS = [
    r"\bprice\b", r"\bquotation\b", r"\bquote\b",
    r"\bcost\b", r"\bUSD\b", r"\bFOB\b", r"\bCIF\b"
]

SAMPLE_PATTERNS = [
    r"\bsample\b", r"\bsampling\b", r"\btest\b"
]

MOQ_PATTERNS = [
    r"\bMOQ\b", r"\bminimum order\b", r"\bmin\.?\s*order\b"
]


def detect_request_type(text: str):
    text = text.lower()

    for p in PRICE_PATTERNS:
        if re.search(p, text):
            return "price"

    for p in SAMPLE_PATTERNS:
        if re.search(p, text):
            return "sample"

    for p in MOQ_PATTERNS:
        if re.search(p, text):
            return "moq"

    return None


def detect_request_types(text: str):
    text = text.lower()
    found = []

    for p in PRICE_PATTERNS:
        if re.search(p, text):
            found.append("price")
            break

    for p in SAMPLE_PATTERNS:
        if re.search(p, text):
            found.append("sample")
            break

    for p in MOQ_PATTERNS:
        if re.search(p, text):
            found.append("moq")
            break

    return found


def clean_html(raw_html: str) -> str:
    if not raw_html:
        return ""

    raw_html = re.sub(
        r"<(script|style|meta|head).*?>.*?</\1>",
        "",
        raw_html,
        flags=re.DOTALL | re.IGNORECASE
    )

    text = re.sub(r"<[^>]+>", "", raw_html)
    text = unescape(text)

    text = re.sub(r"\r\n|\r", "\n", text)
    text = re.sub(r"\n\s*\n\s*\n+", "\n\n", text)

    return text.strip()


class TimelineWindow(QDialog):
    def __init__(self, client_id, company_name):
        super().__init__()

        self.client_id = client_id  # ← (2) إضافة مهمة

        self.setWindowTitle(f"Timeline – {company_name}")
        self.setMinimumSize(750, 600)

        main_layout = QVBoxLayout(self)

        title = QLabel(f"📜 Timeline – {company_name}")
        title.setFont(QFont("Segoe UI", 12, QFont.Bold))
        main_layout.addWidget(title)

        # ===============================
        # === EFM ADDITION – SUMMARY BAR ===
        # ===============================
        self.summary_label = QLabel("📊 Requests Summary")
        self.summary_label.setFont(QFont("Segoe UI", 9, QFont.Bold))
        self.summary_label.setStyleSheet(
            "background:#F5F5F5; padding:6px; border-radius:4px;"
        )
        main_layout.addWidget(self.summary_label)

        # ===== Scroll Area =====
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)

        container = QWidget()
        layout = QVBoxLayout(container)

        price_count = 0
        sample_count = 0
        moq_count = 0

        messages = get_client_messages(client_id)

        if not messages:
            layout.addWidget(QLabel("No messages found for this client."))
        else:
            for msg in messages:
                # التعامل مع الرسائل القديمة (بدون actual_date) والجديدة (مع actual_date)
                if len(msg) >= 7:
                    (
                        message_date,
                        actual_date,
                        message_type,
                        channel,
                        client_response,
                        notes,
                        score_effect
                    ) = msg
                else:
                    # رسائل قديمة بدون actual_date
                    (
                        message_date,
                        message_type,
                        channel,
                        client_response,
                        notes,
                        score_effect
                    ) = msg
                    actual_date = None

                clean_text = clean_html(notes or "")
                types = detect_request_types(clean_text)

                if "price" in types:
                    price_count += 1
                if "sample" in types:
                    sample_count += 1
                if "moq" in types:
                    moq_count += 1

                request_type = detect_request_type(clean_text)

                # تحسين عرض التاريخ والتفاصيل
                # عرض التاريخ الفعلي إذا كان موجوداً، وإلا عرض تاريخ الإضافة
                if actual_date and actual_date != message_date:
                    date_display = f"📅 {actual_date} (تم الإضافة: {message_date})"
                else:
                    date_display = f"📅 {message_date}"
                type_display = f"✉️ {message_type}"
                channel_display = f"📡 {channel}"
                
                header_text = f"{date_display}   |   {type_display}   |   {channel_display}"
                header = QLabel(header_text)
                header.setFont(QFont("Segoe UI", 10, QFont.Bold))
                header.setWordWrap(True)

                # تحسين الألوان والتنسيق
                if request_type == "price":
                    header.setStyleSheet(
                        "background:#E8F5E9; padding:8px; border-radius:6px; "
                        "border-left:4px solid #4CAF50; color:#1B5E20;"
                    )
                elif request_type == "sample":
                    header.setStyleSheet(
                        "background:#FFFDE7; padding:8px; border-radius:6px; "
                        "border-left:4px solid #FBC02D; color:#F57F17;"
                    )
                elif request_type == "moq":
                    header.setStyleSheet(
                        "background:#E3F2FD; padding:8px; border-radius:6px; "
                        "border-left:4px solid #2196F3; color:#0D47A1;"
                    )
                else:
                    header.setStyleSheet(
                        "background:#F5F5F5; padding:8px; border-radius:6px; "
                        "border-left:4px solid #9E9E9E; color:#424242;"
                    )

                layout.addWidget(header)

                if client_response:
                    subject_label = QLabel(f"📝 Subject:")
                    subject_label.setFont(QFont("Segoe UI", 9, QFont.Bold))
                    subject_label.setStyleSheet("color:#555; padding:4px 0px 2px 4px;")
                    layout.addWidget(subject_label)
                    
                    subject = QLabel(client_response)
                    subject.setFont(QFont("Segoe UI", 9))
                    subject.setStyleSheet("color:#333; padding:2px 4px 6px 20px; background:#FAFAFA; border-radius:4px;")
                    subject.setWordWrap(True)
                    layout.addWidget(subject)

                body = QTextEdit()
                body.setReadOnly(True)
                body.setFont(QFont("Segoe UI", 10))
                body.setStyleSheet(
                    "background:#FFFFFF; padding:10px; border:1px solid #E0E0E0; "
                    "border-radius:4px; color:#212121; line-height:1.5;"
                )
                body.setPlainText(clean_text)
                body.setMinimumHeight(120)
                body.setMaximumHeight(300)
                layout.addWidget(body)

                # Footer with action buttons and score
                footer_layout = QHBoxLayout()
                
                if request_type:
                    btn = QPushButton("📌 Extract Request")
                    btn.setFixedWidth(160)
                    btn.setStyleSheet(
                        "padding:6px; font-weight:bold; background:#FF6B6B; "
                        "color:white; border-radius:4px; border:none;"
                    )
                    btn.clicked.connect(
                        lambda _, txt=clean_text:
                        self.on_extract_request(txt)
                    )
                    footer_layout.addWidget(btn)
                
                footer_layout.addStretch()
                
                if score_effect:
                    score_icon = "📈" if score_effect > 0 else "📉" if score_effect < 0 else "➖"
                    score_color = "#4CAF50" if score_effect > 0 else "#F44336" if score_effect < 0 else "#757575"
                    score_lbl = QLabel(f"{score_icon} Score Effect: {score_effect:+d}")
                    score_lbl.setFont(QFont("Segoe UI", 9, QFont.Bold))
                    score_lbl.setStyleSheet(f"color:{score_color}; padding:4px 8px; background:#F5F5F5; border-radius:4px;")
                    footer_layout.addWidget(score_lbl)
                
                layout.addLayout(footer_layout)
                layout.addSpacing(20)

        self.summary_label.setText(
            f"📊 Requests Summary   "
            f"PRICE: {price_count}   |   "
            f"SAMPLE: {sample_count}   |   "
            f"MOQ: {moq_count}"
        )

        layout.addStretch()
        scroll.setWidget(container)
        main_layout.addWidget(scroll)

    def on_extract_request(self, text):
        types = detect_request_types(text)

        if not types:
            QMessageBox.information(
                self,
                "Request Detected",
                "No commercial request detected in this message."
            )
            return

        # ===============================
        # === Stage C – Save Requests ===
        # ===============================
        for t in types:
            save_request(self.client_id, t, text)

        msg = "✔ Request detected & saved successfully\n\nTypes:\n"
        for t in ["price", "sample", "moq"]:
            if t in types:
                msg += f"✔ {t.upper()}\n"
            else:
                msg += f"✖ {t.upper()}\n"

        QMessageBox.information(self, "Request Saved", msg)

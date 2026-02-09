from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QLabel,
    QTextEdit, QPushButton, QHBoxLayout,
    QTabWidget
)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt


class SuggestedReplyPopup(QDialog):
    def __init__(self, company, status):
        super().__init__()

        self.setWindowTitle(f"Suggested Reply – {company}")
        self.setMinimumSize(700, 520)

        layout = QVBoxLayout()

        title = QLabel(f"💡 Suggested Replies for: {company}")
        title.setFont(QFont("Arial", 12, QFont.Bold))
        layout.addWidget(title)

        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        # ===== Generate replies =====
        short_reply = self.build_short_reply(company, status)
        full_reply = self.build_full_reply(company, status)
        followup_reply = self.build_followup_reply(company, status)

        self.add_tab("✉️ Short Reply", short_reply)
        self.add_tab("📧 Professional Email", full_reply)
        self.add_tab("🔁 Follow-Up", followup_reply)

        self.setLayout(layout)

    def add_tab(self, title, text):
        tab = QVBoxLayout()
        box = QTextEdit()
        box.setReadOnly(False)
        box.setFont(QFont("Calibri", 11))
        box.setText(text)

        copy_btn = QPushButton("📋 Copy")
        copy_btn.clicked.connect(lambda: self.copy_text(box))

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(copy_btn)

        tab.addWidget(box)
        tab.addLayout(btn_layout)

        container = QDialog()
        container.setLayout(tab)
        self.tabs.addTab(container, title)

    def copy_text(self, box):
        box.selectAll()
        box.copy()

    # ==========================
    # Reply Builders
    # ==========================
    def build_short_reply(self, company, status):
        if "Price" in status:
            return (
                f"Dear {company},\n\n"
                "Thank you for your interest.\n"
                "Please find our price details below.\n\n"
                "Best regards,"
            )

        if "Samples" in status:
            return (
                f"Dear {company},\n\n"
                "Thank you for your message.\n"
                "We will arrange the samples as requested.\n\n"
                "Best regards,"
            )

        return (
            f"Dear {company},\n\n"
            "Just following up on our previous message.\n"
            "Looking forward to your feedback.\n\n"
            "Best regards,"
        )

    def build_full_reply(self, company, status):
        if "Price" in status:
            return (
                f"Dear {company},\n\n"
                "Thank you for your inquiry and interest in our products.\n\n"
                "Please find below our quotation and specifications as requested. "
                "Should you require any clarification or adjustments, "
                "we will be pleased to assist.\n\n"
                "We look forward to your feedback and potential cooperation.\n\n"
                "Best regards,\n"
                "Export Sales Team"
            )

        if "Samples" in status:
            return (
                f"Dear {company},\n\n"
                "Thank you for your interest in our products.\n\n"
                "We are pleased to confirm that we can prepare and dispatch the samples "
                "as per your request. Kindly advise your delivery details.\n\n"
                "Best regards,\n"
                "Export Sales Team"
            )

        return (
            f"Dear {company},\n\n"
            "I hope this message finds you well.\n\n"
            "We would like to kindly follow up regarding our previous correspondence "
            "and check if you require any further information from our side.\n\n"
            "Looking forward to your reply.\n\n"
            "Best regards,\n"
            "Export Sales Team"
        )

    def build_followup_reply(self, company, status):
        return (
            f"Dear {company},\n\n"
            "Just a gentle follow-up to our previous message.\n\n"
            "Please let us know if you have any questions or if further details "
            "are required. We will be happy to support.\n\n"
            "Kind regards,\n"
            "Export Sales Team"
        )

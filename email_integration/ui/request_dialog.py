from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QLabel,
    QTextEdit, QPushButton, QComboBox
)
from PyQt5.QtGui import QFont


class RequestDialog(QDialog):
    def __init__(self, request_type, text, parent=None):
        super().__init__(parent)

        self.setWindowTitle("📌 Extract Request")
        self.setMinimumSize(500, 420)

        layout = QVBoxLayout(self)

        title = QLabel("Extracted Request")
        title.setFont(QFont("Segoe UI", 11, QFont.Bold))
        layout.addWidget(title)

        layout.addWidget(QLabel("Request Type"))
        self.type_box = QComboBox()
        self.type_box.addItems(["price", "sample", "moq"])
        self.type_box.setCurrentText(request_type)
        layout.addWidget(self.type_box)

        layout.addWidget(QLabel("Message Content"))
        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        self.text_edit.setPlainText(text)
        layout.addWidget(self.text_edit)

        layout.addWidget(QLabel("Your Notes"))
        self.notes_edit = QTextEdit()
        layout.addWidget(self.notes_edit)

        btn = QPushButton("💾 Save Request")
        btn.clicked.connect(self.accept)
        layout.addWidget(btn)

    def get_data(self):
        return {
            "type": self.type_box.currentText(),
            "notes": self.notes_edit.toPlainText()
        }

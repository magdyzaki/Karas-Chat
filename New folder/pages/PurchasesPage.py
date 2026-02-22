from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt

class PurchasesPage(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        title = QLabel("📄 Purchases")
        title.setFont(QFont("Amiri", 16, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        desc = QLabel("هذه الصفحة تحت التطوير — سيتم تفعيلها قريبًا ⚙️")
        desc.setAlignment(Qt.AlignCenter)
        desc.setStyleSheet("color:#666; font-size:14px; margin-top:10px;")
        layout.addWidget(desc)
        
        self.setLayout(layout)

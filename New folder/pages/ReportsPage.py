from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QTextEdit, QMessageBox
import sqlite3, os, json
from PyQt5.QtCore import Qt
DB = os.path.join(os.path.dirname(__file__), "..", "database", "crm.db")

class ReportsPage(QWidget):
    def __init__(self):
        super().__init__()
        self.conn = sqlite3.connect(DB); self.cursor = self.conn.cursor()
        layout = QVBoxLayout()
        title = QLabel("التقارير")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        self.output = QTextEdit(); self.output.setReadOnly(True)
        self.gen_btn = QPushButton("توليد مبسط")
        layout.addWidget(self.gen_btn); layout.addWidget(self.output)
        self.setLayout(layout)
        self.gen_btn.clicked.connect(self.generate_report)

    def generate_report(self):
        try:
            self.cursor.execute("SELECT COUNT(*), COALESCE(SUM(total_egp),0) FROM sales")
            cnt, total = self.cursor.fetchone()
            report = {"sales_count": cnt, "sales_total_egp": total}
            self.output.setText(json.dumps(report, ensure_ascii=False, indent=2))
        except Exception as e:
            QMessageBox.critical(self, "خطأ", str(e))

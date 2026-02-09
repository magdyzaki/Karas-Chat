from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QTextEdit
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt
from core.db import get_connection


class ClientReportWindow(QDialog):
    def __init__(self, client_id, company, parent=None):
        super().__init__(parent)

        self.setWindowTitle(f"📊 Client Report – {company}")
        self.setMinimumSize(700, 500)

        layout = QVBoxLayout(self)

        title = QLabel(f"📊 Full Report for: {company}")
        title.setFont(QFont("Segoe UI", 12, QFont.Bold))
        layout.addWidget(title)

        self.text = QTextEdit()
        self.text.setReadOnly(True)
        layout.addWidget(self.text)

        self.load_report(client_id)

    def load_report(self, client_id):
        conn = get_connection()
        cur = conn.cursor()

        report = []

        # ===== Requests =====
        cur.execute("""
            SELECT request_type, status, reply_status, created_at
            FROM requests
            WHERE client_id=?
            ORDER BY id ASC
        """, (client_id,))
        report.append("=== REQUESTS ===")
        for r in cur.fetchall():
            report.append(f"- {r[0]} | status={r[1]} | reply={r[2]} | {r[3]}")

        # ===== Messages =====
        cur.execute("""
            SELECT message_date, channel, client_response
            FROM messages
            WHERE client_id=?
            ORDER BY message_date ASC
        """, (client_id,))
        report.append("\n=== MESSAGES ===")
        for m in cur.fetchall():
            report.append(f"- {m[0]} [{m[1]}] {m[2]}")

        conn.close()
        self.text.setText("\n".join(report))

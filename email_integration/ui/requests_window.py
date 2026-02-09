from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QLabel,
    QTableWidget, QTableWidgetItem,
    QMessageBox, QPushButton,
    QHBoxLayout, QLineEdit
)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt

from core.db import (
    get_connection,
    sync_all_requests_from_clients,
    get_request_reply_email,
    update_request_reply_status
)

from core.ms_reply import open_reply_draft
from core.templates import build_reply_template
from ui.add_client_popup import AddClientPopup
from ui.suggested_reply_popup import SuggestedReplyPopup


class RequestsWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("📋 Requests List")
        self.setMinimumSize(950, 520)

        layout = QVBoxLayout(self)

        # ================= Title =================
        title = QLabel("📋 Extracted Requests")
        title.setFont(QFont("Segoe UI", 12, QFont.Bold))
        layout.addWidget(title)

        # ================= Search =================
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search by email / request / status...")
        self.search_input.textChanged.connect(self.load_requests)
        layout.addWidget(self.search_input)

        # ================= Table =================
        self.table = QTableWidget()
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.cellDoubleClicked.connect(self.safe_edit_client)
        layout.addWidget(self.table)

        # ================= Buttons =================
        btns = QHBoxLayout()

        self.create_client_btn = QPushButton("➕ Create Client")
        self.create_client_btn.clicked.connect(self.create_client_from_request)
        btns.addWidget(self.create_client_btn)

        self.reply_btn = QPushButton("📨 Reply")
        self.reply_btn.clicked.connect(self.reply_to_request)
        btns.addWidget(self.reply_btn)

        self.mark_replied_btn = QPushButton("✅ Mark as Replied")
        self.mark_replied_btn.clicked.connect(self.mark_request_replied)
        btns.addWidget(self.mark_replied_btn)

        refresh = QPushButton("🔄 Refresh / Sync")
        refresh.clicked.connect(self.load_requests)
        btns.addWidget(refresh)

        btns.addStretch()
        layout.addLayout(btns)

        self.load_requests()

    # ==================================================
    # Resolve Outlook token dynamically
    # ==================================================
    def get_graph_token(self):
        w = self.parent()
        while w:
            if hasattr(w, "graph_token") and w.graph_token:
                return w.graph_token
            w = w.parent()
        return None

    # ==================================================
    # Load Requests
    # ==================================================
    def load_requests(self):
        try:
            sync_all_requests_from_clients()

            conn = get_connection()
            cur = conn.cursor()

            search = self.search_input.text().strip()
            params = []

            query = """
                SELECT
                    id,
                    client_id,
                    client_email,
                    request_type,
                    reply_status,
                    status,
                    created_at
                FROM requests
            """

            if search:
                query += """
                    WHERE
                        client_email LIKE ?
                        OR request_type LIKE ?
                        OR status LIKE ?
                """
                params.extend([
                    f"%{search}%",
                    f"%{search}%",
                    f"%{search}%"
                ])

            query += " ORDER BY id DESC"
            cur.execute(query, params)
            rows = cur.fetchall()
            conn.close()

            headers = [
                "Request ID",
                "Client ID",
                "Client Email",
                "Request Type",
                "Reply Status",   # 👈 جديد
                "Request Status",
                "Created At"
            ]

            self.table.setColumnCount(len(headers))
            self.table.setHorizontalHeaderLabels(headers)
            self.table.setRowCount(0)

            for r, row in enumerate(rows):
                self.table.insertRow(r)
                for c, val in enumerate(row):
                    item = QTableWidgetItem("" if val is None else str(val))
                    item.setTextAlignment(Qt.AlignCenter)
                    self.table.setItem(r, c, item)

        except Exception as e:
            QMessageBox.critical(self, "Requests Error", str(e))

    # ==================================================
    # Helpers
    # ==================================================
    def get_selected_request(self):
        row = self.table.currentRow()
        if row < 0:
            return None
        request_id = int(self.table.item(row, 0).text())
        request_type = self.table.item(row, 3).text().strip()
        return request_id, request_type

    # ==================================================
    # Create Client
    # ==================================================
    def create_client_from_request(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Select", "Select a request first.")
            return

        client_email = self.table.item(row, 2).text().strip()
        if not client_email:
            QMessageBox.warning(
                self,
                "Missing Email",
                "This request has no email."
            )
            return

        def after_save():
            sync_all_requests_from_clients()
            self.load_requests()

        popup = AddClientPopup(after_save)
        popup.email_input.setText(client_email)
        popup.exec_()

    # ==================================================
    # Reply (Suggestions → Edit → Outlook)
    # ==================================================
    def reply_to_request(self):
        try:
            data = self.get_selected_request()
            if not data:
                QMessageBox.warning(self, "Select", "Select a request first.")
                return

            request_id, request_type = data
            email = get_request_reply_email(request_id)

            if not email:
                QMessageBox.warning(self, "No Email", "Email not available.")
                return

            graph_token = self.get_graph_token()
            if not graph_token:
                QMessageBox.warning(self, "Outlook", "Connect Outlook first.")
                return

            company = email.split("@")[0]
            subject, body = build_reply_template(company, request_type)

            popup = SuggestedReplyPopup(
                company=company,
                request_type=request_type,
                initial_subject=subject,
                initial_body=body
            )

            if popup.exec_() != QDialog.Accepted:
                return

            open_reply_draft(
                graph_token,
                email,
                popup.subject,
                popup.body
            )

        except Exception as e:
            QMessageBox.critical(self, "Reply Error", str(e))

    # ==================================================
    # Mark as Replied
    # ==================================================
    def mark_request_replied(self):
        row = self.table.currentRow()
        if row < 0:
            return

        request_id = int(self.table.item(row, 0).text())
        client_id = self.table.item(row, 1).text()

        # 1️⃣ Update request status
        update_request_reply_status(request_id, "replied")

        # 2️⃣ Update client status (IMPORTANT)
        if client_id and client_id.isdigit():
            from core.db import get_client_by_id, update_client

            client = get_client_by_id(int(client_id))
            if client:
                update_client(client[0], {
                    "company_name": client[1],
                    "country": client[2],
                    "contact_person": client[3],
                    "email": client[4],
                    "phone": client[5],
                    "website": client[6],
                    "status": "Replied",          # ✅ THIS IS THE FIX
                    "seriousness_score": client[9],
                    "classification": client[10],
                    "is_focus": client[11]
                })

        self.load_requests()

        # 🔄 FORCE refresh main window instantly
        parent = self.parent()
        while parent:
            if hasattr(parent, "load_clients"):
                parent.load_clients()
                break
            parent = parent.parent()


        QMessageBox.information(
            self,
            "Done",
            "Request marked as replied and client status updated."
        )


    # ==================================================
    # Safe Edit
    # ==================================================
    def safe_edit_client(self, row, column):
        QMessageBox.information(
            self,
            "Auto Sync Enabled",
            "Clients are synced automatically."
        )

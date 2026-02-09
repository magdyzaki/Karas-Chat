from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QTableWidget, QTableWidgetItem,
    QMessageBox, QLineEdit, QComboBox
)
from PyQt5.QtGui import QColor, QBrush
from PyQt5.QtCore import Qt
from datetime import datetime

from core.db import (
    init_db,
    ensure_focus_column,
    get_all_clients,
    get_client_by_id,
    get_clients_needing_followup,
    find_client_by_email,
    find_client_by_domain,
    get_focus_emails,
    add_client,
    update_client,
    add_message,
    delete_client
)

# 🔐 Outlook / Graph
from core.ms_auth import acquire_token_interactive
from core.ms_mail_reader import read_messages_from_folder

from ui.add_client_popup import AddClientPopup
from ui.add_message_popup import AddMessagePopup
from ui.timeline_window import TimelineWindow
from ui.suggested_reply_popup import SuggestedReplyPopup
from ui.requests_window import RequestsWindow


# ==============================
# Smart request detection
# ==============================
def detect_request(subject, body):
    text = (subject + " " + body).lower()
    score = 0
    detected = []

    if "price" in text or "quotation" in text or "offer" in text:
        score += 15
        detected.append("Price Request")

    if "sample" in text:
        score += 25
        detected.append("Sample Request")

    if "spec" in text or "specification" in text:
        score += 10
        detected.append("Specs Request")

    if "moq" in text or "quantity" in text:
        score += 10
        detected.append("MOQ / Quantity")

    return score, ", ".join(detected)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # DB safety
        init_db()
        ensure_focus_column()

        self.setWindowTitle("Export Follow-Up Manager (EFM)")
        self.setMinimumSize(1300, 720)

        self.all_clients = []
        self.graph_token = None

        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout()

        # ===== Dashboard =====
        self.dashboard = QLabel()
        self.dashboard.setStyleSheet("font-size:16px; font-weight:bold;")
        main_layout.addWidget(self.dashboard)

        # ===== Search & Filters =====
        filter_layout = QHBoxLayout()

        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("🔍 Search company, country, email...")
        self.search_box.textChanged.connect(self.apply_filters)

        self.class_filter = QComboBox()
        self.class_filter.addItems([
            "All Classifications",
            "🔥 Serious Buyer",
            "👍 Potential",
            "❌ Not Serious",
            "⭐ Focus"
        ])
        self.class_filter.currentIndexChanged.connect(self.apply_filters)

        self.status_filter = QComboBox()
        self.status_filter.addItems([
            "All Status",
            "New",
            "No Reply",
            "Requested Price",
            "Samples Requested",
            "Replied"
        ])
        self.status_filter.currentIndexChanged.connect(self.apply_filters)

        filter_layout.addWidget(self.search_box)
        filter_layout.addWidget(self.class_filter)
        filter_layout.addWidget(self.status_filter)
        main_layout.addLayout(filter_layout)

        # ===== Buttons =====
        btn_layout = QHBoxLayout()

        self.add_client_btn = QPushButton("➕ Add Client")
        self.add_client_btn.clicked.connect(self.open_add_client)

        self.edit_client_btn = QPushButton("✏️ Edit Client")
        self.edit_client_btn.clicked.connect(self.edit_client_safe)

        self.add_message_btn = QPushButton("✉️ Add Message")
        self.add_message_btn.clicked.connect(self.open_add_message)

        self.timeline_btn = QPushButton("📜 View Timeline")
        self.timeline_btn.clicked.connect(self.open_timeline)

        self.requests_btn = QPushButton("📋 Requests")
        self.requests_btn.clicked.connect(self.open_requests)

        self.reply_btn = QPushButton("💡 Suggested Reply")
        self.reply_btn.clicked.connect(self.open_suggested_reply)

        self.focus_btn = QPushButton("⭐ Toggle Focus")
        self.focus_btn.clicked.connect(self.toggle_focus)

        self.delete_btn = QPushButton("🗑 Delete Client")
        self.delete_btn.clicked.connect(self.delete_selected_client)

        self.connect_outlook_btn = QPushButton("🔐 Connect Outlook")
        self.connect_outlook_btn.clicked.connect(self.connect_outlook)

        self.sync_all_btn = QPushButton("📥 Sync ALL Emails")
        self.sync_all_btn.clicked.connect(lambda: self.sync_outlook(mode="all"))

        self.sync_focus_btn = QPushButton("🎯 Sync FOCUS Clients")
        self.sync_focus_btn.clicked.connect(lambda: self.sync_outlook(mode="focus"))

        for b in [
            self.add_client_btn,
            self.edit_client_btn,
            self.add_message_btn,
            self.timeline_btn,
            self.requests_btn,
            self.reply_btn,
            self.focus_btn,
            self.delete_btn,
            self.connect_outlook_btn,
            self.sync_all_btn,
            self.sync_focus_btn
        ]:
            btn_layout.addWidget(b)

        btn_layout.addStretch()
        main_layout.addLayout(btn_layout)

        # ===== Clients Table =====
        self.table = QTableWidget()
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels([
            "Company", "Country", "Contact", "Email",
            "Date Added", "Status", "Score", "Classification", "⭐"
        ])
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSortingEnabled(True)
        self.table.horizontalHeader().setStretchLastSection(True)
        main_layout.addWidget(self.table)

        central.setLayout(main_layout)

        self.load_clients()
        self.show_followup_alert()

    # ==============================
    # SAFE Edit Client
    # ==============================
    def edit_client_safe(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Select Client", "Please select a client first.")
            return

        QMessageBox.information(
            self,
            "Edit Client",
            "Client editing is temporarily disabled.\n"
            "It will be enabled in the next step."
        )

    # ==============================
    # Toggle Focus
    # ==============================
    def toggle_focus(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Select Client", "Please select a client first.")
            return

        client_id = self.table.item(row, 0).data(Qt.UserRole)
        client = get_client_by_id(client_id)

        if not client:
            QMessageBox.warning(self, "Error", "Client not found.")
            return

        new_focus = 0 if client[11] else 1
        classification = "⭐ Focus" if new_focus else client[10].replace("⭐ ", "")

        update_client(client_id, {
            "company_name": client[1],
            "country": client[2],
            "contact_person": client[3],
            "email": client[4],
            "phone": client[5],
            "website": client[6],
            "status": client[8],
            "seriousness_score": client[9],
            "classification": classification,
            "is_focus": new_focus
        })

        self.load_clients()

    # ==============================
    # Delete Client (FIXED)
    # ==============================
    def delete_selected_client(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Select Client", "Please select a client first.")
            return

        client_id = self.table.item(row, 0).data(Qt.UserRole)
        company = self.table.item(row, 0).text()

        if QMessageBox.question(
            self,
            "Confirm Delete",
            f"Delete '{company}'?\nAll messages will be deleted.",
            QMessageBox.Yes | QMessageBox.No
        ) == QMessageBox.Yes:
            delete_client(client_id)
            self.load_clients()

    # ==============================
    # Outlook / Data / UI
    # ==============================
    def connect_outlook(self):
        try:
            self.graph_token = acquire_token_interactive()
            QMessageBox.information(self, "Success", "Outlook connected successfully.")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def sync_outlook(self, mode="all"):
        if not self.graph_token:
            QMessageBox.warning(self, "Not Connected", "Please connect Outlook first.")
            return

        messages = read_messages_from_folder(
            self.graph_token,
            folder_name="EFM_Clients",
            top=50
        )

        focus_emails = set()
        if mode == "focus":
            focus_emails = set(get_focus_emails())

        created = linked = 0

        for msg in messages:
            sender_info = msg.get("from", {}).get("emailAddress", {})
            sender = sender_info.get("address", "")
            sender_name = sender_info.get("name", "")

            if not sender or "@" not in sender:
                continue

            if mode == "focus" and sender.lower() not in focus_emails:
                continue

            subject = msg.get("subject", "")
            body = msg.get("body", {}).get("content", "")

            client = find_client_by_email(sender)
            if not client:
                add_client({
                    "company_name": sender_name or sender.split("@")[0],
                    "country": None,
                    "contact_person": sender_name,
                    "email": sender,
                    "phone": None,
                    "website": None,
                    "date_added": datetime.now().strftime("%d/%m/%Y"),
                    "status": "New",
                    "seriousness_score": 0,
                    "classification": "❌ Not Serious",
                    "is_focus": 0
                })
                client = find_client_by_email(sender)
                created += 1

            score, detected = detect_request(subject, body)

            add_message({
                "client_id": client[0],
                "message_date": datetime.now().strftime("%d/%m/%Y"),
                "message_type": "Email",
                "channel": "Outlook",
                "client_response": subject,
                "notes": f"{detected}\n\n{body}",
                "score_effect": score
            })
            linked += 1

        self.load_clients()

        QMessageBox.information(
            self,
            "Sync Complete",
            f"📥 {len(messages)} emails fetched\n"
            f"🆕 New Clients: {created}\n"
            f"🔗 Linked Messages: {linked}"
        )

    def load_clients(self):
        self.all_clients = get_all_clients()
        self.apply_filters()

    def apply_filters(self):
        search = self.search_box.text().lower()
        class_filter = self.class_filter.currentText()
        status_filter = self.status_filter.currentText()

        filtered = []
        for c in self.all_clients:
            (
                client_id, company, country, contact, email,
                phone, website, date_added,
                status, score, classification, is_focus
            ) = c

            if (
                search in (company or "").lower()
                or search in (country or "").lower()
                or search in (email or "").lower()
            ) and (
                class_filter == "All Classifications"
                or classification == class_filter
                or (class_filter == "⭐ Focus" and is_focus)
            ) and (
                status_filter == "All Status"
                or status == status_filter
            ):
                filtered.append(c)

        self.populate_table(filtered)

    def populate_table(self, data):
        self.table.setRowCount(len(data))
        serious = potential = weak = 0

        for row, c in enumerate(data):
            (
                client_id, company, country, contact, email,
                phone, website, date_added,
                status, score, classification, is_focus
            ) = c

            values = [
                company, country, contact, email,
                date_added, status, str(score),
                classification, "⭐" if is_focus else ""
            ]

            for col, val in enumerate(values):
                item = QTableWidgetItem(val or "")
                item.setData(Qt.UserRole, client_id)
                self.table.setItem(row, col, item)

                if is_focus:
                    item.setBackground(QBrush(QColor("#FFF2CC")))
                elif classification.startswith("🔥"):
                    item.setBackground(QBrush(QColor("#FFD6D6")))
                elif classification.startswith("👍"):
                    item.setBackground(QBrush(QColor("#FFF4CC")))
                else:
                    item.setBackground(QBrush(QColor("#E8E8E8")))

            if classification.startswith("🔥"):
                serious += 1
            elif classification.startswith("👍"):
                potential += 1
            else:
                weak += 1

        self.dashboard.setText(
            f"🔥 Serious: {serious}    "
            f"👍 Potential: {potential}    "
            f"❌ Not Serious: {weak}    "
            f"📦 Total: {len(data)}"
        )

    def open_add_client(self):
        AddClientPopup(self.load_clients).exec_()

    def open_add_message(self):
        if self.table.currentRow() < 0:
            QMessageBox.warning(self, "Select Client", "Please select a client first.")
            return
        AddMessagePopup(self.load_clients).exec_()

    def open_timeline(self):
        row = self.table.currentRow()
        if row < 0:
            return
        client_id = self.table.item(row, 0).data(Qt.UserRole)
        company = self.table.item(row, 0).text()
        TimelineWindow(client_id, company).exec_()

    def open_suggested_reply(self):
        row = self.table.currentRow()
        if row < 0:
            return
        company = self.table.item(row, 0).text()
        status = self.table.item(row, 5).text()
        SuggestedReplyPopup(company, status).exec_()

    def show_followup_alert(self):
        due = get_clients_needing_followup()
        if due:
            QMessageBox.information(
                self,
                "Follow-Up Alert",
                "Clients requiring follow-up:\n" + "\n".join(due)
            )

    def open_requests(self):
        try:
            dlg = RequestsWindow()
            dlg.exec_()
        except Exception as e:
            QMessageBox.critical(
                self,
                "Requests Error",
                f"Failed to open Requests window:\n\n{e}"
            )

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QTableWidget, QTableWidgetItem,
    QMessageBox, QLineEdit, QComboBox, QGroupBox,
    QGridLayout, QToolButton, QMenu, QAction, QDialog,
    QScrollArea, QFrame, QSystemTrayIcon
)
from PyQt5.QtGui import QColor, QBrush, QClipboard, QFont
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt5.QtWidgets import QApplication
from datetime import datetime
from typing import List, Dict, Optional

from core.db import (
    init_db,
    ensure_focus_column,
    ensure_requests_reply_status_column,  # ✅ أضف هذا السطر
    get_all_clients,
    get_client_by_id,
    get_clients_needing_followup,
    find_client_by_email,
    find_client_by_domain,
    get_focus_emails,
    add_client,
    update_client,
    add_message,
    delete_client,
    save_request
)
from core.dashboard import (
    get_dashboard_stats,
    get_actions_needed,
    get_monthly_comparison
)
from core.settings import load_settings
from core.logging_system import get_logger, log_error, log_info, log_warning, log_sync
from core.theme import get_theme_manager

# 🔐 Outlook / Graph
from core.ms_auth import acquire_token_interactive
from core.ms_mail_reader import read_messages_from_folder

from ui.add_client_popup import AddClientPopup
from ui.add_message_popup import AddMessagePopup
from ui.timeline_window import TimelineWindow
from ui.suggested_reply_popup import SuggestedReplyPopup
from ui.requests_window import RequestsWindow
from ui.edit_client_popup import EditClientPopup
from ui.backup_window import BackupWindow
from ui.export_window import ExportWindow
from ui.statistics_window import StatisticsWindow
from ui.sales_window import SalesWindow
from ui.advanced_message_popup import AdvancedMessagePopup
from ui.scoring_config_window import ScoringConfigWindow
from ui.tasks_window import TasksWindow
from ui.buyer_search_window import BuyerSearchWindow
from ui.importer_search_window import ImporterSearchWindow
from ui.advanced_search_window import AdvancedSearchWindow
from ui.specialized_search_window import SpecializedSearchWindow
from ui.documents_window import DocumentsWindow
from ui.products_window import ProductsWindow
from ui.quotes_window import QuotesWindow
from ui.settings_window import SettingsWindow
from ui.logs_window import LogsWindow
from ui.sync_window import SyncWindow


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


class FetchMessagesThread(QThread):
    """
    تحميل الرسائل من المصدر في الخلفية لتجنب تجميد واجهة المستخدم.
    """
    finished = pyqtSignal(list)
    failed = pyqtSignal(str)

    def __init__(self, account_type: str, graph_token: str = None, imap_params: dict = None, cpanel_params: dict = None):
        super().__init__()
        self.account_type = account_type
        self.graph_token = graph_token
        self.imap_params = imap_params or {}
        self.cpanel_params = cpanel_params or {}

    def run(self):
        try:
            if self.account_type == "outlook":
                from core.ms_mail_reader import read_messages_from_folder
                messages = read_messages_from_folder(
                    self.graph_token,
                    folder_name="Inbox",
                    top=100,
                    max_messages=500
                )
                self.finished.emit(messages or [])
                return

            if self.account_type == "cpanel_api":
                from core.cpanel_api_reader import read_messages_from_cpanel_api
                messages = read_messages_from_cpanel_api(
                    cpanel_host=self.cpanel_params.get("cpanel_host"),
                    cpanel_username=self.cpanel_params.get("cpanel_username"),
                    api_token=self.cpanel_params.get("cpanel_api_token"),
                    email_account=self.cpanel_params.get("email_account"),
                    max_messages=500
                )
                self.finished.emit(messages or [])
                return

            # default: IMAP
            from core.imap_reader import read_messages_from_imap
            messages = read_messages_from_imap(
                imap_server=self.imap_params.get("imap_server"),
                imap_port=self.imap_params.get("imap_port", 993),
                username=self.imap_params.get("imap_username"),
                password=self.imap_params.get("imap_password"),
                use_ssl=self.imap_params.get("use_ssl", True),
                folder="INBOX",
                max_messages=500,
                timeout=30
            )
            self.finished.emit(messages or [])
        except Exception as e:
            self.failed.emit(str(e))


class ProcessMessagesThread(QThread):
    """
    معالجة الرسائل (فلترة + إنشاء/ربط العملاء + حفظ الرسائل/الطلبات) في الخلفية
    لتجنب تجميد واجهة المستخدم.
    """
    progress = pyqtSignal(str)
    finished = pyqtSignal(dict)
    failed = pyqtSignal(str)

    def __init__(self, messages: list, account_type: str, mode: str):
        super().__init__()
        self.messages = messages or []
        self.account_type = account_type  # "outlook" or others
        self.mode = mode or "all"

    def run(self):
        try:
            from core.message_filter import should_import_message, detect_request_type
            from core.ai_reply_scoring import detect_positive_reply
            from core.db import (
                get_focus_emails, find_client_by_email, add_client, add_message, save_request
            )
            from datetime import datetime as dt

            focus_emails = set(get_focus_emails()) if self.mode == "focus" else set()

            created = 0
            linked = 0
            filtered = 0
            focus_notifications = 0

            total_messages = len(self.messages)
            processed = 0

            for msg in self.messages:
                processed += 1
                if processed % 10 == 0 or processed == 1 or processed == total_messages:
                    self.progress.emit(f"⏳ جاري مزامنة الرسائل... ({processed}/{total_messages})")

                sender_info = msg.get("from", {}).get("emailAddress", {})
                sender = sender_info.get("address", "")
                sender_name = sender_info.get("name", "")

                if not sender or "@" not in sender:
                    continue

                subject = msg.get("subject", "")
                body = msg.get("body", {}).get("content", "")

                # استخراج التاريخ الفعلي للرسالة
                actual_date = None
                if self.account_type == "outlook":
                    received_date = msg.get("receivedDateTime") or msg.get("sentDateTime")
                    if received_date:
                        try:
                            date_obj = dt.fromisoformat(received_date.replace('Z', '+00:00'))
                            actual_date = date_obj.strftime("%d/%m/%Y")
                        except Exception:
                            pass
                else:
                    actual_date = msg.get("date") or None
                    if not actual_date:
                        received_date = msg.get("receivedDateTime")
                        if received_date:
                            try:
                                if isinstance(received_date, str):
                                    if 'T' in received_date:
                                        date_obj = dt.fromisoformat(received_date.replace('Z', '+00:00'))
                                    else:
                                        date_obj = dt.fromisoformat(received_date)
                                    actual_date = date_obj.strftime("%d/%m/%Y")
                            except Exception:
                                pass

                # فلترة الرسائل
                should_import, _reason = should_import_message(subject, body, sender)
                if not should_import:
                    filtered += 1
                    continue

                # focus only
                if self.mode == "focus" and sender.lower() not in focus_emails:
                    filtered += 1
                    continue

                is_focus_client = sender.lower() in focus_emails
                if is_focus_client:
                    focus_notifications += 1  # سنعرضها لاحقاً من الواجهة

                client = find_client_by_email(sender)
                if not client:
                    add_client({
                        "company_name": sender_name or sender.split("@")[0],
                        "country": None,
                        "contact_person": sender_name,
                        "email": sender,
                        "phone": None,
                        "website": None,
                        "date_added": dt.now().strftime("%d/%m/%Y"),
                        "status": "New",
                        "seriousness_score": 0,
                        "classification": None,
                        "is_focus": 1 if is_focus_client else 0
                    })
                    client = find_client_by_email(sender)
                    created += 1

                # اكتشاف نوع الطلب
                request_type, score = detect_request_type(subject, body)
                if request_type != "General Inquiry":
                    save_request(
                        client_email=sender,
                        request_type=request_type,
                        extracted_text=body
                    )

                score_effect = 0
                if len(body) > 50:
                    try:
                        score_effect = detect_positive_reply(body)
                    except Exception:
                        pass
                score_effect += score

                add_message({
                    "client_id": client[0],
                    "message_date": dt.now().strftime("%d/%m/%Y"),
                    "actual_date": actual_date,
                    "message_type": "Email",
                    "channel": "Outlook" if self.account_type == "outlook" else "IMAP",
                    "client_response": subject,
                    "notes": body,
                    "score_effect": score_effect
                })

                linked += 1

            self.finished.emit({
                "created": created,
                "linked": linked,
                "filtered": filtered,
                "focus_notifications": focus_notifications,
                "total_messages": total_messages,
            })
        except Exception as e:
            self.failed.emit(str(e))


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # DB safety
        init_db()
        ensure_requests_reply_status_column()
        ensure_focus_column()

        self.setWindowTitle("Export Follow-Up Manager (EFM)")
        self.setMinimumSize(1300, 720)

        # تطبيق الثيم عند بدء التشغيل
        try:
            theme_manager = get_theme_manager()
            self.setStyleSheet(theme_manager.get_stylesheet())
            self.update_theme_button_text()
        except:
            pass

        self.all_clients = []
        self.graph_token = None
        self.current_account_id = None  # ID الحساب المحدد حالياً
        
        # Timer للنسخ الاحتياطي التلقائي - التحقق كل ساعة
        self.backup_timer = QTimer(self)
        self.backup_timer.timeout.connect(self.check_scheduled_backup)
        self.backup_timer.start(3600000)  # كل ساعة = 3600000 مللي ثانية
        
        # Timer للمهام المتكررة - التحقق كل 6 ساعات
        self.recurring_tasks_timer = QTimer(self)
        self.recurring_tasks_timer.timeout.connect(self.check_recurring_tasks)
        self.recurring_tasks_timer.start(21600000)  # كل 6 ساعات = 21600000 مللي ثانية
        
        # Timer للتحقق من الرسائل الجديدة من عملاء Focus - كل 15 دقيقة
        self.focus_messages_timer = QTimer(self)
        self.focus_messages_timer.timeout.connect(self.check_focus_messages)
        self.focus_messages_timer.start(900000)  # كل 15 دقيقة = 900000 مللي ثانية
        
        # نظام الإشعارات
        self.notification_manager = None
        self.notification_timer = None
        self.init_notifications()
        
        # تتبع آخر رسالة تم فحصها
        self.last_checked_message_id = None

        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout()

        # ===== Search & Filters =====
        filter_layout = QHBoxLayout()
        
        # زر التبديل السريع للوضع الداكن
        self.theme_toggle_btn = QPushButton("🌙 وضع داكن")
        self.theme_toggle_btn.setCheckable(True)
        self.theme_toggle_btn.setMinimumWidth(120)
        self.theme_toggle_btn.setMaximumWidth(120)
        self.theme_toggle_btn.clicked.connect(self.toggle_theme)
        self.update_theme_button_text()
        filter_layout.addWidget(self.theme_toggle_btn)

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

        # ===== Buttons Organized in Groups (Grid Layout - 2 Rows) =====
        buttons_container = QWidget()
        buttons_layout = QGridLayout()
        buttons_layout.setSpacing(10)
        buttons_layout.setContentsMargins(5, 5, 5, 5)
        buttons_container.setLayout(buttons_layout)
        buttons_container.setStyleSheet("QGroupBox { border: 2px solid #CCCCCC; border-radius: 8px; margin-top: 10px; padding-top: 10px; } QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px; }")

        # === مجموعة إدارة العملاء ===
        clients_group = QGroupBox("إدارة العملاء")
        clients_group_layout = QHBoxLayout()
        clients_group_layout.setSpacing(8)
        clients_group_layout.setContentsMargins(10, 15, 10, 10)
        
        self.add_client_btn = QPushButton("➕ إضافة عميل")
        self.add_client_btn.clicked.connect(self.open_add_client)
        self.add_client_btn.setMinimumWidth(110)
        self.add_client_btn.setMinimumHeight(35)

        self.edit_client_btn = QPushButton("✏️ تعديل")
        self.edit_client_btn.clicked.connect(self.edit_client_safe)
        self.edit_client_btn.setMinimumWidth(90)
        self.edit_client_btn.setMinimumHeight(35)

        self.delete_btn = QPushButton("🗑 حذف")
        self.delete_btn.clicked.connect(self.delete_selected_client)
        self.delete_btn.setMinimumWidth(85)
        self.delete_btn.setMinimumHeight(35)
        
        self.focus_btn = QPushButton("⭐ Focus")
        self.focus_btn.clicked.connect(self.toggle_focus)
        self.focus_btn.setMinimumWidth(95)
        self.focus_btn.setMinimumHeight(35)
        self.focus_btn.setStyleSheet("background-color: #FFD93D; font-weight: bold; border-radius: 5px;")
        
        clients_group_layout.addWidget(self.add_client_btn)
        clients_group_layout.addWidget(self.edit_client_btn)
        clients_group_layout.addWidget(self.delete_btn)
        clients_group_layout.addWidget(self.focus_btn)
        clients_group_layout.addStretch()
        
        clients_group.setLayout(clients_group_layout)
        clients_group.setStyleSheet("QGroupBox { font-weight: bold; font-size: 11px; }")
        buttons_layout.addWidget(clients_group, 0, 0)  # Row 0, Col 0

        # === مجموعة الرسائل والتواصل ===
        messages_group = QGroupBox("الرسائل والتواصل")
        messages_group_layout = QHBoxLayout()
        messages_group_layout.setSpacing(8)
        messages_group_layout.setContentsMargins(10, 15, 10, 10)
        
        self.add_message_btn = QPushButton("✉️ رسالة جديدة")
        self.add_message_btn.clicked.connect(self.open_add_message)
        self.add_message_btn.setMinimumWidth(120)
        self.add_message_btn.setMinimumHeight(35)

        self.timeline_btn = QPushButton("📜 الخط الزمني")
        self.timeline_btn.clicked.connect(self.open_timeline)
        self.timeline_btn.setMinimumWidth(105)
        self.timeline_btn.setMinimumHeight(35)

        self.requests_btn = QPushButton("📋 الطلبات")
        self.requests_btn.clicked.connect(self.open_requests)
        self.requests_btn.setMinimumWidth(95)
        self.requests_btn.setMinimumHeight(35)

        self.reply_btn = QPushButton("💡 رد مقترح")
        self.reply_btn.clicked.connect(self.open_suggested_reply)
        self.reply_btn.setMinimumWidth(105)
        self.reply_btn.setMinimumHeight(35)
        
        self.tasks_btn = QPushButton("📋 المهام")
        self.tasks_btn.clicked.connect(self.open_tasks)
        self.tasks_btn.setMinimumWidth(95)
        self.tasks_btn.setMinimumHeight(35)
        
        self.documents_btn = QPushButton("📄 المستندات")
        self.documents_btn.clicked.connect(self.open_documents)
        self.documents_btn.setMinimumWidth(110)
        self.documents_btn.setMinimumHeight(35)
        
        messages_group_layout.addWidget(self.add_message_btn)
        
        self.advanced_message_btn = QPushButton("💬 رسالة متقدمة")
        self.advanced_message_btn.clicked.connect(self.open_advanced_message)
        self.advanced_message_btn.setMinimumWidth(120)
        self.advanced_message_btn.setMinimumHeight(35)
        messages_group_layout.addWidget(self.advanced_message_btn)
        
        messages_group_layout.addWidget(self.timeline_btn)
        messages_group_layout.addWidget(self.requests_btn)
        messages_group_layout.addWidget(self.reply_btn)
        messages_group_layout.addWidget(self.tasks_btn)
        messages_group_layout.addWidget(self.documents_btn)
        messages_group_layout.addStretch()
        
        messages_group.setLayout(messages_group_layout)
        messages_group.setStyleSheet("QGroupBox { font-weight: bold; font-size: 11px; }")
        buttons_layout.addWidget(messages_group, 0, 1)  # Row 0, Col 1

        # === مجموعة المنتجات والعروض ===
        products_group = QGroupBox("المنتجات والعروض")
        products_group_layout = QHBoxLayout()
        products_group_layout.setSpacing(8)
        products_group_layout.setContentsMargins(10, 15, 10, 10)
        
        self.products_btn = QPushButton("📦 المنتجات")
        self.products_btn.clicked.connect(self.open_products)
        self.products_btn.setMinimumWidth(100)
        self.products_btn.setMinimumHeight(35)
        
        self.quotes_btn = QPushButton("💼 العروض")
        self.quotes_btn.clicked.connect(self.open_quotes)
        self.quotes_btn.setMinimumWidth(95)
        self.quotes_btn.setMinimumHeight(35)
        
        products_group_layout.addWidget(self.products_btn)
        products_group_layout.addWidget(self.quotes_btn)
        products_group_layout.addStretch()
        
        products_group.setLayout(products_group_layout)
        products_group.setStyleSheet("QGroupBox { font-weight: bold; font-size: 11px; }")
        buttons_layout.addWidget(products_group, 0, 2)  # Row 0, Col 2

        # === مجموعة Outlook ===
        outlook_group = QGroupBox("Outlook")
        outlook_group_layout = QVBoxLayout()
        outlook_group_layout.setSpacing(5)
        outlook_group_layout.setContentsMargins(10, 15, 10, 10)
        
        # قائمة منسدلة لاختيار الحساب
        account_layout = QHBoxLayout()
        account_layout.addWidget(QLabel("الحساب:"))
        self.account_combo = QComboBox()
        self.account_combo.setMinimumWidth(200)
        self.account_combo.currentIndexChanged.connect(self.on_account_changed)
        account_layout.addWidget(self.account_combo)
        
        self.manage_accounts_btn = QPushButton("⚙️ إدارة الحسابات")
        self.manage_accounts_btn.clicked.connect(self.open_accounts_window)
        self.manage_accounts_btn.setMinimumWidth(130)
        self.manage_accounts_btn.setMinimumHeight(30)
        self.manage_accounts_btn.setStyleSheet("background-color: #6C757D; color: white; font-weight: bold; border-radius: 5px; padding: 5px;")
        account_layout.addWidget(self.manage_accounts_btn)
        account_layout.addStretch()
        outlook_group_layout.addLayout(account_layout)
        
        # أزرار Outlook
        buttons_layout_outlook = QHBoxLayout()
        buttons_layout_outlook.setSpacing(8)
        
        self.connect_outlook_btn = QPushButton("🔐 ربط الحساب")
        self.connect_outlook_btn.clicked.connect(self.connect_outlook)
        self.connect_outlook_btn.setMinimumWidth(110)
        self.connect_outlook_btn.setMinimumHeight(35)
        self.connect_outlook_btn.setStyleSheet("background-color: #0078D4; color: white; font-weight: bold; border-radius: 5px;")
        
        # زر مزامنة مع قائمة منسدلة
        self.sync_menu_btn = QToolButton()
        self.sync_menu_btn.setText("📥 مزامنة ▼")
        self.sync_menu_btn.setPopupMode(QToolButton.InstantPopup)
        self.sync_menu_btn.setMinimumWidth(110)
        self.sync_menu_btn.setMinimumHeight(35)
        self.sync_menu_btn.setStyleSheet("background-color: #4A90E2; color: white; font-weight: bold; border-radius: 5px;")
        sync_menu = QMenu(self.sync_menu_btn)
        
        sync_all_action = QAction("📥 مزامنة جميع الرسائل", self)
        sync_all_action.triggered.connect(lambda: self.sync_outlook(mode="all"))
        sync_menu.addAction(sync_all_action)
        
        sync_focus_action = QAction("🎯 مزامنة Focus فقط", self)
        sync_focus_action.triggered.connect(lambda: self.sync_outlook(mode="focus"))
        sync_menu.addAction(sync_focus_action)
        
        sync_custom_action = QAction("⚙️ مزامنة مخصصة", self)
        sync_custom_action.triggered.connect(self.open_sync_window)
        sync_menu.addAction(sync_custom_action)
        
        self.sync_menu_btn.setMenu(sync_menu)
        
        buttons_layout_outlook.addWidget(self.connect_outlook_btn)
        buttons_layout_outlook.addWidget(self.sync_menu_btn)
        buttons_layout_outlook.addStretch()
        outlook_group_layout.addLayout(buttons_layout_outlook)
        
        outlook_group.setLayout(outlook_group_layout)
        outlook_group.setStyleSheet("QGroupBox { font-weight: bold; font-size: 11px; }")
        buttons_layout.addWidget(outlook_group, 1, 0)  # Row 1, Col 0

        # === مجموعة التقارير والإحصائيات ===
        reports_group = QGroupBox("التقارير والإحصائيات")
        reports_group_layout = QHBoxLayout()
        reports_group_layout.setSpacing(8)
        reports_group_layout.setContentsMargins(10, 15, 10, 10)
        
        self.report_btn = QPushButton("📊 تقرير عميل")
        self.report_btn.clicked.connect(self.open_client_report)
        self.report_btn.setMinimumWidth(110)
        self.report_btn.setMinimumHeight(35)
        
        self.statistics_btn = QPushButton("📈 إحصائيات")
        self.statistics_btn.clicked.connect(self.open_statistics_window)
        self.statistics_btn.setMinimumWidth(100)
        self.statistics_btn.setMinimumHeight(35)
        
        self.buyer_search_btn = QPushButton("🔍 بحث المشترين")
        self.buyer_search_btn.clicked.connect(self.open_buyer_search)
        self.buyer_search_btn.setMinimumWidth(120)
        self.buyer_search_btn.setMinimumHeight(35)
        
        self.importer_search_btn = QPushButton("🌐 بحث المستوردين")
        self.importer_search_btn.clicked.connect(self.open_importer_search)
        self.importer_search_btn.setMinimumWidth(130)
        self.importer_search_btn.setMinimumHeight(35)
        self.importer_search_btn.setStyleSheet("background-color: #4ECDC4; color: white; font-weight: bold; border-radius: 5px;")
        
        self.specialized_search_btn = QPushButton("🎯 بحث متخصص - بصل/كراث مجفف")
        self.specialized_search_btn.clicked.connect(self.open_specialized_search)
        self.specialized_search_btn.setMinimumWidth(200)
        self.specialized_search_btn.setMinimumHeight(35)
        self.specialized_search_btn.setStyleSheet("background-color: #FF6B6B; color: white; font-weight: bold; border-radius: 5px;")
        
        reports_group_layout.addWidget(self.report_btn)
        reports_group_layout.addWidget(self.statistics_btn)
        self.advanced_search_btn = QPushButton("🔍 بحث متقدم")
        self.advanced_search_btn.clicked.connect(self.open_advanced_search)
        self.advanced_search_btn.setMinimumWidth(120)
        self.advanced_search_btn.setMinimumHeight(35)
        
        reports_group_layout.addWidget(self.buyer_search_btn)
        reports_group_layout.addWidget(self.importer_search_btn)
        reports_group_layout.addWidget(self.specialized_search_btn)
        reports_group_layout.addWidget(self.advanced_search_btn)
        reports_group_layout.addStretch()
        
        reports_group.setLayout(reports_group_layout)
        reports_group.setStyleSheet("QGroupBox { font-weight: bold; font-size: 11px; }")
        buttons_layout.addWidget(reports_group, 1, 1)  # Row 1, Col 1

        # === مجموعة البيانات والإعدادات ===
        data_group = QGroupBox("البيانات والإعدادات")
        data_group_layout = QHBoxLayout()
        data_group_layout.setSpacing(8)
        data_group_layout.setContentsMargins(10, 15, 10, 10)
        
        self.backup_btn = QPushButton("💾 نسخ احتياطي")
        self.backup_btn.clicked.connect(self.open_backup_manager)
        self.backup_btn.setMinimumWidth(120)
        self.backup_btn.setMinimumHeight(35)
        
        self.import_btn = QPushButton("📥 استيراد")
        self.import_btn.clicked.connect(self.open_import_window)
        self.import_btn.setMinimumWidth(90)
        self.import_btn.setMinimumHeight(35)
        self.import_btn.setStyleSheet("background-color: #4ECDC4; color: white; font-weight: bold; border-radius: 5px;")
        
        self.export_btn = QPushButton("📤 تصدير")
        self.export_btn.clicked.connect(self.open_export_window)
        
        self.sales_btn = QPushButton("💰 مبيعات")
        self.sales_btn.clicked.connect(self.open_sales_window)
        self.sales_btn.setMinimumWidth(100)
        self.sales_btn.setMinimumHeight(35)
        self.sales_btn.setStyleSheet("background-color: #FFD93D; color: black; font-weight: bold; border-radius: 5px;")
        self.export_btn.setMinimumWidth(90)
        self.export_btn.setMinimumHeight(35)
        
        self.scoring_config_btn = QPushButton("⚙️ إعدادات التقييم")
        self.scoring_config_btn.clicked.connect(self.open_scoring_config)
        self.scoring_config_btn.setMinimumWidth(130)
        self.scoring_config_btn.setMinimumHeight(35)
        
        self.import_btn = QPushButton("📥 استيراد")
        self.import_btn.clicked.connect(self.open_import_window)
        self.import_btn.setMinimumWidth(90)
        self.import_btn.setMinimumHeight(35)
        self.import_btn.setStyleSheet("background-color: #4ECDC4; color: white; font-weight: bold; border-radius: 5px;")
        
        data_group_layout.addWidget(self.backup_btn)
        data_group_layout.addWidget(self.import_btn)
        data_group_layout.addWidget(self.export_btn)
        data_group_layout.addWidget(self.sales_btn)
        self.settings_btn = QPushButton("⚙️ إعدادات عامة")
        self.settings_btn.clicked.connect(self.open_settings)
        self.settings_btn.setMinimumWidth(130)
        self.settings_btn.setMinimumHeight(35)
        
        data_group_layout.addWidget(self.scoring_config_btn)
        data_group_layout.addWidget(self.settings_btn)
        
        self.logs_btn = QPushButton("📋 Logs")
        self.logs_btn.clicked.connect(self.open_logs)
        self.logs_btn.setMinimumWidth(100)
        self.logs_btn.setMinimumHeight(35)
        self.logs_btn.setStyleSheet("background-color: #34495E; color: white; font-weight: bold; border-radius: 5px;")
        data_group_layout.addWidget(self.logs_btn)
        
        data_group_layout.addStretch()
        
        data_group.setLayout(data_group_layout)
        data_group.setStyleSheet("QGroupBox { font-weight: bold; font-size: 11px; }")
        buttons_layout.addWidget(data_group, 1, 2)  # Row 1, Col 2

        # حفظ المراجع للزرين القديمين للتوافق
        self.sync_all_btn = sync_all_action
        self.sync_focus_btn = sync_focus_action

        main_layout.addWidget(buttons_container)

        # ===== Clients Table =====
        self.table = QTableWidget()
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels([
            "Company", "Country", "Contact", "Email",
            "Date Added", "Status", "Score", "Classification", "⭐"
        ])
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.ExtendedSelection)  # تفعيل تحديد متعدد
        self.table.setSortingEnabled(True)
        self.table.horizontalHeader().setStretchLastSection(True)
        # تعطيل الألوان المتناوبة لأننا نطبقها يدوياً
        self.table.setAlternatingRowColors(False)
        main_layout.addWidget(self.table)

        central.setLayout(main_layout)

        self.load_clients()
        self.load_accounts()  # تحميل الحسابات (بما فيها الحساب الثابت contact@el-raee.com)
        self.show_followup_alert()
        self.check_auto_backup()

        # Context for async sync
        self._sync_status_msg = None
        self._sync_fetch_thread = None
        self._sync_process_thread = None
        self._sync_context = None

    # ==============================
    # SAFE Edit Client
    # ==============================
    def edit_client_safe(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Select Client", "Please select a client first.")
            return

        client_id = self.table.item(row, 0).data(Qt.UserRole)

        dlg = EditClientPopup(client_id, self.load_clients)
        dlg.exec_()


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
        classification = (client[10] or "").replace("⭐ ", "")
        if new_focus:
            classification = "⭐ Focus"

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
    # Delete Client(s)
    # ==============================
    def delete_selected_client(self):
        # الحصول على جميع الصفوف المحددة
        selected_rows = set()
        for item in self.table.selectedItems():
            selected_rows.add(item.row())
        
        if not selected_rows:
            QMessageBox.warning(self, "تحديد عملاء", "يرجى تحديد عميل أو أكثر أولاً.")
            return

        # الحصول على معلومات العملاء المحددين
        selected_clients = []
        for row in sorted(selected_rows):
            client_id = self.table.item(row, 0).data(Qt.UserRole)
            company = self.table.item(row, 0).text()
            selected_clients.append((client_id, company))
        
        # إعداد رسالة التأكيد
        if len(selected_clients) == 1:
            client_id, company = selected_clients[0]
            confirm_msg = f"هل أنت متأكد من حذف '{company}'؟\n\n"
        else:
            client_names = [name for _, name in selected_clients[:5]]  # أول 5 أسماء فقط
            names_text = "\n".join([f"• {name}" for name in client_names])
            if len(selected_clients) > 5:
                names_text += f"\n• ... و {len(selected_clients) - 5} عميل آخر"
            confirm_msg = f"هل أنت متأكد من حذف {len(selected_clients)} عميل؟\n\n"
            confirm_msg += f"العملاء المحددين:\n{names_text}\n\n"
        
        confirm_msg += "سيتم حذف:\n"
        confirm_msg += "• جميع الرسائل المرتبطة\n"
        confirm_msg += "• جميع الطلبات المرتبطة\n"
        confirm_msg += "• جميع المهام والمستندات المرتبطة\n\n"
        confirm_msg += "هذا الإجراء لا يمكن التراجع عنه!"
        
        reply = QMessageBox.question(
            self,
            "تأكيد الحذف",
            confirm_msg,
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                total_messages_deleted = 0
                total_requests_deleted = 0
                total_tasks_deleted = 0
                total_documents_deleted = 0
                total_deals_deleted = 0
                deleted_count = 0
                failed_count = 0
                failed_clients = []
                
                # حذف جميع العملاء المحددين
                for client_id, company in selected_clients:
                    try:
                        result = delete_client(client_id)
                        
                        if result and result.get('success'):
                            total_messages_deleted += result.get('messages_deleted', 0)
                            total_requests_deleted += result.get('requests_deleted', 0)
                            total_tasks_deleted += result.get('tasks_deleted', 0)
                            total_documents_deleted += result.get('documents_deleted', 0)
                            total_deals_deleted += result.get('deals_deleted', 0)
                            deleted_count += 1
                        else:
                            failed_count += 1
                            failed_clients.append(company)
                    except Exception as e:
                        failed_count += 1
                        failed_clients.append(company)
                        log_error(f"Error deleting client {client_id} ({company}): {str(e)}", "Delete Client")
                
                # عرض رسالة النجاح
                if deleted_count > 0:
                    success_msg = f"✅ تم حذف {deleted_count} عميل بنجاح!\n\n"
                    success_msg += "📊 الإحصائيات:\n"
                    success_msg += f"• الرسائل المحذوفة: {total_messages_deleted}\n"
                    success_msg += f"• الطلبات المحذوفة: {total_requests_deleted}\n"
                    if total_tasks_deleted > 0:
                        success_msg += f"• المهام المحذوفة: {total_tasks_deleted}\n"
                    if total_documents_deleted > 0:
                        success_msg += f"• المستندات المحذوفة: {total_documents_deleted}\n"
                    if total_deals_deleted > 0:
                        success_msg += f"• الصفقات المحذوفة: {total_deals_deleted}\n"
                    
                    if failed_count > 0:
                        success_msg += f"\n⚠️ فشل حذف {failed_count} عميل:\n"
                        success_msg += "\n".join([f"• {name}" for name in failed_clients[:5]])
                        if len(failed_clients) > 5:
                            success_msg += f"\n• ... و {len(failed_clients) - 5} عميل آخر"
                    
                    QMessageBox.information(self, "تم الحذف", success_msg)
                else:
                    QMessageBox.warning(
                        self,
                        "فشل الحذف",
                        f"فشل حذف جميع العملاء المحددين.\n\n"
                        f"العملاء الذين فشل حذفهم:\n"
                        + "\n".join([f"• {name}" for name in failed_clients[:10]])
                    )
                
                self.load_clients()
            
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "خطأ",
                    f"حدث خطأ أثناء حذف العملاء:\n{str(e)}"
                )
                log_error(f"Error deleting clients: {str(e)}", "Delete Client")

    # ==============================
    # Outlook / Data / UI
    # ==============================
    def load_accounts(self):
        """تحميل الحسابات في القائمة المنسدلة"""
        from core.db import get_all_outlook_accounts
        from core.ms_auth import acquire_token_for_account
        
        self.account_combo.clear()
        accounts = get_all_outlook_accounts()
        
        for account in accounts:
            # الحسابات القديمة قد تحتوي على 7 عناصر فقط
            if len(account) >= 8:
                account_id, account_name, email, token_cache_path, is_active, created_at, last_sync, account_type = account[:8]
            else:
                account_id, account_name, email, token_cache_path, is_active, created_at, last_sync = account
                account_type = "outlook"
            
            display_text = f"{account_name}"
            type_text = " (Outlook)" if account_type == "outlook" else " (cPanel)"
            display_text += type_text
            if email:
                display_text += f" - {email}"
            if not is_active:
                display_text += " [غير نشط]"
            
            self.account_combo.addItem(display_text, account_id)
        
        # إذا كان هناك حساب واحد فقط، حدده تلقائياً
        if self.account_combo.count() > 0:
            self.account_combo.setCurrentIndex(0)
            self.on_account_changed()
    
    def on_account_changed(self):
        """عند تغيير الحساب المحدد"""
        if self.account_combo.currentIndex() < 0:
            self.current_account_id = None
            self.graph_token = None
            return
        
        account_id = self.account_combo.currentData()
        self.current_account_id = account_id
        
        # محاولة الحصول على token للحساب المحدد
        from core.db import get_outlook_account_by_id
        from core.ms_auth import acquire_token_for_account
        
        account = get_outlook_account_by_id(account_id)
        if account:
            account_type = account[7] if len(account) >= 8 else "outlook"
            
            # فقط لحسابات Outlook
            if account_type == "outlook":
                account_name = account[1]
                token_cache_path = account[3]
                
                if token_cache_path:
                    try:
                        # محاولة الحصول على token بدون نافذة تسجيل دخول
                        self.graph_token = acquire_token_for_account(account_name, token_cache_path)
                    except:
                        # إذا فشل، سيحتاج المستخدم للضغط على "ربط الحساب"
                        self.graph_token = None
            else:
                # حسابات IMAP لا تحتاج token
                self.graph_token = None
    
    def open_accounts_window(self):
        """فتح نافذة إدارة الحسابات"""
        from ui.accounts_window import AccountsWindow
        window = AccountsWindow(self)
        # تحديث القائمة دائماً بعد إغلاق النافذة (حتى لو لم يكن Accepted)
        window.finished.connect(lambda result: self.load_accounts())
        window.exec_()
    
    def connect_outlook(self):
        """ربط الحساب المحدد (تسجيل دخول Microsoft)"""
        if self.account_combo.currentIndex() < 0:
            QMessageBox.warning(self, "تنبيه", "الرجاء اختيار حساب أولاً")
            return
        
        account_id = self.account_combo.currentData()
        from core.db import get_outlook_account_by_id
        from core.ms_auth import acquire_token_for_account, get_account_email
        from core.db import update_outlook_account
        
        account = get_outlook_account_by_id(account_id)
        if not account:
            QMessageBox.warning(self, "خطأ", "لم يتم العثور على الحساب")
            return
        
        account_name = account[1]
        token_cache_path = account[3]
        
        try:
            self.graph_token = acquire_token_for_account(account_name, token_cache_path)
            
            # تحديث البريد الإلكتروني إذا كان متاحاً
            email = get_account_email(self.graph_token)
            if email:
                update_outlook_account(account_id, email=email)
                self.load_accounts()  # تحديث القائمة
            
            QMessageBox.information(
                self,
                "نجح",
                f"تم ربط الحساب '{account_name}' بنجاح!\nالبريد: {email or 'غير متاح'}"
            )
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"حدث خطأ أثناء ربط الحساب:\n{str(e)}")

    def sync_outlook(self, mode="all"):
        # التحقق من وجود حساب محدد
        if self.account_combo.currentIndex() < 0:
                QMessageBox.warning(self, "تنبيه", "الرجاء اختيار حساب من القائمة أولاً")
                return
            
        # التأكد من أن current_account_id محدث
        account_id = self.account_combo.currentData()
        if not account_id:
            QMessageBox.warning(self, "تنبيه", "لم يتم العثور على حساب محدد. الرجاء اختيار حساب من القائمة.")
            return
        
        # تحديث current_account_id إذا كان مختلفاً
        if self.current_account_id != account_id:
            self.current_account_id = account_id
            self.on_account_changed()  # تحديث token إذا لزم الأمر
        
        # تعطيل الأزرار أثناء المزامنة لمنع الضغط المتكرر
        self.sync_menu_btn.setEnabled(False)
        self.connect_outlook_btn.setEnabled(False)
        self.account_combo.setEnabled(False)
        
        # إظهار رسالة تأكيد (تعريف خارج try لضمان الوصول إليه في finally)
        status_msg = QMessageBox(self)
        status_msg.setWindowTitle("جاري المزامنة...")
        status_msg.setText("⏳ جاري مزامنة الرسائل، الرجاء الانتظار...")
        status_msg.setStandardButtons(QMessageBox.NoButton)
        status_msg.setWindowModality(Qt.NonModal)
        status_msg.show()
        
        # تحديث الواجهة فوراً
        QApplication.processEvents()
        
        try:
            from core.db import get_outlook_account_by_id

            account = get_outlook_account_by_id(self.current_account_id)
            if not account:
                status_msg.close()
                self.sync_menu_btn.setEnabled(True)
                self.connect_outlook_btn.setEnabled(True)
                self.account_combo.setEnabled(True)
                QMessageBox.warning(self, "خطأ", "لم يتم العثور على الحساب")
                return

            account_type = account[7] if len(account) >= 8 else "outlook"

            # تحديث الرسالة قبل قراءة الرسائل
            status_msg.setText("⏳ جاري قراءة الرسائل من الخادم...")
            QApplication.processEvents()

            # تجهيز thread لقراءة الرسائل بدون تجميد
            fetch_type = "outlook"
            graph_token = None
            imap_params = None
            cpanel_params = None

            if account_type == "outlook":
                # حساب Outlook - التأكد من token
                if not self.graph_token:
                    from core.ms_auth import acquire_token_for_account
                    account_name = account[1]
                    token_cache_path = account[3]

                    if not token_cache_path:
                        status_msg.close()
                        self.sync_menu_btn.setEnabled(True)
                        self.connect_outlook_btn.setEnabled(True)
                        self.account_combo.setEnabled(True)
                        QMessageBox.warning(self, "تنبيه", "الرجاء ربط الحساب أولاً (زر 'ربط الحساب')")
                        return

                    self.graph_token = acquire_token_for_account(account_name, token_cache_path)

                graph_token = self.graph_token
                fetch_type = "outlook"
            else:
                # حساب IMAP (cPanel) أو cPanel API
                use_cpanel_api = account[16] == 1 if len(account) >= 17 else False
                if use_cpanel_api:
                    cpanel_host = account[13] if len(account) >= 14 else None
                    cpanel_username = account[14] if len(account) >= 15 else None
                    cpanel_api_token = account[15] if len(account) >= 16 else None
                    email_account = account[2] or account[10] if len(account) >= 11 else None

                    if not cpanel_host or not cpanel_username or not cpanel_api_token or not email_account:
                        status_msg.close()
                        self.sync_menu_btn.setEnabled(True)
                        self.connect_outlook_btn.setEnabled(True)
                        self.account_combo.setEnabled(True)
                        QMessageBox.warning(
                            self,
                            "تنبيه",
                            "معلومات cPanel API غير مكتملة. الرجاء التحقق من إعدادات الحساب."
                        )
                        return

                    fetch_type = "cpanel_api"
                    cpanel_params = {
                        "cpanel_host": cpanel_host,
                        "cpanel_username": cpanel_username,
                        "cpanel_api_token": cpanel_api_token,
                        "email_account": email_account,
                    }
                else:
                    imap_server = account[8] if len(account) >= 9 else None
                    imap_port = account[9] if len(account) >= 10 else 993
                    imap_username = account[10] if len(account) >= 11 else None
                    imap_password = account[11] if len(account) >= 12 else None
                    use_ssl = account[12] == 1 if len(account) >= 13 else True

                    if not imap_server or not imap_username or not imap_password:
                        status_msg.close()
                        self.sync_menu_btn.setEnabled(True)
                        self.connect_outlook_btn.setEnabled(True)
                        self.account_combo.setEnabled(True)
                        QMessageBox.warning(
                            self,
                            "تنبيه",
                            "معلومات IMAP غير مكتملة. الرجاء التحقق من إعدادات الحساب."
                        )
                        return

                    fetch_type = "imap"
                    imap_params = {
                        "imap_server": imap_server,
                        "imap_port": imap_port,
                        "imap_username": imap_username,
                        "imap_password": imap_password,
                        "use_ssl": use_ssl,
                    }

            # حفظ سياق المزامنة للمرحلة الثانية (المعالجة)
            self._sync_status_msg = status_msg
            self._sync_context = {
                "account": account,
                "account_type": account_type,
                "mode": mode,
            }

            # إيقاف أي thread سابق
            try:
                if self._sync_fetch_thread and self._sync_fetch_thread.isRunning():
                    self._sync_fetch_thread.terminate()
            except Exception:
                pass

            self._sync_fetch_thread = FetchMessagesThread(
                account_type=fetch_type,
                graph_token=graph_token,
                imap_params=imap_params,
                cpanel_params=cpanel_params,
            )

            self._sync_fetch_thread.finished.connect(self._on_fetch_messages_finished)
            self._sync_fetch_thread.failed.connect(self._on_fetch_messages_failed)
            self._sync_fetch_thread.start()

            # نخرج هنا — المتابعة ستكون في callback
            return

            focus_emails = set(get_focus_emails()) if mode == "focus" else set()

            created = 0
            linked = 0
            filtered = 0
            focus_notifications = 0
            
            total_messages = len(messages)
            processed = 0

            for msg in messages:
                processed += 1
                # تحديث الواجهة كل 10 رسائل لتقليل استدعاءات processEvents (تحسين الأداء)
                if processed % 10 == 0 or processed == 1 or processed == total_messages:
                    status_msg.setText(f"⏳ جاري مزامنة الرسائل... ({processed}/{total_messages})")
                    QApplication.processEvents()
                
                sender_info = msg.get("from", {}).get("emailAddress", {})
                sender = sender_info.get("address", "")
                sender_name = sender_info.get("name", "")

                if not sender or "@" not in sender:
                    continue

                subject = msg.get("subject", "")
                body = msg.get("body", {}).get("content", "")
                
                # استخراج التاريخ الفعلي للرسالة
                actual_date = None
                if account_type == "outlook":
                    # Outlook - استخدام receivedDateTime أو sentDateTime
                    received_date = msg.get("receivedDateTime") or msg.get("sentDateTime")
                    if received_date:
                        try:
                            # تحويل من ISO format إلى dd/mm/yyyy
                            from datetime import datetime as dt
                            date_obj = dt.fromisoformat(received_date.replace('Z', '+00:00'))
                            actual_date = date_obj.strftime("%d/%m/%Y")
                        except:
                            pass
                else:
                    # IMAP - استخدام date من الرسالة (إذا كان بتنسيق dd/mm/yyyy) أو receivedDateTime
                    actual_date = msg.get("date")  # imap_reader يعيده بتنسيق dd/mm/yyyy
                    if not actual_date:
                        # محاولة استخراج من receivedDateTime
                        received_date = msg.get("receivedDateTime")
                        if received_date:
                            try:
                                from datetime import datetime as dt
                                if isinstance(received_date, str):
                                    # محاولة تحليل ISO format
                                    if 'T' in received_date:
                                        date_obj = dt.fromisoformat(received_date.replace('Z', '+00:00'))
                                    else:
                                        date_obj = dt.fromisoformat(received_date)
                                    actual_date = date_obj.strftime("%d/%m/%Y")
                            except:
                                pass
                
                # فلترة الرسائل - استيراد فقط الرسائل المتعلقة بالعمل
                should_import, reason = should_import_message(subject, body, sender)
                if not should_import:
                    filtered += 1
                    continue

                # إذا كان الوضع "focus" فقط، تخطي الرسائل من غير عملاء Focus
                if mode == "focus" and sender.lower() not in focus_emails:
                    filtered += 1
                    continue

                from core.ai_reply_scoring import detect_positive_reply

                client = find_client_by_email(sender)

                # التحقق إذا كان العميل من Focus Clients
                is_focus_client = sender.lower() in focus_emails

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
                        "classification": None,
                        "is_focus": 1 if is_focus_client else 0
                    })
                    client = find_client_by_email(sender)
                    created += 1
                    # تحديث الواجهة بعد إضافة عميل جديد (تقليل الاستدعاءات)
                    if created % 10 == 0:
                        QApplication.processEvents()

                    # إشعار إذا كان عميل Focus جديد
                    if is_focus_client:
                        focus_notifications += 1
                        self.show_focus_client_notification(sender, subject, is_new=True)

                # إشعار إذا كان عميل Focus موجود
                elif is_focus_client:
                    focus_notifications += 1
                    self.show_focus_client_notification(sender, subject, is_new=False)

                # اكتشاف نوع الطلب
                request_type, score = detect_request_type(subject, body)
                
                if request_type != "General Inquiry":
                    save_request(
                        client_email=sender,
                        request_type=request_type,
                        extracted_text=body
                    )

                score_effect = 0
                # تحسين الأداء: تخطي detect_positive_reply للرسائل القصيرة جداً
                is_client_reply = True
                if is_client_reply and len(body) > 50:  # فقط للرسائل الطويلة
                    try:
                        score_effect = detect_positive_reply(body)
                    except:
                        pass  # تخطي في حالة الخطأ لتسريع المزامنة
                
                # إضافة النقاط من الطلبات
                score_effect += score

                add_message({
                    "client_id": client[0],
                    "message_date": datetime.now().strftime("%d/%m/%Y"),
                    "actual_date": actual_date,  # التاريخ الفعلي للرسالة
                    "message_type": "Email",
                    "channel": "Outlook" if account_type == "outlook" else "IMAP",
                    "client_response": subject,
                    "notes": body,
                    "score_effect": score_effect
                })

                linked += 1
                
                # تحديث الواجهة كل 10 رسائل معالجة (تقليل الاستدعاءات لتحسين الأداء)
                if linked % 10 == 0:
                    QApplication.processEvents()

            self.load_clients()

            # تحديث تاريخ آخر مزامنة
            if self.current_account_id:
                update_account_last_sync(self.current_account_id)
                self.load_accounts()  # تحديث القائمة لعرض آخر مزامنة

            message = f"تم إنشاء: {created} عميل جديد\n"
            message += f"تم معالجة: {linked} رسالة\n"
            message += f"تم تصفية: {filtered} رسالة غير متعلقة\n"
            if focus_notifications > 0:
                message += f"\n🔔 تم إرسال {focus_notifications} إشعار من عملاء Focus"
            
            # إغلاق رسالة التقدم قبل عرض رسالة النجاح
            status_msg.close()
            QApplication.processEvents()  # تحديث الواجهة لضمان إغلاق الرسالة
            
            QMessageBox.information(
                self,
                "اكتمل المزامنة",
                message
            )

        except Exception as e:
            status_msg.close()
            QApplication.processEvents()
            QMessageBox.critical(self, "خطأ في المزامنة", f"حدث خطأ أثناء المزامنة:\n{str(e)}")
            log_error(f"Outlook sync error: {str(e)}", "Outlook Sync")
            self._sync_cleanup()


    def _sync_cleanup(self):
        """إعادة تفعيل عناصر الواجهة وإغلاق نافذة الحالة"""
        try:
            if self._sync_status_msg:
                self._sync_status_msg.close()
                self._sync_status_msg.deleteLater()
        except Exception:
            pass
        self._sync_status_msg = None
        self._sync_context = None

        try:
            self.sync_menu_btn.setEnabled(True)
            self.connect_outlook_btn.setEnabled(True)
            self.account_combo.setEnabled(True)
        except Exception:
            pass


    def _on_fetch_messages_failed(self, err: str):
        """فشل تحميل الرسائل (مرحلة القراءة)"""
        try:
            QMessageBox.critical(self, "خطأ في الاتصال", f"فشل قراءة الرسائل من الخادم:\n{err}")
            log_error(f"Fetch messages error: {err}", "Outlook Sync")
        finally:
            self._sync_cleanup()


    def _on_fetch_messages_finished(self, messages: list):
        """تم تحميل الرسائل بنجاح — نبدأ المعالجة (في نفس الواجهة مع تحديثات)"""
        if not self._sync_context:
            self._sync_cleanup()
            return

        status_msg = self._sync_status_msg
        account = self._sync_context.get("account")
        account_type = self._sync_context.get("account_type")
        mode = self._sync_context.get("mode", "all")

        try:
            if status_msg:
                status_msg.setText(f"⏳ تم قراءة {len(messages)} رسالة، جاري المعالجة...")
                QApplication.processEvents()

            if not messages:
                if status_msg:
                    status_msg.close()
                QMessageBox.information(self, "لا توجد رسائل", "لم يتم العثور على رسائل جديدة للمزامنة.")
                self._sync_cleanup()
                return

            # بدء معالجة الرسائل في Thread لتجنب تجميد الواجهة
            try:
                if self._sync_process_thread and self._sync_process_thread.isRunning():
                    self._sync_process_thread.terminate()
            except Exception:
                pass

            self._sync_process_thread = ProcessMessagesThread(
                messages=messages,
                account_type=account_type,
                mode=mode
            )
            self._sync_process_thread.progress.connect(self._on_process_messages_progress)
            self._sync_process_thread.finished.connect(self._on_process_messages_finished)
            self._sync_process_thread.failed.connect(self._on_process_messages_failed)
            self._sync_process_thread.start()
            return
        except Exception as e:
            if status_msg:
                status_msg.close()
                QApplication.processEvents()
            QMessageBox.critical(self, "خطأ في المزامنة", f"حدث خطأ أثناء المزامنة:\n{str(e)}")
            log_error(f"Outlook sync error: {str(e)}", "Outlook Sync")
        finally:
            # cleanup سيتم بعد انتهاء Thread المعالجة
            pass


    def _on_process_messages_progress(self, text: str):
        try:
            if self._sync_status_msg:
                self._sync_status_msg.setText(text)
                QApplication.processEvents()
        except Exception:
            pass


    def _on_process_messages_failed(self, err: str):
        try:
            if self._sync_status_msg:
                self._sync_status_msg.close()
            QMessageBox.critical(self, "خطأ في المزامنة", f"حدث خطأ أثناء المعالجة:\n{err}")
            log_error(f"Process messages error: {err}", "Outlook Sync")
        finally:
            self._sync_cleanup()


    def _on_process_messages_finished(self, stats: dict):
        try:
            from core.db import update_account_last_sync

            # تحديث البيانات بعد المعالجة
            self.load_clients()
            if self.current_account_id:
                update_account_last_sync(self.current_account_id)
                self.load_accounts()

            created = stats.get("created", 0)
            linked = stats.get("linked", 0)
            filtered = stats.get("filtered", 0)
            focus_notifications = stats.get("focus_notifications", 0)

            msg = f"تم إنشاء: {created} عميل جديد\n"
            msg += f"تم معالجة: {linked} رسالة\n"
            msg += f"تم تصفية: {filtered} رسالة غير متعلقة\n"
            if focus_notifications > 0:
                msg += f"\n🔔 تم اكتشاف {focus_notifications} رسالة من عملاء Focus"

            if self._sync_status_msg:
                self._sync_status_msg.close()
                QApplication.processEvents()

            QMessageBox.information(self, "اكتمل المزامنة", msg)
        except Exception as e:
            QMessageBox.critical(self, "خطأ في المزامنة", f"حدث خطأ بعد المعالجة:\n{str(e)}")
            log_error(f"Post-process sync error: {str(e)}", "Outlook Sync")
        finally:
            self._sync_cleanup()


    def load_clients(self):
        self.all_clients = get_all_clients()
        self.apply_filters()

    def client_has_reply_status(self, client_id: int, reply_status: str) -> bool:
        """
        Check if client has any request with a given reply_status
        reply_status: 'pending' | 'replied'
        """
        from core.db import get_connection

        conn = get_connection()
        cur = conn.cursor()

        cur.execute("""
            SELECT 1
            FROM requests
            WHERE client_id = ?
              AND reply_status = ?
            LIMIT 1
        """, (client_id, reply_status))

        result = cur.fetchone()
        conn.close()

        return result is not None

    def open_client_report(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Select Client", "Please select a client first.")
            return

        client_id = self.table.item(row, 0).data(Qt.UserRole)
        company = self.table.item(row, 0).text()

        from ui.client_report_window import ClientReportWindow
        dlg = ClientReportWindow(client_id, company, self)
        dlg.exec_()

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

            classification = classification or ""

            # ---------- Search ----------
            search_ok = (
                search in (company or "").lower()
                or search in (country or "").lower()
                or search in (email or "").lower()
            )

            # ---------- Classification ----------
            class_ok = (
                class_filter == "All Classifications"
                or classification == class_filter
                or (class_filter == "⭐ Focus" and is_focus)
            )

            # ---------- Status / Requests ----------
            if status_filter == "All Status":
                status_ok = True

            elif status_filter == "Requested Price":
                status_ok = self.client_has_request(client_id, "Price Request")

            elif status_filter == "Samples Requested":
                status_ok = self.client_has_request(client_id, "Sample Request")

            elif status_filter == "Replied":
                status_ok = self.client_has_reply_status(client_id, "replied")

            elif status_filter == "No Reply":
                status_ok = self.client_has_reply_status(client_id, "pending")

            else:
                status_ok = (status == status_filter)

            # ---------- Final ----------
            if search_ok and class_ok and status_ok:
                filtered.append(c)

        self.populate_table(filtered)

    def client_has_request(self, client_id: int, request_keyword: str) -> bool:
        """
        Check if client has an OPEN request that CONTAINS a keyword
        (e.g. 'Price Request')
        """
        from core.db import get_connection

        conn = get_connection()
        cur = conn.cursor()

        cur.execute("""
            SELECT 1
            FROM requests
            WHERE client_id = ?
              AND request_type LIKE ?
              AND status = 'open'
            LIMIT 1
        """, (client_id, f"%{request_keyword}%"))

        result = cur.fetchone()
        conn.close()

        return result is not None

    def populate_table(self, data):
        self.table.setRowCount(len(data))
        serious = potential = weak = 0

        for row, c in enumerate(data):
            (
                client_id, company, country, contact, email,
                phone, website, date_added,
                status, score, classification, is_focus
            ) = c

            classification = classification or ""

            values = [
                company, country, contact, email,
                date_added, status, str(score),
                classification, "⭐" if is_focus else ""
            ]

            # التحقق من الوضع الداكن - مرة واحدة لكل صف
            from core.theme import get_theme_manager
            theme_manager = get_theme_manager()
            is_dark = theme_manager.get_theme() == "dark"
            
            # تحديد ألوان الصف حسب التصنيف
            if is_dark:
                # ألوان للوضع الداكن - خلفيات داكنة مع نصوص فاتحة واضحة
                if is_focus:
                    row_bg = QColor("#5A5A00")  # أصفر داكن
                    row_fg = QColor("#FFD700")  # نص ذهبي فاتح وواضح
                elif classification.startswith("🔥"):
                    row_bg = QColor("#5A0000")  # أحمر داكن
                    row_fg = QColor("#FFAAAA")  # نص أحمر فاتح وواضح
                elif classification.startswith("👍"):
                    row_bg = QColor("#5A5A00")  # أصفر داكن
                    row_fg = QColor("#FFD700")  # نص ذهبي فاتح وواضح
                else:
                    # للصفوف العادية - خلفية داكنة مع نص أبيض واضح
                    if row % 2 == 0:
                        row_bg = QColor("#1E1E1E")  # خلفية داكنة جداً
                    else:
                        row_bg = QColor("#252525")  # خلفية داكنة أغمق قليلاً
                    row_fg = QColor("#FFFFFF")  # نص أبيض واضح جداً
            else:
                # ألوان للوضع الفاتح (الأصلية)
                if is_focus:
                    row_bg = QColor("#FFF2CC")
                    row_fg = QColor("#000000")
                elif classification.startswith("🔥"):
                    row_bg = QColor("#FFD6D6")
                    row_fg = QColor("#000000")
                elif classification.startswith("👍"):
                    row_bg = QColor("#FFF4CC")
                    row_fg = QColor("#000000")
                else:
                    row_bg = QColor("#E8E8E8")
                    row_fg = QColor("#000000")
            
            # تطبيق الألوان على جميع أعمدة الصف
            for col, val in enumerate(values):
                item = QTableWidgetItem(str(val) if val else "")
                item.setData(Qt.UserRole, client_id)
                
                # تطبيق الألوان بشكل صريح وقوي - إجبار التطبيق
                item.setBackground(QBrush(row_bg))
                item.setForeground(QBrush(row_fg))
                
                # التأكد من أن النص واضح
                item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                
                # إضافة العنصر أولاً
                self.table.setItem(row, col, item)
                
                # إعادة تطبيق الألوان بعد إضافة العنصر للتأكد من التطبيق
                item = self.table.item(row, col)
                if item:
                    item.setBackground(QBrush(row_bg))
                    item.setForeground(QBrush(row_fg))

            if classification.startswith("🔥"):
                serious += 1
            elif classification.startswith("👍"):
                potential += 1
            else:
                weak += 1

    def open_add_client(self):
        AddClientPopup(self.load_clients).exec_()

    def open_add_message(self):
        if self.table.currentRow() < 0:
            QMessageBox.warning(self, "Select Client", "Please select a client first.")
            return
        AddMessagePopup(self.load_clients).exec_()

    def open_advanced_message(self):
        """فتح نافذة إضافة رسالة متقدمة من قنوات مختلفة"""
        try:
            # تحديد معرف العميل المحدد إن وجد
            client_id = None
            row = self.table.currentRow()
            if row >= 0:
                client_id = self.table.item(row, 0).data(Qt.UserRole)
            
            dlg = AdvancedMessagePopup(self, client_id=client_id)
            if dlg.exec_() == QDialog.Accepted:
                self.load_clients()
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to open Advanced Message window:\n\n{e}"
            )

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
            QMessageBox.warning(self, "Select Client", "Please select a client first.")
            return
        
        client_id = self.table.item(row, 0).data(Qt.UserRole)
        company = self.table.item(row, 0).text()
        status = self.table.item(row, 5).text()
        
        # فتح نافذة الردود المقترحة مع معلومات العميل
        popup = SuggestedReplyPopup(
            company=company, 
            request_type=status,
            status=status,
            client_id=client_id
        )
        
        if popup.exec_() == QDialog.Accepted:
            # استخدام الرد (يمكن إرساله عبر Outlook أو نسخه)
            subject = popup.subject
            body = popup.body
            
            if subject and body:
                # عرض خيارات: نسخ أو إرسال
                reply = QMessageBox.question(
                    self,
                    "Reply Ready",
                    f"Subject: {subject}\n\nReply is ready!\n\nWould you like to copy it to clipboard?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.Yes
                )
                
                if reply == QMessageBox.Yes:
                    # نسخ إلى الحافظة باستخدام QClipboard
                    clipboard = QApplication.clipboard()
                    full_text = f"Subject: {subject}\n\n{body}"
                    clipboard.setText(full_text)
                    QMessageBox.information(self, "Copied", "Reply copied to clipboard!")

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
            dlg = RequestsWindow(self)
            dlg.exec_()
        except Exception as e:
            QMessageBox.critical(
                self,
                "Requests Error",
                f"Failed to open Requests window:\n\n{e}"
            )

    def open_backup_manager(self):
        """فتح نافذة إدارة النسخ الاحتياطي"""
        try:
            dlg = BackupWindow(self)
            dlg.exec_()
        except Exception as e:
            QMessageBox.critical(
                self,
                "Backup Error",
                f"Failed to open Backup Manager:\n\n{e}"
            )

    def check_auto_backup(self):
        """التحقق من النسخ التلقائي عند بدء التشغيل"""
        try:
            from core.backup import get_backup_config, run_auto_backup_if_needed, create_backup
            
            config = get_backup_config()
            
            # النسخ عند بدء التشغيل
            if config.get("backup_on_startup", False):
                create_backup("نسخ احتياطي عند بدء التشغيل")
                log_info("Startup backup created", "Backup")
            
            # النسخ التلقائي المجدول
            backup_path = run_auto_backup_if_needed()
            if backup_path:
                log_info(f"Scheduled backup created: {backup_path}", "Backup")
                
        except Exception as e:
            log_error(e, "Auto Backup Check")
    
    def open_import_window(self):
        """فتح نافذة استيراد البيانات"""
        try:
            from ui.import_window import ImportWindow
            dlg = ImportWindow(self)
            if dlg.exec_() == QDialog.Accepted:
                # تحديث قائمة العملاء بعد الاستيراد
                self.load_clients()
        except Exception as e:
            QMessageBox.critical(
                self,
                "خطأ",
                f"حدث خطأ أثناء فتح نافذة الاستيراد:\n{str(e)}"
            )
    
    def open_export_window(self):
        """فتح نافذة تصدير البيانات"""
        try:
            # تحديد معرف العميل المحدد إن وجد
            client_id = None
            row = self.table.currentRow()
            if row >= 0:
                client_id = self.table.item(row, 0).data(Qt.UserRole)
            
            dlg = ExportWindow(self, selected_client_id=client_id)
            dlg.exec_()
        except Exception as e:
            QMessageBox.critical(
                self,
                "Export Error",
                f"Failed to open Export window:\n\n{e}"
            )

    def open_statistics_window(self):
        """فتح نافذة الإحصائيات المرئية"""
        try:
            dlg = StatisticsWindow(self)
            dlg.exec_()
        except Exception as e:
            QMessageBox.critical(
                self,
                "Statistics Error",
                f"Failed to open Statistics window:\n\n{e}"
            )
    
    def open_sync_window(self):
        """فتح نافذة المزامنة المخصصة"""
        try:
            dlg = SyncWindow(self)
            dlg.exec_()
        except Exception as e:
            QMessageBox.critical(
                self,
                "Sync Window Error",
                f"Failed to open Sync window:\n\n{e}"
            )
    
    def open_sync_window(self):
        """فتح نافذة المزامنة المخصصة"""
        try:
            dlg = SyncWindow(self)
            dlg.exec_()
            # تحديث قائمة العملاء بعد المزامنة
            self.load_clients()
        except Exception as e:
            QMessageBox.critical(
                self,
                "Sync Window Error",
                f"Failed to open Sync window:\n\n{e}"
            )

    def open_sales_window(self):
        """فتح نافذة إدارة المبيعات"""
        try:
            dlg = SalesWindow(self)
            dlg.exec_()
        except Exception as e:
            QMessageBox.critical(
                self,
                "Sales Error",
                f"Failed to open Sales window:\n\n{e}"
            )

    def open_scoring_config(self):
        """فتح نافذة إعدادات نظام التقييم"""
        try:
            dlg = ScoringConfigWindow(self)
            dlg.exec_()
            # إعادة تحميل العملاء بعد تحديث الإعدادات
            self.load_clients()
        except Exception as e:
            QMessageBox.critical(
                self,
                "Scoring Config Error",
                f"Failed to open Scoring Config window:\n\n{e}"
            )
    
    def open_settings(self):
        """فتح نافذة الإعدادات العامة"""
        try:
            dlg = SettingsWindow(self)
            dlg.exec_()
        except Exception as e:
            log_error(e, "Open Settings")
            QMessageBox.critical(
                self,
                "Settings Error",
                f"Failed to open Settings window:\n\n{e}"
            )
    
    def open_logs(self):
        """فتح نافذة عرض Logs"""
        try:
            dlg = LogsWindow(self)
            dlg.exec_()
        except Exception as e:
            log_error(e, "Open Logs")
            QMessageBox.critical(
                self,
                "Logs Error",
                f"Failed to open Logs window:\n\n{e}"
            )
    
    def toggle_theme(self):
        """تبديل الوضع الداكن/الفاتح"""
        try:
            theme_manager = get_theme_manager()
            current_theme = theme_manager.get_theme()
            
            # التبديل بين الوضعين
            new_theme = "dark" if current_theme == "light" else "light"
            theme_manager.set_theme(new_theme)
            
            # تحديث زر التبديل
            self.update_theme_button_text()
            
            # تطبيق الثيم على التطبيق
            QApplication.instance().setStyleSheet(theme_manager.get_stylesheet())
            
            # إعادة تحميل الجدول لتطبيق الألوان الجديدة
            self.load_clients()
            
            log_info(f"Theme changed to {new_theme}")
        except Exception as e:
            log_error(e, "Toggle Theme")
            QMessageBox.warning(self, "Theme Error", f"Failed to toggle theme:\n\n{e}")
    
    def update_theme_button_text(self):
        """تحديث نص زر التبديل حسب الثيم الحالي"""
        try:
            theme_manager = get_theme_manager()
            current_theme = theme_manager.get_theme()
            
            if current_theme == "dark":
                self.theme_toggle_btn.setText("☀️ وضع فاتح")
                self.theme_toggle_btn.setChecked(True)
            else:
                self.theme_toggle_btn.setText("🌙 وضع داكن")
                self.theme_toggle_btn.setChecked(False)
        except Exception:
            pass

    def check_recurring_tasks(self):
        """التحقق من المهام المتكررة وإنشاء المهام الجديدة"""
        try:
            from core.tasks import create_recurring_task_occurrences
            created_count = create_recurring_task_occurrences()
            if created_count > 0:
                log_info(f"Created {created_count} recurring task(s) automatically")
        except Exception as e:
            log_error(f"Error checking recurring tasks: {str(e)}")
    
    def check_focus_messages(self):
        """التحقق من الرسائل الجديدة من عملاء Focus"""
        try:
            if not self.graph_token:
                return
            
            from core.ms_mail_reader import read_new_messages_from_inbox
            from core.message_filter import should_import_message, detect_request_type
            from core.ai_reply_scoring import detect_positive_reply
            
            # قراءة آخر 20 رسالة
            messages = read_new_messages_from_inbox(self.graph_token, top=20)
            
            focus_emails = set(get_focus_emails())
            if not focus_emails:
                return
            
            new_messages_count = 0
            
            for msg in messages:
                # تخطي إذا كانت نفس الرسالة الأخيرة
                msg_id = msg.get("id")
                if msg_id == self.last_checked_message_id:
                    break
                
                sender_info = msg.get("from", {}).get("emailAddress", {})
                sender = sender_info.get("address", "")
                
                if not sender or sender.lower() not in focus_emails:
                    continue
                
                subject = msg.get("subject", "")
                body = msg.get("body", {}).get("content", "")
                
                # فلترة الرسائل المتعلقة بالعمل
                should_import, reason = should_import_message(subject, body, sender)
                if not should_import:
                    continue
                
                # إشعار فوري
                self.show_focus_client_notification(sender, subject, is_new=False)
                new_messages_count += 1
                
                # معالجة الرسالة
                client = find_client_by_email(sender)
                if client:
                    request_type, score = detect_request_type(subject, body)
                    score_effect = detect_positive_reply(body) + score
                    
                    add_message({
                        "client_id": client[0],
                        "message_date": datetime.now().strftime("%d/%m/%Y"),
                        "message_type": "Email",
                        "channel": "Outlook",
                        "client_response": subject,
                        "notes": body,
                        "score_effect": score_effect
                    })
                    
                    if request_type != "General Inquiry":
                        save_request(
                            client_email=sender,
                            request_type=request_type,
                            extracted_text=body
                        )
            
            # تحديث آخر رسالة تم فحصها
            if messages:
                self.last_checked_message_id = messages[0].get("id")
            
            if new_messages_count > 0:
                self.load_clients()
                log_info(f"Found {new_messages_count} new message(s) from Focus clients")
        
        except Exception as e:
            log_error(f"Error checking focus messages: {str(e)}", "Focus Messages Check")
    
    def show_focus_client_notification(self, sender_email: str, subject: str, is_new: bool = False):
        """عرض إشعار عند استلام رسالة من عميل Focus"""
        try:
            if not self.notification_manager:
                return
            
            client = find_client_by_email(sender_email)
            client_name = client[1] if client else sender_email.split("@")[0]
            
            title = "🔔 رسالة جديدة من عميل Focus"
            if is_new:
                title = "🆕 عميل Focus جديد"
            
            message = f"من: {client_name}\nالموضوع: {subject[:50]}"
            
            # إشعار سطح المكتب
            if self.notification_manager and self.notification_manager.tray_icon:
                self.notification_manager.tray_icon.showMessage(
                    title,
                    message,
                    QSystemTrayIcon.Information,
                    10000  # 10 ثواني
                )
            
            # إشعار في البرنامج
            log_info(f"Focus client notification: {sender_email} - {subject}", "Focus Notification")
        
        except Exception as e:
            log_error(f"Error showing focus notification: {str(e)}", "Focus Notification")
    
    def open_tasks(self):
        """فتح نافذة إدارة المهام"""
        try:
            # إذا كان هناك عميل محدد، فتح مهامه
            client_id = None
            row = self.table.currentRow()
            if row >= 0:
                client_id = self.table.item(row, 0).data(Qt.UserRole)
            
            dlg = TasksWindow(self, client_id=client_id)
            dlg.exec_()
        except Exception as e:
            QMessageBox.critical(
                self,
                "Tasks Error",
                f"Failed to open Tasks window:\n\n{e}"
            )

    def open_buyer_search(self):
        """فتح نافذة البحث عن المشترين حسب المنتج والدول"""
        try:
            dlg = BuyerSearchWindow(self)
            dlg.exec_()
        except Exception as e:
            QMessageBox.critical(
                self,
                "Buyer Search Error",
                f"Failed to open Buyer Search window:\n\n{e}"
            )
    
    def open_importer_search(self):
        """فتح نافذة البحث عن المستوردين بناءً على اسم الشركة المصدرة"""
        try:
            dlg = ImporterSearchWindow(self)
            dlg.exec_()
            # تحديث قائمة العملاء بعد إضافة عملاء جدد
            self.load_clients()
        except Exception as e:
            QMessageBox.critical(
                self,
                "Importer Search Error",
                f"Failed to open Importer Search window:\n\n{e}"
            )
    
    def open_importer_search(self):
        """فتح نافذة البحث عن المستوردين بناءً على اسم الشركة المصدرة"""
        try:
            dlg = ImporterSearchWindow(self)
            dlg.exec_()
            # تحديث قائمة العملاء بعد إضافة عملاء جدد
            self.load_clients()
        except Exception as e:
            QMessageBox.critical(
                self,
                "Importer Search Error",
                f"Failed to open Buyer Search window:\n\n{e}"
            )

    def open_advanced_search(self):
        """فتح نافذة البحث المتقدم"""
        try:
            dlg = AdvancedSearchWindow(self)
            dlg.exec_()
        except Exception as e:
            QMessageBox.critical(
                self,
                "Advanced Search Error",
                f"Failed to open Advanced Search window:\n\n{e}"
            )
    
    def open_specialized_search(self):
        """فتح نافذة البحث المتخصص - بصل وكراث مجفف"""
        try:
            dlg = SpecializedSearchWindow(self)
            dlg.exec_()
            # تحديث قائمة العملاء بعد إضافة عملاء جدد
            self.load_clients()
        except Exception as e:
            QMessageBox.critical(
                self,
                "Specialized Search Error",
                f"Failed to open Specialized Search window:\n\n{e}"
            )

    def open_documents(self):
        """فتح نافذة إدارة المستندات"""
        try:
            # إذا كان هناك عميل محدد، فتح مستنداته
            client_id = None
            row = self.table.currentRow()
            if row >= 0:
                client_id = self.table.item(row, 0).data(Qt.UserRole)
            
            dlg = DocumentsWindow(self, client_id=client_id)
            dlg.exec_()
        except Exception as e:
            QMessageBox.critical(
                self,
                "Documents Error",
                f"Failed to open Documents window:\n\n{e}"
            )

    def open_products(self):
        """فتح نافذة إدارة المنتجات"""
        try:
            dlg = ProductsWindow(self)
            dlg.exec_()
        except Exception as e:
            QMessageBox.critical(
                self,
                "Products Error",
                f"Failed to open Products window:\n\n{e}"
            )

    def open_quotes(self):
        """فتح نافذة إدارة العروض"""
        try:
            # إذا كان هناك عميل محدد، فتح عروضه
            client_id = None
            row = self.table.currentRow()
            if row >= 0:
                client_id = self.table.item(row, 0).data(Qt.UserRole)
            
            dlg = QuotesWindow(self, client_id=client_id)
            dlg.exec_()
        except Exception as e:
            QMessageBox.critical(
                self,
                "Quotes Error",
                f"Failed to open Quotes window:\n\n{e}"
            )

    def check_scheduled_backup(self):
        """التحقق من النسخ التلقائي المجدول (يتم استدعاؤه دورياً)"""
        try:
            from core.backup import get_backup_config, should_run_auto_backup, create_backup
            from datetime import datetime
            
            config = get_backup_config()
            
            if not config.get("auto_backup_enabled", False):
                return
            
            # التحقق من الوقت المحدد
            backup_time_str = config.get("backup_time", "02:00")
            try:
                backup_hour, backup_minute = map(int, backup_time_str.split(":"))
                now = datetime.now()
                
                # التحقق من التوقيت اليومي
                if config.get("backup_frequency", "daily") == "daily":
                    # التحقق كل 10 دقائق إذا كان الوقت الحالي في نفس ساعة النسخ
                    if now.hour == backup_hour:
                        # في نفس الساعة، تحقق من النسخ كل 10 دقائق
                        if now.minute % 10 == 0:
                            # التحقق من أننا لم نقم بالنسخ اليوم
                            last_backup_str = config.get("last_backup")
                            if last_backup_str:
                                try:
                                    last_backup = datetime.fromisoformat(last_backup_str)
                                    # إذا كان آخر نسخ اليوم، لا نكرر
                                    if last_backup.date() == now.date():
                                        return
                                except (ValueError, TypeError):
                                    pass
                            
                            from core.backup import create_backup
                            create_backup("نسخ احتياطي تلقائي مجدول")
                
            except Exception:
                pass
            
            # التحقق من النسخ الأسبوعي
            if config.get("backup_frequency", "daily") == "weekly":
                if should_run_auto_backup():
                    create_backup("نسخ احتياطي أسبوعي تلقائي")
                    
        except Exception as e:
            print(f"خطأ في النسخ الاحتياطي التلقائي: {e}")
    
    def init_notifications(self):
        """تهيئة نظام الإشعارات"""
        try:
            from core.notifications import NotificationManager, set_notification_manager
            
            # إنشاء مدير الإشعارات
            self.notification_manager = NotificationManager(self)
            set_notification_manager(self.notification_manager)
            
            # Timer للتحقق من الإشعارات
            self.notification_timer = QTimer(self)
            self.notification_timer.timeout.connect(self.check_notifications)
            
            # فترة التحقق (افتراضياً 30 دقيقة)
            check_interval = self.notification_manager.get_check_interval()
            self.notification_timer.start(check_interval * 60 * 1000)  # تحويل الدقائق إلى مللي ثانية
            
            # التحقق الفوري عند بدء التشغيل (إذا كان مفعّل)
            if self.notification_manager.config.get("show_on_startup", True):
                # تأخير بسيط لإعطاء التطبيق وقت للبدء
                QTimer.singleShot(5000, self.check_notifications)  # بعد 5 ثوان
        
        except Exception as e:
            # إذا فشل تهيئة الإشعارات، لا نوقف التطبيق
            print(f"Failed to initialize notifications: {e}")
    
    def check_notifications(self):
        """التحقق من الإشعارات وعرضها"""
        if self.notification_manager:
            try:
                self.notification_manager.check_and_show_notifications()
            except Exception:
                pass  # إذا فشل، لا نوقف التطبيق

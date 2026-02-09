"""
نافذة إدارة المهام والمتابعة
Tasks and Follow-up Management Window
"""
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTableWidget, QTableWidgetItem,
    QMessageBox, QComboBox, QLineEdit, QTextEdit,
    QDateEdit, QGroupBox, QCheckBox, QTabWidget, QWidget,
    QCalendarWidget
)
from PyQt5.QtGui import QFont, QColor, QBrush, QTextCharFormat
from PyQt5.QtCore import Qt, QDate
from datetime import datetime, timedelta

from core.tasks import (
    create_task, update_task, delete_task, get_task,
    get_all_tasks, get_client_tasks, get_upcoming_tasks,
    get_overdue_tasks, get_tasks_due_today, get_reminders_due,
    complete_task, get_task_statistics,
    PRIORITIES, TASK_STATUSES, TASK_TYPES,
    PRIORITY_LOW, PRIORITY_MEDIUM, PRIORITY_HIGH, PRIORITY_URGENT,
    STATUS_PENDING, STATUS_IN_PROGRESS, STATUS_COMPLETED, STATUS_CANCELLED
)
from core.db import get_all_clients


class TasksWindow(QDialog):
    def __init__(self, parent=None, client_id=None):
        super().__init__(parent)
        self.setWindowTitle("📋 Tasks Management")
        self.setMinimumSize(1200, 700)
        
        self.client_id = client_id
        self.selected_task_id = None
        
        self.init_ui()
        self.load_tasks()
        self.update_statistics()
        self.update_calendar_highlights()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        
        # ===== Header with Statistics =====
        header_layout = QHBoxLayout()
        
        title = QLabel("📋 Tasks Management")
        title.setFont(QFont("Segoe UI", 14, QFont.Bold))
        header_layout.addWidget(title)
        header_layout.addStretch()
        
        self.stats_label = QLabel("")
        self.stats_label.setStyleSheet("color: #4ECDC4; font-weight: bold;")
        header_layout.addWidget(self.stats_label)
        
        layout.addLayout(header_layout)
        
        # ===== Filters =====
        filter_group = QGroupBox("Filters")
        filter_layout = QHBoxLayout()
        
        # Status filter
        status_label = QLabel("Status:")
        filter_layout.addWidget(status_label)
        self.status_filter = QComboBox()
        self.status_filter.addItems([
            "All", "Pending", "In Progress", "Completed", "Cancelled"
        ])
        self.status_filter.currentTextChanged.connect(self.load_tasks)
        filter_layout.addWidget(self.status_filter)
        
        # Priority filter
        priority_label = QLabel("Priority:")
        filter_layout.addWidget(priority_label)
        self.priority_filter = QComboBox()
        self.priority_filter.addItems([
            "All", "Urgent", "High", "Medium", "Low"
        ])
        self.priority_filter.currentTextChanged.connect(self.load_tasks)
        filter_layout.addWidget(self.priority_filter)
        
        # Client filter
        client_label = QLabel("Client:")
        filter_layout.addWidget(client_label)
        self.client_filter = QComboBox()
        self.client_filter.addItem("All Clients")
        clients = get_all_clients()
        for client in clients:
            self.client_filter.addItem(f"{client[1]} (ID: {client[0]})", client[0])
        if self.client_id:
            # البحث عن العميل المحدد في القائمة
            for i in range(self.client_filter.count()):
                if self.client_filter.itemData(i) == self.client_id:
                    self.client_filter.setCurrentIndex(i)
                    break
        self.client_filter.currentIndexChanged.connect(self.load_tasks)
        filter_layout.addWidget(self.client_filter)
        
        # Quick filters
        filter_layout.addStretch()
        
        overdue_btn = QPushButton("⚠️ Overdue")
        overdue_btn.clicked.connect(lambda: self.filter_overdue())
        overdue_btn.setStyleSheet("background-color: #FF6B6B; color: white; font-weight: bold; border-radius: 5px; padding: 6px;")
        filter_layout.addWidget(overdue_btn)
        
        due_today_btn = QPushButton("📅 Due Today")
        due_today_btn.clicked.connect(lambda: self.filter_due_today())
        due_today_btn.setStyleSheet("background-color: #FFD93D; color: white; font-weight: bold; border-radius: 5px; padding: 6px;")
        filter_layout.addWidget(due_today_btn)
        
        upcoming_btn = QPushButton("📆 Upcoming (7 days)")
        upcoming_btn.clicked.connect(lambda: self.filter_upcoming())
        upcoming_btn.setStyleSheet("background-color: #4ECDC4; color: white; font-weight: bold; border-radius: 5px; padding: 6px;")
        filter_layout.addWidget(upcoming_btn)
        
        filter_layout.addWidget(QLabel("|"))
        
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.clicked.connect(self.load_tasks)
        filter_layout.addWidget(refresh_btn)
        
        filter_group.setLayout(filter_layout)
        layout.addWidget(filter_group)
        
        # ===== Tabs (Table View & Calendar View) =====
        self.tabs = QTabWidget()
        
        # Tab 1: Table View
        table_widget = QWidget()
        table_layout = QVBoxLayout(table_widget)
        table_layout.setContentsMargins(0, 0, 0, 0)
        
        self.tasks_table = QTableWidget()
        self.tasks_table.setColumnCount(11)
        self.tasks_table.setHorizontalHeaderLabels([
            "ID", "Client", "Title", "Type", "Priority", "Status", 
            "Due Date", "Reminder", "Deal", "Recurrence", "Actions"
        ])
        self.tasks_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tasks_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.tasks_table.setSortingEnabled(True)
        self.tasks_table.horizontalHeader().setStretchLastSection(True)
        self.tasks_table.setAlternatingRowColors(True)
        self.tasks_table.cellDoubleClicked.connect(self.edit_selected_task)
        table_layout.addWidget(self.tasks_table)
        
        self.tabs.addTab(table_widget, "📋 قائمة المهام - Task List")
        
        # Tab 2: Calendar View
        calendar_widget = QWidget()
        calendar_layout = QVBoxLayout(calendar_widget)
        calendar_layout.setContentsMargins(10, 10, 10, 10)
        
        self.calendar = QCalendarWidget()
        self.calendar.setGridVisible(True)
        self.calendar.setMinimumDate(QDate.currentDate().addYears(-1))
        self.calendar.setMaximumDate(QDate.currentDate().addYears(1))
        self.calendar.clicked.connect(self.on_calendar_date_clicked)
        calendar_layout.addWidget(self.calendar)
        
        self.calendar_tasks_label = QLabel("المهام في اليوم المحدد:")
        self.calendar_tasks_label.setFont(QFont("Segoe UI", 10, QFont.Bold))
        calendar_layout.addWidget(self.calendar_tasks_label)
        
        self.calendar_tasks_table = QTableWidget()
        self.calendar_tasks_table.setColumnCount(5)
        self.calendar_tasks_table.setHorizontalHeaderLabels([
            "Title", "Client", "Priority", "Status", "Actions"
        ])
        self.calendar_tasks_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.calendar_tasks_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.calendar_tasks_table.horizontalHeader().setStretchLastSection(True)
        self.calendar_tasks_table.setAlternatingRowColors(True)
        self.calendar_tasks_table.cellDoubleClicked.connect(self.edit_calendar_task)
        calendar_layout.addWidget(self.calendar_tasks_table)
        
        self.tabs.addTab(calendar_widget, "📅 التقويم - Calendar")
        
        layout.addWidget(self.tabs)
        
        # Update calendar when date changes
        self.calendar.currentPageChanged.connect(self.update_calendar_highlights)
        
        # ===== Buttons =====
        buttons_layout = QHBoxLayout()
        
        add_btn = QPushButton("➕ Add Task")
        add_btn.clicked.connect(self.add_task)
        add_btn.setStyleSheet("background-color: #4ECDC4; color: white; font-weight: bold; border-radius: 5px; padding: 8px;")
        buttons_layout.addWidget(add_btn)
        
        edit_btn = QPushButton("✏️ Edit")
        edit_btn.clicked.connect(self.edit_selected_task)
        buttons_layout.addWidget(edit_btn)
        
        complete_btn = QPushButton("✅ Complete")
        complete_btn.clicked.connect(self.complete_selected_task)
        complete_btn.setStyleSheet("background-color: #2ECC71; color: white; font-weight: bold; border-radius: 5px; padding: 8px;")
        buttons_layout.addWidget(complete_btn)
        
        delete_btn = QPushButton("🗑 Delete")
        delete_btn.clicked.connect(self.delete_selected_task)
        delete_btn.setStyleSheet("background-color: #FF6B6B; color: white; font-weight: bold; border-radius: 5px; padding: 8px;")
        buttons_layout.addWidget(delete_btn)
        
        buttons_layout.addStretch()
        
        close_btn = QPushButton("❌ Close")
        close_btn.clicked.connect(self.accept)
        buttons_layout.addWidget(close_btn)
        
        layout.addLayout(buttons_layout)
    
    def load_tasks(self):
        """تحميل المهام في الجدول"""
        # الحصول على الفلاتر
        status_filter = self.status_filter.currentText().lower().replace(" ", "_")
        if status_filter == "all":
            status_filter = None
        
        priority_filter = self.priority_filter.currentText().lower()
        if priority_filter == "all":
            priority_filter = None
        
        client_id = None
        if self.client_filter.currentIndex() > 0:
            client_id = self.client_filter.currentData()
        
        # تحميل المهام
        if client_id:
            tasks = get_client_tasks(client_id, status_filter)
        else:
            tasks = get_all_tasks(status=status_filter, priority=priority_filter)
        
        # عرض المهام
        self.tasks_table.setRowCount(len(tasks))
        
        for row, task in enumerate(tasks):
            # ID
            id_item = QTableWidgetItem(str(task['id']))
            id_item.setData(Qt.UserRole, task['id'])
            self.tasks_table.setItem(row, 0, id_item)
            
            # Client
            client_item = QTableWidgetItem(task.get('company_name', 'Unknown'))
            self.tasks_table.setItem(row, 1, client_item)
            
            # Title
            title_item = QTableWidgetItem(task['title'])
            self.tasks_table.setItem(row, 2, title_item)
            
            # Type
            task_type = task['task_type']
            type_label = TASK_TYPES.get(task_type, {}).get('label', task_type)
            type_icon = TASK_TYPES.get(task_type, {}).get('icon', '📋')
            type_item = QTableWidgetItem(f"{type_icon} {type_label}")
            self.tasks_table.setItem(row, 3, type_item)
            
            # Priority
            priority = task['priority']
            priority_info = PRIORITIES.get(priority, {})
            priority_label = priority_info.get('label', priority)
            priority_icon = priority_info.get('icon', '⚪')
            priority_color = priority_info.get('color', '#95A5A6')
            priority_item = QTableWidgetItem(f"{priority_icon} {priority_label}")
            priority_item.setForeground(QBrush(QColor(priority_color)))
            self.tasks_table.setItem(row, 4, priority_item)
            
            # Status
            status = task['status']
            status_info = TASK_STATUSES.get(status, {})
            status_label = status_info.get('label', status)
            status_color = status_info.get('color', '#95A5A6')
            status_item = QTableWidgetItem(status_label)
            status_item.setForeground(QBrush(QColor(status_color)))
            self.tasks_table.setItem(row, 5, status_item)
            
            # Due Date
            due_date_item = QTableWidgetItem(task.get('due_date', ''))
            due_date_item.setTextAlignment(Qt.AlignCenter)
            self.tasks_table.setItem(row, 6, due_date_item)
            
            # تحقق من التأخير
            if status == STATUS_PENDING and task.get('due_date'):
                try:
                    due_date = datetime.strptime(task['due_date'], "%d/%m/%Y")
                    if due_date < datetime.now():
                        due_date_item.setForeground(QBrush(QColor("#FF6B6B")))
                        due_date_item.setText(f"⚠️ {task['due_date']} (OVERDUE)")
                    elif due_date.date() == datetime.now().date():
                        due_date_item.setForeground(QBrush(QColor("#FFD93D")))
                        due_date_item.setText(f"📅 {task['due_date']} (TODAY)")
                except:
                    pass
            
            # Reminder
            reminder_item = QTableWidgetItem(task.get('reminder_date', '') or 'No reminder')
            reminder_item.setTextAlignment(Qt.AlignCenter)
            self.tasks_table.setItem(row, 7, reminder_item)
            
            # Deal (if linked)
            deal_id = task.get('deal_id')
            if deal_id:
                try:
                    from core.sales import get_deal_by_id
                    deal = get_deal_by_id(deal_id)
                    if deal:
                        deal_name = deal[3] if len(deal) > 3 else f"Deal #{deal_id}"
                        deal_item = QTableWidgetItem(f"🔗 {deal_name}")
                        deal_item.setToolTip(f"Linked to Deal: {deal_name}")
                    else:
                        deal_item = QTableWidgetItem(f"🔗 Deal #{deal_id}")
                except:
                    deal_item = QTableWidgetItem(f"🔗 Deal #{deal_id}")
            else:
                deal_item = QTableWidgetItem("—")
            deal_item.setTextAlignment(Qt.AlignCenter)
            self.tasks_table.setItem(row, 8, deal_item)
            
            # Recurrence
            recurrence_pattern = task.get('recurrence_pattern')
            if recurrence_pattern and recurrence_pattern != 'none':
                interval = task.get('recurrence_interval', 1)
                if recurrence_pattern == 'daily':
                    recurrence_text = f"🔄 Daily ({interval}d)"
                elif recurrence_pattern == 'weekly':
                    recurrence_text = f"📅 Weekly ({interval}w)"
                elif recurrence_pattern == 'monthly':
                    recurrence_text = f"📆 Monthly ({interval}m)"
                else:
                    recurrence_text = f"🔄 {recurrence_pattern}"
                recurrence_item = QTableWidgetItem(recurrence_text)
                recurrence_item.setToolTip(f"Recurring: {recurrence_pattern}, Interval: {interval}")
            else:
                recurrence_item = QTableWidgetItem("—")
            recurrence_item.setTextAlignment(Qt.AlignCenter)
            self.tasks_table.setItem(row, 9, recurrence_item)
            
            # Actions
            actions_item = QTableWidgetItem("View Details")
            actions_item.setTextAlignment(Qt.AlignCenter)
            self.tasks_table.setItem(row, 10, actions_item)
            
            # تلوين الصف حسب الأولوية
            if priority == PRIORITY_URGENT:
                for col in range(11):
                    item = self.tasks_table.item(row, col)
                    if item:
                        item.setBackground(QBrush(QColor("#FFE5E5")))
            elif priority == PRIORITY_HIGH:
                for col in range(11):
                    item = self.tasks_table.item(row, col)
                    if item:
                        item.setBackground(QBrush(QColor("#FFF4CC")))
        
        self.tasks_table.resizeColumnsToContents()
    
    def update_statistics(self):
        """تحديث الإحصائيات"""
        try:
            stats = get_task_statistics()
            stats_text = (
                f"Total: {stats['total']} | "
                f"Pending: {stats['pending']} | "
                f"Overdue: {stats['overdue']} | "
                f"Due Today: {stats['due_today']} | "
                f"Upcoming (7d): {stats['upcoming_7_days']}"
            )
            self.stats_label.setText(stats_text)
        except Exception:
            pass
    
    def filter_overdue(self):
        """فلتر المهام المتأخرة"""
        self.status_filter.setCurrentText("Pending")
        tasks = get_overdue_tasks()
        self.display_tasks(tasks)
    
    def filter_due_today(self):
        """فلتر المهام المستحقة اليوم"""
        self.status_filter.setCurrentText("Pending")
        tasks = get_tasks_due_today()
        self.display_tasks(tasks)
    
    def filter_upcoming(self):
        """فلتر المهام القادمة"""
        self.status_filter.setCurrentText("Pending")
        tasks = get_upcoming_tasks(7)
        self.display_tasks(tasks)
    
    def display_tasks(self, tasks):
        """عرض قائمة مهام محددة"""
        # استخدام نفس منطق load_tasks
        self.tasks_table.setRowCount(len(tasks))
        
        for row, task in enumerate(tasks):
            # نفس الكود من load_tasks
            id_item = QTableWidgetItem(str(task['id']))
            id_item.setData(Qt.UserRole, task['id'])
            self.tasks_table.setItem(row, 0, id_item)
            
            client_item = QTableWidgetItem(task.get('company_name', 'Unknown'))
            self.tasks_table.setItem(row, 1, client_item)
            
            title_item = QTableWidgetItem(task['title'])
            self.tasks_table.setItem(row, 2, title_item)
            
            # Type
            task_type = task['task_type']
            type_label = TASK_TYPES.get(task_type, {}).get('label', task_type)
            type_icon = TASK_TYPES.get(task_type, {}).get('icon', '📋')
            type_item = QTableWidgetItem(f"{type_icon} {type_label}")
            self.tasks_table.setItem(row, 3, type_item)
            
            # Priority
            priority = task['priority']
            priority_info = PRIORITIES.get(priority, {})
            priority_label = priority_info.get('label', priority)
            priority_icon = priority_info.get('icon', '⚪')
            priority_color = priority_info.get('color', '#95A5A6')
            priority_item = QTableWidgetItem(f"{priority_icon} {priority_label}")
            priority_item.setForeground(QBrush(QColor(priority_color)))
            self.tasks_table.setItem(row, 4, priority_item)
            
            # Status
            status = task['status']
            status_info = TASK_STATUSES.get(status, {})
            status_label = status_info.get('label', status)
            status_color = status_info.get('color', '#95A5A6')
            status_item = QTableWidgetItem(status_label)
            status_item.setForeground(QBrush(QColor(status_color)))
            self.tasks_table.setItem(row, 5, status_item)
            
            # Due Date
            due_date_item = QTableWidgetItem(task.get('due_date', ''))
            due_date_item.setTextAlignment(Qt.AlignCenter)
            self.tasks_table.setItem(row, 6, due_date_item)
            
            # تحقق من التأخير
            if status == STATUS_PENDING and task.get('due_date'):
                try:
                    due_date = datetime.strptime(task['due_date'], "%d/%m/%Y")
                    if due_date < datetime.now():
                        due_date_item.setForeground(QBrush(QColor("#FF6B6B")))
                        due_date_item.setText(f"⚠️ {task['due_date']} (OVERDUE)")
                    elif due_date.date() == datetime.now().date():
                        due_date_item.setForeground(QBrush(QColor("#FFD93D")))
                        due_date_item.setText(f"📅 {task['due_date']} (TODAY)")
                except:
                    pass
            
            # Reminder
            reminder_item = QTableWidgetItem(task.get('reminder_date', '') or 'No reminder')
            reminder_item.setTextAlignment(Qt.AlignCenter)
            self.tasks_table.setItem(row, 7, reminder_item)
            
            # Deal (if linked)
            deal_id = task.get('deal_id')
            if deal_id:
                try:
                    from core.sales import get_deal_by_id
                    deal = get_deal_by_id(deal_id)
                    if deal:
                        deal_name = deal[3] if len(deal) > 3 else f"Deal #{deal_id}"
                        deal_item = QTableWidgetItem(f"🔗 {deal_name}")
                        deal_item.setToolTip(f"Linked to Deal: {deal_name}")
                    else:
                        deal_item = QTableWidgetItem(f"🔗 Deal #{deal_id}")
                except:
                    deal_item = QTableWidgetItem(f"🔗 Deal #{deal_id}")
            else:
                deal_item = QTableWidgetItem("—")
            deal_item.setTextAlignment(Qt.AlignCenter)
            self.tasks_table.setItem(row, 8, deal_item)
            
            # Recurrence
            recurrence_pattern = task.get('recurrence_pattern')
            if recurrence_pattern and recurrence_pattern != 'none':
                interval = task.get('recurrence_interval', 1)
                if recurrence_pattern == 'daily':
                    recurrence_text = f"🔄 Daily ({interval}d)"
                elif recurrence_pattern == 'weekly':
                    recurrence_text = f"📅 Weekly ({interval}w)"
                elif recurrence_pattern == 'monthly':
                    recurrence_text = f"📆 Monthly ({interval}m)"
                else:
                    recurrence_text = f"🔄 {recurrence_pattern}"
                recurrence_item = QTableWidgetItem(recurrence_text)
                recurrence_item.setToolTip(f"Recurring: {recurrence_pattern}, Interval: {interval}")
            else:
                recurrence_item = QTableWidgetItem("—")
            recurrence_item.setTextAlignment(Qt.AlignCenter)
            self.tasks_table.setItem(row, 9, recurrence_item)
            
            # Actions
            actions_item = QTableWidgetItem("View Details")
            actions_item.setTextAlignment(Qt.AlignCenter)
            self.tasks_table.setItem(row, 10, actions_item)
            
            # تلوين الصف حسب الأولوية
            if priority == PRIORITY_URGENT:
                for col in range(11):
                    item = self.tasks_table.item(row, col)
                    if item:
                        item.setBackground(QBrush(QColor("#FFE5E5")))
            elif priority == PRIORITY_HIGH:
                for col in range(11):
                    item = self.tasks_table.item(row, col)
                    if item:
                        item.setBackground(QBrush(QColor("#FFF4CC")))
        
        self.tasks_table.resizeColumnsToContents()
        self.update_statistics()
    
    def add_task(self):
        """إضافة مهمة جديدة"""
        from ui.task_edit_dialog import TaskEditDialog
        
        dialog = TaskEditDialog(self, client_id=self.client_id)
        if dialog.exec_() == QDialog.Accepted:
            self.load_tasks()
            self.update_statistics()
            self.update_calendar_highlights()
    
    def edit_selected_task(self):
        """تعديل المهمة المحددة"""
        row = self.tasks_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Select Task", "Please select a task first.")
            return
        
        task_id_item = self.tasks_table.item(row, 0)
        if not task_id_item:
            return
        
        task_id = task_id_item.data(Qt.UserRole)
        
        from ui.task_edit_dialog import TaskEditDialog
        dialog = TaskEditDialog(self, task_id=task_id)
        if dialog.exec_() == QDialog.Accepted:
            self.load_tasks()
            self.update_statistics()
            self.update_calendar_highlights()
    
    def complete_selected_task(self):
        """إكمال المهمة المحددة"""
        row = self.tasks_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Select Task", "Please select a task first.")
            return
        
        task_id_item = self.tasks_table.item(row, 0)
        if not task_id_item:
            return
        
        task_id = task_id_item.data(Qt.UserRole)
        
        reply = QMessageBox.question(
            self,
            "Complete Task",
            "Mark this task as completed?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes
        )
        
        if reply == QMessageBox.Yes:
            complete_task(task_id)
            self.load_tasks()
            self.update_statistics()
            self.update_calendar_highlights()
            QMessageBox.information(self, "Success", "Task marked as completed!")
    
    def delete_selected_task(self):
        """حذف المهمة المحددة"""
        row = self.tasks_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Select Task", "Please select a task first.")
            return
        
        task_id_item = self.tasks_table.item(row, 0)
        if not task_id_item:
            return
        
        task_id = task_id_item.data(Qt.UserRole)
        task_title = self.tasks_table.item(row, 2).text()
        
        reply = QMessageBox.question(
            self,
            "Delete Task",
            f"Delete task '{task_title}'?\nThis action cannot be undone.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            delete_task(task_id)
            self.load_tasks()
            self.update_statistics()
            self.update_calendar_highlights()
            QMessageBox.information(self, "Success", "Task deleted successfully!")
    
    def on_calendar_date_clicked(self, date):
        """عند النقر على تاريخ في التقويم"""
        self.update_calendar_tasks_for_date(date)
    
    def update_calendar_tasks_for_date(self, date):
        """تحديث قائمة المهام للتاريخ المحدد"""
        date_str = date.toString("dd/MM/yyyy")
        
        # الحصول على جميع المهام
        tasks = get_all_tasks()
        
        # تصفية المهام للتاريخ المحدد
        tasks_for_date = []
        for task in tasks:
            if task.get('due_date') == date_str or task.get('reminder_date') == date_str:
                tasks_for_date.append(task)
        
        # عرض المهام
        self.calendar_tasks_table.setRowCount(len(tasks_for_date))
        for row, task in enumerate(tasks_for_date):
            # Title
            title_item = QTableWidgetItem(task['title'])
            self.calendar_tasks_table.setItem(row, 0, title_item)
            
            # Client
            client_item = QTableWidgetItem(task.get('company_name', 'Unknown'))
            self.calendar_tasks_table.setItem(row, 1, client_item)
            
            # Priority
            priority = task['priority']
            priority_info = PRIORITIES.get(priority, {})
            priority_label = priority_info.get('label', priority)
            priority_icon = priority_info.get('icon', '⚪')
            priority_color = priority_info.get('color', '#95A5A6')
            priority_item = QTableWidgetItem(f"{priority_icon} {priority_label}")
            priority_item.setForeground(QBrush(QColor(priority_color)))
            self.calendar_tasks_table.setItem(row, 2, priority_item)
            
            # Status
            status = task['status']
            status_info = TASK_STATUSES.get(status, {})
            status_label = status_info.get('label', status)
            status_color = status_info.get('color', '#95A5A6')
            status_item = QTableWidgetItem(status_label)
            status_item.setForeground(QBrush(QColor(status_color)))
            self.calendar_tasks_table.setItem(row, 3, status_item)
            
            # Actions
            actions_item = QTableWidgetItem("View/Edit")
            actions_item.setData(Qt.UserRole, task['id'])
            self.calendar_tasks_table.setItem(row, 4, actions_item)
        
        self.calendar_tasks_table.resizeColumnsToContents()
        
        # تحديث النص
        if tasks_for_date:
            self.calendar_tasks_label.setText(f"المهام في {date_str}: {len(tasks_for_date)} مهمة")
        else:
            self.calendar_tasks_label.setText(f"لا توجد مهام في {date_str}")
    
    def edit_calendar_task(self, row, col):
        """تعديل مهمة من التقويم"""
        task_id_item = self.calendar_tasks_table.item(row, 4)
        if not task_id_item:
            return
        
        task_id = task_id_item.data(Qt.UserRole)
        if not task_id:
            return
        
        from ui.task_edit_dialog import TaskEditDialog
        dialog = TaskEditDialog(self, task_id=task_id)
        if dialog.exec_() == QDialog.Accepted:
            self.load_tasks()
            self.update_statistics()
            self.update_calendar_highlights()
            self.update_calendar_tasks_for_date(self.calendar.selectedDate())
    
    def update_calendar_highlights(self):
        """تحديث تمييز التواريخ في التقويم"""
        try:
            # الحصول على جميع المهام
            tasks = get_all_tasks()
            
            # إنشاء قاموس للتواريخ
            date_format = "%d/%m/%Y"
            
            # تنسيق للأيام المستحقة (أصفر)
            due_format = QTextCharFormat()
            due_format.setBackground(QBrush(QColor("#FFD93D")))
            due_format.setForeground(QBrush(QColor("#000000")))
            
            # تنسيق للأيام المتأخرة (أحمر)
            overdue_format = QTextCharFormat()
            overdue_format.setBackground(QBrush(QColor("#FF6B6B")))
            overdue_format.setForeground(QBrush(QColor("#FFFFFF")))
            
            # تنسيق للأيام المكتملة (أخضر)
            completed_format = QTextCharFormat()
            completed_format.setBackground(QBrush(QColor("#2ECC71")))
            completed_format.setForeground(QBrush(QColor("#FFFFFF")))
            
            today = datetime.now().date()
            
            for task in tasks:
                if not task.get('due_date'):
                    continue
                
                try:
                    task_date = datetime.strptime(task['due_date'], date_format).date()
                    qdate = QDate(task_date.year, task_date.month, task_date.day)
                    
                    status = task.get('status', '')
                    
                    if status == STATUS_COMPLETED:
                        self.calendar.setDateTextFormat(qdate, completed_format)
                    elif task_date < today:
                        self.calendar.setDateTextFormat(qdate, overdue_format)
                    else:
                        self.calendar.setDateTextFormat(qdate, due_format)
                except:
                    pass
            
            # تحديث المهام للتاريخ المحدد
            self.update_calendar_tasks_for_date(self.calendar.selectedDate())
        except Exception as e:
            pass

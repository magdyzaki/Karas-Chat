"""
نافذة إضافة/تعديل مهمة
Task Add/Edit Dialog
"""
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QTextEdit, QComboBox,
    QDateEdit, QMessageBox, QGroupBox, QFormLayout, QSpinBox
)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt, QDate
from datetime import datetime, timedelta

from core.tasks import (
    create_task, update_task, get_task,
    PRIORITIES, TASK_STATUSES, TASK_TYPES,
    PRIORITY_LOW, PRIORITY_MEDIUM, PRIORITY_HIGH, PRIORITY_URGENT,
    STATUS_PENDING, STATUS_IN_PROGRESS, STATUS_COMPLETED
)
from core.db import get_all_clients
from core.sales import get_all_deals
from core.db import get_all_clients, get_client_by_id


class TaskEditDialog(QDialog):
    def __init__(self, parent=None, task_id=None, client_id=None):
        super().__init__(parent)
        
        self.task_id = task_id
        self.is_edit_mode = task_id is not None
        
        if self.is_edit_mode:
            self.setWindowTitle("✏️ Edit Task")
        else:
            self.setWindowTitle("➕ Add New Task")
        
        self.setMinimumSize(600, 600)
        
        self.init_ui()
        
        if self.is_edit_mode:
            self.load_task_data()
        elif client_id:
            # تحديد العميل إذا تم تمريره
            for i in range(self.client_combo.count()):
                if self.client_combo.itemData(i) == client_id:
                    self.client_combo.setCurrentIndex(i)
                    break
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # ===== Client Selection =====
        client_group = QGroupBox("Client")
        client_layout = QFormLayout()
        
        self.client_combo = QComboBox()
        self.client_combo.addItem("-- Select Client --", None)
        clients = get_all_clients()
        for client in clients:
            self.client_combo.addItem(f"{client[1]} ({client[2] or 'N/A'})", client[0])
        
        client_layout.addRow("Client:", self.client_combo)
        client_group.setLayout(client_layout)
        layout.addWidget(client_group)
        
        # ===== Task Details =====
        details_group = QGroupBox("Task Details")
        details_layout = QFormLayout()
        
        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText("Enter task title...")
        details_layout.addRow("Title *:", self.title_edit)
        
        self.description_edit = QTextEdit()
        self.description_edit.setPlaceholderText("Enter task description...")
        self.description_edit.setMaximumHeight(100)
        details_layout.addRow("Description:", self.description_edit)
        
        self.type_combo = QComboBox()
        for task_type, info in TASK_TYPES.items():
            self.type_combo.addItem(f"{info['icon']} {info['label']}", task_type)
        details_layout.addRow("Type:", self.type_combo)
        
        details_group.setLayout(details_layout)
        layout.addWidget(details_group)
        
        # ===== Priority and Status =====
        priority_group = QGroupBox("Priority & Status")
        priority_layout = QFormLayout()
        
        self.priority_combo = QComboBox()
        self.priority_combo.addItem(f"{PRIORITIES[PRIORITY_LOW]['icon']} {PRIORITIES[PRIORITY_LOW]['label']}", PRIORITY_LOW)
        self.priority_combo.addItem(f"{PRIORITIES[PRIORITY_MEDIUM]['icon']} {PRIORITIES[PRIORITY_MEDIUM]['label']}", PRIORITY_MEDIUM)
        self.priority_combo.addItem(f"{PRIORITIES[PRIORITY_HIGH]['icon']} {PRIORITIES[PRIORITY_HIGH]['label']}", PRIORITY_HIGH)
        self.priority_combo.addItem(f"{PRIORITIES[PRIORITY_URGENT]['icon']} {PRIORITIES[PRIORITY_URGENT]['label']}", PRIORITY_URGENT)
        self.priority_combo.setCurrentIndex(1)  # Default: Medium
        priority_layout.addRow("Priority:", self.priority_combo)
        
        self.status_combo = QComboBox()
        self.status_combo.addItem(TASK_STATUSES[STATUS_PENDING]['label'], STATUS_PENDING)
        self.status_combo.addItem(TASK_STATUSES[STATUS_IN_PROGRESS]['label'], STATUS_IN_PROGRESS)
        if self.is_edit_mode:
            self.status_combo.addItem(TASK_STATUSES[STATUS_COMPLETED]['label'], STATUS_COMPLETED)
        priority_layout.addRow("Status:", self.status_combo)
        
        priority_group.setLayout(priority_layout)
        layout.addWidget(priority_group)
        
        # ===== Dates =====
        dates_group = QGroupBox("Dates")
        dates_layout = QFormLayout()
        
        self.due_date_edit = QDateEdit()
        self.due_date_edit.setCalendarPopup(True)
        self.due_date_edit.setDate(QDate.currentDate().addDays(7))
        self.due_date_edit.setDisplayFormat("dd/MM/yyyy")
        dates_layout.addRow("Due Date *:", self.due_date_edit)
        
        self.reminder_date_edit = QDateEdit()
        self.reminder_date_edit.setCalendarPopup(True)
        self.reminder_date_edit.setDate(QDate.currentDate().addDays(6))
        self.reminder_date_edit.setDisplayFormat("dd/MM/yyyy")
        self.reminder_date_edit.setEnabled(True)
        dates_layout.addRow("Reminder Date:", self.reminder_date_edit)
        
        dates_group.setLayout(dates_layout)
        layout.addWidget(dates_group)
        
        # ===== Advanced Options =====
        advanced_group = QGroupBox("⚙️ Advanced Options")
        advanced_layout = QFormLayout()
        
        # Link to Deal
        self.deal_combo = QComboBox()
        self.deal_combo.addItem("-- None (No Deal) --", None)
        try:
            from core.sales import get_all_deals
            deals = get_all_deals()
            for deal in deals:
                deal_id, client_id, deal_name, product_name, stage, value, currency = deal[:7]
                display_text = f"{deal_name}"
                if product_name:
                    display_text += f" - {product_name}"
                display_text += f" ({stage})"
                self.deal_combo.addItem(display_text, deal_id)
        except:
            pass
        advanced_layout.addRow("🔗 Link to Deal:", self.deal_combo)
        
        # Recurrence
        self.recurrence_combo = QComboBox()
        self.recurrence_combo.addItem("None (One-time)", "none")
        self.recurrence_combo.addItem("🔄 Daily", "daily")
        self.recurrence_combo.addItem("📅 Weekly", "weekly")
        self.recurrence_combo.addItem("📆 Monthly", "monthly")
        advanced_layout.addRow("🔄 Recurrence:", self.recurrence_combo)
        
        self.recurrence_interval_spin = QSpinBox()
        self.recurrence_interval_spin.setRange(1, 365)
        self.recurrence_interval_spin.setValue(1)
        self.recurrence_interval_spin.setEnabled(False)
        self.recurrence_combo.currentTextChanged.connect(
            lambda: self.recurrence_interval_spin.setEnabled(self.recurrence_combo.currentData() != "none")
        )
        advanced_layout.addRow("Interval (days):", self.recurrence_interval_spin)
        
        advanced_group.setLayout(advanced_layout)
        layout.addWidget(advanced_group)
        
        # ===== Notes =====
        notes_group = QGroupBox("Additional Notes")
        notes_layout = QVBoxLayout()
        
        self.notes_edit = QTextEdit()
        self.notes_edit.setPlaceholderText("Add any additional notes or comments...")
        self.notes_edit.setMaximumHeight(80)
        notes_layout.addWidget(self.notes_edit)
        notes_group.setLayout(notes_layout)
        layout.addWidget(notes_group)
        
        # ===== Buttons =====
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        
        save_btn = QPushButton("💾 Save")
        save_btn.clicked.connect(self.save_task)
        save_btn.setStyleSheet("background-color: #4ECDC4; color: white; font-weight: bold; border-radius: 5px; padding: 8px 20px;")
        buttons_layout.addWidget(save_btn)
        
        cancel_btn = QPushButton("❌ Cancel")
        cancel_btn.clicked.connect(self.reject)
        cancel_btn.setStyleSheet("background-color: #95A5A6; color: white; border-radius: 5px; padding: 8px 20px;")
        buttons_layout.addWidget(cancel_btn)
        
        layout.addLayout(buttons_layout)
    
    def load_task_data(self):
        """تحميل بيانات المهمة للتعديل"""
        if not self.task_id:
            return
        
        task = get_task(self.task_id)
        if not task:
            QMessageBox.warning(self, "Error", "Task not found.")
            self.reject()
            return
        
        # Task fields: id, client_id, title, description, task_type, priority, status, 
        # due_date, reminder_date, completed_date, created_at, updated_at, notes
        
        # Client
        client_id = task[1]
        for i in range(self.client_combo.count()):
            if self.client_combo.itemData(i) == client_id:
                self.client_combo.setCurrentIndex(i)
                break
        
        # Title
        self.title_edit.setText(task[2] or "")
        
        # Description
        self.description_edit.setPlainText(task[3] or "")
        
        # Type
        task_type = task[4] or "followup"
        for i in range(self.type_combo.count()):
            if self.type_combo.itemData(i) == task_type:
                self.type_combo.setCurrentIndex(i)
                break
        
        # Priority
        priority = task[5] or PRIORITY_MEDIUM
        for i in range(self.priority_combo.count()):
            if self.priority_combo.itemData(i) == priority:
                self.priority_combo.setCurrentIndex(i)
                break
        
        # Status
        status = task[6] or STATUS_PENDING
        for i in range(self.status_combo.count()):
            if self.status_combo.itemData(i) == status:
                self.status_combo.setCurrentIndex(i)
                break
        
        # Due Date
        due_date_str = task[7]
        if due_date_str:
            try:
                due_date = datetime.strptime(due_date_str, "%d/%m/%Y")
                self.due_date_edit.setDate(QDate(due_date.year, due_date.month, due_date.day))
            except:
                pass
        
        # Reminder Date
        reminder_date_str = task[8]
        if reminder_date_str:
            try:
                # قد يكون التاريخ بصيغة مختلفة
                if len(reminder_date_str) == 10:
                    reminder_date = datetime.strptime(reminder_date_str, "%d/%m/%Y")
                    self.reminder_date_edit.setDate(QDate(reminder_date.year, reminder_date.month, reminder_date.day))
                else:
                    reminder_date = datetime.strptime(reminder_date_str, "%Y-%m-%d %H:%M:%S")
                    self.reminder_date_edit.setDate(QDate(reminder_date.year, reminder_date.month, reminder_date.day))
            except:
                pass
        
        # Notes
        self.notes_edit.setPlainText(task[12] if len(task) > 12 else "")
        
        # Deal ID (if exists)
        if len(task) > 13 and task[13]:
            deal_id = task[13]
            for i in range(self.deal_combo.count()):
                if self.deal_combo.itemData(i) == deal_id:
                    self.deal_combo.setCurrentIndex(i)
                    break
        
        # Recurrence (if exists)
        if len(task) > 14 and task[14]:
            recurrence_pattern = task[14]
            for i in range(self.recurrence_combo.count()):
                if self.recurrence_combo.itemData(i) == recurrence_pattern:
                    self.recurrence_combo.setCurrentIndex(i)
                    break
        
        # Recurrence Interval (if exists)
        if len(task) > 15 and task[15]:
            self.recurrence_interval_spin.setValue(task[15])
            if task[14] and task[14] != "none":
                self.recurrence_interval_spin.setEnabled(True)
    
    def save_task(self):
        """حفظ المهمة"""
        # التحقق من البيانات المطلوبة
        if not self.title_edit.text().strip():
            QMessageBox.warning(self, "Validation Error", "Please enter a task title.")
            return
        
        client_id = self.client_combo.currentData()
        if not client_id:
            QMessageBox.warning(self, "Validation Error", "Please select a client.")
            return
        
        # جمع البيانات
        title = self.title_edit.text().strip()
        description = self.description_edit.toPlainText().strip()
        task_type = self.type_combo.currentData()
        priority = self.priority_combo.currentData()
        status = self.status_combo.currentData()
        
        # تحويل التاريخ من QDate إلى string
        due_date_qdate = self.due_date_edit.date()
        due_date = f"{due_date_qdate.day():02d}/{due_date_qdate.month():02d}/{due_date_qdate.year()}"
        
        reminder_date = None
        if self.reminder_date_edit.isEnabled():
            reminder_date_qdate = self.reminder_date_edit.date()
            reminder_date = f"{reminder_date_qdate.day():02d}/{reminder_date_qdate.month():02d}/{reminder_date_qdate.year()}"
        
        notes = self.notes_edit.toPlainText().strip()
        
        # Advanced options
        deal_id = self.deal_combo.currentData()
        recurrence_pattern = self.recurrence_combo.currentData()
        recurrence_interval = self.recurrence_interval_spin.value() if recurrence_pattern != "none" else None
        
        try:
            if self.is_edit_mode:
                # تحديث المهمة
                update_task(
                    task_id=self.task_id,
                    title=title,
                    description=description,
                    task_type=task_type,
                    priority=priority,
                    status=status,
                    due_date=due_date,
                    reminder_date=reminder_date,
                    notes=notes,
                    deal_id=deal_id,
                    recurrence_pattern=recurrence_pattern,
                    recurrence_interval=recurrence_interval
                )
                QMessageBox.information(self, "Success", "Task updated successfully!")
            else:
                # إنشاء مهمة جديدة
                create_task(
                    client_id=client_id,
                    title=title,
                    description=description,
                    task_type=task_type,
                    priority=priority,
                    due_date=due_date,
                    reminder_date=reminder_date,
                    notes=notes,
                    deal_id=deal_id,
                    recurrence_pattern=recurrence_pattern,
                    recurrence_interval=recurrence_interval
                )
                QMessageBox.information(self, "Success", "Task created successfully!")
            
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save task:\n{str(e)}")

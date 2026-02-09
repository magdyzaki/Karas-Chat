"""
نافذة الإعدادات العامة
General Settings Window
"""
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGroupBox, QColorDialog, QLineEdit, QComboBox, QSpinBox,
    QCheckBox, QTabWidget, QWidget, QMessageBox, QTimeEdit, QDateTimeEdit
)
from PyQt5.QtGui import QColor, QFont, QPalette
from PyQt5.QtCore import Qt, QTime

from core.settings import (
    load_settings, save_settings, get_setting, set_setting,
    reset_settings, DEFAULT_SETTINGS
)
from core.theme import get_theme_manager
from core.performance import optimize_database


class SettingsWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setWindowTitle("⚙️ الإعدادات العامة - General Settings")
        self.setMinimumSize(700, 600)
        
        self.settings = load_settings()
        self.color_buttons = {}
        
        self.init_ui()
        self.load_current_settings()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Tabs
        tabs = QTabWidget()
        
        # Tab 1: Dashboard Settings
        dashboard_tab = self.create_dashboard_tab()
        tabs.addTab(dashboard_tab, "📊 لوحة التحكم")
        
        # Tab 2: Notifications Settings
        notifications_tab = self.create_notifications_tab()
        tabs.addTab(notifications_tab, "🔔 الإشعارات")
        
        # Tab 3: UI Settings
        ui_tab = self.create_ui_tab()
        tabs.addTab(ui_tab, "🎨 الواجهة")
        
        # Tab 4: General Settings
        general_tab = self.create_general_tab()
        tabs.addTab(general_tab, "⚙️ عام")
        
        layout.addWidget(tabs)
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        reset_btn = QPushButton("🔄 إعادة تعيين")
        reset_btn.clicked.connect(self.reset_all_settings)
        btn_layout.addWidget(reset_btn)
        
        btn_layout.addStretch()
        
        cancel_btn = QPushButton("إلغاء")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        save_btn = QPushButton("💾 حفظ")
        save_btn.setStyleSheet("background-color: #4ECDC4; color: white; font-weight: bold; padding: 8px;")
        save_btn.clicked.connect(self.save_all_settings)
        btn_layout.addWidget(save_btn)
        
        layout.addLayout(btn_layout)
    
    def create_dashboard_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Colors Group
        colors_group = QGroupBox("🎨 ألوان البطاقات الإحصائية")
        colors_layout = QVBoxLayout()
        
        color_labels = {
            'total_clients': '👥 إجمالي العملاء',
            'serious_clients': '🔥 عملاء جادون',
            'potential_clients': '👍 عملاء محتملون',
            'focus_clients': '⭐ عملاء مميزون',
            'total_messages': '✉️ إجمالي الرسائل',
            'pending_requests': '📋 طلبات معلقة',
            'pending_tasks': '📝 مهام معلقة',
            'active_deals': '💰 صفقات نشطة'
        }
        
        for key, label in color_labels.items():
            row = QHBoxLayout()
            
            label_widget = QLabel(label)
            label_widget.setMinimumWidth(150)
            row.addWidget(label_widget)
            
            color_btn = QPushButton()
            color_btn.setMinimumWidth(100)
            color_btn.setMinimumHeight(30)
            color_btn.clicked.connect(lambda checked, k=key: self.choose_color(k))
            self.color_buttons[key] = color_btn
            row.addWidget(color_btn)
            
            colors_layout.addLayout(row)
        
        colors_group.setLayout(colors_layout)
        layout.addWidget(colors_group)
        
        # Other Dashboard Settings
        other_group = QGroupBox("إعدادات أخرى")
        other_layout = QVBoxLayout()
        
        self.show_actions_check = QCheckBox("عرض قائمة الإجراءات المطلوبة")
        other_layout.addWidget(self.show_actions_check)
        
        actions_height_layout = QHBoxLayout()
        actions_height_layout.addWidget(QLabel("الحد الأقصى لارتفاع قائمة الإجراءات:"))
        self.actions_height_spin = QSpinBox()
        self.actions_height_spin.setRange(50, 200)
        self.actions_height_spin.setSuffix(" px")
        actions_height_layout.addWidget(self.actions_height_spin)
        actions_height_layout.addStretch()
        other_layout.addLayout(actions_height_layout)
        
        other_group.setLayout(other_layout)
        layout.addWidget(other_group)
        
        layout.addStretch()
        return widget
    
    def create_notifications_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Enable Notifications
        self.notifications_enabled_check = QCheckBox("تفعيل الإشعارات")
        layout.addWidget(self.notifications_enabled_check)
        
        # Check Interval
        interval_layout = QHBoxLayout()
        interval_layout.addWidget(QLabel("فترة التحقق من الإشعارات:"))
        self.check_interval_spin = QSpinBox()
        self.check_interval_spin.setRange(60, 3600)
        self.check_interval_spin.setSuffix(" ثانية")
        interval_layout.addWidget(self.check_interval_spin)
        interval_layout.addStretch()
        layout.addLayout(interval_layout)
        
        # Notification Types
        types_group = QGroupBox("أنواع الإشعارات")
        types_layout = QVBoxLayout()
        
        self.followup_check = QCheckBox("إشعارات العملاء الذين يحتاجون متابعة")
        types_layout.addWidget(self.followup_check)
        
        self.requests_check = QCheckBox("إشعارات الطلبات المعلقة")
        types_layout.addWidget(self.requests_check)
        
        self.tasks_check = QCheckBox("إشعارات المهام المعلقة")
        types_layout.addWidget(self.tasks_check)
        
        self.deals_check = QCheckBox("إشعارات الصفقات القريبة من الإغلاق")
        types_layout.addWidget(self.deals_check)
        
        types_group.setLayout(types_layout)
        layout.addWidget(types_group)
        
        layout.addStretch()
        return widget
    
    def create_ui_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Language
        lang_layout = QHBoxLayout()
        lang_layout.addWidget(QLabel("اللغة:"))
        self.language_combo = QComboBox()
        self.language_combo.addItems(["العربية", "English"])
        lang_layout.addWidget(self.language_combo)
        lang_layout.addStretch()
        layout.addLayout(lang_layout)
        
        # Theme
        theme_layout = QHBoxLayout()
        theme_layout.addWidget(QLabel("المظهر:"))
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["فاتح", "داكن"])
        theme_layout.addWidget(self.theme_combo)
        theme_layout.addStretch()
        layout.addLayout(theme_layout)
        
        # Font Size
        font_layout = QHBoxLayout()
        font_layout.addWidget(QLabel("حجم الخط:"))
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(8, 16)
        self.font_size_spin.setSuffix(" px")
        font_layout.addWidget(self.font_size_spin)
        font_layout.addStretch()
        layout.addLayout(font_layout)
        
        layout.addStretch()
        return widget
    
    def create_general_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Auto Backup
        backup_group = QGroupBox("النسخ الاحتياطي التلقائي")
        backup_layout = QVBoxLayout()
        
        self.auto_backup_check = QCheckBox("تفعيل النسخ الاحتياطي التلقائي")
        backup_layout.addWidget(self.auto_backup_check)
        
        frequency_layout = QHBoxLayout()
        frequency_layout.addWidget(QLabel("التكرار:"))
        self.backup_frequency_combo = QComboBox()
        self.backup_frequency_combo.addItems(["يومي", "أسبوعي"])
        frequency_layout.addWidget(self.backup_frequency_combo)
        frequency_layout.addStretch()
        backup_layout.addLayout(frequency_layout)
        
        time_layout = QHBoxLayout()
        time_layout.addWidget(QLabel("الوقت:"))
        self.backup_time_edit = QTimeEdit()
        self.backup_time_edit.setDisplayFormat("HH:mm")
        time_layout.addWidget(self.backup_time_edit)
        time_layout.addStretch()
        backup_layout.addLayout(time_layout)
        
        backup_group.setLayout(backup_layout)
        layout.addWidget(backup_group)
        
        # Database Optimization
        optimize_group = QGroupBox("تحسين قاعدة البيانات")
        optimize_layout = QVBoxLayout()
        
        optimize_btn = QPushButton("⚡ تحسين قاعدة البيانات")
        optimize_btn.setToolTip("تحسين الأداء وإعادة تنظيم قاعدة البيانات")
        optimize_btn.clicked.connect(self.optimize_database)
        optimize_layout.addWidget(optimize_btn)
        
        optimize_group.setLayout(optimize_layout)
        layout.addWidget(optimize_group)
        
        layout.addStretch()
        return widget
    
    def optimize_database(self):
        """تحسين قاعدة البيانات"""
        reply = QMessageBox.question(
            self,
            "تحسين قاعدة البيانات",
            "هل تريد تحسين قاعدة البيانات الآن؟\n"
            "سيتم إعادة تنظيم قاعدة البيانات وتحسين الأداء.\n"
            "قد يستغرق هذا بعض الوقت...",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes
        )
        
        if reply == QMessageBox.Yes:
            try:
                optimize_database()
                QMessageBox.information(
                    self,
                    "نجح",
                    "تم تحسين قاعدة البيانات بنجاح! ✅"
                )
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "خطأ",
                    f"فشل تحسين قاعدة البيانات:\n{str(e)}"
                )
    
    def load_current_settings(self):
        """تحميل الإعدادات الحالية"""
        # Dashboard colors
        colors = self.settings.get('dashboard', {}).get('colors', {})
        for key, button in self.color_buttons.items():
            color = colors.get(key, DEFAULT_SETTINGS['dashboard']['colors'][key])
            button.setStyleSheet(f"background-color: {color}; border: 2px solid #333; border-radius: 5px;")
            button.setText(color)
        
        # Dashboard other
        self.show_actions_check.setChecked(
            self.settings.get('dashboard', {}).get('show_actions', True)
        )
        self.actions_height_spin.setValue(
            self.settings.get('dashboard', {}).get('actions_max_height', 95)
        )
        
        # Notifications
        notif_settings = self.settings.get('notifications', {})
        self.notifications_enabled_check.setChecked(notif_settings.get('enabled', True))
        self.check_interval_spin.setValue(notif_settings.get('check_interval', 300))
        self.followup_check.setChecked(notif_settings.get('followup_clients', True))
        self.requests_check.setChecked(notif_settings.get('pending_requests', True))
        self.tasks_check.setChecked(notif_settings.get('pending_tasks', True))
        self.deals_check.setChecked(notif_settings.get('deals_closing', True))
        
        # UI
        ui_settings = self.settings.get('ui', {})
        lang = ui_settings.get('language', 'ar')
        self.language_combo.setCurrentIndex(0 if lang == 'ar' else 1)
        theme = ui_settings.get('theme', 'light')
        self.theme_combo.setCurrentIndex(0 if theme == 'light' else 1)
        self.font_size_spin.setValue(ui_settings.get('font_size', 10))
        
        # General
        general_settings = self.settings.get('general', {})
        self.auto_backup_check.setChecked(general_settings.get('auto_backup', True))
        freq = general_settings.get('backup_frequency', 'daily')
        self.backup_frequency_combo.setCurrentIndex(0 if freq == 'daily' else 1)
        time_str = general_settings.get('backup_time', '02:00')
        hour, minute = map(int, time_str.split(':'))
        self.backup_time_edit.setTime(QTime(hour, minute))
    
    def choose_color(self, key):
        """اختيار لون للبطاقة"""
        current_color = self.settings.get('dashboard', {}).get('colors', {}).get(key, DEFAULT_SETTINGS['dashboard']['colors'][key])
        color = QColorDialog.getColor(QColor(current_color), self, f"اختر لون {key}")
        
        if color.isValid():
            color_str = color.name()
            button = self.color_buttons[key]
            button.setStyleSheet(f"background-color: {color_str}; border: 2px solid #333; border-radius: 5px;")
            button.setText(color_str)
    
    def save_all_settings(self):
        """حفظ جميع الإعدادات"""
        # Dashboard
        dashboard_colors = {}
        for key, button in self.color_buttons.items():
            color = button.text()
            dashboard_colors[key] = color
        
        self.settings['dashboard'] = {
            'colors': dashboard_colors,
            'show_actions': self.show_actions_check.isChecked(),
            'actions_max_height': self.actions_height_spin.value()
        }
        
        # Notifications
        self.settings['notifications'] = {
            'enabled': self.notifications_enabled_check.isChecked(),
            'check_interval': self.check_interval_spin.value(),
            'followup_clients': self.followup_check.isChecked(),
            'pending_requests': self.requests_check.isChecked(),
            'pending_tasks': self.tasks_check.isChecked(),
            'deals_closing': self.deals_check.isChecked()
        }
        
        # UI
        self.settings['ui'] = {
            'language': 'ar' if self.language_combo.currentIndex() == 0 else 'en',
            'theme': 'light' if self.theme_combo.currentIndex() == 0 else 'dark',
            'font_size': self.font_size_spin.value()
        }
        
        # General
        time = self.backup_time_edit.time()
        self.settings['general'] = {
            'auto_backup': self.auto_backup_check.isChecked(),
            'backup_frequency': 'daily' if self.backup_frequency_combo.currentIndex() == 0 else 'weekly',
            'backup_time': f"{time.hour():02d}:{time.minute():02d}"
        }
        
        save_settings(self.settings)
        
        # Apply theme immediately if changed
        theme_manager = get_theme_manager()
        new_theme = 'light' if self.theme_combo.currentIndex() == 0 else 'dark'
        theme_manager.set_theme(new_theme)
        
        QMessageBox.information(self, "تم الحفظ", "تم حفظ الإعدادات بنجاح!\nيرجى إعادة تشغيل التطبيق لتطبيق بعض التغييرات.")
        self.accept()
    
    def reset_all_settings(self):
        """إعادة تعيين جميع الإعدادات"""
        reply = QMessageBox.question(
            self,
            "تأكيد",
            "هل أنت متأكد من إعادة تعيين جميع الإعدادات إلى القيم الافتراضية؟",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            reset_settings()
            self.settings = load_settings()
            self.load_current_settings()
            QMessageBox.information(self, "تم", "تم إعادة تعيين الإعدادات.")

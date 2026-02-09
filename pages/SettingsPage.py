import json
import os
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QCheckBox, QMessageBox,
    QComboBox, QPushButton, QSpinBox, QGroupBox, QFormLayout, QScrollArea
)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt, pyqtSignal

CONFIG_FILE = "config.json"

class SettingsPage(QWidget):
    # إشارة لتحديث المظهر في MainWindow
    theme_changed = pyqtSignal(dict)
    
    def __init__(self):
        super().__init__()

        # إزالة الستايل الثابت للسماح بتطبيق الستايل من MainWindow
        # سيتم تطبيق الستايل ديناميكياً من MainWindow حسب الوضع (فاتح/داكن)
        # self.setStyleSheet("...")  # تم إزالة الستايل الثابت

        # تحميل الإعدادات
        self.settings = self.load_settings()

        # إنشاء منطقة التمرير
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; }")
        
        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)
        layout.setSpacing(15)
        layout.setContentsMargins(30, 20, 30, 20)

        # العنوان
        title = QLabel("⚙️ إعدادات النظام")
        title.setFont(QFont("Amiri", 24, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #222; margin-bottom: 5px;")
        layout.addWidget(title)

        subtitle = QLabel("تخصيص تجربة الاستخدام")
        subtitle.setFont(QFont("Amiri", 12))
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("color: #666; margin-bottom: 20px;")
        layout.addWidget(subtitle)

        # ==================== المظهر ====================
        appearance_group = QGroupBox("🎨 المظهر")
        appearance_layout = QFormLayout()
        appearance_layout.setSpacing(12)

        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["فاتح", "داكن"])
        self.theme_combo.setCurrentText(self.settings.get("theme", "فاتح"))
        self.theme_combo.currentTextChanged.connect(self.on_setting_changed)
        appearance_layout.addRow("المظهر:", self.theme_combo)

        appearance_group.setLayout(appearance_layout)
        layout.addWidget(appearance_group)

        # ==================== الخط ====================
        font_group = QGroupBox("🔤 الخط")
        font_layout = QFormLayout()
        font_layout.setSpacing(12)

        self.font_family_combo = QComboBox()
        self.font_family_combo.addItems([
            "Amiri", "Segoe UI", "Tahoma", "Arial Unicode MS", 
            "Cairo", "Arial"
        ])
        current_font = self.settings.get("font_family", "Amiri")
        index = self.font_family_combo.findText(current_font)
        if index >= 0:
            self.font_family_combo.setCurrentIndex(index)
        self.font_family_combo.currentTextChanged.connect(self.on_setting_changed)
        font_layout.addRow("نوع الخط:", self.font_family_combo)

        font_size_layout = QHBoxLayout()
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setMinimum(8)
        self.font_size_spin.setMaximum(24)
        self.font_size_spin.setValue(self.settings.get("font_size", 13))
        self.font_size_spin.valueChanged.connect(self.on_setting_changed)
        font_size_layout.addWidget(self.font_size_spin)
        font_size_layout.addStretch()
        font_layout.addRow("حجم الخط:", font_size_layout)

        self.bold_checkbox = QCheckBox("خط عريض")
        self.bold_checkbox.setChecked(self.settings.get("font_bold", False))
        self.bold_checkbox.stateChanged.connect(self.on_setting_changed)
        font_layout.addRow("", self.bold_checkbox)

        font_group.setLayout(font_layout)
        layout.addWidget(font_group)

        # ==================== اللغة ====================
        language_group = QGroupBox("🌐 اللغة")
        language_layout = QFormLayout()
        language_layout.setSpacing(12)

        self.language_combo = QComboBox()
        self.language_combo.addItems(["العربية", "English"])
        self.language_combo.setCurrentText(self.settings.get("language", "العربية"))
        self.language_combo.currentTextChanged.connect(self.on_setting_changed)
        language_layout.addRow("اللغة:", self.language_combo)

        language_group.setLayout(language_layout)
        layout.addWidget(language_group)

        # ==================== إعدادات عامة ====================
        general_group = QGroupBox("⚙️ إعدادات عامة")
        general_layout = QVBoxLayout()
        general_layout.setSpacing(10)

        self.sound_checkbox = QCheckBox("تشغيل نغمة الترحيب عند بدء التشغيل")
        self.sound_checkbox.setChecked(self.settings.get("play_welcome_sound", True))
        self.sound_checkbox.stateChanged.connect(self.on_setting_changed)
        general_layout.addWidget(self.sound_checkbox)

        self.auto_save_checkbox = QCheckBox("حفظ تلقائي للبيانات")
        self.auto_save_checkbox.setChecked(self.settings.get("auto_save", True))
        self.auto_save_checkbox.stateChanged.connect(self.on_setting_changed)
        general_layout.addWidget(self.auto_save_checkbox)

        general_group.setLayout(general_layout)
        layout.addWidget(general_group)

        layout.addStretch()

        # ==================== أزرار التحكم ====================
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(15)
        
        save_btn = QPushButton("💾 حفظ")
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 12px 30px;
                border-radius: 8px;
                font-weight: bold;
                font-size: 14px;
                min-width: 120px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
        """)
        save_btn.clicked.connect(self.save_all_settings)

        reset_btn = QPushButton("🔄 إعادة تعيين")
        reset_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                padding: 12px 30px;
                border-radius: 8px;
                font-weight: bold;
                font-size: 14px;
                min-width: 120px;
            }
            QPushButton:hover {
                background-color: #F57C00;
            }
            QPushButton:pressed {
                background-color: #E65100;
            }
        """)
        reset_btn.clicked.connect(self.reset_settings)

        buttons_layout.addStretch()
        buttons_layout.addWidget(save_btn)
        buttons_layout.addWidget(reset_btn)
        buttons_layout.addStretch()

        layout.addLayout(buttons_layout)
        layout.addSpacing(20)

        scroll.setWidget(content_widget)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll)

    def on_setting_changed(self):
        """عند تغيير أي إعداد - حفظ تلقائي"""
        # تحديث الإعدادات في الذاكرة
        self.settings["theme"] = self.theme_combo.currentText()
        self.settings["font_family"] = self.font_family_combo.currentText()
        self.settings["font_size"] = self.font_size_spin.value()
        self.settings["font_bold"] = self.bold_checkbox.isChecked()
        self.settings["language"] = self.language_combo.currentText()
        self.settings["play_welcome_sound"] = self.sound_checkbox.isChecked()
        self.settings["auto_save"] = self.auto_save_checkbox.isChecked()

    def save_all_settings(self):
        """حفظ جميع الإعدادات"""
        self.on_setting_changed()  # التأكد من تحديث جميع القيم
        self.save_settings()
        self.theme_changed.emit(self.settings)
        QMessageBox.information(
            self, 
            "تم الحفظ", 
            "✅ تم حفظ جميع الإعدادات بنجاح!\n\nسيتم تطبيق التغييرات فوراً."
        )

    def reset_settings(self):
        """إعادة تعيين الإعدادات للافتراضية"""
        reply = QMessageBox.question(
            self, 
            "تأكيد إعادة التعيين", 
            "هل تريد إعادة تعيين جميع الإعدادات للقيم الافتراضية؟\n\nسيتم فقدان جميع التخصيصات الحالية.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.settings = {
                "play_welcome_sound": True,
                "theme": "فاتح",
                "font_family": "Amiri",
                "font_size": 13,
                "font_bold": False,
                "language": "العربية",
                "auto_save": True,
                "background_color": "#FFFBEA",
                "text_color": "#222222",
                "tab_color": "#FFD700"
            }
            
            # تحديث الواجهة
            self.theme_combo.setCurrentText("فاتح")
            self.font_family_combo.setCurrentText("Amiri")
            self.font_size_spin.setValue(13)
            self.bold_checkbox.setChecked(False)
            self.language_combo.setCurrentText("العربية")
            self.sound_checkbox.setChecked(True)
            self.auto_save_checkbox.setChecked(True)
            
            self.save_settings()
            self.theme_changed.emit(self.settings)
            QMessageBox.information(self, "تم", "✅ تم إعادة تعيين جميع الإعدادات للقيم الافتراضية.")

    def load_settings(self):
        """تحميل الإعدادات من ملف JSON"""
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    settings = json.load(f)
                    # إضافة القيم الافتراضية للمفاتيح المفقودة
                    defaults = {
                        "play_welcome_sound": True,
                        "theme": "فاتح",
                        "font_family": "Amiri",
                        "font_size": 13,
                        "font_bold": False,
                        "language": "العربية",
                        "auto_save": True,
                        "background_color": "#FFFBEA",
                        "text_color": "#222222",
                        "tab_color": "#FFD700"
                    }
                    for key, value in defaults.items():
                        if key not in settings:
                            settings[key] = value
                    return settings
            except Exception as e:
                print(f"خطأ في تحميل الإعدادات: {e}")
        
        return {
            "play_welcome_sound": True,
            "theme": "فاتح",
            "font_family": "Amiri",
            "font_size": 13,
            "font_bold": False,
            "language": "العربية",
            "auto_save": True,
            "background_color": "#FFFBEA",
            "text_color": "#222222",
            "tab_color": "#FFD700"
        }

    def save_settings(self):
        """حفظ الإعدادات في ملف JSON"""
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(self.settings, f, ensure_ascii=False, indent=4)
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل حفظ الإعدادات:\n{e}")

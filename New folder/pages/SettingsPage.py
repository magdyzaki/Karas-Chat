import json
import os
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QCheckBox, QMessageBox
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt

CONFIG_FILE = "config.json"

class SettingsPage(QWidget):
    def __init__(self):
        super().__init__()

        self.setStyleSheet("background-color: #FFFBEA;")
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignTop)

        title = QLabel("⚙️ إعدادات النظام")
        title.setFont(QFont("Amiri", 20, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #222; margin-top: 15px;")

        subtitle = QLabel("قم بتخصيص تجربة النظام كما تحب 🎛️")
        subtitle.setFont(QFont("Amiri", 13))
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("color: #444; margin-bottom: 20px;")

        # ✅ تحميل الإعدادات
        self.settings = self.load_settings()

        # 🔊 خيار تشغيل/إيقاف نغمة الترحيب
        self.sound_checkbox = QCheckBox("تشغيل نغمة الترحيب عند بدء التشغيل 🎵")
        self.sound_checkbox.setFont(QFont("Amiri", 13))
        self.sound_checkbox.setChecked(self.settings.get("play_welcome_sound", True))
        self.sound_checkbox.stateChanged.connect(self.toggle_sound)
        self.sound_checkbox.setStyleSheet("""
            QCheckBox {
                color: #333;
                spacing: 8px;
                padding: 6px;
                font-weight: bold;
            }
            QCheckBox::indicator {
                width: 24px;
                height: 24px;
            }
            QCheckBox::indicator:unchecked {
                border: 2px solid #E6C200;
                background-color: #FFFBEA;
                border-radius: 6px;
            }
            QCheckBox::indicator:checked {
                background-color: #FFD700;
                border: 2px solid #C9A700;
                border-radius: 6px;
            }
        """)

        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addWidget(self.sound_checkbox)
        layout.addStretch()
        self.setLayout(layout)

    def toggle_sound(self, state):
        """تحديث إعداد نغمة الترحيب"""
        self.settings["play_welcome_sound"] = bool(state)
        self.save_settings()
        msg = "تم تفعيل نغمة الترحيب 🎶" if state else "تم إيقاف نغمة الترحيب 🔇"
        QMessageBox.information(self, "تأكيد الإعداد", msg)

    def load_settings(self):
        """تحميل الإعدادات من ملف JSON"""
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {"play_welcome_sound": True}

    def save_settings(self):
        """حفظ الإعدادات في ملف JSON"""
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(self.settings, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"خطأ أثناء حفظ الإعدادات: {e}")
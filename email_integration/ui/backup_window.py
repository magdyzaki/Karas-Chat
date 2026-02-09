"""
نافذة إدارة النسخ الاحتياطي
Backup Management Window
"""
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QMessageBox, QTextEdit,
    QFileDialog, QGroupBox, QCheckBox, QComboBox, QTimeEdit,
    QSpinBox, QFormLayout, QSplitter, QWidget
)
from PyQt5.QtGui import QFont, QIcon
from PyQt5.QtCore import Qt, QTime

from core.backup import (
    create_backup, list_backups, restore_backup,
    get_backup_config, save_backup_config,
    get_backup_statistics, BACKUP_DIR
)
import os


class BackupWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setWindowTitle("💾 إدارة النسخ الاحتياطي - Backup Management")
        self.setMinimumSize(1000, 700)
        
        main_layout = QVBoxLayout(self)
        
        # ===== العنوان =====
        title = QLabel("💾 إدارة النسخ الاحتياطي")
        title.setFont(QFont("Segoe UI", 14, QFont.Bold))
        main_layout.addWidget(title)
        
        # ===== Splitter للتنظيم =====
        splitter = QSplitter(Qt.Horizontal)
        
        # ===== الجانب الأيسر: الإعدادات =====
        left_panel = QGroupBox("⚙️ الإعدادات - Settings")
        left_layout = QFormLayout()
        
        # النسخ التلقائي
        self.auto_backup_check = QCheckBox("تفعيل النسخ الاحتياطي التلقائي")
        self.auto_backup_check.stateChanged.connect(self.on_config_changed)
        left_layout.addRow(self.auto_backup_check)
        
        # التكرار
        self.frequency_combo = QComboBox()
        self.frequency_combo.addItems(["يومي - Daily", "أسبوعي - Weekly"])
        self.frequency_combo.currentIndexChanged.connect(self.on_config_changed)
        left_layout.addRow("التكرار - Frequency:", self.frequency_combo)
        
        # الوقت
        self.time_edit = QTimeEdit()
        self.time_edit.setDisplayFormat("HH:mm")
        self.time_edit.timeChanged.connect(self.on_config_changed)
        left_layout.addRow("وقت النسخ - Backup Time:", self.time_edit)
        
        # عدد النسخ المحفوظة
        self.keep_spin = QSpinBox()
        self.keep_spin.setMinimum(5)
        self.keep_spin.setMaximum(365)
        self.keep_spin.setValue(30)
        self.keep_spin.valueChanged.connect(self.on_config_changed)
        left_layout.addRow("عدد النسخ المحفوظة - Keep Backups:", self.keep_spin)
        
        # النسخ عند بدء التشغيل
        self.startup_check = QCheckBox("نسخ احتياطي عند بدء التشغيل")
        self.startup_check.stateChanged.connect(self.on_config_changed)
        left_layout.addRow(self.startup_check)
        
        # إحصائيات
        stats_label = QLabel()
        stats_label.setWordWrap(True)
        self.stats_label = stats_label
        left_layout.addRow("📊 الإحصائيات - Statistics:", stats_label)
        
        # زر الحفظ
        save_btn = QPushButton("💾 حفظ الإعدادات")
        save_btn.clicked.connect(self.save_settings)
        left_layout.addRow(save_btn)
        
        left_panel.setLayout(left_layout)
        
        # ===== الجانب الأيمن: قائمة النسخ =====
        right_panel = QVBoxLayout()
        
        # العنوان
        list_title = QLabel("📋 قائمة النسخ الاحتياطية")
        list_title.setFont(QFont("Segoe UI", 12, QFont.Bold))
        right_panel.addWidget(list_title)
        
        # الأزرار
        btn_layout = QHBoxLayout()
        
        self.create_btn = QPushButton("➕ نسخ احتياطي جديد")
        self.create_btn.clicked.connect(self.create_new_backup)
        btn_layout.addWidget(self.create_btn)
        
        self.restore_btn = QPushButton("🔄 استعادة")
        self.restore_btn.clicked.connect(self.restore_selected_backup)
        btn_layout.addWidget(self.restore_btn)
        
        self.delete_btn = QPushButton("🗑️ حذف")
        self.delete_btn.clicked.connect(self.delete_selected_backup)
        btn_layout.addWidget(self.delete_btn)
        
        self.refresh_btn = QPushButton("🔄 تحديث")
        self.refresh_btn.clicked.connect(self.load_backups)
        btn_layout.addWidget(self.refresh_btn)
        
        self.export_btn = QPushButton("📤 تصدير نسخة")
        self.export_btn.clicked.connect(self.export_backup)
        btn_layout.addWidget(self.export_btn)
        
        self.import_btn = QPushButton("📥 استيراد نسخة")
        self.import_btn.clicked.connect(self.import_backup)
        btn_layout.addWidget(self.import_btn)
        
        btn_layout.addStretch()
        right_panel.addLayout(btn_layout)
        
        # الجدول
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            "الاسم - Filename",
            "التاريخ - Date",
            "الحجم - Size (MB)",
            "الوصف - Description",
            "المسار - Path"
        ])
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setColumnWidth(0, 250)
        self.table.setColumnWidth(1, 150)
        self.table.setColumnWidth(2, 100)
        self.table.setColumnWidth(3, 200)
        right_panel.addWidget(self.table)
        
        right_widget = QGroupBox("📋 النسخ الاحتياطية المتوفرة")
        right_widget.setLayout(right_panel)
        
        splitter.addWidget(left_panel)
        splitter.addWidget(right_widget)
        splitter.setSizes([350, 650])
        
        main_layout.addWidget(splitter)
        
        # ===== الأزرار السفلية =====
        bottom_btn = QHBoxLayout()
        close_btn = QPushButton("إغلاق - Close")
        close_btn.clicked.connect(self.accept)
        bottom_btn.addStretch()
        bottom_btn.addWidget(close_btn)
        main_layout.addLayout(bottom_btn)
        
        # تحميل البيانات
        self.load_settings()
        self.load_backups()
        self.update_statistics()
    
    def load_settings(self):
        """تحميل الإعدادات الحالية"""
        config = get_backup_config()
        
        self.auto_backup_check.setChecked(config.get("auto_backup_enabled", False))
        
        frequency = config.get("backup_frequency", "daily")
        self.frequency_combo.setCurrentIndex(0 if frequency == "daily" else 1)
        
        backup_time = config.get("backup_time", "02:00")
        try:
            hour, minute = map(int, backup_time.split(":"))
            self.time_edit.setTime(QTime(hour, minute))
        except Exception:
            self.time_edit.setTime(QTime(2, 0))
        
        self.keep_spin.setValue(config.get("keep_backups", 30))
        self.startup_check.setChecked(config.get("backup_on_startup", True))
    
    def save_settings(self):
        """حفظ الإعدادات"""
        config = get_backup_config()
        
        config["auto_backup_enabled"] = self.auto_backup_check.isChecked()
        config["backup_frequency"] = "daily" if self.frequency_combo.currentIndex() == 0 else "weekly"
        
        time = self.time_edit.time()
        config["backup_time"] = f"{time.hour():02d}:{time.minute():02d}"
        
        config["keep_backups"] = self.keep_spin.value()
        config["backup_on_startup"] = self.startup_check.isChecked()
        
        save_backup_config(config)
        
        QMessageBox.information(
            self,
            "تم الحفظ",
            "تم حفظ الإعدادات بنجاح! - Settings saved successfully!"
        )
        
        self.update_statistics()
    
    def on_config_changed(self):
        """عند تغيير الإعدادات (يمكن إضافة منطق هنا)"""
        pass
    
    def update_statistics(self):
        """تحديث الإحصائيات"""
        stats = get_backup_statistics()
        
        text = f"""إجمالي النسخ: {stats['total_backups']}
الحجم الإجمالي: {stats['total_size_mb']} MB
النسخ التلقائي: {'مفعل' if stats['auto_backup_enabled'] else 'معطل'}
عدد النسخ المحفوظة: {stats['keep_backups']}
"""
        
        if stats['last_backup']:
            try:
                from datetime import datetime
                last_backup = datetime.fromisoformat(stats['last_backup'])
                text += f"آخر نسخ: {last_backup.strftime('%Y-%m-%d %H:%M')}"
            except Exception:
                pass
        
        self.stats_label.setText(text)
    
    def load_backups(self):
        """تحميل قائمة النسخ الاحتياطية"""
        backups = list_backups()
        
        self.table.setRowCount(len(backups))
        
        for row, backup in enumerate(backups):
            # الاسم
            self.table.setItem(row, 0, QTableWidgetItem(backup["filename"]))
            
            # التاريخ
            date_str = backup["created"].strftime("%Y-%m-%d %H:%M")
            self.table.setItem(row, 1, QTableWidgetItem(date_str))
            
            # الحجم
            size_mb = round(backup["size"] / (1024 * 1024), 2)
            self.table.setItem(row, 2, QTableWidgetItem(f"{size_mb} MB"))
            
            # الوصف
            desc = backup.get("description", "")
            self.table.setItem(row, 3, QTableWidgetItem(desc))
            
            # المسار (مخفي عادة)
            self.table.setItem(row, 4, QTableWidgetItem(backup["path"]))
            
            # حفظ مسار النسخة في البيانات
            for col in range(5):
                item = self.table.item(row, col)
                if item:
                    item.setData(Qt.UserRole, backup["path"])
        
        self.update_statistics()
    
    def get_selected_backup_path(self):
        """الحصول على مسار النسخة المحددة"""
        row = self.table.currentRow()
        if row < 0:
            return None
        
        item = self.table.item(row, 4)
        if not item:
            return None
        
        return item.data(Qt.UserRole)
    
    def create_new_backup(self):
        """إنشاء نسخة احتياطية جديدة"""
        reply = QMessageBox.question(
            self,
            "تأكيد",
            "هل تريد إنشاء نسخة احتياطية الآن؟",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            backup_path = create_backup("نسخ احتياطي يدوي")
            
            if backup_path:
                QMessageBox.information(
                    self,
                    "نجح",
                    f"تم إنشاء النسخة الاحتياطية بنجاح!\n{os.path.basename(backup_path)}"
                )
                self.load_backups()
            else:
                QMessageBox.critical(
                    self,
                    "خطأ",
                    "فشل إنشاء النسخة الاحتياطية!"
                )
    
    def restore_selected_backup(self):
        """استعادة النسخة المحددة"""
        backup_path = self.get_selected_backup_path()
        
        if not backup_path:
            QMessageBox.warning(
                self,
                "تحذير",
                "يرجى اختيار نسخة احتياطية للاستعادة!"
            )
            return
        
        reply = QMessageBox.warning(
            self,
            "تحذير",
            "⚠️ سيتم استبدال قاعدة البيانات الحالية بالنسخة الاحتياطية!\n"
            "يرجى إغلاق التطبيق وإعادة فتحه بعد الاستعادة.\n\n"
            "هل تريد المتابعة؟",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            if restore_backup(backup_path):
                QMessageBox.information(
                    self,
                    "نجح",
                    "تم استعادة النسخة الاحتياطية بنجاح!\n"
                    "يرجى إعادة تشغيل التطبيق لتطبيق التغييرات."
                )
                self.load_backups()
            else:
                QMessageBox.critical(
                    self,
                    "خطأ",
                    "فشل استعادة النسخة الاحتياطية!"
                )
    
    def delete_selected_backup(self):
        """حذف النسخة المحددة"""
        backup_path = self.get_selected_backup_path()
        
        if not backup_path:
            QMessageBox.warning(
                self,
                "تحذير",
                "يرجى اختيار نسخة احتياطية للحذف!"
            )
            return
        
        reply = QMessageBox.warning(
            self,
            "تأكيد الحذف",
            f"هل أنت متأكد من حذف النسخة الاحتياطية؟\n{os.path.basename(backup_path)}",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                if os.path.exists(backup_path):
                    os.remove(backup_path)
                    
                    # حذف ملف المعلومات
                    info_path = backup_path.replace(".db", ".info")
                    if os.path.exists(info_path):
                        os.remove(info_path)
                    
                    QMessageBox.information(
                        self,
                        "نجح",
                        "تم حذف النسخة الاحتياطية بنجاح!"
                    )
                    self.load_backups()
                else:
                    QMessageBox.warning(
                        self,
                        "تحذير",
                        "الملف غير موجود!"
                    )
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "خطأ",
                    f"فشل حذف النسخة الاحتياطية:\n{str(e)}"
                )
    
    def export_backup(self):
        """تصدير نسخة احتياطية إلى مكان آخر"""
        backup_path = self.get_selected_backup_path()
        
        if not backup_path:
            QMessageBox.warning(
                self,
                "تحذير",
                "يرجى اختيار نسخة احتياطية للتصدير!"
            )
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "تصدير النسخة الاحتياطية",
            os.path.join(os.path.expanduser("~"), "Desktop", os.path.basename(backup_path)),
            "Database Files (*.db);;All Files (*.*)"
        )
        
        if file_path:
            try:
                import shutil
                shutil.copy2(backup_path, file_path)
                
                # نسخ ملف المعلومات أيضاً
                info_path = backup_path.replace(".db", ".info")
                if os.path.exists(info_path):
                    shutil.copy2(info_path, file_path.replace(".db", ".info"))
                
                QMessageBox.information(
                    self,
                    "نجح",
                    f"تم تصدير النسخة الاحتياطية بنجاح!\n{file_path}"
                )
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "خطأ",
                    f"فشل تصدير النسخة الاحتياطية:\n{str(e)}"
                )
    
    def import_backup(self):
        """استيراد نسخة احتياطية من مكان آخر"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "استيراد النسخة الاحتياطية",
            os.path.expanduser("~"),
            "Database Files (*.db);;All Files (*.*)"
        )
        
        if file_path:
            try:
                import shutil
                from datetime import datetime
                
                # نسخ الملف إلى مجلد النسخ الاحتياطية
                timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                backup_filename = f"efm_backup_imported_{timestamp}.db"
                backup_path = os.path.join(BACKUP_DIR, backup_filename)
                
                shutil.copy2(file_path, backup_path)
                
                # نسخ ملف المعلومات إن وجد
                info_path = file_path.replace(".db", ".info")
                if os.path.exists(info_path):
                    shutil.copy2(info_path, backup_path.replace(".db", ".info"))
                
                QMessageBox.information(
                    self,
                    "نجح",
                    f"تم استيراد النسخة الاحتياطية بنجاح!"
                )
                self.load_backups()
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "خطأ",
                    f"فشل استيراد النسخة الاحتياطية:\n{str(e)}"
                )

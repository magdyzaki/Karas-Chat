"""
نافذة عرض Logs البرنامج
Application Logs Viewer Window
"""
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTextEdit, QComboBox, QMessageBox,
    QGroupBox, QFileDialog
)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt
from pathlib import Path

from core.logging_system import get_logger


class LogsWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setWindowTitle("📋 Application Logs - سجل البرنامج")
        self.setMinimumSize(900, 600)
        
        self.logger = get_logger()
        
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("📋 Application Logs - سجل البرنامج")
        title.setFont(QFont("Segoe UI", 14, QFont.Bold))
        layout.addWidget(title)
        
        # Filters
        filter_layout = QHBoxLayout()
        
        filter_label = QLabel("Log Type:")
        filter_layout.addWidget(filter_label)
        
        self.log_type_combo = QComboBox()
        self.log_type_combo.addItems(["Errors", "Application", "Sync", "All"])
        self.log_type_combo.currentIndexChanged.connect(self.load_logs)
        filter_layout.addWidget(self.log_type_combo)
        
        filter_layout.addStretch()
        
        # Refresh button
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.clicked.connect(self.load_logs)
        filter_layout.addWidget(refresh_btn)
        
        # Clear button
        clear_btn = QPushButton("🗑️ Clear Logs")
        clear_btn.clicked.connect(self.clear_logs)
        clear_btn.setStyleSheet("background-color: #FF6B6B; color: white; font-weight: bold; padding: 5px;")
        filter_layout.addWidget(clear_btn)
        
        # Export button
        export_btn = QPushButton("💾 Export")
        export_btn.clicked.connect(self.export_logs)
        filter_layout.addWidget(export_btn)
        
        layout.addLayout(filter_layout)
        
        # Logs display
        logs_group = QGroupBox("Logs Content")
        logs_layout = QVBoxLayout()
        
        self.logs_text = QTextEdit()
        self.logs_text.setReadOnly(True)
        self.logs_text.setFont(QFont("Courier", 9))
        self.logs_text.setStyleSheet("""
            QTextEdit {
                background-color: #1E1E1E;
                color: #D4D4D4;
                border: 1px solid #3F3F46;
                padding: 10px;
            }
        """)
        logs_layout.addWidget(self.logs_text)
        
        logs_group.setLayout(logs_layout)
        layout.addWidget(logs_group)
        
        # Info
        info_label = QLabel("ℹ️ Logs are automatically rotated when they reach 10 MB. Last 5 backups are kept.")
        info_label.setStyleSheet("color: #666666; font-size: 9px;")
        layout.addWidget(info_label)
        
        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)
        
        # Load initial logs
        self.load_logs()
    
    def load_logs(self):
        """تحميل Logs"""
        try:
            log_type = self.log_type_combo.currentText()
            
            self.logs_text.clear()
            
            if log_type == "Errors":
                logs = self.logger.get_error_logs(limit=200)
                content = "\n".join(logs)
            elif log_type == "Application":
                logs = self.logger.get_app_logs(limit=200)
                content = "\n".join(logs)
            elif log_type == "Sync":
                logs = self.logger.get_app_logs(limit=200)  # Sync logs in app log
                content = "\n".join([log for log in logs if "[Sync]" in log or "sync" in log.lower()])
            else:  # All
                error_logs = self.logger.get_error_logs(limit=100)
                app_logs = self.logger.get_app_logs(limit=100)
                content = "=== ERROR LOGS ===\n" + "\n".join(error_logs)
                content += "\n\n=== APPLICATION LOGS ===\n" + "\n".join(app_logs)
            
            if not content.strip():
                content = "No logs available."
            
            self.logs_text.setPlainText(content)
            
            # Scroll to bottom
            cursor = self.logs_text.textCursor()
            cursor.movePosition(cursor.End)
            self.logs_text.setTextCursor(cursor)
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to load logs:\n{str(e)}"
            )
    
    def clear_logs(self):
        """مسح Logs"""
        reply = QMessageBox.question(
            self,
            "Clear Logs",
            "Are you sure you want to clear all logs?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                log_type = self.log_type_combo.currentText()
                
                if log_type == "Errors":
                    self.logger.clear_logs("error")
                elif log_type == "Application":
                    self.logger.clear_logs("app")
                elif log_type == "Sync":
                    self.logger.clear_logs("sync")
                else:  # All
                    self.logger.clear_logs("all")
                
                self.load_logs()
                
                QMessageBox.information(
                    self,
                    "Success",
                    "Logs cleared successfully."
                )
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Error",
                    f"Failed to clear logs:\n{str(e)}"
                )
    
    def export_logs(self):
        """تصدير Logs إلى ملف"""
        try:
            log_type = self.log_type_combo.currentText()
            filename = f"EFM_Logs_{log_type}_{Path(__file__).parent.parent.name}.txt"
            
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Export Logs",
                filename,
                "Text Files (*.txt);;All Files (*.*)"
            )
            
            if file_path:
                content = self.logs_text.toPlainText()
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                QMessageBox.information(
                    self,
                    "Success",
                    f"Logs exported successfully to:\n{file_path}"
                )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to export logs:\n{str(e)}"
            )

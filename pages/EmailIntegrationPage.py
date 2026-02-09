# pages/EmailIntegrationPage.py
# صفحة بسيطة تفتح برنامج Export Follow-Up Manager الكامل
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt
import sys
import os

# إضافة مسار email_integration إلى sys.path
email_integration_path = os.path.join(os.path.dirname(__file__), "..", "email_integration")
if email_integration_path not in sys.path:
    sys.path.insert(0, email_integration_path)

# إضافة مسار core و ui
core_path = os.path.join(email_integration_path, "core")
ui_path = os.path.join(email_integration_path, "ui")
if core_path not in sys.path:
    sys.path.insert(0, core_path)
if ui_path not in sys.path:
    sys.path.insert(0, ui_path)


class EmailIntegrationPage(QWidget):
    """صفحة بسيطة تفتح برنامج Export Follow-Up Manager الكامل"""
    def __init__(self):
        super().__init__()
        self.efm_window = None
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)
        
        title = QLabel("📧 Export Follow-Up Manager")
        title.setFont(QFont("Amiri", 28, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        desc = QLabel("برنامج متكامل لإدارة العملاء والرسائل ومتابعة الصادرات\nمع ربط كامل بالإيميل (Outlook & IMAP)")
        desc.setFont(QFont("Amiri", 14))
        desc.setAlignment(Qt.AlignCenter)
        desc.setWordWrap(True)
        layout.addWidget(desc)
        
        open_btn = QPushButton("🚀 فتح Export Follow-Up Manager")
        open_btn.setFont(QFont("Amiri", 18, QFont.Bold))
        open_btn.setMinimumHeight(70)
        open_btn.setMinimumWidth(500)
        open_btn.clicked.connect(self.open_efm_manager)
        layout.addWidget(open_btn, alignment=Qt.AlignCenter)
        
        layout.addStretch()
        self.setLayout(layout)
    
    def open_efm_manager(self):
        """فتح برنامج Export Follow-Up Manager الكامل"""
        try:
            # استيراد MainWindow من Export Follow-Up Manager
            from ui.main_window import MainWindow as EFMMainWindow
            
            if self.efm_window is None or not self.efm_window.isVisible():
                # إنشاء نافذة جديدة
                self.efm_window = EFMMainWindow()
                # تطبيق الستايل من النافذة الرئيسية إذا كان متاحاً
                if self.parent():
                    try:
                        main_window = self.parent()
                        while main_window and not hasattr(main_window, 'styleSheet'):
                            main_window = main_window.parent()
                        if main_window:
                            # تطبيق الستايل من النافذة الرئيسية
                            main_style = main_window.styleSheet()
                            if main_style:
                                self.efm_window.setStyleSheet(main_style)
                            # إذا كان الوضع الداكن مفعّل في النافذة الرئيسية، نفعّله هنا أيضاً
                            if hasattr(main_window, 'current_theme') and main_window.current_theme == "dark":
                                try:
                                    from email_integration.core.theme import get_theme_manager
                                    theme_manager = get_theme_manager()
                                    theme_manager.set_theme("dark")
                                    self.efm_window.setStyleSheet(theme_manager.get_stylesheet())
                                except:
                                    pass
                    except:
                        pass
                self.efm_window.show()
            else:
                self.efm_window.raise_()
                self.efm_window.activateWindow()
        except ImportError as e:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.critical(
                self, "خطأ في الاستيراد",
                f"فشل تحميل برنامج Export Follow-Up Manager:\n{str(e)}\n\n"
                "تأكد من وجود جميع الملفات في مجلد email_integration/"
            )
        except Exception as e:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.critical(
                self, "خطأ",
                f"حدث خطأ أثناء فتح البرنامج:\n{str(e)}"
            )

# MainWindow.py
import sys
import os
import warnings

# قمع تحذيرات libpng و Qt بشكل أفضل - يجب أن يكون قبل استيراد PyQt5
os.environ['QT_LOGGING_RULES'] = '*.debug=false;qt5ct.debug=false'
os.environ['QT_FATAL_WARNINGS'] = '0'
# قمع تحذيرات Python
warnings.filterwarnings('ignore', category=UserWarning)

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QTabWidget, QVBoxLayout,
    QLabel, QPushButton, QHBoxLayout
)
from PyQt5.QtGui import QFont, QFontDatabase
from PyQt5.QtCore import Qt, QLoggingCategory

# قمع تحذيرات Qt بشكل مباشر
try:
    QLoggingCategory.setFilterRules('*.debug=false')
except:
    pass

# استيراد الصفحات الأساسية (تأكد أن هذه الملفات موجودة في pages/)
from pages.HomePage import HomePage
from pages.CustomersPage import CustomersPage
from pages.ProductsPage import ProductsPage
from pages.SalesPage import SalesPage
from pages.InvoicesPage import InvoicesPage
from pages.PaymentsPage import PaymentsPage   # ← التبويب الجديد
from pages.StockPage import StockPage
from pages.PurchasesPage import PurchasesPage
from pages.SuppliersPage import SuppliersPage
from pages.ReportsPage import ReportsPage
from pages.NotificationsPage import NotificationsPage
from pages.SettingsPage import SettingsPage
from pages.EmailIntegrationPage import EmailIntegrationPage  # ← ربط الإيميل (Export Follow-Up Manager)

def get_arabic_font(size=12, bold=False):
    """الحصول على خط عربي واضح مع خطوط احتياطية"""
    # محاولة تحميل خط Amiri إذا كان موجوداً
    font_path = "assets/Amiri-Regular.ttf"
    if os.path.exists(font_path):
        QFontDatabase.addApplicationFont(font_path)
        font = QFont("Amiri", size)
    else:
        # استخدام خطوط النظام المدعومة للعربية
        font = QFont("Segoe UI", size)
        # محاولة خطوط أخرى كبديل
        if not font.exactMatch():
            font = QFont("Tahoma", size)
        if not font.exactMatch():
            font = QFont("Arial Unicode MS", size)
    
    if bold:
        font.setBold(True)
    font.setPixelSize(int(size * 1.2))  # زيادة الوضوح
    return font

def PlaceholderPage(title):
    page = QWidget()
    layout = QVBoxLayout()
    label = QLabel(f"🚧 صفحة {title} تحت التطوير 🚧")
    label.setFont(get_arabic_font(18, True))
    label.setAlignment(Qt.AlignCenter)
    layout.addWidget(label)
    page.setLayout(layout)
    return page

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("نظام إدارة KARAS CRM")
        self.resize(1200, 820)

        self.current_theme = "light"
        self.apply_theme(self.current_theme)

        self.tabs = QTabWidget()
        self.tabs.setTabPosition(QTabWidget.North)
        self.tabs.setMovable(False)

        # التبويبات الرئيسية
        self.tabs.addTab(HomePage(), "الصفحة الرئيسية")
        self.tabs.addTab(CustomersPage(), "العملاء")
        self.tabs.addTab(ProductsPage(), "المنتجات")
        self.tabs.addTab(SalesPage(), "المبيعات")

        # تبويب تحصيل المدفوعات قبل الفواتير (كما طلبت)
        self.tabs.addTab(PaymentsPage(), "تحصيل المدفوعات")

        # تبويب الفواتير (نترك كما هو)
        self.tabs.addTab(InvoicesPage(), "الفواتير")

        # تبويبات مساعدة
        self.tabs.addTab(StockPage(), "المخزون")
        self.tabs.addTab(SuppliersPage(), "الموردين")
        self.tabs.addTab(PurchasesPage(), "المشتريات")
        self.tabs.addTab(ReportsPage(), "التقارير")
        self.tabs.addTab(NotificationsPage(), "الإشعارات")
        
        # تبويب ربط الإيميل واستيراد الرسائل (Export Follow-Up Manager)
        self.tabs.addTab(EmailIntegrationPage(), "Email")
        
        settings_page = SettingsPage()
        settings_page.theme_changed.connect(self.apply_settings)
        self.tabs.addTab(settings_page, "الإعدادات")

        # زر تبديل المظهر
        btn_theme = QPushButton("🌓 تبديل المظهر")
        btn_theme.setFont(get_arabic_font(12, True))
        btn_theme.setFixedWidth(160)
        btn_theme.setStyleSheet("""
            QPushButton {
                background-color: #FFD700; color: black; border-radius: 8px; padding:6px;
            }
            QPushButton:hover { background-color: #FFC107; }
        """)
        btn_theme.clicked.connect(self.toggle_theme)

        top_layout = QHBoxLayout()
        top_layout.addWidget(btn_theme)
        top_layout.addStretch()

        wrapper = QWidget()
        wlayout = QVBoxLayout(wrapper)
        wlayout.addLayout(top_layout)
        wlayout.addWidget(self.tabs)

        self.setCentralWidget(wrapper)

    def apply_theme(self, theme):
        # الحصول على خطوط احتياطية للعربية
        font_family = "'Segoe UI', 'Tahoma', 'Arial Unicode MS', 'Arial', sans-serif"
        font_path = "assets/Amiri-Regular.ttf"
        if os.path.exists(font_path):
            font_family = "'Amiri', " + font_family
        
        if theme == "dark":
            self.setStyleSheet(f"""
                QWidget {{ 
                    background:#2B2B2B; 
                    color:#FFFFFF; 
                    font-family: {font_family};
                    font-size: 15px;
                }}
                QLabel {{
                    color: #FFFFFF;
                    background: transparent;
                }}
                QLineEdit, QTextEdit, QPlainTextEdit {{
                    background: #3B3B3B;
                    color: #FFFFFF;
                    border: 1px solid #555;
                    border-radius: 4px;
                    padding: 5px;
                }}
                QComboBox, QSpinBox {{
                    background: #3B3B3B;
                    color: #FFFFFF;
                    border: 1px solid #555;
                    border-radius: 4px;
                    padding: 5px;
                }}
                QTableWidget {{
                    background: #1E1E1E;
                    color: #FFFFFF;
                    gridline-color: #555;
                    alternate-background-color: #2B2B2B;
                    border: 1px solid #444;
                    selection-background-color: #FFD700;
                    selection-color: #000000;
                }}
                QTableWidget::item {{
                    color: #FFFFFF;
                    background: #2B2B2B;
                    padding: 6px;
                    border: none;
                }}
                QTableWidget::item:selected {{
                    background: #FFD700;
                    color: #000000;
                    font-weight: bold;
                }}
                QTableWidget::item:alternate {{
                    background: #252525;
                }}
                QTableWidget::item:hover {{
                    background: #3B3B3B;
                }}
                QHeaderView::section {{
                    background: #333;
                    color: #FFD700;
                    padding: 10px;
                    font-weight: bold;
                    font-size: 13px;
                    border: 1px solid #555;
                    border-bottom: 2px solid #FFD700;
                }}
                QTabBar::tab {{ 
                    background:#444; 
                    color:#FFD700; 
                    padding:10px 18px; 
                    font-family: {font_family};
                    font-size: 14px;
                    font-weight: bold;
                    border: 1px solid #555;
                }}
                QTabBar::tab:selected {{ 
                    background:#FFD700; 
                    color:#000000; 
                }}
                QTabBar::tab:hover {{
                    background:#555;
                }}
            """)
        else:
            self.setStyleSheet(f"""
                QWidget {{ 
                    background:#FFFBEA; 
                    color:#222; 
                    font-family: {font_family};
                    font-size: 15px;
                }}
                QTabBar::tab {{ 
                    background:#FFD700; 
                    color:black; 
                    padding:10px 18px; 
                    font-family: {font_family};
                    font-size: 14px;
                    font-weight: bold;
                }}
                QTabBar::tab:selected {{ 
                    background:#FFC107; 
                    color:white; 
                }}
            """)

    def toggle_theme(self):
        self.current_theme = "dark" if self.current_theme == "light" else "light"
        self.apply_theme(self.current_theme)
    
    def apply_settings(self, settings):
        """تطبيق الإعدادات من صفحة الإعدادات"""
        import json
        try:
            # تطبيق المظهر
            theme = settings.get("theme", "فاتح")
            if theme == "داكن":
                self.current_theme = "dark"
            else:
                self.current_theme = "light"
            
            # تطبيق الخط
            font_family = settings.get("font_family", "Amiri")
            font_size = settings.get("font_size", 13)
            font_bold = settings.get("font_bold", False)
            
            # تطبيق الألوان
            bg_color = settings.get("background_color", "#FFFBEA")
            text_color = settings.get("text_color", "#222")
            tab_color = settings.get("tab_color", "#FFD700")
            
            # بناء الستايل
            font_path = "assets/Amiri-Regular.ttf"
            if os.path.exists(font_path):
                QFontDatabase.addApplicationFont(font_path)
            
            font_weight = "bold" if font_bold else "normal"
            
            if self.current_theme == "dark":
                self.setStyleSheet(f"""
                    QWidget {{ 
                        background:#2B2B2B; 
                        color:#FFFFFF; 
                        font-family: {font_family};
                        font-size: {font_size}px;
                        font-weight: {font_weight};
                    }}
                    QLabel {{
                        color: #FFFFFF;
                        background: transparent;
                    }}
                    QLabel[class="title"], QLabel[class="desc"], QLabel[class="datetime"], QLabel[class="signature"] {{
                        color: #FFFFFF;
                    }}
                    QLineEdit, QTextEdit, QPlainTextEdit {{
                        background: #3B3B3B;
                        color: #FFFFFF;
                        border: 1px solid #555;
                        border-radius: 4px;
                        padding: 5px;
                    }}
                    QComboBox, QSpinBox {{
                        background: #3B3B3B;
                        color: #FFFFFF;
                        border: 1px solid #555;
                        border-radius: 4px;
                        padding: 5px;
                    }}
                    QComboBox::drop-down {{
                        border: none;
                        background: #555;
                    }}
                    QComboBox::down-arrow {{
                        image: none;
                        border: 1px solid #FFD700;
                        width: 10px;
                        height: 10px;
                    }}
                    QPushButton {{
                        background: #3B3B3B;
                        color: #FFFFFF;
                        border: 1px solid #555;
                        border-radius: 4px;
                        padding: 8px 15px;
                        font-weight: bold;
                    }}
                    QPushButton:hover {{
                        background: #4B4B4B;
                        border: 1px solid #FFD700;
                    }}
                    QPushButton:pressed {{
                        background: #2B2B2B;
                    }}
                    QGroupBox {{
                        border: 2px solid #555;
                        border-radius: 8px;
                        margin-top: 10px;
                        padding-top: 15px;
                        color: #FFFFFF;
                        font-weight: bold;
                    }}
                    QGroupBox::title {{
                        subcontrol-origin: margin;
                        left: 10px;
                        padding: 0 5px;
                        color: #FFD700;
                    }}
                    QCheckBox {{
                        color: #FFFFFF;
                        spacing: 8px;
                    }}
                    QCheckBox::indicator {{
                        width: 18px;
                        height: 18px;
                        border: 2px solid #555;
                        border-radius: 3px;
                        background: #3B3B3B;
                    }}
                    QCheckBox::indicator:checked {{
                        background: #FFD700;
                        border: 2px solid #FFD700;
                    }}
                    QCheckBox::indicator:hover {{
                        border: 2px solid #FFD700;
                    }}
                    QScrollArea {{
                        background: #2B2B2B;
                        border: 1px solid #555;
                    }}
                    QScrollArea QWidget {{
                        background: #2B2B2B;
                    }}
                    QDialog {{
                        background: #2B2B2B;
                        color: #FFFFFF;
                    }}
                    QMessageBox {{
                        background: #2B2B2B;
                        color: #FFFFFF;
                    }}
                    QMessageBox QLabel {{
                        color: #FFFFFF;
                    }}
                    QMessageBox QPushButton {{
                        background: #3B3B3B;
                        color: #FFFFFF;
                        border: 1px solid #555;
                        padding: 8px 15px;
                        border-radius: 4px;
                    }}
                    QMessageBox QPushButton:hover {{
                        background: #4B4B4B;
                        border: 1px solid #FFD700;
                    }}
                    QTableWidget {{
                        background: #1E1E1E;
                        color: #FFFFFF;
                        gridline-color: #555;
                        alternate-background-color: #2B2B2B;
                        border: 1px solid #444;
                        selection-background-color: #FFD700;
                        selection-color: #000000;
                    }}
                    QTableWidget::item {{
                        color: #FFFFFF;
                        background: #2B2B2B;
                        padding: 6px;
                        border: none;
                    }}
                    QTableWidget::item:selected {{
                        background: #FFD700;
                        color: #000000;
                        font-weight: bold;
                    }}
                    QTableWidget::item:alternate {{
                        background: #252525;
                    }}
                    QTableWidget::item:hover {{
                        background: #3B3B3B;
                    }}
                    QHeaderView::section {{
                        background: #333;
                        color: #FFD700;
                        padding: 10px;
                        font-weight: bold;
                        font-size: 13px;
                        border: 1px solid #555;
                        border-bottom: 2px solid #FFD700;
                    }}
                    QTabBar::tab {{ 
                        background:#444; 
                        color:#FFD700; 
                        padding:10px 18px; 
                        font-family: {font_family};
                        font-size: {font_size}px;
                        font-weight: bold;
                        border: 1px solid #555;
                    }}
                    QTabBar::tab:selected {{ 
                        background:#FFD700; 
                        color:#000000; 
                    }}
                    QTabBar::tab:hover {{
                        background:#555;
                    }}
                """)
            else:
                self.setStyleSheet(f"""
                    QWidget {{ 
                        background:{bg_color}; 
                        color:{text_color}; 
                        font-family: {font_family};
                        font-size: {font_size}px;
                        font-weight: {font_weight};
                    }}
                    QLabel {{
                        color: {text_color};
                        background: transparent;
                    }}
                    QLineEdit, QTextEdit, QPlainTextEdit {{
                        background: #FFFDE7;
                        color: {text_color};
                        border: 1px solid #E6C200;
                        border-radius: 4px;
                        padding: 5px;
                    }}
                    QComboBox, QSpinBox {{
                        background: #FFFDE7;
                        color: {text_color};
                        border: 1px solid #E6C200;
                        border-radius: 4px;
                        padding: 5px;
                    }}
                    QPushButton {{
                        background: {tab_color};
                        color: black;
                        border: 1px solid #E6C200;
                        border-radius: 4px;
                        padding: 8px 15px;
                        font-weight: bold;
                    }}
                    QPushButton:hover {{
                        background: #FFC107;
                        color: white;
                    }}
                    QGroupBox {{
                        border: 2px solid #FFD700;
                        border-radius: 8px;
                        margin-top: 10px;
                        padding-top: 15px;
                        color: {text_color};
                        font-weight: bold;
                    }}
                    QGroupBox::title {{
                        subcontrol-origin: margin;
                        left: 10px;
                        padding: 0 5px;
                        color: {text_color};
                    }}
                    QCheckBox {{
                        color: {text_color};
                        spacing: 8px;
                    }}
                    QTableWidget {{
                        background: #FFFDF5;
                        color: {text_color};
                        gridline-color: #ddd;
                        alternate-background-color: #FAFAFA;
                        border: 1px solid #E6C200;
                    }}
                    QTableWidget::item {{
                        color: {text_color};
                        background: #FFFDF5;
                        padding: 5px;
                    }}
                    QTableWidget::item:selected {{
                        background: #FFC107;
                        color: #FFFFFF;
                    }}
                    QHeaderView::section {{
                        background: #FFD700;
                        color: black;
                        padding: 8px;
                        font-weight: bold;
                        border: 1px solid #E6C200;
                    }}
                    QTabBar::tab {{ 
                        background:{tab_color}; 
                        color:black; 
                        padding:10px 18px; 
                        font-family: {font_family};
                        font-size: {font_size}px;
                        font-weight: bold;
                        border: 1px solid #E6C200;
                    }}
                    QTabBar::tab:selected {{ 
                        background:#FFC107; 
                        color:white; 
                    }}
                """)
            
            # تطبيق الخط على التطبيق
            app = QApplication.instance()
            if app:
                font = QFont(font_family, font_size)
                if font_bold:
                    font.setBold(True)
                app.setFont(font)
                
        except Exception as e:
            print(f"خطأ في تطبيق الإعدادات: {e}")

if __name__ == "__main__":
    # قمع تحذيرات libpng بشكل أفضل
    import logging
    logging.getLogger().setLevel(logging.ERROR)
    
    # قمع stderr مؤقتاً أثناء إنشاء QApplication
    old_stderr = sys.stderr
    devnull = None
    try:
        devnull = open(os.devnull, 'w', encoding='utf-8')
        sys.stderr = devnull
    except:
        pass
    
    # إنشاء QApplication
    app = QApplication(sys.argv)
    
    # استعادة stderr بعد إنشاء QApplication
    if devnull:
        try:
            devnull.close()
        except:
            pass
    sys.stderr = old_stderr
    
    # تعيين خط واضح للبرنامج بالكامل
    app.setFont(get_arabic_font(13, False))
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())
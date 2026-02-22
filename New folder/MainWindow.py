# MainWindow.py
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QTabWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout
)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt
import sys, os

# ✅ استيراد الصفحات الكاملة
from pages.HomePage import HomePage
from pages.CustomersPage import CustomersPage
from pages.ProductsPage import ProductsPage
from pages.SalesPage import SalesPage
from pages.InvoicesPage import InvoicesPage


# ✅ دالة توليد صفحات مؤقتة Placeholder
def PlaceholderPage(title):
    page = QWidget()
    layout = QVBoxLayout()
    label = QLabel(f"🚧 صفحة {title} تحت التطوير 🚧")
    label.setFont(QFont("Amiri", 18, QFont.Bold))
    label.setAlignment(Qt.AlignCenter)
    label.setStyleSheet("color: #CCC; background-color: transparent; padding: 40px;")
    layout.addWidget(label)
    page.setLayout(layout)
    return page


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("نظام إدارة KARAS CRM")
        self.resize(1200, 800)

        # 🌟 الوضع الافتراضي (فاتح)
        self.current_theme = "light"
        self.apply_theme(self.current_theme)

        # 🔹 إنشاء التبويبات
        self.tabs = QTabWidget()
        self.tabs.setTabPosition(QTabWidget.North)
        self.tabs.setMovable(False)

        # 🔸 إضافة التبويبات الرئيسية
        self.tabs.addTab(HomePage(), "الصفحة الرئيسية")
        self.tabs.addTab(CustomersPage(), "العملاء")
        self.tabs.addTab(ProductsPage(), "المنتجات")
        self.tabs.addTab(SalesPage(), "المبيعات")
        self.tabs.addTab(InvoicesPage(), "الفواتير")
        self.tabs.addTab(PlaceholderPage("المخزون"), "المخزون")
        self.tabs.addTab(PlaceholderPage("المشتريات"), "المشتريات")
        self.tabs.addTab(PlaceholderPage("الموردين"), "الموردين")
        self.tabs.addTab(PlaceholderPage("التقارير"), "التقارير")
        self.tabs.addTab(PlaceholderPage("الإشعارات"), "الإشعارات")
        self.tabs.addTab(PlaceholderPage("الصديق الذكي"), "الصديق الذكي")
        self.tabs.addTab(PlaceholderPage("الإعدادات"), "الإعدادات")

        # 🔘 زر تبديل الثيم (فاتح / داكن)
        toggle_btn = QPushButton("🌓 تبديل المظهر")
        toggle_btn.setFont(QFont("Amiri", 11, QFont.Bold))
        toggle_btn.setFixedWidth(160)
        toggle_btn.setStyleSheet("""
            QPushButton {
                background-color: #FFD700;
                color: black;
                border-radius: 10px;
                padding: 6px 12px;
            }
            QPushButton:hover {
                background-color: #FFC107;
            }
        """)
        toggle_btn.clicked.connect(self.toggle_theme)

        top_layout = QHBoxLayout()
        top_layout.addWidget(toggle_btn, alignment=Qt.AlignLeft)
        top_layout.addStretch()

        wrapper = QWidget()
        wrapper_layout = QVBoxLayout(wrapper)
        wrapper_layout.addLayout(top_layout)
        wrapper_layout.addWidget(self.tabs)

        self.setCentralWidget(wrapper)

    # 🎨 دالة تطبيق الستايل
    def apply_theme(self, theme):
        if theme == "dark":
            self.setStyleSheet("""
                QTabWidget::pane { border: none; }
                QTabBar::tab {
                    background-color: #444;
                    color: #FFD700;
                    padding: 10px 20px;
                    border-top-left-radius: 10px;
                    border-top-right-radius: 10px;
                    margin-right: 2px;
                    font-weight: bold;
                    font-family: 'Amiri';
                }
                QTabBar::tab:selected {
                    background-color: #FFD700;
                    color: black;
                }
                QWidget {
                    background-color: #2B2B2B;
                    color: #EEE;
                }
            """)
        else:
            self.setStyleSheet("""
                QTabWidget::pane { border: none; }
                QTabBar::tab {
                    background-color: #FFD700;
                    color: black;
                    padding: 10px 20px;
                    border-top-left-radius: 10px;
                    border-top-right-radius: 10px;
                    margin-right: 2px;
                    font-weight: bold;
                    font-family: 'Amiri';
                }
                QTabBar::tab:selected {
                    background-color: #FFC107;
                    color: white;
                }
                QWidget {
                    background-color: #FFFBEA;
                    color: #222;
                }
            """)

    # 🌗 تبديل الثيم عند الضغط
    def toggle_theme(self):
        if self.current_theme == "light":
            self.current_theme = "dark"
        else:
            self.current_theme = "light"
        self.apply_theme(self.current_theme)


# 🚀 تشغيل التطبيق
if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setFont(QFont("Amiri", 10))
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
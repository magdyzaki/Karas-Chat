# MainWindow.py
import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QTabWidget, QVBoxLayout,
    QLabel, QPushButton, QHBoxLayout
)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt

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

def PlaceholderPage(title):
    page = QWidget()
    layout = QVBoxLayout()
    label = QLabel(f"🚧 صفحة {title} تحت التطوير 🚧")
    label.setFont(QFont("Amiri", 18, QFont.Bold))
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
        self.tabs.addTab(PlaceholderPage("التقارير"), "التقارير")
        self.tabs.addTab(PlaceholderPage("الإشعارات"), "الإشعارات")
        self.tabs.addTab(PlaceholderPage("الصديق الذكي"), "الصديق الذكي")
        self.tabs.addTab(PlaceholderPage("الإعدادات"), "الإعدادات")

        # زر تبديل المظهر
        btn_theme = QPushButton("🌓 تبديل المظهر")
        btn_theme.setFont(QFont("Amiri", 11, QFont.Bold))
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
        if theme == "dark":
            self.setStyleSheet("""
                QWidget { background:#2B2B2B; color:#EEE; }
                QTabBar::tab { background:#444; color:#FFD700; padding:10px 18px; }
                QTabBar::tab:selected { background:#FFD700; color:black; }
            """)
        else:
            self.setStyleSheet("""
                QWidget { background:#FFFBEA; color:#222; }
                QTabBar::tab { background:#FFD700; color:black; padding:10px 18px; }
                QTabBar::tab:selected { background:#FFC107; color:white; }
            """)

    def toggle_theme(self):
        self.current_theme = "dark" if self.current_theme == "light" else "light"
        self.apply_theme(self.current_theme)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setFont(QFont("Amiri", 10))
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())
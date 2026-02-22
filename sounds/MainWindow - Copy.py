# MainWindow.py
import sys
import os
from PyQt5.QtWidgets import QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout, QLabel
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt

# تأكد أن مجلد pages في المسار الصحيح
from pages.InvoicesPage import InvoicesPage
# إذا عندك SalesPage.py ضمن pages، سيعمل. إذا اسمه مختلف عدل السطر التالي
try:
    from pages.SalesPage import SalesPage
except Exception:
    # إذا مفيش SalesPage أو اسمه غير موجود، ننشئ Tab مؤقت
    class SalesPage(QWidget):
        def __init__(self):
            super().__init__()
            l = QVBoxLayout()
            l.addWidget(QLabel("صفحة المبيعات (غير موجودة على القرص - مؤقت)"))
            self.setLayout(l)

# تبويب المدفوعات الجديد
from pages.PaymentsPage import PaymentsPage

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Smart CRM")
        self.resize(1100, 700)
        self.init_ui()

    def init_ui(self):
        tabs = QTabWidget()
        tabs.setTabsClosable(False)

        # تبويب المبيعات (أصلي)
        self.sales_tab = SalesPage()
        tabs.addTab(self.sales_tab, "المبيعات")

        # تبويب المدفوعات الجديد - يجب أن يكون قبل تبويب الفواتير
        self.payments_tab = PaymentsPage()
        tabs.addTab(self.payments_tab, "تحصيل الفواتير")

        # تبويب الفواتير الحالي (نترك ملف InvoicesPage كما هو)
        self.invoices_tab = InvoicesPage()
        tabs.addTab(self.invoices_tab, "إصدار فاتورة")

        # يمكنك إضافة تبويبات أخرى بعد ذلك إذا أردت
        # example:
        # from pages.CustomersPage import CustomersPage
        # tabs.addTab(CustomersPage(), "العملاء")

        self.setCentralWidget(tabs)

def main():
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
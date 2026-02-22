from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QTableWidget,
    QTableWidgetItem, QHeaderView
)
from PyQt5.QtGui import QFont, QColor
from PyQt5.QtCore import Qt
import sqlite3, os

DB = os.path.join(os.path.dirname(__file__), "..", "database", "crm.db")


class NotificationsPage(QWidget):
    def __init__(self):
        super().__init__()

        # إزالة الستايل الثابت للسماح بتطبيق الستايل من MainWindow
        # self.setStyleSheet("background-color:#FFFDF5;")  # تم إزالة الستايل الثابت
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        title = QLabel("🔔 الإشعارات والتنبيهات")
        title.setFont(QFont("Amiri", 20, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels([
            "النوع", "الوصف", "الحالة"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setDefaultSectionSize(40)

        layout.addWidget(self.table)
        self.setLayout(layout)

        self.load_notifications()

    def connect_db(self):
        return sqlite3.connect(DB)

    def add_notification(self, n_type, desc, status):
        r = self.table.rowCount()
        self.table.insertRow(r)

        items = [
            QTableWidgetItem(n_type),
            QTableWidgetItem(desc),
            QTableWidgetItem(status)
        ]

        for i, item in enumerate(items):
            item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(r, i, item)

        # 🎨 ألوان حسب النوع
        if "مخزون" in n_type:
            color = QColor("#FFCDD2")
        elif "عميل" in n_type:
            color = QColor("#FFF9C4")
        elif "فاتورة" in n_type:
            color = QColor("#BBDEFB")
        else:
            color = QColor("#C8E6C9")

        for i in range(3):
            self.table.item(r, i).setBackground(color)

    def load_notifications(self):
        self.table.setRowCount(0)
        conn = self.connect_db()
        cur = conn.cursor()

        # 🔴 تنبيه مخزون
        try:
            cur.execute("SELECT name, quantity FROM products WHERE quantity <= 10")
            for name, qty in cur.fetchall():
                self.add_notification(
                    "مخزون منخفض",
                    f"المنتج ({name}) المتبقي {qty}",
                    "⚠️ يحتاج إجراء"
                )
        except:
            pass

        # 🟡 عملاء Hot
        try:
            cur.execute("SELECT name FROM customers WHERE rating='Hot'")
            for (name,) in cur.fetchall():
                self.add_notification(
                    "عميل مهم",
                    f"العميل {name} مصنف Hot",
                    "📞 متابعة مطلوبة"
                )
        except:
            pass

        # 🟢 مبيعات
        try:
            cur.execute("SELECT product_name, quantity FROM sales ORDER BY id DESC LIMIT 5")
            for pname, qty in cur.fetchall():
                self.add_notification(
                    "عملية بيع",
                    f"بيع {qty} من {pname}",
                    "✅ تمت"
                )
        except:
            pass

        conn.close()

import os

# 📂 تحديد مسار مجلد الصفحات
PAGES_DIR = os.path.join(os.path.dirname(__file__), "pages")

# 🧩 أسماء الملفات اللي المفروض تكون موجودة
PAGES = [
    "InventoryPage",
    "SuppliersPage",
    "PurchasesPage",
    "NotificationsPage"
]

# 🧱 القالب الافتراضي لكل صفحة
TEMPLATE = '''from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt

class {class_name}(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        title = QLabel("📄 {title}")
        title.setFont(QFont("Amiri", 16, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        desc = QLabel("هذه الصفحة تحت التطوير — سيتم تفعيلها قريبًا ⚙️")
        desc.setAlignment(Qt.AlignCenter)
        desc.setStyleSheet("color:#666; font-size:14px; margin-top:10px;")
        layout.addWidget(desc)
        
        self.setLayout(layout)
'''

# 🚀 إنشاء المجلد إذا مش موجود
os.makedirs(PAGES_DIR, exist_ok=True)

for name in PAGES:
    file_path = os.path.join(PAGES_DIR, f"{name}.py")
    if not os.path.exists(file_path):
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(TEMPLATE.format(class_name=name, title=name.replace("Page", "")))
        print(f"✅ تم إنشاء الملف: {file_path}")
    else:
        print(f"⏩ الملف موجود مسبقًا: {file_path}")

print("\n🎯 جميع الصفحات تم التحقق منها أو إنشاؤها بنجاح.")
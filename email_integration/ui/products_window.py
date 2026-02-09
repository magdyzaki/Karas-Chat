"""
نافذة إدارة المنتجات
Products Management Window
"""
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QMessageBox, QTableWidget, QTableWidgetItem, QLineEdit,
    QGroupBox, QComboBox, QDoubleSpinBox, QTextEdit
)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt

from core.db import (
    get_all_products, add_product, update_product,
    delete_product, get_product_by_id
)


class ProductsWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setWindowTitle("📦 إدارة المنتجات - Products Management")
        self.setMinimumSize(900, 600)
        
        main_layout = QVBoxLayout(self)
        
        # العنوان
        title = QLabel("📦 إدارة المنتجات - Products Management")
        title.setFont(QFont("Segoe UI", 14, QFont.Bold))
        main_layout.addWidget(title)
        
        # البحث
        search_group = QGroupBox("بحث - Search")
        search_layout = QHBoxLayout()
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("ابحث في اسم المنتج، الكود، الفئة...")
        self.search_input.textChanged.connect(self.load_products)
        search_layout.addWidget(self.search_input)
        
        search_group.setLayout(search_layout)
        main_layout.addWidget(search_group)
        
        # جدول المنتجات
        self.products_table = QTableWidget()
        self.products_table.setColumnCount(8)
        self.products_table.setHorizontalHeaderLabels([
            "ID", "اسم المنتج", "الكود", "الفئة", "الوحدة", "سعر البيع", "سعر التكلفة", "الربح"
        ])
        self.products_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.products_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.products_table.setSortingEnabled(True)
        self.products_table.horizontalHeader().setStretchLastSection(True)
        self.products_table.cellDoubleClicked.connect(self.edit_product)
        main_layout.addWidget(self.products_table)
        
        # الأزرار
        buttons_layout = QHBoxLayout()
        
        self.add_btn = QPushButton("➕ إضافة منتج")
        self.add_btn.clicked.connect(self.add_product)
        self.add_btn.setStyleSheet("background-color: #4ECDC4; color: white; font-weight: bold; border-radius: 5px; padding: 8px;")
        buttons_layout.addWidget(self.add_btn)
        
        self.edit_btn = QPushButton("✏️ تعديل")
        self.edit_btn.clicked.connect(self.edit_product)
        buttons_layout.addWidget(self.edit_btn)
        
        self.delete_btn = QPushButton("🗑 حذف")
        self.delete_btn.clicked.connect(self.delete_selected_product)
        self.delete_btn.setStyleSheet("background-color: #FF6B6B; color: white; font-weight: bold; border-radius: 5px; padding: 8px;")
        buttons_layout.addWidget(self.delete_btn)
        
        buttons_layout.addStretch()
        
        self.close_btn = QPushButton("❌ إغلاق")
        self.close_btn.clicked.connect(self.accept)
        buttons_layout.addWidget(self.close_btn)
        
        main_layout.addLayout(buttons_layout)
        
        # تحميل المنتجات
        self.load_products()
    
    def load_products(self):
        """تحميل المنتجات"""
        search_text = self.search_input.text().strip().lower()
        products = get_all_products(active_only=False)
        
        # فلترة حسب البحث
        if search_text:
            filtered_products = []
            for product in products:
                (
                    product_id, product_name, product_code, category,
                    unit, unit_price, cost_price, description,
                    specifications, active, created_date
                ) = product
                
                if (search_text in (product_name or "").lower() or
                    search_text in (product_code or "").lower() or
                    search_text in (category or "").lower()):
                    filtered_products.append(product)
            products = filtered_products
        
        # عرض في الجدول
        self.products_table.setRowCount(len(products))
        
        for row, product in enumerate(products):
            (
                product_id, product_name, product_code, category,
                unit, unit_price, cost_price, description,
                specifications, active, created_date
            ) = product
            
            unit_price = unit_price or 0
            cost_price = cost_price or 0
            profit = unit_price - cost_price
            profit_margin = (profit / unit_price * 100) if unit_price > 0 else 0
            
            values = [
                str(product_id),
                product_name or "",
                product_code or "",
                category or "",
                unit or "",
                f"${unit_price:.2f}",
                f"${cost_price:.2f}",
                f"${profit:.2f} ({profit_margin:.1f}%)"
            ]
            
            for col, val in enumerate(values):
                item = QTableWidgetItem(str(val))
                item.setData(Qt.UserRole, product_id)
                self.products_table.setItem(row, col, item)
                
                # تلوين الربح
                if col == 7:
                    if profit < 0:
                        item.setForeground(Qt.red)
                    elif profit_margin < 10:
                        item.setForeground(Qt.darkYellow)
                    else:
                        item.setForeground(Qt.darkGreen)
    
    def get_selected_product_id(self):
        """الحصول على معرف المنتج المحدد"""
        row = self.products_table.currentRow()
        if row < 0:
            return None
        
        item = self.products_table.item(row, 0)
        if item:
            return item.data(Qt.UserRole)
        return None
    
    def add_product(self):
        """إضافة منتج جديد"""
        dialog = ProductEditDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            data = dialog.get_data()
            try:
                add_product(data)
                QMessageBox.information(self, "نجح", "تم إضافة المنتج بنجاح")
                self.load_products()
            except Exception as e:
                QMessageBox.critical(self, "خطأ", f"حدث خطأ أثناء الإضافة:\n{str(e)}")
    
    def edit_product(self):
        """تعديل منتج"""
        product_id = self.get_selected_product_id()
        if not product_id:
            QMessageBox.warning(self, "تنبيه", "الرجاء تحديد منتج أولاً")
            return
        
        product = get_product_by_id(product_id)
        if not product:
            return
        
        dialog = ProductEditDialog(self, product)
        if dialog.exec_() == QDialog.Accepted:
            data = dialog.get_data()
            try:
                update_product(product_id, data)
                QMessageBox.information(self, "نجح", "تم تحديث المنتج بنجاح")
                self.load_products()
            except Exception as e:
                QMessageBox.critical(self, "خطأ", f"حدث خطأ أثناء التحديث:\n{str(e)}")
    
    def delete_selected_product(self):
        """حذف المنتج المحدد"""
        product_id = self.get_selected_product_id()
        if not product_id:
            QMessageBox.warning(self, "تنبيه", "الرجاء تحديد منتج أولاً")
            return
        
        product = get_product_by_id(product_id)
        if not product:
            return
        
        product_name = product[1]
        
        reply = QMessageBox.question(
            self,
            "تأكيد الحذف",
            f"هل تريد حذف المنتج '{product_name}'؟",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                delete_product(product_id)
                QMessageBox.information(self, "نجح", "تم حذف المنتج بنجاح")
                self.load_products()
            except Exception as e:
                QMessageBox.critical(self, "خطأ", f"حدث خطأ أثناء الحذف:\n{str(e)}")


class ProductEditDialog(QDialog):
    def __init__(self, parent=None, product=None):
        super().__init__(parent)
        
        self.product = product
        self.setWindowTitle("إضافة/تعديل منتج" if product else "إضافة منتج")
        self.setMinimumWidth(500)
        
        layout = QVBoxLayout(self)
        
        # اسم المنتج
        layout.addWidget(QLabel("اسم المنتج *:"))
        self.name_input = QLineEdit()
        if product:
            self.name_input.setText(product[1] or "")
        layout.addWidget(self.name_input)
        
        # الكود
        layout.addWidget(QLabel("كود المنتج:"))
        self.code_input = QLineEdit()
        if product:
            self.code_input.setText(product[2] or "")
        layout.addWidget(self.code_input)
        
        # الفئة
        layout.addWidget(QLabel("الفئة:"))
        self.category_input = QLineEdit()
        if product:
            self.category_input.setText(product[3] or "")
        layout.addWidget(self.category_input)
        
        # الوحدة
        layout.addWidget(QLabel("الوحدة:"))
        self.unit_input = QLineEdit()
        self.unit_input.setPlaceholderText("مثال: kg, ton, piece")
        if product:
            self.unit_input.setText(product[4] or "")
        layout.addWidget(self.unit_input)
        
        # السعر والتكلفة
        price_layout = QHBoxLayout()
        
        price_layout.addWidget(QLabel("سعر البيع:"))
        self.price_input = QDoubleSpinBox()
        self.price_input.setMaximum(999999.99)
        self.price_input.setPrefix("$ ")
        if product:
            self.price_input.setValue(product[5] or 0)
        price_layout.addWidget(self.price_input)
        
        price_layout.addWidget(QLabel("سعر التكلفة:"))
        self.cost_input = QDoubleSpinBox()
        self.cost_input.setMaximum(999999.99)
        self.cost_input.setPrefix("$ ")
        if product:
            self.cost_input.setValue(product[6] or 0)
        price_layout.addWidget(self.cost_input)
        
        layout.addLayout(price_layout)
        
        # الوصف
        layout.addWidget(QLabel("الوصف:"))
        self.description_input = QTextEdit()
        self.description_input.setMaximumHeight(80)
        if product:
            self.description_input.setPlainText(product[7] or "")
        layout.addWidget(self.description_input)
        
        # الأزرار
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        
        save_btn = QPushButton("💾 حفظ")
        save_btn.clicked.connect(self.accept)
        save_btn.setStyleSheet("background-color: #4ECDC4; color: white; font-weight: bold; border-radius: 5px; padding: 8px;")
        buttons_layout.addWidget(save_btn)
        
        cancel_btn = QPushButton("إلغاء")
        cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_btn)
        
        layout.addLayout(buttons_layout)
    
    def get_data(self):
        """الحصول على البيانات"""
        return {
            "product_name": self.name_input.text().strip(),
            "product_code": self.code_input.text().strip() or None,
            "category": self.category_input.text().strip() or None,
            "unit": self.unit_input.text().strip() or None,
            "unit_price": self.price_input.value(),
            "cost_price": self.cost_input.value(),
            "description": self.description_input.toPlainText().strip() or None,
            "specifications": None,
            "active": 1
        }
    
    def accept(self):
        """التحقق من البيانات قبل الحفظ"""
        if not self.name_input.text().strip():
            QMessageBox.warning(self, "تنبيه", "اسم المنتج مطلوب")
            return
        
        super().accept()

"""
نافذة إضافة صفقة جديدة
Add Deal Popup
"""
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QComboBox, QDoubleSpinBox, QDateEdit, QTextEdit,
    QFormLayout, QMessageBox
)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt, QDate
from datetime import datetime

from core.sales import add_sale_deal, SALES_STAGES, STAGE_PROBABILITY
from core.db import get_all_clients, get_all_products


class AddDealPopup(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setWindowTitle("➕ Add New Deal")
        self.setMinimumSize(500, 400)
        
        layout = QVBoxLayout(self)
        
        title = QLabel("➕ Add New Deal")
        title.setFont(QFont("Segoe UI", 12, QFont.Bold))
        layout.addWidget(title)
        
        form = QFormLayout()
        
        # Client
        self.client_combo = QComboBox()
        clients = get_all_clients()
        self.client_combo.addItem("-- Select Client --", None)
        for client in clients:
            client_id, company = client[0], client[1]
            self.client_combo.addItem(company or f"Client {client_id}", client_id)
        form.addRow("Client:", self.client_combo)
        
        # Deal Name
        self.deal_name_input = QLineEdit()
        form.addRow("Deal Name:", self.deal_name_input)
        
        # Product Name
        self.product_combo = QComboBox()
        self.product_combo.setEditable(True)  # يمكن إدخال منتج جديد
        self.product_combo.addItem("-- Select or Enter Product --", None)
        try:
            products = get_all_products(active_only=True)
            for product in products:
                product_id, product_name = product[0], product[1]
                self.product_combo.addItem(product_name or f"Product {product_id}", product_name)
        except Exception:
            pass  # إذا لم يكن هناك منتجات
        form.addRow("Product Name:", self.product_combo)
        
        # Stage
        self.stage_combo = QComboBox()
        self.stage_combo.addItems(SALES_STAGES)
        self.stage_combo.currentIndexChanged.connect(self.on_stage_changed)
        form.addRow("Stage:", self.stage_combo)
        
        # Value
        self.value_spin = QDoubleSpinBox()
        self.value_spin.setMaximum(999999999)
        self.value_spin.setValue(0)
        form.addRow("Value:", self.value_spin)
        
        # Currency
        self.currency_combo = QComboBox()
        self.currency_combo.addItems(["USD", "EUR", "GBP", "EGP", "SAR", "AED"])
        form.addRow("Currency:", self.currency_combo)
        
        # Probability
        self.probability_spin = QDoubleSpinBox()
        self.probability_spin.setRange(0, 100)
        self.probability_spin.setSuffix("%")
        self.probability_spin.setValue(10)
        form.addRow("Probability:", self.probability_spin)
        
        # Expected Close Date
        self.expected_date = QDateEdit()
        self.expected_date.setDate(QDate.currentDate().addMonths(1))
        self.expected_date.setCalendarPopup(True)
        form.addRow("Expected Close Date:", self.expected_date)
        
        # Notes
        self.notes_text = QTextEdit()
        self.notes_text.setMaximumHeight(100)
        form.addRow("Notes:", self.notes_text)
        
        layout.addLayout(form)
        
        # Buttons
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("💾 Save")
        save_btn.clicked.connect(self.save_deal)
        btn_layout.addWidget(save_btn)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addStretch()
        btn_layout.addWidget(cancel_btn)
        
        layout.addLayout(btn_layout)
    
    def on_stage_changed(self):
        """عند تغيير المرحلة"""
        stage = self.stage_combo.currentText()
        probability = STAGE_PROBABILITY.get(stage, 0.1) * 100
        self.probability_spin.setValue(probability)
    
    def save_deal(self):
        """حفظ الصفقة"""
        client_id = self.client_combo.currentData()
        if not client_id:
            QMessageBox.warning(self, "Error", "Please select a client!")
            return
        
        deal_name = self.deal_name_input.text().strip()
        if not deal_name:
            QMessageBox.warning(self, "Error", "Please enter a deal name!")
            return
        
        # الحصول على اسم المنتج
        product_name = self.product_combo.currentText().strip()
        if product_name == "-- Select or Enter Product --":
            product_name = None
        
        data = {
            "client_id": client_id,
            "deal_name": deal_name,
            "product_name": product_name if product_name else None,
            "stage": self.stage_combo.currentText(),
            "value": self.value_spin.value(),
            "currency": self.currency_combo.currentText(),
            "probability": self.probability_spin.value() / 100,
            "expected_close_date": self.expected_date.date().toString("dd/MM/yyyy"),
            "notes": self.notes_text.toPlainText()
        }
        
        try:
            add_sale_deal(data)
            QMessageBox.information(self, "Success", "Deal added successfully!")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to add deal:\n{str(e)}")

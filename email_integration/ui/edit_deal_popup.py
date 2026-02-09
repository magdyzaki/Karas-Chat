"""
نافذة تعديل صفقة
Edit Deal Popup
"""
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QComboBox, QDoubleSpinBox, QDateEdit, QTextEdit,
    QFormLayout, QMessageBox
)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt, QDate
from datetime import datetime

from core.sales import (
    get_deal_by_id, update_sale_deal, SALES_STAGES, STAGE_PROBABILITY
)
from core.db import get_all_products


class EditDealPopup(QDialog):
    def __init__(self, deal_id, parent=None):
        super().__init__(parent)
        
        self.deal_id = deal_id
        self.setWindowTitle("✏️ Edit Deal")
        self.setMinimumSize(500, 400)
        
        layout = QVBoxLayout(self)
        
        title = QLabel("✏️ Edit Deal")
        title.setFont(QFont("Segoe UI", 12, QFont.Bold))
        layout.addWidget(title)
        
        form = QFormLayout()
        
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
        form.addRow("Value:", self.value_spin)
        
        # Currency
        self.currency_combo = QComboBox()
        self.currency_combo.addItems(["USD", "EUR", "GBP", "EGP", "SAR", "AED"])
        form.addRow("Currency:", self.currency_combo)
        
        # Probability
        self.probability_spin = QDoubleSpinBox()
        self.probability_spin.setRange(0, 100)
        self.probability_spin.setSuffix("%")
        form.addRow("Probability:", self.probability_spin)
        
        # Expected Close Date
        self.expected_date = QDateEdit()
        self.expected_date.setCalendarPopup(True)
        form.addRow("Expected Close Date:", self.expected_date)
        
        # Actual Close Date
        self.actual_date = QDateEdit()
        self.actual_date.setCalendarPopup(True)
        form.addRow("Actual Close Date:", self.actual_date)
        
        # Status
        self.status_combo = QComboBox()
        self.status_combo.addItems(["active", "inactive"])
        form.addRow("Status:", self.status_combo)
        
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
        
        # Load data
        self.load_deal()
    
    def load_deal(self):
        """تحميل بيانات الصفقة"""
        deal = get_deal_by_id(self.deal_id)
        if not deal:
            QMessageBox.critical(self, "Error", "Deal not found!")
            self.reject()
            return
        
        (
            deal_id, client_id, company, deal_name, product_name, stage,
            value, currency, probability, expected_close, actual_close,
            status, notes, created, updated
        ) = deal
        
        self.deal_name_input.setText(deal_name or "")
        
        # تعيين المنتج
        if product_name:
            index = self.product_combo.findText(product_name)
            if index >= 0:
                self.product_combo.setCurrentIndex(index)
            else:
                self.product_combo.setCurrentText(product_name)
        else:
            self.product_combo.setCurrentIndex(0)
        self.stage_combo.setCurrentText(stage or "Lead")
        self.value_spin.setValue(value or 0)
        
        index = self.currency_combo.findText(currency or "USD")
        if index >= 0:
            self.currency_combo.setCurrentIndex(index)
        
        self.probability_spin.setValue((probability or 0.1) * 100)
        
        if expected_close:
            try:
                parts = expected_close.split("/")
                if len(parts) == 3:
                    date = QDate(int(parts[2]), int(parts[1]), int(parts[0]))
                    self.expected_date.setDate(date)
            except Exception:
                pass
        
        if actual_close:
            try:
                parts = actual_close.split("/")
                if len(parts) == 3:
                    date = QDate(int(parts[2]), int(parts[1]), int(parts[0]))
                    self.actual_date.setDate(date)
            except Exception:
                pass
        
        index = self.status_combo.findText(status or "active")
        if index >= 0:
            self.status_combo.setCurrentIndex(index)
        
        self.notes_text.setPlainText(notes or "")
    
    def on_stage_changed(self):
        """عند تغيير المرحلة"""
        stage = self.stage_combo.currentText()
        probability = STAGE_PROBABILITY.get(stage, 0.1) * 100
        self.probability_spin.setValue(probability)
    
    def save_deal(self):
        """حفظ التعديلات"""
        # الحصول على اسم المنتج
        product_name = self.product_combo.currentText().strip()
        if product_name == "-- Select or Enter Product --":
            product_name = None
        
        data = {
            "deal_name": self.deal_name_input.text().strip(),
            "product_name": product_name if product_name else None,
            "stage": self.stage_combo.currentText(),
            "value": self.value_spin.value(),
            "currency": self.currency_combo.currentText(),
            "probability": self.probability_spin.value() / 100,
            "expected_close_date": self.expected_date.date().toString("dd/MM/yyyy"),
            "actual_close_date": self.actual_date.date().toString("dd/MM/yyyy") if self.actual_date.date().isValid() else None,
            "status": self.status_combo.currentText(),
            "notes": self.notes_text.toPlainText()
        }
        
        try:
            update_sale_deal(self.deal_id, data)
            QMessageBox.information(self, "Success", "Deal updated successfully!")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to update deal:\n{str(e)}")

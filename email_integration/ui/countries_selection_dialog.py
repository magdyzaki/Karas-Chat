"""
نافذة منبثقة لاختيار الدول
Countries Selection Dialog
"""
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QCheckBox, QScrollArea, QWidget, QGridLayout
)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt


class CountriesSelectionDialog(QDialog):
    def __init__(self, parent=None, selected_countries=None):
        super().__init__(parent)
        
        self.setWindowTitle("🌍 اختر الدول - Select Countries")
        self.setMinimumSize(600, 500)
        self.resize(650, 550)
        
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(10)
        
        # العنوان
        title = QLabel("🌍 اختر الدول - Select Countries")
        title.setFont(QFont("Segoe UI", 12, QFont.Bold))
        main_layout.addWidget(title)
        
        # قائمة الدول الأوروبية
        eu_countries = [
            "Austria", "Belgium", "Bulgaria", "Croatia", "Cyprus", "Czech Republic",
            "Denmark", "Estonia", "Finland", "France", "Germany", "Greece", "Hungary",
            "Ireland", "Italy", "Latvia", "Lithuania", "Luxembourg", "Malta",
            "Netherlands", "Poland", "Portugal", "Romania", "Slovakia", "Slovenia",
            "Spain", "Sweden", "United Kingdom"
        ]
        
        # قائمة الدول الأمريكية
        us_countries = ["USA", "United States"]
        
        # منطقة تمرير للدول
        scroll = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QGridLayout()
        scroll_widget.setLayout(scroll_layout)
        
        self.country_checkboxes = {}
        row, col = 0, 0
        
        # جميع الدول
        self.all_countries_checkbox = QCheckBox("✅ تحديد الكل / Select All")
        self.all_countries_checkbox.stateChanged.connect(self.toggle_all_countries)
        scroll_layout.addWidget(self.all_countries_checkbox, 0, 0, 1, 3)
        
        # الاتحاد الأوروبي
        eu_label = QLabel("🇪🇺 الاتحاد الأوروبي - European Union:")
        eu_label.setFont(QFont("Segoe UI", 10, QFont.Bold))
        scroll_layout.addWidget(eu_label, 1, 0, 1, 3)
        
        row = 2
        for country in eu_countries:
            checkbox = QCheckBox(country)
            # تحديد الدول المحددة مسبقاً
            if selected_countries is None or country in selected_countries:
                checkbox.setChecked(True)
            checkbox.stateChanged.connect(self.update_select_all)
            self.country_checkboxes[country] = checkbox
            scroll_layout.addWidget(checkbox, row, col)
            col += 1
            if col > 2:
                col = 0
                row += 1
        
        row += 1
        us_label = QLabel("🇺🇸 أمريكا - United States:")
        us_label.setFont(QFont("Segoe UI", 10, QFont.Bold))
        scroll_layout.addWidget(us_label, row, 0, 1, 3)
        
        row += 1
        col = 0
        for country in us_countries:
            checkbox = QCheckBox(country)
            # تحديد الدول المحددة مسبقاً
            if selected_countries is None or country in selected_countries:
                checkbox.setChecked(True)
            checkbox.stateChanged.connect(self.update_select_all)
            self.country_checkboxes[country] = checkbox
            scroll_layout.addWidget(checkbox, row, col)
            col += 1
            if col > 2:
                col = 0
                row += 1
        
        scroll.setWidget(scroll_widget)
        scroll.setWidgetResizable(True)
        main_layout.addWidget(scroll)
        
        # الأزرار
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        
        ok_btn = QPushButton("✅ موافق")
        ok_btn.clicked.connect(self.accept)
        ok_btn.setStyleSheet("background-color: #4ECDC4; color: white; font-weight: bold; border-radius: 5px; padding: 8px;")
        buttons_layout.addWidget(ok_btn)
        
        cancel_btn = QPushButton("❌ إلغاء")
        cancel_btn.clicked.connect(self.reject)
        cancel_btn.setStyleSheet("background-color: #CCCCCC; color: #333333; font-weight: bold; border-radius: 5px; padding: 8px;")
        buttons_layout.addWidget(cancel_btn)
        
        main_layout.addLayout(buttons_layout)
    
    def toggle_all_countries(self, state):
        """تحديد/إلغاء تحديد جميع الدول"""
        checked = (state == Qt.Checked)
        for checkbox in self.country_checkboxes.values():
            checkbox.blockSignals(True)
            checkbox.setChecked(checked)
            checkbox.blockSignals(False)
    
    def update_select_all(self):
        """تحديث حالة زر تحديد الكل"""
        all_checked = all(cb.isChecked() for cb in self.country_checkboxes.values())
        none_checked = not any(cb.isChecked() for cb in self.country_checkboxes.values())
        
        self.all_countries_checkbox.blockSignals(True)
        if all_checked:
            self.all_countries_checkbox.setCheckState(Qt.Checked)
        elif none_checked:
            self.all_countries_checkbox.setCheckState(Qt.Unchecked)
        else:
            self.all_countries_checkbox.setCheckState(Qt.PartiallyChecked)
        self.all_countries_checkbox.blockSignals(False)
    
    def get_selected_countries(self):
        """الحصول على قائمة الدول المحددة"""
        selected = []
        for country, checkbox in self.country_checkboxes.items():
            if checkbox.isChecked():
                selected.append(country)
        return selected

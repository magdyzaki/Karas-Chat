"""
نافذة إدارة عوامل التقييم القابلة للتخصيص
Customizable Scoring Factors Configuration Window
"""
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTableWidget, QTableWidgetItem,
    QMessageBox, QLineEdit, QCheckBox, QSpinBox,
    QTabWidget, QWidget, QGroupBox, QComboBox,
    QHeaderView, QAbstractItemView
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor

from core.scoring_config import (
    load_scoring_config,
    save_scoring_config,
    get_classification_thresholds,
    update_score_rule,
    is_ai_enabled,
    set_ai_enabled,
    is_trend_analysis_enabled,
    set_trend_analysis_enabled,
    DEFAULT_SCORE_RULES,
    DEFAULT_CLASSIFICATION_THRESHOLDS
)


class ScoringConfigWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("إعدادات نظام التقييم")
        self.setMinimumSize(900, 700)
        
        self.config = load_scoring_config()
        
        self.init_ui()
        self.load_data()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # ===== Tabs =====
        tabs = QTabWidget()
        
        # Tab 1: عوامل التقييم
        score_rules_tab = QWidget()
        score_rules_layout = QVBoxLayout()
        
        # جدول عوامل التقييم
        self.score_rules_table = QTableWidget()
        self.score_rules_table.setColumnCount(4)
        self.score_rules_table.setHorizontalHeaderLabels([
            "اسم العامل", "النقاط", "مفعّل", "الوصف"
        ])
        self.score_rules_table.horizontalHeader().setStretchLastSection(True)
        self.score_rules_table.setAlternatingRowColors(True)
        self.score_rules_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        
        score_rules_layout.addWidget(QLabel("<b>عوامل التقييم:</b>"))
        score_rules_layout.addWidget(self.score_rules_table)
        
        # أزرار التحكم
        rules_buttons = QHBoxLayout()
        add_rule_btn = QPushButton("إضافة عامل جديد")
        add_rule_btn.clicked.connect(self.add_new_rule)
        remove_rule_btn = QPushButton("حذف المحدد")
        remove_rule_btn.clicked.connect(self.remove_selected_rule)
        save_rules_btn = QPushButton("حفظ التغييرات")
        save_rules_btn.clicked.connect(self.save_score_rules)
        save_rules_btn.setStyleSheet("background-color: #4ECDC4; font-weight: bold;")
        
        rules_buttons.addWidget(add_rule_btn)
        rules_buttons.addWidget(remove_rule_btn)
        rules_buttons.addStretch()
        rules_buttons.addWidget(save_rules_btn)
        
        score_rules_layout.addLayout(rules_buttons)
        score_rules_tab.setLayout(score_rules_layout)
        tabs.addTab(score_rules_tab, "عوامل التقييم")
        
        # Tab 2: عتبات التصنيف
        thresholds_tab = QWidget()
        thresholds_layout = QVBoxLayout()
        
        self.thresholds_table = QTableWidget()
        self.thresholds_table.setColumnCount(5)
        self.thresholds_table.setHorizontalHeaderLabels([
            "التصنيف", "أقل نقاط", "الأيقونة", "التسمية", "اللون"
        ])
        self.thresholds_table.horizontalHeader().setStretchLastSection(True)
        self.thresholds_table.setAlternatingRowColors(True)
        self.thresholds_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        
        thresholds_layout.addWidget(QLabel("<b>عتبات التصنيف:</b>"))
        thresholds_layout.addWidget(self.thresholds_table)
        
        thresholds_buttons = QHBoxLayout()
        add_threshold_btn = QPushButton("إضافة تصنيف جديد")
        add_threshold_btn.clicked.connect(self.add_new_threshold)
        remove_threshold_btn = QPushButton("حذف المحدد")
        remove_threshold_btn.clicked.connect(self.remove_selected_threshold)
        save_thresholds_btn = QPushButton("حفظ التغييرات")
        save_thresholds_btn.clicked.connect(self.save_thresholds)
        save_thresholds_btn.setStyleSheet("background-color: #4ECDC4; font-weight: bold;")
        
        thresholds_buttons.addWidget(add_threshold_btn)
        thresholds_buttons.addWidget(remove_threshold_btn)
        thresholds_buttons.addStretch()
        thresholds_buttons.addWidget(save_thresholds_btn)
        
        thresholds_layout.addLayout(thresholds_buttons)
        thresholds_tab.setLayout(thresholds_layout)
        tabs.addTab(thresholds_tab, "عتبات التصنيف")
        
        # Tab 3: إعدادات عامة
        general_tab = QWidget()
        general_layout = QVBoxLayout()
        
        general_group = QGroupBox("الإعدادات العامة")
        general_group_layout = QVBoxLayout()
        
        # تفعيل الذكاء الاصطناعي
        ai_checkbox_layout = QHBoxLayout()
        self.ai_enabled_checkbox = QCheckBox("تفعيل التقييم المتقدم بالذكاء الاصطناعي")
        self.ai_enabled_checkbox.setChecked(is_ai_enabled())
        ai_checkbox_layout.addWidget(self.ai_enabled_checkbox)
        ai_checkbox_layout.addStretch()
        general_group_layout.addLayout(ai_checkbox_layout)
        
        # تفعيل تتبع الاتجاهات
        trend_checkbox_layout = QHBoxLayout()
        self.trend_enabled_checkbox = QCheckBox("تفعيل تتبع اتجاهات النقاط")
        self.trend_enabled_checkbox.setChecked(is_trend_analysis_enabled())
        trend_checkbox_layout.addWidget(self.trend_enabled_checkbox)
        trend_checkbox_layout.addStretch()
        general_group_layout.addLayout(trend_checkbox_layout)
        
        general_group.setLayout(general_group_layout)
        general_layout.addWidget(general_group)
        general_layout.addStretch()
        
        # زر إعادة التعيين
        reset_buttons = QHBoxLayout()
        reset_defaults_btn = QPushButton("إعادة التعيين للقيم الافتراضية")
        reset_defaults_btn.clicked.connect(self.reset_to_defaults)
        reset_defaults_btn.setStyleSheet("background-color: #FF6B6B; color: white;")
        reset_buttons.addWidget(reset_defaults_btn)
        reset_buttons.addStretch()
        general_layout.addLayout(reset_buttons)
        
        general_tab.setLayout(general_layout)
        tabs.addTab(general_tab, "إعدادات عامة")
        
        layout.addWidget(tabs)
        
        # ===== Buttons =====
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        
        close_btn = QPushButton("إغلاق")
        close_btn.clicked.connect(self.accept)
        buttons_layout.addWidget(close_btn)
        
        layout.addLayout(buttons_layout)
        
        self.setLayout(layout)
    
    def load_data(self):
        """تحميل البيانات في الجداول"""
        # تحميل عوامل التقييم
        score_rules = self.config.get("score_rules", {})
        self.score_rules_table.setRowCount(len(score_rules))
        
        for row, (rule_name, rule_data) in enumerate(score_rules.items()):
            # اسم العامل
            name_item = QTableWidgetItem(rule_name)
            name_item.setFlags(name_item.flags() & ~Qt.ItemIsEditable)
            self.score_rules_table.setItem(row, 0, name_item)
            
            # النقاط
            score_item = QTableWidgetItem(str(rule_data.get("score", 0)))
            self.score_rules_table.setItem(row, 1, score_item)
            
            # مفعّل
            enabled_item = QTableWidgetItem()
            enabled_item.setCheckState(Qt.Checked if rule_data.get("enabled", True) else Qt.Unchecked)
            self.score_rules_table.setItem(row, 2, enabled_item)
            
            # الوصف
            desc_item = QTableWidgetItem(rule_data.get("description", ""))
            self.score_rules_table.setItem(row, 3, desc_item)
        
        # تحميل عتبات التصنيف
        thresholds = self.config.get("classification_thresholds", {})
        self.thresholds_table.setRowCount(len(thresholds))
        
        for row, (key, threshold_data) in enumerate(thresholds.items()):
            # المفتاح (غير قابل للتحرير)
            key_item = QTableWidgetItem(key)
            key_item.setFlags(key_item.flags() & ~Qt.ItemIsEditable)
            self.thresholds_table.setItem(row, 0, key_item)
            
            # أقل نقاط
            min_score_item = QTableWidgetItem(str(threshold_data.get("min_score", 0)))
            self.thresholds_table.setItem(row, 1, min_score_item)
            
            # الأيقونة
            icon_item = QTableWidgetItem(threshold_data.get("icon", ""))
            self.thresholds_table.setItem(row, 2, icon_item)
            
            # التسمية
            label_item = QTableWidgetItem(threshold_data.get("label", ""))
            self.thresholds_table.setItem(row, 3, label_item)
            
            # اللون
            color_item = QTableWidgetItem(threshold_data.get("color", "#000000"))
            self.thresholds_table.setItem(row, 4, color_item)
        
        # تعديل عرض الأعمدة
        self.score_rules_table.resizeColumnsToContents()
        self.thresholds_table.resizeColumnsToContents()
    
    def save_score_rules(self):
        """حفظ عوامل التقييم"""
        try:
            score_rules = {}
            
            for row in range(self.score_rules_table.rowCount()):
                rule_name = self.score_rules_table.item(row, 0).text()
                if not rule_name:
                    continue
                
                score_text = self.score_rules_table.item(row, 1).text()
                try:
                    score = int(score_text)
                except ValueError:
                    QMessageBox.warning(self, "خطأ", f"النقاط غير صحيحة في الصف {row + 1}")
                    return
                
                enabled = self.score_rules_table.item(row, 2).checkState() == Qt.Checked
                description = self.score_rules_table.item(row, 3).text()
                
                score_rules[rule_name] = {
                    "score": score,
                    "enabled": enabled,
                    "description": description
                }
            
            self.config["score_rules"] = score_rules
            save_scoring_config(self.config)
            
            QMessageBox.information(self, "نجح", "تم حفظ عوامل التقييم بنجاح!")
            self.load_data()
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل الحفظ: {str(e)}")
    
    def save_thresholds(self):
        """حفظ عتبات التصنيف"""
        try:
            thresholds = {}
            
            for row in range(self.thresholds_table.rowCount()):
                key = self.thresholds_table.item(row, 0).text()
                if not key:
                    continue
                
                min_score_text = self.thresholds_table.item(row, 1).text()
                try:
                    min_score = int(min_score_text)
                except ValueError:
                    QMessageBox.warning(self, "خطأ", f"أقل نقاط غير صحيحة في الصف {row + 1}")
                    return
                
                icon = self.thresholds_table.item(row, 2).text()
                label = self.thresholds_table.item(row, 3).text()
                color = self.thresholds_table.item(row, 4).text()
                
                thresholds[key] = {
                    "min_score": min_score,
                    "icon": icon,
                    "label": label,
                    "color": color
                }
            
            self.config["classification_thresholds"] = thresholds
            save_scoring_config(self.config)
            
            QMessageBox.information(self, "نجح", "تم حفظ عتبات التصنيف بنجاح!")
            self.load_data()
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل الحفظ: {str(e)}")
    
    def add_new_rule(self):
        """إضافة عامل تقييم جديد"""
        row = self.score_rules_table.rowCount()
        self.score_rules_table.insertRow(row)
        
        name_item = QTableWidgetItem("new_rule")
        self.score_rules_table.setItem(row, 0, name_item)
        
        score_item = QTableWidgetItem("0")
        self.score_rules_table.setItem(row, 1, score_item)
        
        enabled_item = QTableWidgetItem()
        enabled_item.setCheckState(Qt.Checked)
        self.score_rules_table.setItem(row, 2, enabled_item)
        
        desc_item = QTableWidgetItem("")
        self.score_rules_table.setItem(row, 3, desc_item)
    
    def remove_selected_rule(self):
        """حذف عامل التقييم المحدد"""
        current_row = self.score_rules_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "تحذير", "يرجى اختيار عامل للحذف")
            return
        
        if QMessageBox.question(
            self, "تأكيد", "هل أنت متأكد من حذف هذا العامل؟",
            QMessageBox.Yes | QMessageBox.No
        ) == QMessageBox.Yes:
            self.score_rules_table.removeRow(current_row)
    
    def add_new_threshold(self):
        """إضافة عتبة تصنيف جديدة"""
        row = self.thresholds_table.rowCount()
        self.thresholds_table.insertRow(row)
        
        key_item = QTableWidgetItem("new_classification")
        self.thresholds_table.setItem(row, 0, key_item)
        
        min_score_item = QTableWidgetItem("0")
        self.thresholds_table.setItem(row, 1, min_score_item)
        
        icon_item = QTableWidgetItem("⭐")
        self.thresholds_table.setItem(row, 2, icon_item)
        
        label_item = QTableWidgetItem("New Classification")
        self.thresholds_table.setItem(row, 3, label_item)
        
        color_item = QTableWidgetItem("#95A5A6")
        self.thresholds_table.setItem(row, 4, color_item)
    
    def remove_selected_threshold(self):
        """حذف عتبة التصنيف المحددة"""
        current_row = self.thresholds_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "تحذير", "يرجى اختيار عتبة للحذف")
            return
        
        if QMessageBox.question(
            self, "تأكيد", "هل أنت متأكد من حذف هذه العتبة؟",
            QMessageBox.Yes | QMessageBox.No
        ) == QMessageBox.Yes:
            self.thresholds_table.removeRow(current_row)
    
    def reset_to_defaults(self):
        """إعادة التعيين للقيم الافتراضية"""
        if QMessageBox.question(
            self, "تأكيد", "هل أنت متأكد من إعادة التعيين للقيم الافتراضية؟\nسيتم فقدان جميع الإعدادات المخصصة.",
            QMessageBox.Yes | QMessageBox.No
        ) == QMessageBox.Yes:
            self.config = {
                "score_rules": DEFAULT_SCORE_RULES.copy(),
                "classification_thresholds": DEFAULT_CLASSIFICATION_THRESHOLDS.copy(),
                "ai_enabled": True,
                "trend_analysis_enabled": True
            }
            save_scoring_config(self.config)
            self.load_data()
            QMessageBox.information(self, "نجح", "تم إعادة التعيين للقيم الافتراضية!")
    
    def accept(self):
        """عند الإغلاق، حفظ الإعدادات العامة"""
        try:
            set_ai_enabled(self.ai_enabled_checkbox.isChecked())
            set_trend_analysis_enabled(self.trend_enabled_checkbox.isChecked())
            super().accept()
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل الحفظ: {str(e)}")

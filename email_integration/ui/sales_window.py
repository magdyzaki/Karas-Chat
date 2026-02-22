"""
نافذة إدارة المبيعات
Sales Management Window
"""
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QMessageBox, QComboBox,
    QLineEdit, QDoubleSpinBox, QDateEdit, QTextEdit, QTabWidget,
    QWidget, QGroupBox, QFormLayout, QSplitter
)
from PyQt5.QtGui import QFont, QColor, QBrush
from PyQt5.QtCore import Qt, QDate
from datetime import datetime

from core.sales import (
    SALES_STAGES, STAGE_PROBABILITY,
    add_sale_deal, update_sale_deal, get_all_deals,
    get_deal_by_id, get_deals_by_stage, delete_deal,
    get_pipeline_statistics, get_sales_revenue_forecast,
    get_sales_reports, get_conversion_analysis
)
from core.db import get_all_clients


class SalesWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setWindowTitle("💰 إدارة المبيعات - Sales Management")
        self.setMinimumSize(1400, 800)
        self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint)
        
        main_layout = QVBoxLayout(self)
        
        # العنوان
        title = QLabel("💰 إدارة المبيعات - Sales Management")
        title.setFont(QFont("Segoe UI", 14, QFont.Bold))
        main_layout.addWidget(title)
        
        # Tabs
        self.tabs = QTabWidget()
        
        # Tab 1: Pipeline
        self.pipeline_tab = self.create_pipeline_tab()
        self.tabs.addTab(self.pipeline_tab, "📊 Pipeline")
        
        # Tab 2: All Deals
        self.deals_tab = self.create_deals_tab()
        self.tabs.addTab(self.deals_tab, "📋 All Deals")
        
        # Tab 3: Forecast
        self.forecast_tab = self.create_forecast_tab()
        self.tabs.addTab(self.forecast_tab, "📈 Forecast")
        
        # Tab 4: Reports
        self.reports_tab = self.create_reports_tab()
        self.tabs.addTab(self.reports_tab, "📊 Reports")
        
        # Tab 5: Conversion
        self.conversion_tab = self.create_conversion_tab()
        self.tabs.addTab(self.conversion_tab, "🔄 Conversion")
        
        main_layout.addWidget(self.tabs)
        
        # الأزرار
        btn_layout = QHBoxLayout()
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.clicked.connect(self.refresh_all)
        btn_layout.addWidget(refresh_btn)
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        btn_layout.addStretch()
        btn_layout.addWidget(close_btn)
        
        main_layout.addLayout(btn_layout)
        
        self.refresh_all()
    
    def create_pipeline_tab(self):
        """إنشاء تبويب Pipeline"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Pipeline statistics
        stats_label = QLabel("Pipeline Statistics")
        stats_label.setFont(QFont("Segoe UI", 12, QFont.Bold))
        layout.addWidget(stats_label)
        
        self.pipeline_stats_label = QLabel()
        self.pipeline_stats_label.setStyleSheet("background:#F5F5F5; padding:8px; border-radius:4px;")
        layout.addWidget(self.pipeline_stats_label)
        
        # Pipeline table
        self.pipeline_table = QTableWidget()
        self.pipeline_table.setColumnCount(8)
        self.pipeline_table.setHorizontalHeaderLabels([
            "Stage", "Deal Name", "Product", "Client", "Value", "Currency", 
            "Probability", "Expected Close"
        ])
        self.pipeline_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.pipeline_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.pipeline_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.pipeline_table)
        
        # Buttons
        btn_layout = QHBoxLayout()
        add_deal_btn = QPushButton("➕ Add Deal")
        add_deal_btn.clicked.connect(self.add_new_deal)
        btn_layout.addWidget(add_deal_btn)
        
        edit_deal_btn = QPushButton("✏️ Edit Deal")
        edit_deal_btn.clicked.connect(self.edit_selected_deal)
        btn_layout.addWidget(edit_deal_btn)
        
        delete_deal_btn = QPushButton("🗑️ Delete Deal")
        delete_deal_btn.clicked.connect(self.delete_selected_deal)
        btn_layout.addWidget(delete_deal_btn)
        
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        return widget
    
    def create_deals_tab(self):
        """إنشاء تبويب جميع الصفقات"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Filters
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Stage:"))
        self.stage_filter = QComboBox()
        self.stage_filter.addItems(["All"] + SALES_STAGES)
        self.stage_filter.currentIndexChanged.connect(self.load_deals_table)
        filter_layout.addWidget(self.stage_filter)
        
        filter_layout.addWidget(QLabel("Status:"))
        self.status_filter = QComboBox()
        self.status_filter.addItems(["All", "active", "inactive"])
        self.status_filter.currentIndexChanged.connect(self.load_deals_table)
        filter_layout.addWidget(self.status_filter)
        
        filter_layout.addStretch()
        layout.addLayout(filter_layout)
        
        # Table
        self.deals_table = QTableWidget()
        self.deals_table.setColumnCount(10)
        self.deals_table.setHorizontalHeaderLabels([
            "Deal Name", "Product", "Client", "Stage", "Value", "Currency",
            "Probability", "Expected Close", "Status", "Created"
        ])
        self.deals_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.deals_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.deals_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.deals_table)
        
        return widget
    
    def create_forecast_tab(self):
        """إنشاء تبويب التوقع"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Forecast summary
        self.forecast_label = QLabel("Revenue Forecast")
        self.forecast_label.setFont(QFont("Segoe UI", 12, QFont.Bold))
        layout.addWidget(self.forecast_label)
        
        self.forecast_stats = QLabel()
        self.forecast_stats.setStyleSheet("background:#F5F5F5; padding:8px; border-radius:4px;")
        layout.addWidget(self.forecast_stats)
        
        # Forecast table
        self.forecast_table = QTableWidget()
        self.forecast_table.setColumnCount(2)
        self.forecast_table.setHorizontalHeaderLabels(["Month", "Forecasted Revenue"])
        self.forecast_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.forecast_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.forecast_table)
        
        return widget
    
    def create_reports_tab(self):
        """إنشاء تبويب التقارير"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Period selector
        period_layout = QHBoxLayout()
        period_layout.addWidget(QLabel("Period:"))
        self.report_period = QComboBox()
        self.report_period.addItems(["Monthly", "Yearly"])
        self.report_period.currentIndexChanged.connect(self.load_reports)
        period_layout.addWidget(self.report_period)
        period_layout.addStretch()
        layout.addLayout(period_layout)
        
        # Report summary
        self.report_summary = QLabel()
        self.report_summary.setStyleSheet("background:#F5F5F5; padding:8px; border-radius:4px;")
        layout.addWidget(self.report_summary)
        
        # Report table
        self.reports_table = QTableWidget()
        self.reports_table.setColumnCount(4)
        self.reports_table.setHorizontalHeaderLabels([
            "Period", "Revenue", "Won Deals", "Lost Deals"
        ])
        self.reports_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.reports_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.reports_table)
        
        return widget
    
    def create_conversion_tab(self):
        """إنشاء تبويب التحويل"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Conversion summary
        self.conversion_summary = QLabel()
        self.conversion_summary.setStyleSheet("background:#F5F5F5; padding:8px; border-radius:4px;")
        layout.addWidget(self.conversion_summary)
        
        # Conversion table
        self.conversion_table = QTableWidget()
        self.conversion_table.setColumnCount(2)
        self.conversion_table.setHorizontalHeaderLabels([
            "Stage Transition", "Conversion Rate %"
        ])
        self.conversion_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.conversion_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.conversion_table)
        
        return widget
    
    def load_pipeline_table(self):
        """تحميل Pipeline"""
        deals = get_all_deals(status="active")
        
        self.pipeline_table.setRowCount(0)
        
        for deal in deals:
            (
                deal_id, client_id, company, deal_name, product_name, stage,
                value, currency, probability, expected_close, actual_close,
                status, notes, created, updated
            ) = deal
            
            row = self.pipeline_table.rowCount()
            self.pipeline_table.insertRow(row)
            
            self.pipeline_table.setItem(row, 0, QTableWidgetItem(stage or ""))
            self.pipeline_table.setItem(row, 1, QTableWidgetItem(deal_name or ""))
            self.pipeline_table.setItem(row, 2, QTableWidgetItem(product_name or ""))
            self.pipeline_table.setItem(row, 3, QTableWidgetItem(company or ""))
            self.pipeline_table.setItem(row, 4, QTableWidgetItem(f"{value:,.2f}" if value else "0"))
            self.pipeline_table.setItem(row, 5, QTableWidgetItem(currency or "USD"))
            self.pipeline_table.setItem(row, 6, QTableWidgetItem(f"{probability*100:.1f}%" if probability else "0%"))
            self.pipeline_table.setItem(row, 7, QTableWidgetItem(expected_close or ""))
            
            # Store deal_id
            for col in range(8):
                item = self.pipeline_table.item(row, col)
                if item:
                    item.setData(Qt.UserRole, deal_id)
            
            # Color by stage
            stage_item = self.pipeline_table.item(row, 0)
            if stage_item:
                if stage == "Closed Won":
                    stage_item.setBackground(QBrush(QColor("#C8E6C9")))
                elif stage == "Closed Lost":
                    stage_item.setBackground(QBrush(QColor("#FFCDD2")))
                elif stage == "Negotiation":
                    stage_item.setBackground(QBrush(QColor("#FFF9C4")))
        
        # Update statistics
        stats = get_pipeline_statistics()
        stats_text = f"Total Deals: {stats['total_deals']} | "
        stats_text += f"Total Value: ${stats['total_value']:,.2f} | "
        stats_text += f"Weighted Value: ${stats['weighted_value']:,.2f}"
        self.pipeline_stats_label.setText(stats_text)
    
    def load_deals_table(self):
        """تحميل جدول الصفقات"""
        stage_filter = self.stage_filter.currentText()
        status_filter = self.status_filter.currentText()
        
        if stage_filter == "All":
            deals = get_all_deals(status=status_filter if status_filter != "All" else None)
        else:
            deals = get_deals_by_stage(stage_filter)
        
        self.deals_table.setRowCount(0)
        
        for deal in deals:
            (
                deal_id, client_id, company, deal_name, product_name, stage,
                value, currency, probability, expected_close, actual_close,
                status, notes, created, updated
            ) = deal
            
            # Filter by status if needed
            if status_filter != "All" and status != status_filter:
                continue
            
            row = self.deals_table.rowCount()
            self.deals_table.insertRow(row)
            
            self.deals_table.setItem(row, 0, QTableWidgetItem(deal_name or ""))
            self.deals_table.setItem(row, 1, QTableWidgetItem(product_name or ""))
            self.deals_table.setItem(row, 2, QTableWidgetItem(company or ""))
            self.deals_table.setItem(row, 3, QTableWidgetItem(stage or ""))
            self.deals_table.setItem(row, 4, QTableWidgetItem(f"{value:,.2f}" if value else "0"))
            self.deals_table.setItem(row, 5, QTableWidgetItem(currency or "USD"))
            self.deals_table.setItem(row, 6, QTableWidgetItem(f"{probability*100:.1f}%" if probability else "0%"))
            self.deals_table.setItem(row, 7, QTableWidgetItem(expected_close or ""))
            self.deals_table.setItem(row, 8, QTableWidgetItem(status or ""))
            self.deals_table.setItem(row, 9, QTableWidgetItem(created or ""))
            
            for col in range(10):
                item = self.deals_table.item(row, col)
                if item:
                    item.setData(Qt.UserRole, deal_id)
    
    def load_forecast(self):
        """تحميل التوقع"""
        forecast = get_sales_revenue_forecast(months=12)
        
        # Summary
        stats_text = f"Total Forecast: ${forecast['total_forecast']:,.2f} | "
        stats_text += f"Weighted Forecast: ${forecast['weighted_forecast']:,.2f}"
        self.forecast_stats.setText(stats_text)
        
        # Table
        self.forecast_table.setRowCount(0)
        
        sorted_months = sorted(forecast['by_month'].keys())
        for month in sorted_months:
            revenue = forecast['by_month'][month]
            row = self.forecast_table.rowCount()
            self.forecast_table.insertRow(row)
            self.forecast_table.setItem(row, 0, QTableWidgetItem(month))
            self.forecast_table.setItem(row, 1, QTableWidgetItem(f"${revenue:,.2f}"))
    
    def load_reports(self):
        """تحميل التقارير"""
        period = "monthly" if self.report_period.currentText() == "Monthly" else "yearly"
        reports = get_sales_reports(period=period)
        
        # Summary
        summary_text = f"Total Revenue: ${reports['total_revenue']:,.2f} | "
        summary_text += f"Total Deals: {reports['total_deals']} | "
        summary_text += f"Won: {reports['won_deals']} | "
        summary_text += f"Lost: {reports['lost_deals']} | "
        summary_text += f"Conversion Rate: {reports['conversion_rate']:.1f}%"
        self.report_summary.setText(summary_text)
        
        # Table
        self.reports_table.setRowCount(0)
        
        sorted_periods = sorted(reports['by_period'].keys(), reverse=True)
        for period_key in sorted_periods:
            data = reports['by_period'][period_key]
            row = self.reports_table.rowCount()
            self.reports_table.insertRow(row)
            self.reports_table.setItem(row, 0, QTableWidgetItem(period_key))
            self.reports_table.setItem(row, 1, QTableWidgetItem(f"${data.get('revenue', 0):,.2f}"))
            self.reports_table.setItem(row, 2, QTableWidgetItem(str(data.get('deals', 0))))
            self.reports_table.setItem(row, 3, QTableWidgetItem(str(data.get('lost', 0))))
    
    def load_conversion(self):
        """تحميل تحليل التحويل"""
        analysis = get_conversion_analysis()
        
        # Summary
        summary_text = f"Overall Conversion: {analysis['overall_conversion']:.1f}% | "
        summary_text += f"Win Rate: {analysis['win_rate']:.1f}% | "
        summary_text += f"Loss Rate: {analysis['loss_rate']:.1f}%"
        self.conversion_summary.setText(summary_text)
        
        # Table
        self.conversion_table.setRowCount(0)
        
        for transition, rate in analysis['stage_conversion'].items():
            row = self.conversion_table.rowCount()
            self.conversion_table.insertRow(row)
            self.conversion_table.setItem(row, 0, QTableWidgetItem(transition))
            self.conversion_table.setItem(row, 1, QTableWidgetItem(f"{rate:.1f}%"))
    
    def refresh_all(self):
        """تحديث جميع البيانات"""
        self.load_pipeline_table()
        self.load_deals_table()
        self.load_forecast()
        self.load_reports()
        self.load_conversion()
    
    def get_selected_deal_id(self, table):
        """الحصول على ID الصفقة المحددة"""
        row = table.currentRow()
        if row < 0:
            return None
        
        item = table.item(row, 0)
        if not item:
            return None
        
        return item.data(Qt.UserRole)
    
    def add_new_deal(self):
        """إضافة صفقة جديدة"""
        from ui.add_deal_popup import AddDealPopup
        dlg = AddDealPopup(self)
        if dlg.exec_() == QDialog.Accepted:
            self.refresh_all()
    
    def edit_selected_deal(self):
        """تعديل الصفقة المحددة"""
        deal_id = self.get_selected_deal_id(self.pipeline_table)
        if not deal_id:
            deal_id = self.get_selected_deal_id(self.deals_table)
        
        if not deal_id:
            QMessageBox.warning(self, "Select Deal", "Please select a deal first.")
            return
        
        from ui.edit_deal_popup import EditDealPopup
        dlg = EditDealPopup(deal_id, self)
        if dlg.exec_() == QDialog.Accepted:
            self.refresh_all()
    
    def delete_selected_deal(self):
        """حذف الصفقة المحددة"""
        deal_id = self.get_selected_deal_id(self.pipeline_table)
        if not deal_id:
            deal_id = self.get_selected_deal_id(self.deals_table)
        
        if not deal_id:
            QMessageBox.warning(self, "Select Deal", "Please select a deal first.")
            return
        
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            "Are you sure you want to delete this deal?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            delete_deal(deal_id)
            self.refresh_all()

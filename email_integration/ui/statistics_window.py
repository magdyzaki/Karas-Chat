"""
نافذة الإحصائيات المرئية
Visual Statistics Window
"""
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTabWidget, QWidget, QMessageBox, QGroupBox, QGridLayout
)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt
import os

# Try to import matplotlib
try:
    import matplotlib
    matplotlib.use('Qt5Agg')  # Use Qt5 backend
    from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
    from matplotlib.figure import Figure
    from matplotlib.font_manager import FontProperties
    import matplotlib.pyplot as plt
    
    # محاولة استيراد مكتبات معالجة النص العربي
    try:
        import arabic_reshaper
        from bidi.algorithm import get_display
        ARABIC_SUPPORT = True
    except ImportError:
        ARABIC_SUPPORT = False
        arabic_reshaper = None
        get_display = None
    
    # إعدادات لدعم النص العربي - استخدام خط بسيط متوفر
    plt.rcParams['font.sans-serif'] = ['Tahoma', 'Segoe UI', 'DejaVu Sans', 'Arial']
    plt.rcParams['axes.unicode_minus'] = False  # إصلاح مشكلة علامة الطرح
    plt.rcParams['font.size'] = 10
    
    # إنشاء FontProperties للعربية - استخدام Tahoma كخط افتراضي بسيط
    arabic_font = FontProperties(family='Tahoma', size=10)
    
    # دالة لمعالجة النص العربي
    def prepare_arabic_text(text):
        """معالجة النص العربي للعرض الصحيح في matplotlib"""
        if ARABIC_SUPPORT and text:
            try:
                # إعادة تشكيل النص العربي
                reshaped_text = arabic_reshaper.reshape(text)
                # تطبيق خوارزمية bidi للعرض من اليمين لليسار
                bidi_text = get_display(reshaped_text)
                return bidi_text
            except:
                return text
        return text
    
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    arabic_font = None
    def prepare_arabic_text(text):
        return text

from core.statistics import (
    get_client_statistics,
    get_message_statistics,
    get_request_statistics,
    get_client_growth_statistics,
    get_comprehensive_statistics
)


class StatisticsWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        if not MATPLOTLIB_AVAILABLE:
            QMessageBox.warning(
                self,
                "مكتبة غير متوفرة",
                "مكتبة matplotlib غير مثبتة!\n"
                "يرجى تثبيتها باستخدام:\n"
                "pip install matplotlib\n\n"
                "سيتم إغلاق هذه النافذة."
            )
            self.reject()
            return
        
        self.setWindowTitle("📊 الإحصائيات المرئية - Visual Statistics")
        self.setMinimumSize(1200, 800)
        # إضافة زر Maximize
        self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint)
        
        main_layout = QVBoxLayout(self)
        
        # العنوان
        title = QLabel("📊 الإحصائيات المرئية - Visual Statistics")
        title.setFont(QFont("Segoe UI", 14, QFont.Bold))
        main_layout.addWidget(title)
        
        # Tabs
        self.tabs = QTabWidget()
        
        # Tab 1: Clients Statistics
        self.clients_tab = self.create_clients_tab()
        self.tabs.addTab(self.clients_tab, "👥 العملاء - Clients")
        
        # Tab 2: Messages Statistics
        self.messages_tab = self.create_messages_tab()
        self.tabs.addTab(self.messages_tab, "✉️ الرسائل - Messages")
        
        # Tab 3: Requests Statistics
        self.requests_tab = self.create_requests_tab()
        self.tabs.addTab(self.requests_tab, "📋 الطلبات - Requests")
        
        # Tab 4: Growth Statistics
        self.growth_tab = self.create_growth_tab()
        self.tabs.addTab(self.growth_tab, "📈 النمو - Growth")
        
        # Tab 5: Overview
        self.overview_tab = self.create_overview_tab()
        self.tabs.addTab(self.overview_tab, "📊 نظرة عامة - Overview")
        
        main_layout.addWidget(self.tabs)
        
        # الأزرار
        btn_layout = QHBoxLayout()
        refresh_btn = QPushButton("🔄 تحديث - Refresh")
        refresh_btn.clicked.connect(self.refresh_all)
        btn_layout.addWidget(refresh_btn)
        
        close_btn = QPushButton("إغلاق - Close")
        close_btn.clicked.connect(self.accept)
        btn_layout.addStretch()
        btn_layout.addWidget(close_btn)
        
        main_layout.addLayout(btn_layout)
        
        # تحميل البيانات
        self.refresh_all()
    
    def create_figure_canvas(self, figsize=(8, 5)):
        """إنشاء canvas للرسم البياني"""
        fig = Figure(figsize=figsize)
        canvas = FigureCanvas(fig)
        return fig, canvas
    
    def create_clients_tab(self):
        """إنشاء تبويب إحصائيات العملاء"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Grid for multiple charts
        grid = QGridLayout()
        
        # Chart 1: Classification Distribution
        fig1, canvas1 = self.create_figure_canvas()
        self.classification_fig = fig1
        self.classification_canvas = canvas1
        grid.addWidget(canvas1, 0, 0)
        
        # Chart 2: Status Distribution
        fig2, canvas2 = self.create_figure_canvas()
        self.status_fig = fig2
        self.status_canvas = canvas2
        grid.addWidget(canvas2, 0, 1)
        
        # Chart 3: Score Range Distribution
        fig3, canvas3 = self.create_figure_canvas()
        self.score_fig = fig3
        self.score_canvas = canvas3
        grid.addWidget(canvas3, 1, 0)
        
        # Chart 4: Top Countries
        fig4, canvas4 = self.create_figure_canvas()
        self.countries_fig = fig4
        self.countries_canvas = canvas4
        grid.addWidget(canvas4, 1, 1)
        
        layout.addLayout(grid)
        
        return widget
    
    def create_messages_tab(self):
        """إنشاء تبويب إحصائيات الرسائل"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        grid = QGridLayout()
        
        # Chart 1: Messages by Channel
        fig1, canvas1 = self.create_figure_canvas()
        self.channel_fig = fig1
        self.channel_canvas = canvas1
        grid.addWidget(canvas1, 0, 0)
        
        # Chart 2: Messages by Month
        fig2, canvas2 = self.create_figure_canvas()
        self.messages_month_fig = fig2
        self.messages_month_canvas = canvas2
        grid.addWidget(canvas2, 0, 1)
        
        # Chart 3: Messages by Type
        fig3, canvas3 = self.create_figure_canvas()
        self.message_type_fig = fig3
        self.message_type_canvas = canvas3
        grid.addWidget(canvas3, 1, 0, 1, 2)
        
        layout.addLayout(grid)
        
        return widget
    
    def create_requests_tab(self):
        """إنشاء تبويب إحصائيات الطلبات"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        grid = QGridLayout()
        
        # Chart 1: Requests by Status
        fig1, canvas1 = self.create_figure_canvas()
        self.requests_status_fig = fig1
        self.requests_status_canvas = canvas1
        grid.addWidget(canvas1, 0, 0)
        
        # Chart 2: Requests by Type
        fig2, canvas2 = self.create_figure_canvas()
        self.requests_type_fig = fig2
        self.requests_type_canvas = canvas2
        grid.addWidget(canvas2, 0, 1)
        
        # Chart 3: Requests by Month
        fig3, canvas3 = self.create_figure_canvas()
        self.requests_month_fig = fig3
        self.requests_month_canvas = canvas3
        grid.addWidget(canvas3, 1, 0, 1, 2)
        
        layout.addLayout(grid)
        
        return widget
    
    def create_growth_tab(self):
        """إنشاء تبويب إحصائيات النمو"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Chart: Client Growth Over Time
        fig, canvas = self.create_figure_canvas(figsize=(12, 6))
        self.growth_fig = fig
        self.growth_canvas = canvas
        layout.addWidget(canvas)
        
        return widget
    
    def create_overview_tab(self):
        """إنشاء تبويب النظرة العامة"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Summary stats
        stats_group = QGroupBox("إحصائيات سريعة - Quick Statistics")
        stats_layout = QGridLayout()
        
        self.stats_labels = {}
        stats_layout.addWidget(QLabel("إجمالي العملاء - Total Clients:"), 0, 0)
        self.stats_labels['total_clients'] = QLabel("0")
        self.stats_labels['total_clients'].setFont(QFont("Arial", 12, QFont.Bold))
        stats_layout.addWidget(self.stats_labels['total_clients'], 0, 1)
        
        stats_layout.addWidget(QLabel("🔥 عملاء جادين - Serious Buyers:"), 1, 0)
        self.stats_labels['serious'] = QLabel("0")
        self.stats_labels['serious'].setFont(QFont("Arial", 12, QFont.Bold))
        stats_layout.addWidget(self.stats_labels['serious'], 1, 1)
        
        stats_layout.addWidget(QLabel("👍 عملاء محتملين - Potential:"), 2, 0)
        self.stats_labels['potential'] = QLabel("0")
        self.stats_labels['potential'].setFont(QFont("Arial", 12, QFont.Bold))
        stats_layout.addWidget(self.stats_labels['potential'], 2, 1)
        
        stats_layout.addWidget(QLabel("⭐ عملاء مميزين - Focus:"), 3, 0)
        self.stats_labels['focus'] = QLabel("0")
        self.stats_labels['focus'].setFont(QFont("Arial", 12, QFont.Bold))
        stats_layout.addWidget(self.stats_labels['focus'], 3, 1)
        
        stats_layout.addWidget(QLabel("✉️ إجمالي الرسائل - Total Messages:"), 4, 0)
        self.stats_labels['total_messages'] = QLabel("0")
        self.stats_labels['total_messages'].setFont(QFont("Arial", 12, QFont.Bold))
        stats_layout.addWidget(self.stats_labels['total_messages'], 4, 1)
        
        stats_layout.addWidget(QLabel("📋 إجمالي الطلبات - Total Requests:"), 5, 0)
        self.stats_labels['total_requests'] = QLabel("0")
        self.stats_labels['total_requests'].setFont(QFont("Arial", 12, QFont.Bold))
        stats_layout.addWidget(self.stats_labels['total_requests'], 5, 1)
        
        stats_group.setLayout(stats_layout)
        layout.addWidget(stats_group)
        
        # Overview chart
        fig, canvas = self.create_figure_canvas(figsize=(10, 6))
        self.overview_fig = fig
        self.overview_canvas = canvas
        layout.addWidget(canvas)
        
        layout.addStretch()
        
        return widget
    
    def plot_classification_distribution(self, stats):
        """رسم توزيع العملاء حسب التصنيف"""
        self.classification_fig.clear()
        ax = self.classification_fig.add_subplot(111)
        
        labels = ['🔥 Serious', '👍 Potential', '❌ Not Serious']
        sizes = [stats['serious'], stats['potential'], stats['not_serious']]
        colors = ['#FF6B6B', '#FFE66D', '#95E1D3']
        
        # Remove zero values
        filtered_data = [(l, s, c) for l, s, c in zip(labels, sizes, colors) if s > 0]
        if filtered_data:
            labels, sizes, colors = zip(*filtered_data)
            ax.pie(sizes, labels=labels, autopct='%1.1f%%', colors=colors, startangle=90, textprops={'fontproperties': arabic_font})
            ax.set_title(prepare_arabic_text('توزيع العملاء حسب التصنيف - Client Classification'), fontsize=12, fontweight='bold', fontproperties=arabic_font)
        
        self.classification_canvas.draw()
    
    def plot_status_distribution(self, stats):
        """رسم توزيع العملاء حسب الحالة"""
        self.status_fig.clear()
        ax = self.status_fig.add_subplot(111)
        
        statuses = list(stats['by_status'].keys())[:10]  # Top 10
        counts = [stats['by_status'][s] for s in statuses]
        
        if statuses:
            bars = ax.bar(range(len(statuses)), counts, color='#4ECDC4')
            ax.set_xticks(range(len(statuses)))
            ax.set_xticklabels([prepare_arabic_text(s) for s in statuses], rotation=45, ha='right', fontproperties=arabic_font)
            ax.set_title(prepare_arabic_text('توزيع العملاء حسب الحالة - Status Distribution'), fontsize=12, fontweight='bold', fontproperties=arabic_font)
            ax.set_ylabel(prepare_arabic_text('عدد العملاء - Count'), fontproperties=arabic_font)
            
            # Add value labels on bars
            for bar in bars:
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height,
                       f'{int(height)}', ha='center', va='bottom')
        
        self.status_canvas.draw()
    
    def plot_score_distribution(self, stats):
        """رسم توزيع النقاط"""
        self.score_fig.clear()
        ax = self.score_fig.add_subplot(111)
        
        ranges = list(stats['by_score_range'].keys())
        counts = [stats['by_score_range'][r] for r in ranges]
        
        bars = ax.bar(ranges, counts, color='#FF6B9D')
        ax.set_title(prepare_arabic_text('توزيع النقاط - Score Distribution'), fontsize=12, fontweight='bold', fontproperties=arabic_font)
        ax.set_ylabel(prepare_arabic_text('عدد العملاء - Count'), fontproperties=arabic_font)
        ax.set_xlabel(prepare_arabic_text('نطاق النقاط - Score Range'), fontproperties=arabic_font)
        
        # Add value labels
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{int(height)}', ha='center', va='bottom')
        
        self.score_canvas.draw()
    
    def plot_top_countries(self, stats):
        """رسم أفضل البلدان"""
        self.countries_fig.clear()
        ax = self.countries_fig.add_subplot(111)
        
        # Top 10 countries
        countries = sorted(stats['by_country'].items(), key=lambda x: x[1], reverse=True)[:10]
        
        if countries:
            country_names, counts = zip(*countries)
            bars = ax.barh(range(len(country_names)), counts, color='#95E1D3')
            ax.set_yticks(range(len(country_names)))
            ax.set_yticklabels([prepare_arabic_text(c) for c in country_names], fontproperties=arabic_font)
            ax.set_title(prepare_arabic_text('أفضل 10 بلدان - Top 10 Countries'), fontsize=12, fontweight='bold', fontproperties=arabic_font)
            ax.set_xlabel(prepare_arabic_text('عدد العملاء - Count'), fontproperties=arabic_font)
            
            # Add value labels
            for i, (bar, count) in enumerate(zip(bars, counts)):
                ax.text(count, bar.get_y() + bar.get_height()/2.,
                       f' {int(count)}', va='center')
        
        self.countries_canvas.draw()
    
    def plot_messages_by_channel(self, stats):
        """رسم الرسائل حسب القناة"""
        self.channel_fig.clear()
        ax = self.channel_fig.add_subplot(111)
        
        channels = list(stats['by_channel'].keys())
        counts = [stats['by_channel'][c] for c in channels]
        
        if channels:
            ax.pie(counts, labels=[prepare_arabic_text(c) for c in channels], autopct='%1.1f%%', startangle=90, textprops={'fontproperties': arabic_font})
            ax.set_title(prepare_arabic_text('الرسائل حسب القناة - Messages by Channel'), fontsize=12, fontweight='bold', fontproperties=arabic_font)
        
        self.channel_canvas.draw()
    
    def plot_messages_by_month(self, stats):
        """رسم الرسائل حسب الشهر"""
        self.messages_month_fig.clear()
        ax = self.messages_month_fig.add_subplot(111)
        
        months = sorted(stats['by_month'].keys())[-12:]  # Last 12 months
        counts = [stats['by_month'][m] for m in months]
        
        if months:
            ax.plot(range(len(months)), counts, marker='o', color='#FF6B6B', linewidth=2)
            ax.set_xticks(range(len(months)))
            ax.set_xticklabels([prepare_arabic_text(m[-5:]) for m in months], rotation=45, ha='right', fontproperties=arabic_font)
            ax.set_title(prepare_arabic_text('الرسائل حسب الشهر - Messages by Month'), fontsize=12, fontweight='bold', fontproperties=arabic_font)
            ax.set_ylabel(prepare_arabic_text('عدد الرسائل - Count'), fontproperties=arabic_font)
            ax.grid(True, alpha=0.3)
        
        self.messages_month_canvas.draw()
    
    def plot_messages_by_type(self, stats):
        """رسم الرسائل حسب النوع"""
        self.message_type_fig.clear()
        ax = self.message_type_fig.add_subplot(111)
        
        types = list(stats['by_type'].keys())
        counts = [stats['by_type'][t] for t in types]
        
        if types:
            bars = ax.bar(types, counts, color='#4ECDC4')
            ax.set_title(prepare_arabic_text('الرسائل حسب النوع - Messages by Type'), fontsize=12, fontweight='bold', fontproperties=arabic_font)
            ax.set_ylabel(prepare_arabic_text('عدد الرسائل - Count'), fontproperties=arabic_font)
            ax.set_xlabel(prepare_arabic_text('النوع - Type'), fontproperties=arabic_font)
            ax.set_xticklabels([prepare_arabic_text(t) for t in types], fontproperties=arabic_font)
            
            for bar in bars:
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height,
                       f'{int(height)}', ha='center', va='bottom')
        
        self.message_type_canvas.draw()
    
    def plot_requests_by_status(self, stats):
        """رسم الطلبات حسب الحالة"""
        self.requests_status_fig.clear()
        ax = self.requests_status_fig.add_subplot(111)
        
        statuses = ['Open', 'Closed']
        counts = [stats['open'], stats['closed']]
        colors = ['#FFE66D', '#95E1D3']
        
        ax.pie(counts, labels=statuses, autopct='%1.1f%%', colors=colors, startangle=90, textprops={'fontproperties': arabic_font})
        ax.set_title(prepare_arabic_text('الطلبات حسب الحالة - Requests by Status'), fontsize=12, fontweight='bold', fontproperties=arabic_font)
        
        self.requests_status_canvas.draw()
    
    def plot_requests_by_type(self, stats):
        """رسم الطلبات حسب النوع"""
        self.requests_type_fig.clear()
        ax = self.requests_type_fig.add_subplot(111)
        
        types = list(stats['by_type'].keys())[:10]  # Top 10
        counts = [stats['by_type'][t] for t in types]
        
        if types:
            bars = ax.bar(range(len(types)), counts, color='#FF6B9D')
            ax.set_xticks(range(len(types)))
            ax.set_xticklabels([prepare_arabic_text(t) for t in types], rotation=45, ha='right', fontproperties=arabic_font)
            ax.set_title(prepare_arabic_text('الطلبات حسب النوع - Requests by Type'), fontsize=12, fontweight='bold', fontproperties=arabic_font)
            ax.set_ylabel(prepare_arabic_text('عدد الطلبات - Count'), fontproperties=arabic_font)
            
            for bar in bars:
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height,
                       f'{int(height)}', ha='center', va='bottom')
        
        self.requests_type_canvas.draw()
    
    def plot_requests_by_month(self, stats):
        """رسم الطلبات حسب الشهر"""
        self.requests_month_fig.clear()
        ax = self.requests_month_fig.add_subplot(111)
        
        months = sorted(stats['by_month'].keys())[-12:]  # Last 12 months
        counts = [stats['by_month'][m] for m in months]
        
        if months:
            ax.bar(range(len(months)), counts, color='#4ECDC4')
            ax.set_xticks(range(len(months)))
            ax.set_xticklabels([prepare_arabic_text(m[-5:]) for m in months], rotation=45, ha='right', fontproperties=arabic_font)
            ax.set_title(prepare_arabic_text('الطلبات حسب الشهر - Requests by Month'), fontsize=12, fontweight='bold', fontproperties=arabic_font)
            ax.set_ylabel(prepare_arabic_text('عدد الطلبات - Count'), fontproperties=arabic_font)
            ax.grid(True, alpha=0.3, axis='y')
        
        self.requests_month_canvas.draw()
    
    def plot_growth(self, growth_data):
        """رسم نمو العملاء"""
        self.growth_fig.clear()
        ax = self.growth_fig.add_subplot(111)
        
        months = sorted(growth_data.keys())[-24:]  # Last 24 months
        counts = [growth_data[m] for m in months]
        cumulative = []
        total = 0
        for count in counts:
            total += count
            cumulative.append(total)
        
        if months:
            ax.plot(range(len(months)), cumulative, marker='o', color='#FF6B6B', linewidth=2, markersize=6)
            ax.fill_between(range(len(months)), cumulative, alpha=0.3, color='#FF6B6B')
            ax.set_xticks(range(0, len(months), max(1, len(months)//10)))
            ax.set_xticklabels([prepare_arabic_text(m[-5:]) for m in months[::max(1, len(months)//10)]], rotation=45, ha='right', fontproperties=arabic_font)
            ax.set_title(prepare_arabic_text('نمو قاعدة العملاء - Client Growth Over Time'), fontsize=14, fontweight='bold', fontproperties=arabic_font)
            ax.set_ylabel(prepare_arabic_text('إجمالي العملاء - Total Clients'), fontproperties=arabic_font)
            ax.set_xlabel(prepare_arabic_text('الشهر - Month'), fontproperties=arabic_font)
            ax.grid(True, alpha=0.3)
        
        self.growth_canvas.draw()
    
    def plot_overview(self, client_stats, message_stats, request_stats):
        """رسم النظرة العامة"""
        self.overview_fig.clear()
        ax = self.overview_fig.add_subplot(111)
        
        categories = ['Clients', 'Serious', 'Potential', 'Messages', 'Requests']
        values = [
            client_stats['total'],
            client_stats['serious'],
            client_stats['potential'],
            message_stats['total'],
            request_stats['total']
        ]
        
        bars = ax.bar(categories, values, color=['#4ECDC4', '#FF6B6B', '#FFE66D', '#95E1D3', '#FF6B9D'])
        ax.set_title(prepare_arabic_text('نظرة عامة - Overview'), fontsize=14, fontweight='bold', fontproperties=arabic_font)
        ax.set_ylabel(prepare_arabic_text('العدد - Count'), fontproperties=arabic_font)
        ax.set_xticklabels(categories, fontproperties=arabic_font)
        
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{int(height)}', ha='center', va='bottom', fontweight='bold')
        
        self.overview_canvas.draw()
    
    def refresh_all(self):
        """تحديث جميع الرسوم البيانية"""
        try:
            # Get statistics
            client_stats = get_client_statistics()
            message_stats = get_message_statistics()
            request_stats = get_request_statistics()
            growth_data = get_client_growth_statistics()
            
            # Plot clients charts
            self.plot_classification_distribution(client_stats)
            self.plot_status_distribution(client_stats)
            self.plot_score_distribution(client_stats)
            self.plot_top_countries(client_stats)
            
            # Plot messages charts
            self.plot_messages_by_channel(message_stats)
            self.plot_messages_by_month(message_stats)
            self.plot_messages_by_type(message_stats)
            
            # Plot requests charts
            self.plot_requests_by_status(request_stats)
            self.plot_requests_by_type(request_stats)
            self.plot_requests_by_month(request_stats)
            
            # Plot growth
            self.plot_growth(growth_data)
            
            # Plot overview
            self.plot_overview(client_stats, message_stats, request_stats)
            
            # Update overview stats labels
            if hasattr(self, 'stats_labels'):
                self.stats_labels['total_clients'].setText(str(client_stats['total']))
                self.stats_labels['serious'].setText(str(client_stats['serious']))
                self.stats_labels['potential'].setText(str(client_stats['potential']))
                self.stats_labels['focus'].setText(str(client_stats['focus']))
                self.stats_labels['total_messages'].setText(str(message_stats['total']))
                self.stats_labels['total_requests'].setText(str(request_stats['total']))
                
        except Exception as e:
            QMessageBox.critical(
                self,
                "خطأ",
                f"حدث خطأ أثناء تحديث الإحصائيات:\n\n{str(e)}"
            )

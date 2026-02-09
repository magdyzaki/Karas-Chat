"""
نظام الثيمات (الوضع الداكن/الفاتح)
Theme System (Dark/Light Mode)
"""
from PyQt5.QtCore import QObject, pyqtSignal
from core.settings import load_settings


class ThemeManager(QObject):
    """مدير الثيمات للتطبيق"""
    
    theme_changed = pyqtSignal(str)  # إشارة عند تغيير الثيم
    
    def __init__(self):
        super().__init__()
        self._current_theme = self.get_theme()
    
    def get_theme(self) -> str:
        """الحصول على الثيم الحالي"""
        settings = load_settings()
        return settings.get("ui", {}).get("theme", "light")
    
    def set_theme(self, theme: str):
        """تعيين الثيم (light أو dark)"""
        if theme not in ["light", "dark"]:
            theme = "light"
        
        from core.settings import load_settings, save_settings, _deep_update
        settings = load_settings()
        if "ui" not in settings:
            settings["ui"] = {}
        settings["ui"]["theme"] = theme
        save_settings(settings)
        
        self._current_theme = theme
        self.theme_changed.emit(theme)
    
    def get_stylesheet(self) -> str:
        """الحصول على ورقة الأنماط (Stylesheet) للثيم الحالي"""
        theme = self.get_theme()
        
        if theme == "dark":
            return self._get_dark_stylesheet()
        else:
            return self._get_light_stylesheet()
    
    def _get_light_stylesheet(self) -> str:
        """ورقة الأنماط للوضع الفاتح"""
        return """
        QMainWindow, QDialog, QWidget {
            background-color: #FFFFFF;
            color: #000000;
        }
        QLabel {
            color: #000000;
        }
        QLineEdit, QTextEdit, QComboBox, QSpinBox, QDoubleSpinBox, QDateEdit {
            background-color: #FFFFFF;
            border: 1px solid #CCCCCC;
            border-radius: 4px;
            padding: 4px;
            color: #000000;
        }
        QLineEdit:focus, QTextEdit:focus, QComboBox:focus {
            border: 2px solid #4ECDC4;
        }
        QPushButton {
            background-color: #F0F0F0;
            border: 1px solid #CCCCCC;
            border-radius: 4px;
            padding: 6px 12px;
            color: #000000;
        }
        QPushButton:hover {
            background-color: #E0E0E0;
        }
        QPushButton:pressed {
            background-color: #D0D0D0;
        }
        QTableWidget {
            background-color: #FFFFFF;
            alternate-background-color: #F5F5F5;
            color: #000000;
            gridline-color: #CCCCCC;
        }
        QTableWidget::item:selected {
            background-color: #4ECDC4;
            color: #FFFFFF;
        }
        QHeaderView::section {
            background-color: #E0E0E0;
            color: #000000;
            padding: 4px;
            border: 1px solid #CCCCCC;
        }
        QGroupBox {
            border: 1px solid #CCCCCC;
            border-radius: 4px;
            margin-top: 10px;
            padding-top: 10px;
            color: #000000;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px;
        }
        QTabWidget::pane {
            border: 1px solid #CCCCCC;
            background-color: #FFFFFF;
        }
        QTabBar::tab {
            background-color: #F0F0F0;
            color: #000000;
            padding: 6px 12px;
            margin-right: 2px;
        }
        QTabBar::tab:selected {
            background-color: #4ECDC4;
            color: #FFFFFF;
        }
        QTabBar::tab:hover {
            background-color: #E0E0E0;
        }
        QScrollBar:vertical {
            background-color: #F0F0F0;
            width: 12px;
        }
        QScrollBar::handle:vertical {
            background-color: #CCCCCC;
            border-radius: 6px;
            min-height: 20px;
        }
        QScrollBar::handle:vertical:hover {
            background-color: #AAAAAA;
        }
        QMenuBar {
            background-color: #F0F0F0;
            color: #000000;
        }
        QMenu {
            background-color: #FFFFFF;
            color: #000000;
        }
        QMenu::item:selected {
            background-color: #4ECDC4;
            color: #FFFFFF;
        }
        QMessageBox {
            background-color: #FFFFFF;
            color: #000000;
        }
        """
    
    def _get_dark_stylesheet(self) -> str:
        """ورقة الأنماط للوضع الداكن"""
        return """
        QMainWindow, QDialog, QWidget {
            background-color: #2B2B2B;
            color: #FFFFFF;
        }
        QLabel {
            color: #FFFFFF;
        }
        QLineEdit, QTextEdit, QComboBox, QSpinBox, QDoubleSpinBox, QDateEdit {
            background-color: #3C3C3C;
            border: 1px solid #555555;
            border-radius: 4px;
            padding: 4px;
            color: #FFFFFF;
        }
        QLineEdit:focus, QTextEdit:focus, QComboBox:focus {
            border: 2px solid #4ECDC4;
        }
        QPushButton {
            background-color: #3C3C3C;
            border: 1px solid #555555;
            border-radius: 4px;
            padding: 6px 12px;
            color: #FFFFFF;
        }
        QPushButton:hover {
            background-color: #4C4C4C;
        }
        QPushButton:pressed {
            background-color: #2C2C2C;
        }
        QTableWidget {
            background-color: #2B2B2B;
            alternate-background-color: #353535;
            color: #FFFFFF;
            gridline-color: #555555;
        }
        QTableWidget::item:selected {
            background-color: #4ECDC4;
            color: #000000;
        }
        QHeaderView::section {
            background-color: #3C3C3C;
            color: #FFFFFF;
            padding: 4px;
            border: 1px solid #555555;
        }
        QGroupBox {
            border: 1px solid #555555;
            border-radius: 4px;
            margin-top: 10px;
            padding-top: 10px;
            color: #FFFFFF;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px;
        }
        QTabWidget::pane {
            border: 1px solid #555555;
            background-color: #2B2B2B;
        }
        QTabBar::tab {
            background-color: #3C3C3C;
            color: #FFFFFF;
            padding: 6px 12px;
            margin-right: 2px;
        }
        QTabBar::tab:selected {
            background-color: #4ECDC4;
            color: #000000;
        }
        QTabBar::tab:hover {
            background-color: #4C4C4C;
        }
        QScrollBar:vertical {
            background-color: #3C3C3C;
            width: 12px;
        }
        QScrollBar::handle:vertical {
            background-color: #555555;
            border-radius: 6px;
            min-height: 20px;
        }
        QScrollBar::handle:vertical:hover {
            background-color: #666666;
        }
        QMenuBar {
            background-color: #3C3C3C;
            color: #FFFFFF;
        }
        QMenu {
            background-color: #3C3C3C;
            color: #FFFFFF;
        }
        QMenu::item:selected {
            background-color: #4ECDC4;
            color: #000000;
        }
        QMessageBox {
            background-color: #2B2B2B;
            color: #FFFFFF;
        }
        QCalendarWidget {
            background-color: #2B2B2B;
            color: #FFFFFF;
        }
        QCalendarWidget QTableView {
            background-color: #2B2B2B;
            alternate-background-color: #353535;
            color: #FFFFFF;
            selection-background-color: #4ECDC4;
            selection-color: #000000;
        }
        """


# Global theme manager instance
_theme_manager = None


def get_theme_manager() -> ThemeManager:
    """الحصول على مثيل مدير الثيمات (Singleton)"""
    global _theme_manager
    if _theme_manager is None:
        _theme_manager = ThemeManager()
    return _theme_manager


def apply_theme_to_widget(widget):
    """تطبيق الثيم على Widget"""
    theme_manager = get_theme_manager()
    widget.setStyleSheet(theme_manager.get_stylesheet())

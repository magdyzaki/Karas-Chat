from PyQt5.QtGui import QFontDatabase
import os

def apply_style(app):
    # تحميل الخط الافتراضي الجميل مع معالجة الأخطاء
    font_path = "assets/Amiri-Regular.ttf"
    if os.path.exists(font_path):
        QFontDatabase.addApplicationFont(font_path)
        font_family = "'Amiri', 'Segoe UI', 'Tahoma', 'Arial Unicode MS', 'Arial', sans-serif"
    else:
        # استخدام خطوط النظام المدعومة للعربية
        font_family = "'Segoe UI', 'Tahoma', 'Arial Unicode MS', 'Arial', sans-serif"

    app.setStyleSheet("""
        QWidget {
            background-color: #FFFBEA;
            font-family: """ + font_family + """;
            font-size: 15px;
            color: #333;
        }

        /* التبويبات */
        QTabBar::tab {
            background: #FFD700;
            color: #222;
            border: 1px solid #E6C200;
            padding: 10px 20px;
            border-top-left-radius: 10px;
            border-top-right-radius: 10px;
            margin-right: 2px;
            min-width: 120px;
            font-weight: bold;
        }

        QTabBar::tab:selected {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #FFF8DC, stop:1 #FFD700);
            color: black;
            border-bottom: 2px solid #E6C200;
        }

        QTabWidget::pane {
            border: 2px solid #FFD700;
            border-radius: 8px;
            margin-top: -1px;
        }

        /* الأزرار */
        QPushButton {
            background-color: #FFD700;
            color: black;
            border: 1px solid #E6C200;
            border-radius: 10px;
            padding: 8px 16px;
            font-weight: bold;
            min-width: 120px;
        }

        QPushButton:hover {
            background-color: #FFC107;
            transform: scale(1.05);
        }

        QPushButton:pressed {
            background-color: #FFB300;
        }

        /* الجداول */
        QTableWidget {
            gridline-color: #E6C200;
            selection-background-color: #FFF2B2;
            alternate-background-color: #FFFBEA;
            font-size: 14px;
        }

        QHeaderView::section {
            background-color: #FFD700;
            color: black;
            padding: 6px;
            border: 1px solid #E6C200;
            font-weight: bold;
        }

        /* مربعات النص */
        QLineEdit, QComboBox, QTextEdit {
            border: 1px solid #E6C200;
            border-radius: 6px;
            padding: 6px;
            background-color: #FFFDE7;
            font-size: 15px;
        }

        /* رسائل النظام */
        QMessageBox {
            background-color: #FFFBEA;
        }
    """)
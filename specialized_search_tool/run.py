"""
ملف تشغيل البرنامج المتخصص
Run the Specialized Search Tool
"""
import sys
from PyQt5.QtWidgets import QApplication
from ui.specialized_search_window import SpecializedSearchWindow

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SpecializedSearchWindow()
    window.show()
    sys.exit(app.exec_())

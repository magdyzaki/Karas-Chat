from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout, QPushButton, QHBoxLayout, QSpacerItem, QSizePolicy
from PyQt5.QtGui import QFont, QLinearGradient, QBrush, QColor, QPainter, QPixmap
from PyQt5.QtCore import Qt, QPropertyAnimation, QEasingCurve, QSequentialAnimationGroup, QPoint, QTimer, QDateTime


class GradientLabel(QLabel):
    """نص KARAS المتحرك بلمعة ذهبية بسيطة"""
    def __init__(self, text):
        super().__init__(text)
        self.gradient_shift = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_gradient)
        self.timer.start(80)
        self.setFont(QFont("Amiri", 28, QFont.Bold))
        self.setAlignment(Qt.AlignCenter)

    def update_gradient(self):
        self.gradient_shift = (self.gradient_shift + 0.02) % 1.0
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        gradient = QLinearGradient(0, 0, self.width(), 0)
        gradient.setColorAt((self.gradient_shift - 0.2) % 1.0, QColor("#FFD700"))
        gradient.setColorAt(self.gradient_shift, QColor("#FFF8DC"))
        gradient.setColorAt((self.gradient_shift + 0.2) % 1.0, QColor("#FFD700"))
        painter.setPen(QColor("#FFD700"))
        painter.setBrush(QBrush(gradient))
        painter.setFont(self.font())
        painter.drawText(self.rect(), Qt.AlignCenter, self.text())


class HomePage(QWidget):
    def __init__(self):
        super().__init__()

        # إزالة الستايل الثابت للسماح بتطبيق الستايل من MainWindow
        # self.setStyleSheet("background-color: #FFFBEA;")  # تم إزالة الستايل الثابت
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)

        # ✨ شعار KARAS المتحرك بلمعة ذهبية
        self.karas_label = GradientLabel("KARAS")

        # 🔹 صورة على اليسار (شعار الشركة)
        self.logo_img = QLabel()
        import os
        logo_path = os.path.join(os.path.dirname(__file__), "..", "assets", "logo.png")
        pixmap = QPixmap(logo_path)
        if not pixmap.isNull():
            scaled = pixmap.scaledToWidth(160, Qt.SmoothTransformation)
            self.logo_img.setPixmap(scaled)
            self.logo_img.setAlignment(Qt.AlignLeft)
            self.logo_img.setStyleSheet("margin: 15px;")

        # 🔹 ترتيب KARAS والصورة أفقياً
        header_layout = QHBoxLayout()
        header_layout.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(self.logo_img, alignment=Qt.AlignLeft)
        header_layout.addWidget(self.karas_label, alignment=Qt.AlignRight)

        # 🔹 العنوان الرئيسي
        self.title = QLabel("مرحباً بك في نظام إدارة KARAS CRM")
        self.title.setFont(QFont("Amiri", 22, QFont.Bold))
        self.title.setAlignment(Qt.AlignCenter)
        # إزالة الستايل الثابت للسماح بتطبيق الستايل من MainWindow
        # self.title.setStyleSheet("color: #222;")  # تم إزالة الستايل الثابت

        # 🔹 الوصف
        self.desc = QLabel("إدارة مبيعاتك أصبحت أسهل، أسرع، وأكثر ذكاءً 🌟")
        self.desc.setFont(QFont("Amiri", 14))
        self.desc.setAlignment(Qt.AlignCenter)
        # إزالة الستايل الثابت للسماح بتطبيق الستايل من MainWindow
        # self.desc.setStyleSheet("color: #444;")  # تم إزالة الستايل الثابت

        # 🔹 الأزرار السريعة
        self.buttons_layout = QHBoxLayout()
        self.buttons = []
        data = [
            ("العملاء", "👥"),
            ("المنتجات", "📦"),
            ("المبيعات", "💰"),
            ("الفواتير", "🧾"),
            ("التقارير", "📊")
        ]

        for text, emoji in data:
            btn = HoverButton(f"{emoji}  {text}")
            btn.setFont(QFont("Amiri", 13))
            btn.setFixedSize(140, 50)
            # إزالة الستايل الثابت للسماح بتطبيق الستايل من MainWindow
            # btn.setStyleSheet("...")  # تم إزالة الستايل الثابت
            self.buttons.append(btn)
            self.buttons_layout.addWidget(btn)

        # 🔹 التاريخ والوقت والمؤقت في منتصف الصفحة السفلي
        self.datetime_label = QLabel()
        self.runtime_label = QLabel()
        self.datetime_label.setFont(QFont("Amiri", 12))
        self.runtime_label.setFont(QFont("Amiri", 12))
        # إزالة الستايلات الثابتة للسماح بتطبيق الستايل من MainWindow
        self.datetime_label.setStyleSheet("padding: 4px;")  # فقط padding
        self.runtime_label.setStyleSheet("padding: 4px;")  # فقط padding

        time_layout = QHBoxLayout()
        time_layout.setAlignment(Qt.AlignCenter)
        time_layout.addWidget(self.datetime_label)
        time_layout.addWidget(self.runtime_label)

        # 🔹 التوقيع السفلي
        self.signature_label = QLabel("💡 تم تصميم النظام بواسطة KARAS Dev Team")
        self.signature_label.setFont(QFont("Amiri", 11))
        self.signature_label.setAlignment(Qt.AlignCenter)
        # إزالة الستايل الثابت للسماح بتطبيق الستايل من MainWindow
        self.signature_label.setStyleSheet("margin-top: 8px; margin-bottom: 8px;")  # فقط margin

        # حفظ وقت بدء التشغيل
        self.start_time = QDateTime.currentDateTime()

        # تحديث الوقت والمؤقت كل ثانية
        timer = QTimer(self)
        timer.timeout.connect(self.update_time)
        timer.start(1000)
        self.update_time()

        # 🔹 تجميع الصفحة
        layout.addLayout(header_layout)
        layout.addWidget(self.title)
        layout.addWidget(self.desc)
        layout.addLayout(self.buttons_layout)
        layout.addLayout(time_layout)
        layout.addWidget(self.signature_label)
        layout.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Expanding))
        self.setLayout(layout)

        # 🎬 تشغيل الحركات
        QTimer.singleShot(200, self.animate_page)
        self.animate_logo()
        self.animate_buttons()

    def update_time(self):
        now = QDateTime.currentDateTime()
        formatted_time = now.toString("dddd - dd MMMM yyyy | hh:mm:ss AP")
        self.datetime_label.setText(f"🕒 {formatted_time}")

        elapsed = self.start_time.secsTo(now)
        hours, remainder = divmod(elapsed, 3600)
        minutes, seconds = divmod(remainder, 60)
        self.runtime_label.setText(f"⏱ النظام يعمل منذ: {hours:02}:{minutes:02}:{seconds:02}")

    def animate_page(self):
        for widget in [self.karas_label, self.title, self.desc]:
            anim = QPropertyAnimation(widget, b"windowOpacity")
            anim.setDuration(1500)
            anim.setStartValue(0)
            anim.setEndValue(1)
            anim.setEasingCurve(QEasingCurve.InOutQuad)
            anim.start()
            setattr(self, f"fade_{id(widget)}", anim)

    def animate_buttons(self):
        group = QSequentialAnimationGroup(self)
        for btn in self.buttons:
            anim = QPropertyAnimation(btn, b"windowOpacity")
            anim.setDuration(700)
            anim.setStartValue(0)
            anim.setEndValue(1)
            anim.setEasingCurve(QEasingCurve.InOutQuad)
            group.addAnimation(anim)
        group.start()
        self.anim_group = group

    def animate_logo(self):
        """تحريك شعار KARAS لأعلى وأسفل بشكل ناعم"""
        self.karas_anim = QPropertyAnimation(self.karas_label, b"pos")
        self.karas_anim.setDuration(2000)
        self.karas_anim.setStartValue(QPoint(self.karas_label.x(), self.karas_label.y()))
        self.karas_anim.setEndValue(QPoint(self.karas_label.x(), self.karas_label.y() + 10))
        self.karas_anim.setEasingCurve(QEasingCurve.InOutQuad)
        self.karas_anim.setLoopCount(-1)
        self.karas_anim.start()


class HoverButton(QPushButton):
    """زر يتحرك برفق عند المرور عليه"""
    def __init__(self, text):
        super().__init__(text)
        self._animation = None

    def enterEvent(self, event):
        self.animate_scale(1.08)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.animate_scale(1.0)
        super().leaveEvent(event)

    def animate_scale(self, scale):
        if self._animation:
            self._animation.stop()
        self._animation = QPropertyAnimation(self, b"geometry")
        self._animation.setDuration(150)
        start_rect = self.geometry()
        center = start_rect.center()
        new_width = int(start_rect.width() * scale)
        new_height = int(start_rect.height() * scale)
        new_rect = start_rect
        new_rect.setWidth(new_width)
        new_rect.setHeight(new_height)
        new_rect.moveCenter(center)
        self._animation.setStartValue(start_rect)
        self._animation.setEndValue(new_rect)
        self._animation.setEasingCurve(QEasingCurve.InOutQuad)
        self._animation.start()
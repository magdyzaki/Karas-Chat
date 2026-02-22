from PyQt5.QtWidgets import QLabel
from PyQt5.QtGui import QPixmap, QPainter, QPainterPath
from PyQt5.QtCore import Qt, QPropertyAnimation, QRect

def make_round_pixmap(pixmap: QPixmap, size: int) -> QPixmap:
    """تحويل الصورة إلى دائرية بالحجم المطلوب"""
    if pixmap.isNull():
        return QPixmap()
    scaled = pixmap.scaled(size, size, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
    mask = QPixmap(size, size)
    mask.fill(Qt.transparent)
    p = QPainter(mask)
    p.setRenderHint(QPainter.Antialiasing)
    path = QPainterPath()
    path.addEllipse(0, 0, size, size)
    p.fillPath(path, Qt.white)
    p.end()

    result = QPixmap(size, size)
    result.fill(Qt.transparent)
    p2 = QPainter(result)
    p2.setRenderHint(QPainter.Antialiasing)
    p2.setClipPath(path)
    src_x = (scaled.width() - size) // 2
    src_y = (scaled.height() - size) // 2
    p2.drawPixmap(0, 0, scaled.copy(src_x, src_y, size, size))
    p2.end()
    return result


def add_logo(widget, logo_path="assets/logo.png", corner="right", size=100, margin=15):
    """إضافة شعار دائري للنافذة أو الصفحة"""
    pix = QPixmap(logo_path)
    if pix.isNull():
        print(f"❌ لم يتم العثور على الشعار في: {logo_path}")
        return None

    logo_label = QLabel(widget)
    round_pix = make_round_pixmap(pix, size)
    logo_label.setPixmap(round_pix)
    logo_label.setFixedSize(round_pix.size())
    logo_label.setStyleSheet("background: transparent;")

    # تحديد مكان الشعار
    if corner == "right":
        x = widget.width() - size - margin
    else:
        x = margin
    y = margin
    logo_label.move(x, y)

    # حركة دخول ناعمة
    anim = QPropertyAnimation(logo_label, b"geometry", widget)
    anim.setDuration(500)
    start_rect = QRect(x, -size, size, size)
    end_rect = QRect(x, y, size, size)
    anim.setStartValue(start_rect)
    anim.setEndValue(end_rect)
    anim.start()

    widget._logo_label = logo_label
    widget._logo_anim = anim

    # يبقى في نفس الركن لما تغير حجم النافذة
    orig_resize = widget.resizeEvent if hasattr(widget, "resizeEvent") else None

    def new_resize(event):
        if orig_resize:
            orig_resize(event)
        if hasattr(widget, "_logo_label") and widget._logo_label.pixmap():
            if corner == "right":
                x = widget.width() - size - margin
            else:
                x = margin
            widget._logo_label.move(x, margin)

    widget.resizeEvent = new_resize
    print(f"✅ تم إضافة الشعار بنجاح ({corner})")
    return logo_label
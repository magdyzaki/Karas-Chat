# pages/InvoicePreviewWindow.py
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QTextBrowser, QSizePolicy, QLabel, QSlider
)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt, QTimer
import os, html

# تنتظر dict بنفس البنية اللي بنمرّرها من InvoicesPage.get_invoice_data()
# keys: invoice_no, date, client_name, address, phone, items (list of dicts with description, qty, price, total),
#       payment_terms, bank_info, currency

ASSETS = os.path.join(os.path.dirname(__file__), "..", "assets")
LETTERHEAD_PATH = os.path.join(ASSETS, "letterhead.png")  # تأكد الصورة هنا

class InvoicePreviewWindow(QDialog):
    def __init__(self, invoice_data, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Invoice Preview — {invoice_data.get('invoice_no','')}")
        self.setModal(False)
        self.resize(900, 700)
        self.invoice = invoice_data

        self.main_layout = QVBoxLayout()
        self.setLayout(self.main_layout)

        # أدوات التحكم (تكبير/تصغير - إغلاق)
        ctrl_layout = QHBoxLayout()
        self.zoom_in_btn = QPushButton("🔍 تكبير")
        self.zoom_out_btn = QPushButton("🔍 تصغير")
        self.fit_btn = QPushButton("ملء الصفحة")
        self.close_btn = QPushButton("إغلاق")
        ctrl_layout.addWidget(self.zoom_out_btn)
        ctrl_layout.addWidget(self.zoom_in_btn)
        ctrl_layout.addWidget(self.fit_btn)
        ctrl_layout.addStretch()
        ctrl_layout.addWidget(self.close_btn)
        self.main_layout.addLayout(ctrl_layout)

        # شريط تكبير دقيق (0.5x .. 2.5x)
        slider_layout = QHBoxLayout()
        slider_layout.addWidget(QLabel("حجم:"))
        self.zoom_slider = QSlider(Qt.Horizontal)
        self.zoom_slider.setRange(50, 250)
        self.zoom_slider.setValue(100)
        self.zoom_label = QLabel("100%")
        slider_layout.addWidget(self.zoom_slider)
        slider_layout.addWidget(self.zoom_label)
        self.main_layout.addLayout(slider_layout)

        # منطقة العرض (QTextBrowser لعرض HTML)
        self.browser = QTextBrowser()
        self.browser.setOpenExternalLinks(False)
        self.browser.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.browser.setStyleSheet("background: white;")
        self.main_layout.addWidget(self.browser)

        # توصيل الأحداث
        self.close_btn.clicked.connect(self.close)
        self.zoom_in_btn.clicked.connect(self.zoom_in)
        self.zoom_out_btn.clicked.connect(self.zoom_out)
        self.fit_btn.clicked.connect(self.fit_to_window)
        self.zoom_slider.valueChanged.connect(self.on_slider)

        # تحميل HTML في المتصفح
        html_content = self.build_html()
        self.browser.setHtml(html_content)

        # نؤخّر قليلًا إعادة التطبيق (في حال الصورة الخلفية تحتاج وقت)
        QTimer.singleShot(80, lambda: self.browser.setHtml(self.build_html()))

    def on_slider(self, v):
        self.zoom_label.setText(f"{v}%")
        factor = v / 100.0
        self.browser.setZoomFactor(factor)

    def zoom_in(self):
        v = min(250, self.zoom_slider.value() + 10)
        self.zoom_slider.setValue(v)

    def zoom_out(self):
        v = max(50, self.zoom_slider.value() - 10)
        self.zoom_slider.setValue(v)

    def fit_to_window(self):
        # ستعيد القيمة للـ100% (تقريبًا ملائمة للعرض)
        self.zoom_slider.setValue(100)
        self.browser.setZoomFactor(1.0)

    def safe(self, s):
        # تأمين النصوص قبل إدخالها في HTML
        return html.escape(str(s or ""))

    def build_items_rows(self):
        rows_html = ""
        # اعرض كل بند كسطر جدول. إذا الوصف طويل استخدم <td> مع white-space.
        for it in self.invoice.get("items", []):
            desc = self.safe(it.get("description", ""))
            qty = self.safe(it.get("quantity", ""))
            price = self.safe(it.get("price", ""))
            total = self.safe(it.get("total", ""))
            # نسمح بكسر الأسطر داخل الوصف
            rows_html += f"""
                <tr>
                    <td style="padding:6px; vertical-align:top; border:1px solid #bbb; max-width:380px;">
                        {desc}
                    </td>
                    <td style="padding:6px; text-align:center; border:1px solid #bbb; width:80px;">{qty}</td>
                    <td style="padding:6px; text-align:center; border:1px solid #bbb; width:120px;">{price}</td>
                    <td style="padding:6px; text-align:center; border:1px solid #bbb; width:120px;">{total}</td>
                </tr>
            """
        return rows_html

    def build_html(self):
        # مسارات الصورة تحتاج صيغة file:// لعرضها في QTextBrowser
        background_css = ""
        if os.path.exists(LETTERHEAD_PATH):
            # استخدم background-image في الحاوية الرئيسية
            bg_path = LETTERHEAD_PATH.replace("\\", "/")
            background_css = f"background-image: url('file://{bg_path}'); background-repeat:no-repeat; background-position:top center; background-size:contain;"
        else:
            background_css = "background-color: #ffffff;"

        invoice_no = self.safe(self.invoice.get("invoice_no", ""))
        date = self.safe(self.invoice.get("date", ""))
        client = self.safe(self.invoice.get("client_name", ""))
        address = self.safe(self.invoice.get("address", ""))
        phone = self.safe(self.invoice.get("phone", ""))
        currency = self.safe(self.invoice.get("currency", "EGP"))

        # احسب الإجمالي
        total_sum = 0.0
        for it in self.invoice.get("items", []):
            try:
                total_sum += float(it.get("total", 0) or 0)
            except:
                pass

        # بناء html
        html_doc = f"""
        <html>
        <head>
          <meta charset="utf-8">
          <style>
            body {{ font-family: "Times New Roman", Georgia, serif; margin:0; padding:24px; {background_css} }}
            .wrapper {{ width: 100%; max-width: 780px; margin: auto; background: rgba(255,255,255,0.92); padding: 18px; box-sizing:border-box; border-radius:4px; }}
            .hdr-left {{ float:left; width:65%; }}
            .hdr-right {{ float:right; width:35%; text-align:right; }}
            h1.inv-no {{ font-family: "Arial Black", "Arial", sans-serif; font-size:20px; margin:0; }}
            .meta {{ font-size:12px; color:#222; margin-top:6px; }}
            .client-info {{ margin-top:10px; font-size:13px; }}
            table.inv-table {{ width:100%; border-collapse:collapse; margin-top:12px; font-size:13px; }}
            table.inv-table th {{ background:#f0f0f0; padding:8px; border:1px solid #bbb; font-weight:bold; }}
            table.inv-table td {{ padding:6px; border:1px solid #bbb; vertical-align:top; }}
            .summary {{ margin-top:10px; text-align:right; font-weight:bold; font-size:14px; }}
            .section-title {{ margin-top:12px; font-weight:bold; font-size:13px; }}
            .foot-note {{ margin-top:12px; font-size:12px; color:#333; white-space:pre-wrap; }}
            .clear {{ clear:both; }}
          </style>
        </head>
        <body>
          <div class="wrapper">
            <div class="hdr-left">
                <div style="margin-bottom:6px;">
                    <span style="font-size:12px; color:#555;">Invoice No:</span>
                    <div class="inv-no">{invoice_no}</div>
                </div>
                <div class="meta">Date: {date}</div>
            </div>

            <div class="hdr-right">
                <div style="font-size:16px; font-weight:bold;">{client}</div>
                <div class="client-info">{address}<br/>Tel: {phone}</div>
            </div>

            <div class="clear"></div>

            <table class="inv-table">
                <thead>
                    <tr>
                        <th style="width:50%;">Description</th>
                        <th style="width:12%; text-align:center;">QTY</th>
                        <th style="width:19%; text-align:center;">Price ({currency})</th>
                        <th style="width:19%; text-align:center;">Total ({currency})</th>
                    </tr>
                </thead>
                <tbody>
                    {self.build_items_rows()}
                </tbody>
            </table>

            <div class="summary">Total: {format_number(total_sum)} {currency}</div>

            <div class="section-title">Payment Terms</div>
            <div class="foot-note">{html.escape(self.invoice.get('payment_terms',''))}</div>

            <div class="section-title">Bank Information</div>
            <div class="foot-note">{html.escape(self.invoice.get('bank_info',''))}</div>

          </div>
        </body>
        </html>
        """
        return html_doc

def format_number(v):
    try:
        f = float(v)
        if f.is_integer():
            return str(int(f))
        return f"{f:,.2f}"
    except:
        return str(v)
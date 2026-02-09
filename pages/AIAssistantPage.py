from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit, QLineEdit, QPushButton,
    QMessageBox
)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt, QTimer
import sqlite3
import os

DB = os.path.join(os.path.dirname(__file__), "..", "database", "crm.db")

class AIAssistantPage(QWidget):
    def __init__(self):
        super().__init__()

        self.setStyleSheet("""
            QWidget {
                background-color: #fdfcf3;
            }
            QLabel {
                color: #222;
                font-size: 14px;
            }
            QLineEdit {
                padding: 8px;
                border: 2px solid #e1e1a9;
                border-radius: 10px;
                font-size: 14px;
                background-color: white;
            }
            QPushButton {
                background-color: #f4c842;
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
                font-weight: bold;
                color: #222;
            }
            QPushButton:hover {
                background-color: #ffdb6e;
            }
            QTextEdit {
                background-color: #fff;
                border: 2px solid #f4e8a2;
                border-radius: 10px;
                padding: 10px;
            }
        """)

        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        title = QLabel("🤖 المساعد الذكي - KARAS")
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont("Amiri", 18, QFont.Bold))
        title.setStyleSheet("color: #333; margin-bottom: 10px;")

        # سجل المحادثة
        self.chat_area = QTextEdit()
        self.chat_area.setReadOnly(True)
        self.chat_area.setFont(QFont("Amiri", 12))
        self.chat_area.setMinimumHeight(400)

        # شريط الإدخال
        input_layout = QHBoxLayout()
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("اكتب سؤالك هنا... (مثال: كم عدد العملاء؟ ما هي المبيعات اليوم؟)")
        self.input_field.returnPressed.connect(self.send_message)

        send_button = QPushButton("إرسال 📤")
        send_button.clicked.connect(self.send_message)

        input_layout.addWidget(self.input_field)
        input_layout.addWidget(send_button)

        # أزرار سريعة
        quick_buttons_layout = QHBoxLayout()
        quick_btn1 = QPushButton("📊 إحصائيات")
        quick_btn1.clicked.connect(lambda: self.quick_query("إحصائيات"))
        quick_btn2 = QPushButton("💰 المبيعات")
        quick_btn2.clicked.connect(lambda: self.quick_query("مبيعات"))
        quick_btn3 = QPushButton("📦 المخزون")
        quick_btn3.clicked.connect(lambda: self.quick_query("مخزون"))
        quick_btn4 = QPushButton("❓ مساعدة")
        quick_btn4.clicked.connect(lambda: self.quick_query("مساعدة"))

        for btn in [quick_btn1, quick_btn2, quick_btn3, quick_btn4]:
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #FFD700;
                    padding: 8px 15px;
                    font-size: 11px;
                }
            """)
            quick_buttons_layout.addWidget(btn)

        layout.addWidget(title)
        layout.addWidget(self.chat_area)
        layout.addLayout(quick_buttons_layout)
        layout.addLayout(input_layout)
        
        self.setLayout(layout)

        self.add_bot_message("أهلًا بك 👋، أنا KARAS، مساعدك الذكي!\nيمكنني مساعدتك في:\n• إحصائيات المبيعات والعملاء\n• معلومات المخزون\n• إرشادات استخدام البرنامج\n• الإجابة على أسئلتك\n\nكيف يمكنني مساعدتك اليوم؟")

    def db_conn(self):
        """الاتصال بقاعدة البيانات"""
        try:
            return sqlite3.connect(DB)
        except:
            return None

    def add_bot_message(self, text):
        """إضافة رسالة من البوت"""
        self.chat_area.append(f"<div style='background-color:#f0f0f0; padding:8px; border-radius:5px; margin:5px 0;'><b>🤖 KARAS:</b> {text}</div>")

    def add_user_message(self, text):
        """إضافة رسالة من المستخدم"""
        self.chat_area.append(f"<div style='background-color:#e3f2fd; padding:8px; border-radius:5px; margin:5px 0; text-align:right;'><b>🧑‍💼 أنت:</b> {text}</div>")

    def quick_query(self, query_type):
        """استعلامات سريعة"""
        if query_type == "إحصائيات":
            self.send_message("أعطني إحصائيات")
        elif query_type == "مبيعات":
            self.send_message("ما هي المبيعات")
        elif query_type == "مخزون":
            self.send_message("ما هو المخزون")
        elif query_type == "مساعدة":
            self.send_message("كيف أستخدم البرنامج")

    def send_message(self):
        """إرسال رسالة"""
        user_text = self.input_field.text().strip()
        if not user_text:
            return
        self.add_user_message(user_text)
        self.input_field.clear()

        # محاكاة التفكير
        QTimer.singleShot(500, lambda: self.bot_reply(user_text))

    def bot_reply(self, user_text):
        """رد ذكي بناءً على السؤال"""
        user_text_lower = user_text.lower()
        reply = ""

        # ========== إحصائيات ==========
        if any(word in user_text_lower for word in ["إحصائيات", "إحصاء", "عدد", "كم"]):
            reply = self.get_statistics()

        # ========== المبيعات ==========
        elif any(word in user_text_lower for word in ["مبيعات", "بيع", "مبيع", "فاتورة"]):
            reply = self.get_sales_info()

        # ========== المخزون ==========
        elif any(word in user_text_lower for word in ["مخزون", "منتج", "كمية", "متوفر"]):
            reply = self.get_stock_info()

        # ========== العملاء ==========
        elif any(word in user_text_lower for word in ["عميل", "عملاء", "زبون"]):
            reply = self.get_customers_info()

        # ========== مساعدة ==========
        elif any(word in user_text_lower for word in ["مساعدة", "كيف", "استخدام", "شرح"]):
            reply = self.get_help()

        # ========== شكر ==========
        elif any(word in user_text_lower for word in ["شكر", "شكرا", "ممتاز", "رائع"]):
            reply = "العفو صديقي 😊، يسعدني أساعدك في أي وقت. إذا كان لديك أي سؤال آخر، أنا هنا! 💪"

        # ========== رد افتراضي ذكي ==========
        else:
            reply = self.get_smart_default_reply(user_text)

        self.add_bot_message(reply)

    def get_statistics(self):
        """الحصول على إحصائيات"""
        conn = self.db_conn()
        if not conn:
            return "❌ لا يمكن الاتصال بقاعدة البيانات"

        try:
            cur = conn.cursor()
            
            # عدد العملاء
            cur.execute("SELECT COUNT(*) FROM customers")
            customers_count = cur.fetchone()[0]
            
            # عدد المنتجات
            cur.execute("SELECT COUNT(*) FROM products")
            products_count = cur.fetchone()[0]
            
            # عدد المبيعات
            cur.execute("SELECT COUNT(*) FROM sales")
            sales_count = cur.fetchone()[0]
            
            # إجمالي المبيعات
            cur.execute("SELECT COALESCE(SUM(total_usd), 0) FROM sales")
            total_sales = cur.fetchone()[0]
            
            # إجمالي المرتجعات
            cur.execute("SELECT COALESCE(SUM(return_qty), 0) FROM sales")
            total_returns = cur.fetchone()[0]
            
            conn.close()
            
            return f"""📊 <b>إحصائيات النظام:</b>

👥 <b>العملاء:</b> {customers_count} عميل
📦 <b>المنتجات:</b> {products_count} منتج
💰 <b>المبيعات:</b> {sales_count} عملية بيع
💵 <b>إجمالي المبيعات:</b> ${total_sales:,.2f} USD
🔄 <b>المرتجعات:</b> {total_returns:.2f} طن

💡 <b>نصيحة:</b> يمكنك زيارة صفحة التقارير للحصول على تفاصيل أكثر!"""
            
        except Exception as e:
            return f"❌ حدث خطأ في جلب الإحصائيات: {str(e)}"

    def get_sales_info(self):
        """معلومات المبيعات"""
        conn = self.db_conn()
        if not conn:
            return "❌ لا يمكن الاتصال بقاعدة البيانات"

        try:
            cur = conn.cursor()
            cur.execute("""
                SELECT customer_name, product_name, quantity, total_usd, sale_date
                FROM sales 
                ORDER BY id DESC 
                LIMIT 5
            """)
            sales = cur.fetchall()
            conn.close()
            
            if not sales:
                return "📭 لا توجد مبيعات مسجلة حتى الآن.\n💡 يمكنك إضافة مبيعات من صفحة المبيعات!"
            
            reply = "💰 <b>آخر 5 مبيعات:</b>\n\n"
            for sale in sales:
                customer, product, qty, total, date = sale
                reply += f"• {product} - {qty} طن\n"
                reply += f"  العميل: {customer} | المبلغ: ${total:,.2f}\n"
                reply += f"  التاريخ: {date}\n\n"
            
            reply += "💡 لرؤية جميع المبيعات، انتقل إلى صفحة المبيعات!"
            return reply
            
        except Exception as e:
            return f"❌ حدث خطأ: {str(e)}"

    def get_stock_info(self):
        """معلومات المخزون"""
        conn = self.db_conn()
        if not conn:
            return "❌ لا يمكن الاتصال بقاعدة البيانات"

        try:
            cur = conn.cursor()
            cur.execute("""
                SELECT name, quantity, unit 
                FROM products 
                WHERE quantity > 0
                ORDER BY quantity DESC
                LIMIT 10
            """)
            products = cur.fetchall()
            conn.close()
            
            if not products:
                return "📭 لا توجد منتجات في المخزون.\n💡 يمكنك إضافة منتجات من صفحة المنتجات!"
            
            reply = "📦 <b>المخزون المتوفر:</b>\n\n"
            for product in products:
                name, qty, unit = product
                reply += f"• {name}: {qty} {unit}\n"
            
            reply += "\n💡 لرؤية تفاصيل المخزون الكاملة، انتقل إلى صفحة المخزون!"
            return reply
            
        except Exception as e:
            return f"❌ حدث خطأ: {str(e)}"

    def get_customers_info(self):
        """معلومات العملاء"""
        conn = self.db_conn()
        if not conn:
            return "❌ لا يمكن الاتصال بقاعدة البيانات"

        try:
            cur = conn.cursor()
            cur.execute("SELECT name, country, rating FROM customers ORDER BY id DESC LIMIT 5")
            customers = cur.fetchall()
            conn.close()
            
            if not customers:
                return "📭 لا يوجد عملاء مسجلون.\n💡 يمكنك إضافة عملاء من صفحة العملاء!"
            
            reply = "👥 <b>آخر 5 عملاء:</b>\n\n"
            for cust in customers:
                name, country, rating = cust
                reply += f"• {name} ({country})\n"
                if rating:
                    reply += f"  التقييم: {rating}\n"
                reply += "\n"
            
            reply += "💡 لرؤية جميع العملاء، انتقل إلى صفحة العملاء!"
            return reply
            
        except Exception as e:
            return f"❌ حدث خطأ: {str(e)}"

    def get_help(self):
        """مساعدة المستخدم"""
        return """❓ <b>دليل استخدام البرنامج:</b>

<b>1. إدارة العملاء:</b>
   • انتقل إلى تبويب "العملاء"
   • أضف عميل جديد أو عدّل بيانات موجودة

<b>2. إدارة المنتجات:</b>
   • انتقل إلى تبويب "المنتجات"
   • أضف منتجات مع الكميات والأسعار

<b>3. تسجيل المبيعات:</b>
   • انتقل إلى تبويب "المبيعات"
   • اختر عميل ومنتج وأدخل الكمية

<b>4. الفواتير:</b>
   • انتقل إلى تبويب "الفواتير"
   • أنشئ فواتير احترافية بصيغة Word

<b>5. المخزون:</b>
   • انتقل إلى تبويب "المخزون"
   • تابع الكميات المتبقية من كل منتج

<b>6. التقارير:</b>
   • انتقل إلى تبويب "التقارير"
   • اعرض تقارير مفصلة عن المبيعات والعملاء

💡 <b>نصيحة:</b> يمكنك استخدام الأزرار السريعة أعلاه للحصول على معلومات سريعة!"""

    def get_smart_default_reply(self, user_text):
        """رد ذكي افتراضي"""
        # محاولة فهم السؤال بشكل أفضل
        if "؟" in user_text or "?" in user_text:
            return f"""🤔 سؤالك: "{user_text}"

💡 يمكنني مساعدتك في:
• إحصائيات النظام (اكتب: إحصائيات)
• معلومات المبيعات (اكتب: مبيعات)
• معلومات المخزون (اكتب: مخزون)
• معلومات العملاء (اكتب: عملاء)
• مساعدة في الاستخدام (اكتب: مساعدة)

أو استخدم الأزرار السريعة أعلاه! 🚀"""
        else:
            return """💭 لم أفهم سؤالك تماماً، لكن يمكنني مساعدتك في:

📊 <b>إحصائيات:</b> اكتب "إحصائيات" أو "كم عدد العملاء"
💰 <b>المبيعات:</b> اكتب "مبيعات" أو "ما هي المبيعات"
📦 <b>المخزون:</b> اكتب "مخزون" أو "ما هو المخزون"
👥 <b>العملاء:</b> اكتب "عملاء" أو "من هم العملاء"
❓ <b>مساعدة:</b> اكتب "مساعدة" أو "كيف أستخدم البرنامج"

أو استخدم الأزرار السريعة! 🎯"""

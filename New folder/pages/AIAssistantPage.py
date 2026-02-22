from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QTextEdit, QLineEdit, QPushButton, QScrollArea, QFrame
from PyQt5.QtGui import QFont, QColor, QPalette
from PyQt5.QtCore import Qt, QTimer

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
                padding: 6px;
                border: 2px solid #e1e1a9;
                border-radius: 10px;
                font-size: 14px;
            }
            QPushButton {
                background-color: #f4c842;
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #ffdb6e;
            }
        """)

        layout = QVBoxLayout()
        title = QLabel("🤖 المساعد الذكي - KARAS")
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont("Cairo", 16, QFont.Bold))

        # سجل المحادثة
        self.chat_area = QTextEdit()
        self.chat_area.setReadOnly(True)
        self.chat_area.setFont(QFont("Cairo", 12))
        self.chat_area.setStyleSheet("background-color: #fff; border: 2px solid #f4e8a2; border-radius: 10px; padding: 8px;")

        # إدخال المستخدم
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("اكتب سؤالك هنا...")
        self.input_field.returnPressed.connect(self.send_message)

        # زر الإرسال
        send_button = QPushButton("إرسال")
        send_button.clicked.connect(self.send_message)

        layout.addWidget(title)
        layout.addWidget(self.chat_area)
        layout.addWidget(self.input_field)
        layout.addWidget(send_button)
        self.setLayout(layout)

        self.add_bot_message("أهلًا بك 👋، أنا KARAS، مساعدك الذكي! كيف يمكنني مساعدتك اليوم؟")

    def add_bot_message(self, text):
        self.chat_area.append(f"<p style='color:#444;'><b>🤖 KARAS:</b> {text}</p>")

    def add_user_message(self, text):
        self.chat_area.append(f"<p style='color:#2b7; text-align:right;'><b>🧑‍💼 أنت:</b> {text}</p>")

    def send_message(self):
        user_text = self.input_field.text().strip()
        if not user_text:
            return
        self.add_user_message(user_text)
        self.input_field.clear()

        # رد بسيط تلقائي مؤقت
        QTimer.singleShot(600, lambda: self.bot_reply(user_text))

    def bot_reply(self, user_text):
        user_text_lower = user_text.lower()

        # ردود بسيطة مؤقتة (محاكاة للذكاء)
        if "مبيعات" in user_text or "فاتورة" in user_text:
            reply = "يبدو أنك تسأل عن المبيعات أو الفواتير 💰 — يمكنك الدخول إلى صفحة المبيعات لإدارة العمليات بسهولة."
        elif "مخزون" in user_text:
            reply = "صفحة المخزون 📦 تتيح لك متابعة المنتجات والكميات المتوفرة."
        elif "شكرا" in user_text or "شكر" in user_text:
            reply = "العفو صديقي 😊، يسعدني أساعدك في أي وقت."
        else:
            reply = "سؤالك مميز! لكني ما زلت أتعلم 🤖💡، الإصدار القادم سيتصل مباشرة بالذكاء الاصطناعي لإجابات أدق."

        self.add_bot_message(reply)
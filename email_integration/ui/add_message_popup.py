from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QLabel,
    QComboBox, QTextEdit, QPushButton,
    QMessageBox, QHBoxLayout
)

from core.db import add_message, get_all_clients, get_client_by_id
from core.models import (
    today,
    calculate_score_effect,
    classify_client,
    suggested_status
)
from core.classification_alerts import check_classification_change
from core.scoring_config import is_ai_enabled
from core.reply_scoring import detect_positive_reply
from core.ai_reply_scoring import detect_positive_reply as ai_detect_positive_reply


class AddMessagePopup(QDialog):
    def __init__(self, refresh_callback):
        super().__init__()
        self.refresh_callback = refresh_callback

        self.setWindowTitle("Add Message / Interaction")
        self.setFixedSize(420, 420)

        layout = QVBoxLayout()

        # ===== Client Selector =====
        layout.addWidget(QLabel("Client"))
        self.client_box = QComboBox()
        self.clients_map = {}  # index -> (id, score)

        for c in get_all_clients():
            client_id = c[0]
            company = c[1]
            score = c[9]
            idx = self.client_box.count()
            self.client_box.addItem(company)
            self.clients_map[idx] = (client_id, score)

        layout.addWidget(self.client_box)

        # ===== Message Type =====
        layout.addWidget(QLabel("Message Type"))
        self.message_type = QComboBox()
        self.message_type.addItems([
            "reply",
            "price_request",
            "specs_request",
            "samples_request",
            "vague_reply",
            "long_ignore"
        ])
        layout.addWidget(self.message_type)

        # ===== Channel =====
        layout.addWidget(QLabel("Channel"))
        self.channel = QComboBox()
        self.channel.addItems(["Email", "WhatsApp", "LinkedIn"])
        layout.addWidget(self.channel)

        # ===== Client Response =====
        layout.addWidget(QLabel("Client Response (optional)"))
        self.response = QTextEdit()
        self.response.setFixedHeight(60)
        self.response.textChanged.connect(self.on_response_changed)
        layout.addWidget(self.response)

        # ===== Score Preview =====
        score_layout = QHBoxLayout()
        self.score_preview_label = QLabel("تأثير النقاط: 0")
        self.score_preview_label.setStyleSheet("font-weight: bold; color: #4ECDC4;")
        score_layout.addWidget(self.score_preview_label)
        score_layout.addStretch()
        layout.addLayout(score_layout)

        # ===== Notes =====
        layout.addWidget(QLabel("Notes"))
        self.notes = QTextEdit()
        self.notes.setFixedHeight(80)
        layout.addWidget(self.notes)

        # ===== Buttons =====
        button_layout = QHBoxLayout()
        save_btn = QPushButton("Save Message")
        save_btn.clicked.connect(self.save_message)
        button_layout.addWidget(save_btn)
        layout.addLayout(button_layout)
        
        # ربط تغيير نوع الرسالة لتحديث معاينة النقاط
        self.message_type.currentTextChanged.connect(self.update_score_preview)

        self.setLayout(layout)

    # ===== Update Score Preview =====
    def update_score_preview(self):
        """تحديث معاينة تأثير النقاط"""
        if self.client_box.currentIndex() < 0:
            return
        
        try:
            client_id, current_score = self.clients_map[self.client_box.currentIndex()]
            msg_type = self.message_type.currentText()
            
            # حساب تأثير النقاط من نوع الرسالة
            base_score_effect = calculate_score_effect(msg_type)
            
            # إذا كان هناك رد من العميل، تحليل الرد
            response_text = self.response.toPlainText().strip()
            ai_score_effect = 0
            
            if response_text:
                if is_ai_enabled():
                    # استخدام التقييم المتقدم بالذكاء الاصطناعي
                    ai_score_effect = ai_detect_positive_reply(response_text)
                else:
                    # استخدام التقييم العادي
                    ai_score_effect = detect_positive_reply(response_text)
            
            total_score_effect = base_score_effect + ai_score_effect
            new_score = current_score + total_score_effect
            new_classification = classify_client(new_score)
            
            # تحديث العرض
            if total_score_effect > 0:
                color = "#4ECDC4"  # أخضر
                symbol = "+"
            elif total_score_effect < 0:
                color = "#FF6B6B"  # أحمر
                symbol = ""
            else:
                color = "#95A5A6"  # رمادي
                symbol = ""
            
            self.score_preview_label.setText(
                f"تأثير النقاط: {symbol}{total_score_effect} | "
                f"النقاط الجديدة: {new_score} | "
                f"التصنيف: {new_classification}"
            )
            self.score_preview_label.setStyleSheet(f"font-weight: bold; color: {color};")
        except Exception:
            pass

    # ===== On Response Changed =====
    def on_response_changed(self):
        """عند تغيير نص الرد"""
        self.update_score_preview()

    # ===== Save Message =====
    def save_message(self):
        if self.client_box.currentIndex() < 0:
            QMessageBox.warning(self, "خطأ", "يرجى اختيار عميل")
            return

        client_id, current_score = self.clients_map[self.client_box.currentIndex()]
        msg_type = self.message_type.currentText()

        # الحصول على معلومات العميل الحالية
        client = get_client_by_id(client_id)
        if not client:
            QMessageBox.warning(self, "خطأ", "لم يتم العثور على العميل")
            return
        
        old_score = client[9] or 0
        old_classification = client[10] or "❌ Not Serious"

        # حساب تأثير النقاط
        base_score_effect = calculate_score_effect(msg_type)
        
        # تحليل الرد إذا كان موجوداً
        response_text = self.response.toPlainText().strip()
        ai_score_effect = 0
        
        if response_text:
            if is_ai_enabled():
                ai_score_effect = ai_detect_positive_reply(response_text)
            else:
                ai_score_effect = detect_positive_reply(response_text)
        
        total_score_effect = base_score_effect + ai_score_effect
        new_score = old_score + total_score_effect
        new_classification = classify_client(new_score)
        status = suggested_status(msg_type)

        data = {
            "client_id": client_id,
            "message_date": today(),
            "message_type": msg_type,
            "channel": self.channel.currentText(),
            "client_response": response_text,
            "notes": self.notes.toPlainText(),
            "score_effect": total_score_effect  # استخدام التأثير الإجمالي
        }

        # add_message يقوم بتحديث النقاط والتصنيف تلقائياً
        add_message(data)

        # الحصول على النقاط والتصنيف الجديدة بعد التحديث
        from core.db import get_client_by_id
        updated_client = get_client_by_id(client_id)
        if updated_client:
            final_score = updated_client[9] or 0
            final_classification = updated_client[10] or "❌ Not Serious"
            
            # تحديث الحالة فقط (لأن التصنيف تم تحديثه بالفعل في add_message)
            from core.db import get_connection
            conn = get_connection()
            cur = conn.cursor()
            cur.execute("UPDATE clients SET status = ? WHERE id = ?", (status, client_id))
            conn.commit()
            conn.close()

            # فحص تغيير التصنيف وعرض تنبيه
            if old_classification != final_classification:
                alert_result = check_classification_change(
                    client_id=client_id,
                    old_score=old_score,
                    new_score=final_score,
                    old_classification=old_classification,
                    new_classification=final_classification,
                    change_reason=f"رسالة: {msg_type}",
                    show_alert=False
                )
                
                if isinstance(alert_result, dict) and alert_result.get('show_alert'):
                    QMessageBox.information(
                        self,
                        alert_result.get('alert_type', 'تغيير التصنيف'),
                        alert_result.get('alert_text', ''),
                        QMessageBox.Ok
                    )

        self.refresh_callback()
        self.accept()

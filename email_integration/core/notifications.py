"""
نظام إشعارات سطح المكتب
Desktop Notifications System
"""
import json
import os
from datetime import datetime
from typing import List, Dict, Optional
from PyQt5.QtWidgets import QSystemTrayIcon, QApplication
from PyQt5.QtGui import QIcon, QPixmap, QPainter, QColor
from PyQt5.QtCore import QObject, pyqtSignal, QSize, Qt

# مسار ملف الإعدادات
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
NOTIFICATIONS_CONFIG_FILE = os.path.join(BASE_DIR, "config", "notifications.json")


class NotificationManager(QObject):
    """مدير الإشعارات"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.tray_icon = None
        self.config = self.load_config()
        self.setup_tray_icon()
    
    def setup_tray_icon(self):
        """إعداد أيقونة النظام"""
        if not QSystemTrayIcon.isSystemTrayAvailable():
            return
        
        try:
            self.tray_icon = QSystemTrayIcon(self)
            
            # محاولة إنشاء أيقونة
            icon = None
            
            # محاولة 1: البحث عن أيقونة في الملفات
            try:
                import os
                icon_paths = [
                    os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "elraee.ico"),
                    os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "icon.ico"),
                ]
                for icon_path in icon_paths:
                    if os.path.exists(icon_path):
                        icon = QIcon(icon_path)
                        break
            except Exception:
                pass
            
            # محاولة 2: استخدام أيقونة من النظام
            if not icon:
                try:
                    icon = QIcon.fromTheme("mail-message-new")
                    if icon.isNull():
                        icon = QIcon.fromTheme("mail")
                    if icon.isNull():
                        icon = QIcon.fromTheme("message")
                except Exception:
                    pass
            
            # محاولة 3: إنشاء أيقونة بسيطة باستخدام QPixmap
            if not icon or icon.isNull():
                try:
                    pixmap = QPixmap(QSize(32, 32))
                    pixmap.fill(QColor(70, 130, 180))  # لون أزرق فاتح
                    painter = QPainter(pixmap)
                    painter.setPen(QColor(255, 255, 255))
                    painter.setFont(painter.font())
                    painter.drawText(pixmap.rect(), Qt.AlignCenter, "E")
                    painter.end()
                    icon = QIcon(pixmap)
                except Exception:
                    pass
            
            # إذا لم نجد أيقونة، لا نعرض System Tray Icon
            if icon and not icon.isNull():
                self.tray_icon.setIcon(icon)
                self.tray_icon.setToolTip("Export Follow-Up Manager")
                self.tray_icon.show()
            else:
                # إذا لم نجد أيقونة، لا نعرض System Tray Icon
                self.tray_icon = None
                
        except Exception:
            # إذا فشل إعداد الأيقونة، لا نوقف العملية
            self.tray_icon = None
    
    def load_config(self) -> Dict:
        """تحميل إعدادات الإشعارات"""
        default_config = {
            "enabled": True,
            "followup_clients": True,
            "pending_requests": True,
            "pending_tasks": True,
            "deals_closing": True,
            "check_interval_minutes": 30,  # التحقق كل 30 دقيقة
            "show_on_startup": True
        }
        
        if os.path.exists(NOTIFICATIONS_CONFIG_FILE):
            try:
                os.makedirs(os.path.dirname(NOTIFICATIONS_CONFIG_FILE), exist_ok=True)
                with open(NOTIFICATIONS_CONFIG_FILE, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                    default_config.update(user_config)
            except Exception:
                pass
        
        return default_config
    
    def save_config(self):
        """حفظ إعدادات الإشعارات"""
        try:
            os.makedirs(os.path.dirname(NOTIFICATIONS_CONFIG_FILE), exist_ok=True)
            with open(NOTIFICATIONS_CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
        except Exception:
            pass
    
    def is_enabled(self) -> bool:
        """هل الإشعارات مفعّلة؟"""
        return self.config.get("enabled", True)
    
    def show_notification(self, title: str, message: str, timeout: int = 5000):
        """عرض إشعار"""
        if not self.is_enabled() or not self.tray_icon:
            return
        
        if not self.tray_icon.isSystemTrayAvailable():
            return
        
        try:
            self.tray_icon.showMessage(
                title,
                message,
                QSystemTrayIcon.Information,
                timeout
            )
        except Exception:
            pass  # إذا فشل الإشعار، لا نوقف العملية
    
    def check_and_show_notifications(self):
        """التحقق من الإشعارات وعرضها"""
        if not self.is_enabled():
            return
        
        notifications = []
        
        # إشعارات العملاء الذين يحتاجون متابعة
        if self.config.get("followup_clients", True):
            followup_notifications = self.get_followup_notifications()
            notifications.extend(followup_notifications)
        
        # إشعارات الطلبات المعلقة
        if self.config.get("pending_requests", True):
            request_notifications = self.get_pending_requests_notifications()
            notifications.extend(request_notifications)
        
        # إشعارات المهام المعلقة
        if self.config.get("pending_tasks", True):
            task_notifications = self.get_pending_tasks_notifications()
            notifications.extend(task_notifications)
        
        # إشعارات الصفقات القريبة من الإغلاق
        if self.config.get("deals_closing", True):
            deal_notifications = self.get_deals_closing_notifications()
            notifications.extend(deal_notifications)
        
        # عرض الإشعارات
        for title, message in notifications:
            self.show_notification(title, message)
    
    def get_followup_notifications(self) -> List[tuple]:
        """الحصول على إشعارات العملاء الذين يحتاجون متابعة"""
        notifications = []
        
        try:
            from core.db import get_clients_needing_followup
            clients = get_clients_needing_followup()
            
            if clients:
                count = len(clients)
                if count == 1:
                    title = "⏰ متابعة مطلوبة"
                    message = f"يحتاج العميل '{clients[0]}' إلى متابعة"
                elif count <= 5:
                    title = "⏰ متابعة مطلوبة"
                    message = f"{count} عملاء يحتاجون متابعة: {', '.join(clients[:5])}"
                else:
                    title = "⏰ متابعة مطلوبة"
                    message = f"{count} عملاء يحتاجون متابعة"
                
                notifications.append((title, message))
        except Exception:
            pass
        
        return notifications
    
    def get_pending_requests_notifications(self) -> List[tuple]:
        """الحصول على إشعارات الطلبات المعلقة"""
        notifications = []
        
        try:
            from core.db import get_connection
            
            conn = get_connection()
            cur = conn.cursor()
            
            # الحصول على الطلبات المعلقة
            cur.execute("""
                SELECT COUNT(*) 
                FROM requests 
                WHERE reply_status = 'pending' AND status = 'open'
            """)
            count = cur.fetchone()[0]
            conn.close()
            
            if count > 0:
                if count == 1:
                    title = "📋 طلب معلق"
                    message = "طلب واحد يحتاج رد"
                else:
                    title = "📋 طلبات معلقة"
                    message = f"{count} طلبات تحتاج رد"
                
                notifications.append((title, message))
        except Exception:
            pass
        
        return notifications
    
    def get_pending_tasks_notifications(self) -> List[tuple]:
        """الحصول على إشعارات المهام المعلقة"""
        notifications = []
        
        try:
            from core.tasks import get_tasks_due_today, get_overdue_tasks
            
            # المهام المتأخرة
            overdue_tasks = get_overdue_tasks()
            
            # المهام المستحقة اليوم
            due_today_tasks = get_tasks_due_today()
            
            if overdue_tasks:
                count = len(overdue_tasks)
                title = "🚨 مهام متأخرة"
                message = f"{count} مهام متأخرة تحتاج متابعة"
                notifications.append((title, message))
            
            if due_today_tasks:
                count = len(due_today_tasks)
                if not overdue_tasks:  # إذا لم تكن هناك مهام متأخرة، نعرض المهام المستحقة اليوم
                    title = "📝 مهام مستحقة اليوم"
                    message = f"{count} مهام مستحقة اليوم"
                    notifications.append((title, message))
        except Exception:
            pass
        
        return notifications
    
    def get_deals_closing_notifications(self) -> List[tuple]:
        """الحصول على إشعارات الصفقات القريبة من الإغلاق"""
        notifications = []
        
        try:
            from core.sales import get_all_deals
            
            all_deals = get_all_deals(status="active")
            
            # الصفقات في مرحلة "Negotiation" أو "Proposal"
            # all_deals هي tuples: (id, client_id, company_name, deal_name, product_name, stage, value, currency, probability, expected_close_date, actual_close_date, status, notes, created_date, updated_date)
            closing_deals = [
                deal for deal in all_deals
                if len(deal) > 5 and deal[5] in ["Negotiation", "Proposal"] and (len(deal) <= 11 or deal[11] != "Closed Lost")
            ]
            
            if closing_deals:
                count = len(closing_deals)
                if count == 1:
                    title = "💰 صفقة قريبة"
                    deal = closing_deals[0]
                    company_name = deal[2] if len(deal) > 2 else "عميل"
                    value = deal[6] if len(deal) > 6 else 0
                    message = f"صفقة مع {company_name}: ${value:,.0f}"
                else:
                    title = "💰 صفقات قريبة"
                    total_value = sum(deal[6] if len(deal) > 6 else 0 for deal in closing_deals)
                    message = f"{count} صفقات قريبة: ${total_value:,.0f}"
                
                notifications.append((title, message))
        except Exception:
            pass
        
        return notifications
    
    def set_enabled(self, enabled: bool):
        """تفعيل/تعطيل الإشعارات"""
        self.config["enabled"] = enabled
        self.save_config()
    
    def set_followup_clients(self, enabled: bool):
        """تفعيل/تعطيل إشعارات المتابعة"""
        self.config["followup_clients"] = enabled
        self.save_config()
    
    def set_pending_requests(self, enabled: bool):
        """تفعيل/تعطيل إشعارات الطلبات"""
        self.config["pending_requests"] = enabled
        self.save_config()
    
    def set_pending_tasks(self, enabled: bool):
        """تفعيل/تعطيل إشعارات المهام"""
        self.config["pending_tasks"] = enabled
        self.save_config()
    
    def set_deals_closing(self, enabled: bool):
        """تفعيل/تعطيل إشعارات الصفقات"""
        self.config["deals_closing"] = enabled
        self.save_config()
    
    def set_check_interval(self, minutes: int):
        """تعيين فترة التحقق من الإشعارات (بالدقائق)"""
        self.config["check_interval_minutes"] = minutes
        self.save_config()
    
    def get_check_interval(self) -> int:
        """الحصول على فترة التحقق (بالدقائق)"""
        return self.config.get("check_interval_minutes", 30)


def get_notification_manager() -> Optional[NotificationManager]:
    """الحصول على مدير الإشعارات (Singleton)"""
    global _notification_manager
    if '_notification_manager' not in globals():
        _notification_manager = None
    return _notification_manager


def set_notification_manager(manager: NotificationManager):
    """تعيين مدير الإشعارات"""
    global _notification_manager
    _notification_manager = manager

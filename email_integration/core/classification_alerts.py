"""
نظام التنبيهات عند تغيير التصنيف
Classification Change Alerts System
"""
import sqlite3
from datetime import datetime
from typing import List, Dict
from PyQt5.QtWidgets import QMessageBox
from .db import get_connection
from .score_history import record_score_change, get_classification_changes


def check_classification_change(
    client_id: int,
    old_score: int,
    new_score: int,
    old_classification: str,
    new_classification: str,
    change_reason: str = None,
    message_id: int = None,
    show_alert: bool = True
):
    """
    فحص تغيير التصنيف وإرسال تنبيه إذا لزم الأمر
    Returns: False if no change, True if changed but no alert, Dict if alert needed
    """
    if old_classification == new_classification:
        return False
    
    # تسجيل التغيير في السجل
    try:
        record_score_change(
            client_id=client_id,
            new_score=new_score,
            classification=new_classification,
            change_reason=change_reason or f"Score changed from {old_score} to {new_score}",
            message_id=message_id
        )
    except Exception:
        pass  # إذا فشل التسجيل، لا نوقف العملية
    
    # إظهار تنبيه للمستخدم
    if show_alert:
        try:
            from .db import get_client_by_id
            client = get_client_by_id(client_id)
            if client:
                company_name = client[1] or "Unknown"
                
                # تحديد نوع التنبيه حسب الاتجاه
                if old_score < new_score:
                    alert_type = "تصنيف محسّن"
                    alert_icon = QMessageBox.Information
                else:
                    alert_type = "تنبيه: انخفاض التصنيف"
                    alert_icon = QMessageBox.Warning
                
                alert_text = f"""
تم تغيير تصنيف العميل:

الشركة: {company_name}

التصنيف السابق: {old_classification}
النقاط السابقة: {old_score}

التصنيف الجديد: {new_classification}
النقاط الجديدة: {new_score}

السبب: {change_reason or 'تغيير تلقائي'}
                """
                
                # سيتم استدعاء QMessageBox من واجهة المستخدم
                return {
                    'show_alert': True,
                    'alert_type': alert_type,
                    'alert_icon': alert_icon,
                    'alert_text': alert_text,
                    'company_name': company_name
                }
        except Exception:
            pass
    
    return True


def get_recent_classification_changes(days: int = 7) -> List[Dict]:
    """الحصول على تغييرات التصنيف الحديثة"""
    return get_classification_changes(days=days)


def should_alert_on_classification_change(
    old_classification: str,
    new_classification: str
) -> bool:
    """
    تحديد ما إذا كان يجب إرسال تنبيه عند تغيير التصنيف
    يمكن تخصيص القواعد هنا
    """
    # تنبيه عند أي تغيير في التصنيف
    return old_classification != new_classification
    
    # مثال على قواعد مخصصة:
    # # تنبيه فقط عند التحسين من "Not Serious" إلى "Potential" أو "Serious"
    # if old_classification == "❌ Not Serious" and new_classification != "❌ Not Serious":
    #     return True
    # # تنبيه عند الانخفاض من "Serious" إلى أي تصنيف آخر
    # if "🔥" in old_classification and "🔥" not in new_classification:
    #     return True
    # return False


def get_classification_change_summary(client_id: int = None) -> Dict:
    """الحصول على ملخص تغييرات التصنيف"""
    changes = get_classification_changes(client_id=client_id, days=30)
    
    summary = {
        'total_changes': len(changes),
        'improvements': 0,
        'deteriorations': 0,
        'by_classification': {}
    }
    
    for change in changes:
        old_score = change['old_score']
        new_score = change['new_score']
        
        if new_score > old_score:
            summary['improvements'] += 1
        elif new_score < old_score:
            summary['deteriorations'] += 1
        
        new_class = change['new_classification']
        if new_class not in summary['by_classification']:
            summary['by_classification'][new_class] = 0
        summary['by_classification'][new_class] += 1
    
    return summary

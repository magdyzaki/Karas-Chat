"""
نظام التحقق من صحة البيانات
Data Validation System
"""
import re
from typing import Tuple, Optional
from datetime import datetime


def validate_email(email: str) -> Tuple[bool, Optional[str]]:
    """
    التحقق من صحة البريد الإلكتروني
    
    Args:
        email: البريد الإلكتروني المراد التحقق منه
    
    Returns:
        Tuple[bool, Optional[str]]: (صحيح/خاطئ, رسالة الخطأ إن وجدت)
    """
    if not email or not email.strip():
        return True, None  # البريد الإلكتروني اختياري
    
    email = email.strip()
    
    # نمط بسيط للتحقق من صحة البريد الإلكتروني
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    if not re.match(pattern, email):
        return False, "البريد الإلكتروني غير صحيح. يجب أن يكون على شكل: name@example.com"
    
    # تحقق من الطول
    if len(email) > 255:
        return False, "البريد الإلكتروني طويل جداً (الحد الأقصى 255 حرف)"
    
    return True, None


def validate_phone(phone: str) -> Tuple[bool, Optional[str]]:
    """
    التحقق من صحة رقم الهاتف
    
    Args:
        phone: رقم الهاتف المراد التحقق منه
    
    Returns:
        Tuple[bool, Optional[str]]: (صحيح/خاطئ, رسالة الخطأ إن وجدت)
    """
    if not phone or not phone.strip():
        return True, None  # رقم الهاتف اختياري
    
    phone = phone.strip()
    
    # إزالة المسافات والرموز للتحقق
    cleaned = re.sub(r'[\s\-\(\)\+]', '', phone)
    
    # يجب أن يحتوي على أرقام فقط وأن يكون طوله معقولاً (6-20 رقم)
    if not cleaned.isdigit():
        return False, "رقم الهاتف يجب أن يحتوي على أرقام فقط (يمكن استخدام المسافات والأقواس والرموز + -)"
    
    if len(cleaned) < 6 or len(cleaned) > 20:
        return False, "رقم الهاتف يجب أن يكون بين 6 و 20 رقم"
    
    return True, None


def validate_url(url: str) -> Tuple[bool, Optional[str]]:
    """
    التحقق من صحة رابط الموقع
    
    Args:
        url: الرابط المراد التحقق منه
    
    Returns:
        Tuple[bool, Optional[str]]: (صحيح/خاطئ, رسالة الخطأ إن وجدت)
    """
    if not url or not url.strip():
        return True, None  # الرابط اختياري
    
    url = url.strip()
    
    # إذا لم يبدأ بـ http:// أو https://، أضفه
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    
    # نمط بسيط للتحقق من الرابط
    pattern = r'^https?://[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(/.*)?$'
    
    if not re.match(pattern, url):
        return False, "رابط الموقع غير صحيح. يجب أن يكون على شكل: https://example.com"
    
    return True, None


def validate_date(date_str: str, date_format: str = "%d/%m/%Y") -> Tuple[bool, Optional[str]]:
    """
    التحقق من صحة التاريخ
    
    Args:
        date_str: التاريخ كسلسلة نصية
        date_format: تنسيق التاريخ (افتراضي: %d/%m/%Y)
    
    Returns:
        Tuple[bool, Optional[str]]: (صحيح/خاطئ, رسالة الخطأ إن وجدت)
    """
    if not date_str or not date_str.strip():
        return False, "التاريخ مطلوب"
    
    try:
        datetime.strptime(date_str.strip(), date_format)
        return True, None
    except ValueError:
        return False, f"التاريخ غير صحيح. يجب أن يكون بالتنسيق: {date_format.replace('%', '')}"


def validate_number(value: str, min_value: Optional[float] = None, max_value: Optional[float] = None) -> Tuple[bool, Optional[str]]:
    """
    التحقق من صحة رقم
    
    Args:
        value: القيمة المراد التحقق منها
        min_value: القيمة الدنيا (اختياري)
        max_value: القيمة العليا (اختياري)
    
    Returns:
        Tuple[bool, Optional[str]]: (صحيح/خاطئ, رسالة الخطأ إن وجدت)
    """
    if not value or not value.strip():
        return False, "الرقم مطلوب"
    
    try:
        num_value = float(value.strip())
        
        if min_value is not None and num_value < min_value:
            return False, f"القيمة يجب أن تكون أكبر من أو تساوي {min_value}"
        
        if max_value is not None and num_value > max_value:
            return False, f"القيمة يجب أن تكون أصغر من أو تساوي {max_value}"
        
        return True, None
    except ValueError:
        return False, "القيمة يجب أن تكون رقماً"


def validate_integer(value: str, min_value: Optional[int] = None, max_value: Optional[int] = None) -> Tuple[bool, Optional[str]]:
    """
    التحقق من صحة عدد صحيح
    
    Args:
        value: القيمة المراد التحقق منها
        min_value: القيمة الدنيا (اختياري)
        max_value: القيمة العليا (اختياري)
    
    Returns:
        Tuple[bool, Optional[str]]: (صحيح/خاطئ, رسالة الخطأ إن وجدت)
    """
    if not value or not value.strip():
        return True, None  # الرقم اختياري (يمكن أن يكون 0)
    
    try:
        int_value = int(value.strip())
        
        if min_value is not None and int_value < min_value:
            return False, f"القيمة يجب أن تكون أكبر من أو تساوي {min_value}"
        
        if max_value is not None and int_value > max_value:
            return False, f"القيمة يجب أن تكون أصغر من أو تساوي {max_value}"
        
        return True, None
    except ValueError:
        return False, "القيمة يجب أن تكون رقماً صحيحاً"


def validate_text(value: str, min_length: int = 0, max_length: Optional[int] = None, required: bool = False) -> Tuple[bool, Optional[str]]:
    """
    التحقق من صحة النص
    
    Args:
        value: النص المراد التحقق منه
        min_length: الحد الأدنى للطول
        max_length: الحد الأقصى للطول (اختياري)
        required: هل النص مطلوب
    
    Returns:
        Tuple[bool, Optional[str]]: (صحيح/خاطئ, رسالة الخطأ إن وجدت)
    """
    if not value:
        value = ""
    
    value = value.strip()
    
    if required and len(value) == 0:
        return False, "هذا الحقل مطلوب"
    
    if len(value) < min_length:
        return False, f"النص يجب أن يكون على الأقل {min_length} حرف"
    
    if max_length and len(value) > max_length:
        return False, f"النص يجب أن يكون على الأكثر {max_length} حرف"
    
    return True, None

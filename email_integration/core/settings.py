"""
إعدادات عامة للتطبيق
General Application Settings
"""
import json
import os
from typing import Dict, Optional

SETTINGS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "database")
SETTINGS_FILE = os.path.join(SETTINGS_DIR, "app_settings.json")

# Default settings
DEFAULT_SETTINGS = {
    "dashboard": {
        "colors": {
            "total_clients": "#4ECDC4",
            "serious_clients": "#FF6B6B",
            "potential_clients": "#FFD93D",
            "focus_clients": "#95E1D3",
            "total_messages": "#A8E6CF",
            "pending_requests": "#FFB347",
            "pending_tasks": "#87CEEB",
            "active_deals": "#DDA0DD"
        },
        "show_actions": True,
        "actions_max_height": 95
    },
    "notifications": {
        "enabled": True,
        "check_interval": 300,  # seconds
        "followup_clients": True,
        "pending_requests": True,
        "pending_tasks": True,
        "deals_closing": True
    },
    "ui": {
        "language": "ar",  # ar, en
        "theme": "light",  # light, dark
        "font_size": 10
    },
    "general": {
        "auto_backup": True,
        "backup_frequency": "daily",  # daily, weekly
        "backup_time": "02:00"
    }
}


def load_settings() -> Dict:
    """تحميل الإعدادات"""
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                user_settings = json.load(f)
                # Merge with defaults
                settings = DEFAULT_SETTINGS.copy()
                _deep_update(settings, user_settings)
                return settings
        except Exception:
            pass
    
    return DEFAULT_SETTINGS.copy()


def save_settings(settings: Dict):
    """حفظ الإعدادات"""
    try:
        os.makedirs(SETTINGS_DIR, exist_ok=True)
        with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(settings, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Error saving settings: {e}")


def get_setting(path: str, default=None):
    """
    الحصول على إعداد محدد باستخدام مسار مثل 'dashboard.colors.total_clients'
    
    Args:
        path: مسار الإعداد (مثل 'dashboard.colors.total_clients')
        default: القيمة الافتراضية إذا لم يوجد الإعداد
    
    Returns:
        قيمة الإعداد أو القيمة الافتراضية
    """
    settings = load_settings()
    keys = path.split('.')
    value = settings
    
    for key in keys:
        if isinstance(value, dict) and key in value:
            value = value[key]
        else:
            return default
    
    return value


def set_setting(path: str, value):
    """
    تعيين إعداد محدد
    
    Args:
        path: مسار الإعداد (مثل 'dashboard.colors.total_clients')
        value: القيمة المراد تعيينها
    """
    settings = load_settings()
    keys = path.split('.')
    current = settings
    
    # Navigate to the parent dict
    for key in keys[:-1]:
        if key not in current:
            current[key] = {}
        current = current[key]
    
    # Set the value
    current[keys[-1]] = value
    
    save_settings(settings)


def _deep_update(base_dict: Dict, update_dict: Dict):
    """تحديث عميق للقاموس"""
    for key, value in update_dict.items():
        if key in base_dict and isinstance(base_dict[key], dict) and isinstance(value, dict):
            _deep_update(base_dict[key], value)
        else:
            base_dict[key] = value


def reset_settings():
    """إعادة تعيين الإعدادات إلى القيم الافتراضية"""
    save_settings(DEFAULT_SETTINGS.copy())

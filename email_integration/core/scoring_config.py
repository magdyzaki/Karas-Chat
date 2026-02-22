"""
نظام عوامل التقييم القابلة للتخصيص
Customizable Scoring Factors System
"""
import json
import os
from typing import Dict, List
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, "database", "scoring_config.json")


# ===== Default Scoring Rules =====
DEFAULT_SCORE_RULES = {
    "reply": {"score": 20, "enabled": True, "description": "رد العميل على الرسالة"},
    "price_request": {"score": 15, "enabled": True, "description": "طلب السعر/عرض سعر"},
    "specs_request": {"score": 20, "enabled": True, "description": "طلب المواصفات"},
    "samples_request": {"score": 25, "enabled": True, "description": "طلب عينات"},
    "vague_reply": {"score": -10, "enabled": True, "description": "رد غير واضح"},
    "long_ignore": {"score": -15, "enabled": True, "description": "تجاهل طويل للرسائل"},
    "positive_keyword_match": {"score": 10, "enabled": True, "description": "مطابقة كلمات إيجابية"},
    "negative_keyword_match": {"score": -10, "enabled": True, "description": "مطابقة كلمات سلبية"},
    "quick_reply": {"score": 5, "enabled": True, "description": "رد سريع (أقل من 24 ساعة)"},
    "detailed_inquiry": {"score": 15, "enabled": True, "description": "استفسار مفصل"},
}

# ===== Default Classification Thresholds =====
DEFAULT_CLASSIFICATION_THRESHOLDS = {
    "serious": {"min_score": 80, "icon": "🔥", "label": "Serious Buyer", "color": "#FF6B6B"},
    "potential": {"min_score": 50, "icon": "👍", "label": "Potential", "color": "#4ECDC4"},
    "not_serious": {"min_score": 0, "icon": "❌", "label": "Not Serious", "color": "#95A5A6"},
}


def load_scoring_config() -> Dict:
    """تحميل إعدادات التقييم من الملف"""
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                config = json.load(f)
                # تأكد من وجود جميع المفاتيح المطلوبة
                if "score_rules" not in config:
                    config["score_rules"] = DEFAULT_SCORE_RULES
                if "classification_thresholds" not in config:
                    config["classification_thresholds"] = DEFAULT_CLASSIFICATION_THRESHOLDS
                if "ai_enabled" not in config:
                    config["ai_enabled"] = True
                if "trend_analysis_enabled" not in config:
                    config["trend_analysis_enabled"] = True
                return config
        except Exception:
            pass
    
    # إنشاء إعدادات افتراضية
    return {
        "score_rules": DEFAULT_SCORE_RULES.copy(),
        "classification_thresholds": DEFAULT_CLASSIFICATION_THRESHOLDS.copy(),
        "ai_enabled": True,
        "trend_analysis_enabled": True,
        "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }


def save_scoring_config(config: Dict):
    """حفظ إعدادات التقييم في الملف"""
    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
    config["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)


def get_score_effect(message_type: str) -> int:
    """حساب تأثير النقاط بناءً على نوع الرسالة مع مراعاة الإعدادات المخصصة"""
    config = load_scoring_config()
    rule = config["score_rules"].get(message_type)
    
    if not rule or not rule.get("enabled", True):
        return 0
    
    return rule.get("score", 0)


def update_score_rule(rule_name: str, score: int, enabled: bool = True, description: str = ""):
    """تحديث قاعدة تقييم معينة"""
    config = load_scoring_config()
    
    if rule_name not in config["score_rules"]:
        config["score_rules"][rule_name] = {
            "score": score,
            "enabled": enabled,
            "description": description
        }
    else:
        config["score_rules"][rule_name]["score"] = score
        config["score_rules"][rule_name]["enabled"] = enabled
        if description:
            config["score_rules"][rule_name]["description"] = description
    
    save_scoring_config(config)


def get_classification_thresholds() -> Dict:
    """الحصول على عتبات التصنيف"""
    config = load_scoring_config()
    return config.get("classification_thresholds", DEFAULT_CLASSIFICATION_THRESHOLDS)


def classify_client_custom(score: int) -> tuple:
    """
    تصنيف العميل بناءً على النقاط مع إعدادات مخصصة
    Returns: (classification_text, icon, color)
    """
    thresholds = get_classification_thresholds()
    
    # فرز العتبات حسب النقاط (من الأكبر للأصغر)
    sorted_thresholds = sorted(
        thresholds.items(),
        key=lambda x: x[1]["min_score"],
        reverse=True
    )
    
    for key, data in sorted_thresholds:
        if score >= data["min_score"]:
            icon = data.get("icon", "")
            label = data.get("label", key)
            color = data.get("color", "#000000")
            classification_text = f"{icon} {label}" if icon else label
            return classification_text, icon, color
    
    # Default fallback
    return "❌ Not Serious", "❌", "#95A5A6"


def is_ai_enabled() -> bool:
    """فحص ما إذا كان التقييم بالذكاء الاصطناعي مفعّل"""
    config = load_scoring_config()
    return config.get("ai_enabled", True)


def set_ai_enabled(enabled: bool):
    """تفعيل/تعطيل التقييم بالذكاء الاصطناعي"""
    config = load_scoring_config()
    config["ai_enabled"] = enabled
    save_scoring_config(config)


def is_trend_analysis_enabled() -> bool:
    """فحص ما إذا كان تتبع اتجاهات النقاط مفعّل"""
    config = load_scoring_config()
    return config.get("trend_analysis_enabled", True)


def set_trend_analysis_enabled(enabled: bool):
    """تفعيل/تعطيل تتبع اتجاهات النقاط"""
    config = load_scoring_config()
    config["trend_analysis_enabled"] = enabled
    save_scoring_config(config)

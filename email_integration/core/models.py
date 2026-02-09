from datetime import datetime
from .scoring_config import (
    get_score_effect,
    classify_client_custom,
    is_ai_enabled,
    is_trend_analysis_enabled
)


# ===== Date Helper =====
def today():
    return datetime.now().strftime("%d/%m/%Y")


# ===== Scoring Rules =====
# استخدام النظام الجديد القابل للتخصيص
def calculate_score_effect(message_type: str) -> int:
    """
    Returns score effect based on message type (using customizable rules)
    """
    return get_score_effect(message_type)


# ===== Classification Logic =====
def classify_client(score: int) -> str:
    """
    تصنيف العميل بناءً على النقاط مع إعدادات مخصصة
    Returns classification text with icon
    """
    classification_text, _, _ = classify_client_custom(score)
    return classification_text


# ===== Status Suggestion =====
def suggested_status(message_type: str) -> str:
    """
    Suggests client status based on last interaction
    """
    if message_type in ["price_request", "specs_request"]:
        return "Requested Price"
    if message_type == "samples_request":
        return "Samples Requested"
    if message_type == "reply":
        return "Replied"
    if message_type == "long_ignore":
        return "No Reply"
    return "New"


# ===== Follow-up Logic =====
def followup_days(status: str) -> int:
    """
    Returns suggested follow-up days based on status
    """
    rules = {
        "New": 7,
        "No Reply": 7,
        "Requested Price": 3,
        "Samples Requested": 10,
        "Replied": 5,
        "🔥 Serious Buyer": 3
    }
    return rules.get(status, 7)

"""
نظام التقييم المتقدم بالذكاء الاصطناعي
Advanced AI-based Scoring System
"""
import re
from typing import List, Tuple


def detect_positive_reply(body: str) -> int:
    """
    تحليل رد العميل المتقدم وإرجاع تأثير النقاط
    دعم اللغة العربية والإنجليزية مع تحليل متقدم
    
    Returns:
        int: تأثير النقاط (+ values = positive, - values = negative, 0 = neutral)
    """
    if not body:
        return 0

    text = body.lower()
    
    # الكلمات الإيجابية (عربي + إنجليزي)
    positive_keywords = [
        # English
        "interested", "please send", "price", "quotation", "quote",
        "samples", "sample", "details", "specification", "moq",
        "quantity", "packing", "delivery", "yes", "ok", "sounds good",
        "looking forward", "need", "require", "want", "please share",
        "could you", "would you", "send me", "i need", "i want",
        "purchase", "buy", "order", "catalog", "brochure",
        # Arabic
        "مهتم", "يرجى", "أرسل", "السعر", "عرض سعر", "اقتباس",
        "عينات", "عينة", "التفاصيل", "المواصفات", "الحد الأدنى",
        "الكمية", "التعبئة", "التسليم", "نعم", "حسناً", "جيد",
        "أحتاج", "أريد", "يرجى مشاركة", "هل يمكنك", "أرسل لي",
        "شراء", "شرا", "طلب", "كتالوج", "بروشور", "معني",
        "ممكن", "يرجى الإرسال", "أنا مهتم", "نحن مهتمون"
    ]

    # الكلمات السلبية (عربي + إنجليزي)
    negative_keywords = [
        # English
        "not interested", "no longer", "stop", "unsubscribe", "remove",
        "not now", "not at this time", "maybe later", "no thanks",
        "not right now", "decline", "refuse", "reject",
        # Arabic
        "غير مهتم", "لست مهتماً", "لا شكراً", "ليس الآن",
        "ربما لاحقاً", "رفض", "لا أريد", "توقف", "ألغاء الاشتراك"
    ]

    # الكلمات عالية الأهمية (نقاط إضافية)
    high_priority_keywords = [
        # English
        "urgent", "asap", "immediate", "quick", "fast", "now",
        "ready to buy", "ready to order", "placing order", "purchase order",
        "po number", "po#", "ready to proceed", "let's proceed",
        # Arabic
        "عاجل", "فوري", "سريع", "الآن", "جاهز للشراء", "جاهز للطلب",
        "أريد الشراء", "أريد الطلب", "طلب شراء", "أمر شراء"
    ]

    # الكلمات المتوسطة (نقاط متوسطة)
    medium_priority_keywords = [
        # English
        "information", "info", "more info", "tell me more", "explain",
        "how much", "what is the price", "cost", "pricing",
        # Arabic
        "معلومات", "مزيد من المعلومات", "أخبرني أكثر", "اشرح",
        "كم السعر", "ما هو السعر", "التكلفة", "التسعير"
    ]

    # تحليل النص
    score = 0
    
    # 1. فحص الكلمات السلبية (أولوية عالية)
    for keyword in negative_keywords:
        if keyword in text:
            return -25  # كلمة سلبية واحدة = رفض فوري
    
    # 2. فحص الكلمات عالية الأهمية
    high_priority_count = sum(1 for keyword in high_priority_keywords if keyword in text)
    if high_priority_count > 0:
        score += 20 * min(high_priority_count, 2)  # حد أقصى 40 نقطة
    
    # 3. فحص الكلمات الإيجابية
    positive_count = sum(1 for keyword in positive_keywords if keyword in text)
    if positive_count > 0:
        score += 10 * min(positive_count, 3)  # حد أقصى 30 نقطة
    
    # 4. فحص الكلمات المتوسطة
    medium_count = sum(1 for keyword in medium_priority_keywords if keyword in text)
    if medium_count > 0:
        score += 5 * min(medium_count, 2)  # حد أقصى 10 نقاط
    
    # 5. تحليل طول الرسالة (رسائل مفصلة = إهتمام أكبر)
    word_count = len(text.split())
    if word_count > 50:  # رسالة طويلة ومفصلة
        score += 5
    elif word_count > 100:  # رسالة جداً طويلة
        score += 10
    
    # 6. فحص وجود أرقام (قد تكون طلبات محددة)
    if re.search(r'\d+', text):
        # إذا كانت الأرقام كبيرة (قد تكون كميات)
        numbers = re.findall(r'\d+', text)
        # تصفية الأرقام التي طولها <= 10
        valid_numbers = [int(n) for n in numbers if len(n) <= 10]
        if valid_numbers:  # التحقق من أن القائمة ليست فارغة
            max_number = max(valid_numbers)
            if max_number > 10:  # رقم كبير = ربما كمية طلب
                score += 10
    
    # 7. فحص علامات الاستفهام (أسئلة = إهتمام)
    question_count = text.count('?') + text.count('؟')
    if question_count > 0:
        score += 3 * min(question_count, 3)  # حد أقصى 9 نقاط
    
    # 8. فحص العبارات الإيجابية المحددة
    positive_phrases = [
        "thank you", "thanks", "شكراً", "شكرا لك",
        "looking forward", "أتطلع", "نتطلع",
        "best regards", "مع تحياتي", "تحياتي",
        "waiting for", "في انتظار", "ننتظر"
    ]
    
    phrase_count = sum(1 for phrase in positive_phrases if phrase in text)
    if phrase_count > 0:
        score += 5 * phrase_count
    
    # تحديد الحد الأقصى والأدنى
    score = max(-30, min(50, score))  # بين -30 و +50
    
    return score


def analyze_sentiment(body: str) -> Tuple[str, float]:
    """
    تحليل المشاعر في الرسالة
    
    Returns:
        Tuple[str, float]: (sentiment, confidence)
        sentiment: 'positive', 'negative', 'neutral'
        confidence: 0.0 to 1.0
    """
    if not body:
        return 'neutral', 0.0
    
    text = body.lower()
    
    positive_indicators = [
        "thank", "appreciate", "excellent", "great", "good", "perfect",
        "interested", "excited", "happy", "pleased", "satisfied",
        "شكر", "ممتاز", "رائع", "جيد", "مثالي", "مهتم", "سعيد", "راض"
    ]
    
    negative_indicators = [
        "not interested", "disappointed", "bad", "poor", "terrible",
        "unhappy", "dissatisfied", "reject", "refuse", "decline",
        "غير مهتم", "خيبة أمل", "سيء", "رفض", "مرفوض"
    ]
    
    positive_count = sum(1 for word in positive_indicators if word in text)
    negative_count = sum(1 for word in negative_indicators if word in text)
    
    total = positive_count + negative_count
    if total == 0:
        return 'neutral', 0.5
    
    if positive_count > negative_count:
        confidence = positive_count / total
        return 'positive', confidence
    elif negative_count > positive_count:
        confidence = negative_count / total
        return 'negative', confidence
    else:
        return 'neutral', 0.5


def detect_purchase_intent(body: str) -> Tuple[bool, float]:
    """
    اكتشاف نية الشراء في الرسالة
    
    Returns:
        Tuple[bool, float]: (has_intent, confidence)
    """
    if not body:
        return False, 0.0
    
    text = body.lower()
    
    purchase_indicators = [
        # English
        "ready to buy", "ready to order", "place order", "purchase",
        "placing order", "po number", "po#", "purchase order",
        "how to order", "how to buy", "order now", "buy now",
        "proceed with", "move forward", "let's proceed",
        # Arabic
        "جاهز للشراء", "جاهز للطلب", "طلب شراء", "أمر شراء",
        "كيف أطلب", "كيف أشتري", "الطلب الآن", "الشراء الآن",
        "المضي قدماً", "المتابعة", "نريد المتابعة"
    ]
    
    intent_count = sum(1 for phrase in purchase_indicators if phrase in text)
    
    if intent_count > 0:
        confidence = min(1.0, 0.5 + (intent_count * 0.2))
        return True, confidence
    
    return False, 0.0

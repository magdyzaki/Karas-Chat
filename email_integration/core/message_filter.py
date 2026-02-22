"""
نظام فلترة الرسائل المتعلقة بالعمل
Message Filtering System for Business-Related Emails
"""
import re
from typing import Tuple, List, Dict


def is_business_related_email(subject: str, body: str) -> Tuple[bool, List[str]]:
    """
    التحقق من أن الرسالة متعلقة بالعمل (تصدير، طلبات، أسعار، عينات)
    يركز على المنتجات المجففة: dehydrated, onion, garlic, herbs, spices, etc.
    
    Args:
        subject: موضوع الرسالة
        body: محتوى الرسالة
    
    Returns:
        Tuple[bool, List[str]]: (هل الرسالة متعلقة بالعمل, قائمة الأنواع المكتشفة)
    """
    # دمج الموضوع والمحتوى
    text = (subject + " " + body).lower()
    
    # كلمات مفتاحية قوية للمنتجات المجففة (أولوية عالية)
    dehydrated_products = [
        'dehydrated', 'onion', 'leek', 'garlic', 'spinach', 
        'powder', 'flakes', 'granules', 'minced',
        'herbs', 'spices', 'seeds',
        'dehydrated onion', 'dehydrated leek', 'dehydrated garlic',
        'onion powder', 'garlic powder', 'onion flakes', 'garlic flakes',
        'onion granules', 'garlic granules', 'minced onion', 'minced garlic',
        'dehydrated vegetables', 'dehydrated vegetables',
        'بصل مجفف', 'ثوم مجفف', 'خضار مجفف', 'أعشاب مجففة', 'توابل مجففة'
    ]
    
    # قائمة الكلمات المفتاحية المتعلقة بالعمل
    business_keywords = {
        'dehydrated': dehydrated_products,  # أولوية عالية للمنتجات المجففة
        'price': ['price', 'pricing', 'cost', 'quotation', 'quote', 'offer', 'rate', 'prices',
                  'سعر', 'أسعار', 'تكلفة', 'عرض سعر', 'اقتباس', 'عرض', 'عروض'],
        'sample': ['sample', 'samples', 'specimen', 'test', 'trial', 
                   'عينة', 'عينات', 'تجربة', 'اختبار'],
        'specification': ['spec', 'specification', 'specs', 'technical', 'details', 
                         'مواصفات', 'تفاصيل', 'تقني'],
        'moq': ['moq', 'minimum order', 'minimum quantity', 'order quantity', 
                'أقل كمية', 'حد أدنى', 'كمية الطلب'],
        'quantity': ['tons', 'mt', 'ton', 'metric ton', 'kilogram', 'kg', 'quantity',
                     'طن', 'متر طن', 'كيلو', 'كمية'],
        'export': ['export', 'exporting', 'shipping', 'delivery', 'logistics', 
                   'تصدير', 'شحن', 'تسليم', 'لوجستيات'],
        'product': ['product', 'products', 'item', 'items', 'goods', 
                    'منتج', 'منتجات', 'بضاعة'],
        'inquiry': ['inquiry', 'enquiry', 'request', 'asking', 'question', 
                    'استفسار', 'طلب', 'سؤال'],
        'business': ['business', 'trade', 'commercial', 'transaction', 
                     'تجارة', 'تجاري', 'معاملة']
    }
    
    detected_types = []
    relevance_score = 0
    
    # البحث عن الكلمات المفتاحية - المنتجات المجففة لها أولوية
    has_dehydrated_product = False
    for keyword in dehydrated_products:
        if keyword in text:
            has_dehydrated_product = True
            if 'dehydrated' not in detected_types:
                detected_types.append('dehydrated')
            relevance_score += 3  # نقاط عالية للمنتجات المجففة
            break
    
    # البحث عن باقي الكلمات المفتاحية
    for category, keywords in business_keywords.items():
        if category == 'dehydrated':
            continue  # تم التحقق منها أعلاه
        for keyword in keywords:
            if keyword in text:
                if category not in detected_types:
                    detected_types.append(category)
                relevance_score += 1
                break
    
    # إذا كانت الرسالة تحتوي على منتجات مجففة + كلمات متعلقة بالعمل
    if has_dehydrated_product:
        # إذا كان هناك منتجات مجففة + أي كلمة متعلقة بالعمل، فهي رسالة متعلقة
        is_relevant = len(detected_types) > 1 or relevance_score >= 4
    else:
        # إذا لم تكن هناك منتجات مجففة، يجب أن يكون هناك عدة مؤشرات
        is_relevant = relevance_score >= 3
    
    # استثناءات قوية: رسائل دعائية/تسويقية (يجب استبعادها بقوة)
    strong_spam_indicators = [
        'unsubscribe', 'newsletter', 'promotion', 'advertisement', 'marketing',
        'discount', 'sale', 'special offer', 'limited time', 'click here',
        'shop now', 'buy now', 'visit our website', 'check out',
        'إلغاء الاشتراك', 'نشرة', 'إعلان', 'ترويج', 'تخفيض', 'عرض خاص',
        'تسوق الآن', 'اشتر الآن', 'زر موقعنا', 'عرض محدود',
        'amazon', 'ebay', 'aliexpress', 'etsy', 'shopify', 'woocommerce',
        'amazon.com', 'ebay.com', 'etsy.com', 'shop now', 'add to cart'
    ]
    
    # إذا كانت الرسالة تحتوي على مؤشرات spam قوية، استبعدها
    for spam_word in strong_spam_indicators:
        if spam_word in text:
            # فقط إذا لم تكن هناك منتجات مجففة أو طلبات واضحة
            if not has_dehydrated_product and relevance_score < 5:
                is_relevant = False
                break
    
    return is_relevant, detected_types


def detect_request_type(subject: str, body: str) -> Tuple[str, int]:
    """
    اكتشاف نوع الطلب في الرسالة
    
    Returns:
        Tuple[str, int]: (نوع الطلب, النقاط)
    """
    text = (subject + " " + body).lower()
    detected = []
    score = 0
    
    # Price Request
    if any(word in text for word in ['price', 'pricing', 'cost', 'quotation', 'quote', 
                                     'offer', 'rate', 'سعر', 'أسعار', 'تكلفة', 'عرض سعر']):
        detected.append("Price Request")
        score += 15
    
    # Sample Request
    if any(word in text for word in ['sample', 'samples', 'specimen', 'test', 
                                      'عينة', 'عينات', 'تجربة']):
        detected.append("Sample Request")
        score += 25
    
    # Specification Request
    if any(word in text for word in ['spec', 'specification', 'specs', 'technical', 
                                      'مواصفات', 'تفاصيل', 'تقني']):
        detected.append("Specs Request")
        score += 10
    
    # MOQ Request
    if any(word in text for word in ['moq', 'minimum order', 'minimum quantity', 
                                      'أقل كمية', 'حد أدنى']):
        detected.append("MOQ Request")
        score += 10
    
    request_type = ", ".join(detected) if detected else "General Inquiry"
    
    return request_type, score


def should_import_message(subject: str, body: str, sender_email: str = "") -> Tuple[bool, str]:
    """
    تحديد ما إذا كان يجب استيراد الرسالة أم لا
    يركز على المنتجات المجففة والطلبات التجارية الحقيقية
    
    Args:
        subject: موضوع الرسالة
        body: محتوى الرسالة
        sender_email: بريد المرسل (اختياري)
    
    Returns:
        Tuple[bool, str]: (هل يجب الاستيراد, السبب)
    """
    text = (subject + " " + body).lower()
    
    # كلمات مفتاحية قوية للمنتجات المجففة (أولوية عالية)
    dehydrated_keywords = [
        'dehydrated', 'onion', 'leek', 'garlic', 'spinach', 
        'powder', 'flakes', 'granules', 'minced',
        'herbs', 'spices', 'seeds',
        'dehydrated onion', 'dehydrated leek', 'dehydrated garlic'
    ]
    
    # كلمات مفتاحية للطلبات التجارية
    request_keywords = [
        'price', 'prices', 'pricing', 'quotation', 'quote', 'offer', 'cost',
        'sample', 'samples', 'specimen',
        'moq', 'minimum order', 'quantity', 'tons', 'mt', 'metric ton',
        'spec', 'specification', 'specs',
        'inquiry', 'enquiry', 'request', 'asking',
        'سعر', 'أسعار', 'عرض سعر', 'اقتباس', 'عرض',
        'عينة', 'عينات', 'أقل كمية', 'كمية', 'طن', 'متر طن',
        'مواصفات', 'استفسار', 'طلب'
    ]
    
    # استثناءات قوية: رسائل دعائية/تسويقية
    strong_exclusion_keywords = [
        'unsubscribe', 'newsletter', 'promotion', 'advertisement', 'marketing',
        'discount', 'sale', 'special offer', 'limited time', 'click here',
        'shop now', 'buy now', 'visit our website', 'check out',
        'amazon', 'ebay', 'aliexpress', 'etsy', 'shopify', 'woocommerce',
        'إلغاء الاشتراك', 'نشرة', 'إعلان', 'ترويج', 'تخفيض', 'عرض خاص'
    ]
    
    # 1. استبعاد الرسائل الدعائية/التسويقية
    for exclusion_word in strong_exclusion_keywords:
        if exclusion_word in text:
            return False, f"رسالة دعائية/تسويقية (تحتوي على: {exclusion_word})"
    
    # 2. التحقق من وجود منتجات مجففة
    has_dehydrated_product = any(keyword in text for keyword in dehydrated_keywords)
    
    # 3. التحقق من وجود طلبات تجارية
    has_request = any(keyword in text for keyword in request_keywords)
    
    # 4. إذا كانت الرسالة تحتوي على منتجات مجففة + طلب = استيراد مباشر
    if has_dehydrated_product and has_request:
        request_type, score = detect_request_type(subject, body)
        return True, f"رسالة متعلقة بالمنتجات المجففة + طلب: {request_type}"
    
    # 5. إذا كانت الرسالة تحتوي على منتجات مجففة فقط (بدون طلب صريح)
    if has_dehydrated_product:
        # تحليل محتوى الرسالة بشكل أذكى
        if any(word in text for word in ['interested', 'looking', 'need', 'want', 'require',
                                          'مهتم', 'أبحث', 'أحتاج', 'أريد', 'نحتاج']):
            return True, "رسالة متعلقة بالمنتجات المجففة + إشارة للاهتمام"
        # إذا كانت الرسالة تحتوي على كلمات متعلقة بالتصدير/التجارة
        if any(word in text for word in ['export', 'business', 'trade', 'commercial',
                                          'تصدير', 'تجارة', 'تجاري']):
            return True, "رسالة متعلقة بالمنتجات المجففة + تصدير/تجارة"
    
    # 6. إذا كانت الرسالة تحتوي على طلبات قوية فقط (حتى بدون منتجات مجففة)
    request_type, score = detect_request_type(subject, body)
    if score >= 15:  # طلبات قوية (سعر/عينة)
        return True, f"طلب قوي: {request_type}"
    
    # 7. استخدام الدالة الأصلية للتحقق الإضافي
    is_relevant, detected_types = is_business_related_email(subject, body)
    if is_relevant:
        if detected_types:
            return True, f"رسالة متعلقة بالعمل: {', '.join(detected_types)}"
        return True, "رسالة متعلقة بالعمل"
    
    return False, "لا توجد معلومات كافية - غير متعلقة بالعمل"

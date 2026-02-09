"""
نظام قوالب الردود المتعددة اللغات والقابلة للتخصيص
Multi-language Customizable Reply Templates System
"""
import json
import os
from typing import Dict, List, Optional
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
TEMPLATES_PATH = os.path.join(BASE_DIR, "database", "reply_templates.json")


# ===== Default Templates (Multi-language) =====
DEFAULT_TEMPLATES = {
    "short_reply": {
        "arabic": {
            "subject": "رد: استفسارك",
            "body": "عزيزي {company_name},\n\nشكراً لتواصلك معنا بخصوص {request_type}.\n\nسنكون سعداء بتوفير التفاصيل المطلوبة.\n\nمع أطيب التحيات،\nفريق المبيعات"
        },
        "english": {
            "subject": "Re: Your Inquiry",
            "body": "Dear {company_name},\n\nThank you for contacting us regarding your {request_type}.\n\nWe will be happy to provide you with the requested details.\n\nBest regards,\nExport Sales Team"
        },
        "spanish": {
            "subject": "Re: Su Consulta",
            "body": "Estimado {company_name},\n\nGracias por contactarnos con respecto a su {request_type}.\n\nEstaremos encantados de proporcionarle los detalles solicitados.\n\nSaludos cordiales,\nEquipo de Ventas"
        },
        "french": {
            "subject": "Re: Votre Demande",
            "body": "Cher {company_name},\n\nMerci de nous avoir contactés concernant votre {request_type}.\n\nNous serons heureux de vous fournir les détails demandés.\n\nCordialement,\nÉquipe Commerciale"
        }
    },
    "full_reply": {
        "arabic": {
            "subject": "رد: {request_type}",
            "body": "عزيزي {company_name},\n\nنشكركم على رسالتكم بخصوص {request_type}.\n\nيسعدنا تأكيد أنه يمكننا دعم متطلباتكم. يرجى الاطلاع أدناه على ردنا الأولي، ولا تترددوا في إعلامنا إذا كنتم بحاجة إلى عينات أو مواصفات أو شروط تجارية.\n\nنتطلع إلى ملاحظاتكم.\n\nمع أطيب التحيات،\nفريق المبيعات"
        },
        "english": {
            "subject": "Re: {request_type}",
            "body": "Dear {company_name},\n\nThank you for your message regarding {request_type}.\n\nWe are pleased to confirm that we can support your requirements. Please find below our preliminary response, and feel free to let us know if you need samples, specifications, or commercial terms.\n\nWe look forward to your feedback.\n\nBest regards,\nExport Sales Team"
        },
        "spanish": {
            "subject": "Re: {request_type}",
            "body": "Estimado {company_name},\n\nGracias por su mensaje sobre {request_type}.\n\nNos complace confirmar que podemos apoyar sus requisitos. Por favor, encuentre a continuación nuestra respuesta preliminar, y no dude en informarnos si necesita muestras, especificaciones o términos comerciales.\n\nEsperamos sus comentarios.\n\nSaludos cordiales,\nEquipo de Ventas"
        },
        "french": {
            "subject": "Re: {request_type}",
            "body": "Cher {company_name},\n\nMerci pour votre message concernant {request_type}.\n\nNous sommes heureux de confirmer que nous pouvons répondre à vos besoins. Veuillez trouver ci-dessous notre réponse préliminaire, et n'hésitez pas à nous faire savoir si vous avez besoin d'échantillons, de spécifications ou de conditions commerciales.\n\nNous attendons vos commentaires.\n\nCordialement,\nÉquipe Commerciale"
        }
    },
    "followup_reply": {
        "arabic": {
            "subject": "متابعة: استفسارك",
            "body": "عزيزي {company_name},\n\nنحن نتتبع رسالتنا السابقة بخصوص استفساركم.\n\nيرجى إعلامنا إذا كنت بحاجة إلى أي معلومات إضافية أو توضيحات.\n\nنتطلع إلى سماع منكم.\n\nمع أطيب التحيات،\nفريق المبيعات"
        },
        "english": {
            "subject": "Follow-up: Your Inquiry",
            "body": "Dear {company_name},\n\nWe are following up on our previous message regarding your inquiry.\n\nPlease let us know if you require any additional information or clarification.\n\nLooking forward to hearing from you.\n\nBest regards,\nExport Sales Team"
        },
        "spanish": {
            "subject": "Seguimiento: Su Consulta",
            "body": "Estimado {company_name},\n\nEstamos haciendo seguimiento a nuestro mensaje anterior sobre su consulta.\n\nPor favor, infórmenos si necesita información adicional o aclaraciones.\n\nEsperamos tener noticias suyas.\n\nSaludos cordiales,\nEquipo de Ventas"
        },
        "french": {
            "subject": "Suivi: Votre Demande",
            "body": "Cher {company_name},\n\nNous faisons un suivi de notre message précédent concernant votre demande.\n\nVeuillez nous faire savoir si vous avez besoin d'informations supplémentaires ou de clarifications.\n\nDans l'attente de vos nouvelles.\n\nCordialement,\nÉquipe Commerciale"
        }
    },
    "price_request": {
        "arabic": {
            "subject": "عرض سعر: {company_name}",
            "body": "عزيزي {company_name},\n\nشكراً لاهتمامكم بمنتجاتنا وطلبكم لعرض السعر.\n\nنحن سعداء لتقديم عرض سعر شامل لك. يرجى الاطلاع على التفاصيل المرفقة، وإذا كان لديكم أي استفسارات إضافية، لا تترددوا في التواصل معنا.\n\nنتطلع إلى فرصة التعاون معكم.\n\nمع أطيب التحيات،\nفريق المبيعات"
        },
        "english": {
            "subject": "Price Quotation: {company_name}",
            "body": "Dear {company_name},\n\nThank you for your interest in our products and your request for a price quotation.\n\nWe are pleased to provide you with a comprehensive price quote. Please find the details attached, and if you have any additional inquiries, please do not hesitate to contact us.\n\nWe look forward to the opportunity to work with you.\n\nBest regards,\nExport Sales Team"
        },
        "spanish": {
            "subject": "Cotización de Precio: {company_name}",
            "body": "Estimado {company_name},\n\nGracias por su interés en nuestros productos y su solicitud de cotización de precios.\n\nNos complace proporcionarle una cotización de precios completa. Por favor, encuentre los detalles adjuntos, y si tiene alguna consulta adicional, no dude en contactarnos.\n\nEsperamos la oportunidad de trabajar con usted.\n\nSaludos cordiales,\nEquipo de Ventas"
        },
        "french": {
            "subject": "Devis de Prix: {company_name}",
            "body": "Cher {company_name},\n\nMerci pour votre intérêt pour nos produits et votre demande de devis de prix.\n\nNous sommes heureux de vous fournir un devis de prix complet. Veuillez trouver les détails ci-joints, et si vous avez des questions supplémentaires, n'hésitez pas à nous contacter.\n\nNous espérons avoir l'opportunité de travailler avec vous.\n\nCordialement,\nÉquipe Commerciale"
        }
    },
    "samples_request": {
        "arabic": {
            "subject": "طلب عينات: {company_name}",
            "body": "عزيزي {company_name},\n\nنشكركم على اهتمامكم بمنتجاتنا وطلبكم للعينات.\n\nيسعدنا تأكيد أنه يمكننا تحضير وإرسال العينات حسب طلبكم. يرجى إعلامنا بتفاصيل التسليم.\n\nإذا كان لديكم أي متطلبات خاصة أو مواصفات محددة، يرجى إعلامنا.\n\nمع أطيب التحيات،\nفريق المبيعات"
        },
        "english": {
            "subject": "Samples Request: {company_name}",
            "body": "Dear {company_name},\n\nThank you for your interest in our products and your request for samples.\n\nWe are pleased to confirm that we can prepare and dispatch the samples as per your request. Kindly advise your delivery details.\n\nIf you have any special requirements or specific specifications, please let us know.\n\nBest regards,\nExport Sales Team"
        },
        "spanish": {
            "subject": "Solicitud de Muestras: {company_name}",
            "body": "Estimado {company_name},\n\nGracias por su interés en nuestros productos y su solicitud de muestras.\n\nNos complace confirmar que podemos preparar y enviar las muestras según su solicitud. Por favor, indíquenos sus datos de entrega.\n\nSi tiene algún requisito especial o especificaciones específicas, por favor infórmenos.\n\nSaludos cordiales,\nEquipo de Ventas"
        },
        "french": {
            "subject": "Demande d'Échantillons: {company_name}",
            "body": "Cher {company_name},\n\nMerci pour votre intérêt pour nos produits et votre demande d'échantillons.\n\nNous sommes heureux de confirmer que nous pouvons préparer et expédier les échantillons selon votre demande. Veuillez nous indiquer vos coordonnées de livraison.\n\nSi vous avez des exigences particulières ou des spécifications spécifiques, veuillez nous en informer.\n\nCordialement,\nÉquipe Commerciale"
        }
    }
}


def load_templates() -> Dict:
    """تحميل القوالب من الملف"""
    if os.path.exists(TEMPLATES_PATH):
        try:
            with open(TEMPLATES_PATH, 'r', encoding='utf-8') as f:
                templates = json.load(f)
                # التأكد من وجود القوالب الافتراضية
                for template_type in DEFAULT_TEMPLATES:
                    if template_type not in templates:
                        templates[template_type] = DEFAULT_TEMPLATES[template_type]
                return templates
        except Exception:
            pass
    
    # إنشاء ملف القوالب الافتراضي
    templates = DEFAULT_TEMPLATES.copy()
    save_templates(templates)
    return templates


def save_templates(templates: Dict):
    """حفظ القوالب في الملف"""
    os.makedirs(os.path.dirname(TEMPLATES_PATH), exist_ok=True)
    with open(TEMPLATES_PATH, 'w', encoding='utf-8') as f:
        json.dump(templates, f, ensure_ascii=False, indent=2)


def get_template(template_type: str, language: str = "english", client_info: Optional[Dict] = None) -> Dict[str, str]:
    """
    الحصول على قالب معين باللغة المطلوبة مع دمج معلومات العميل
    
    Args:
        template_type: نوع القالب (short_reply, full_reply, followup_reply, price_request, samples_request)
        language: اللغة (arabic, english, spanish, french)
        client_info: معلومات العميل للدمج {company_name, contact_person, country, email, phone, etc.}
    
    Returns:
        Dict with 'subject' and 'body'
    """
    templates = load_templates()
    
    # الحصول على القالب الافتراضي إذا لم يوجد
    if template_type not in templates:
        template_type = "short_reply"
    
    template = templates[template_type]
    
    # الحصول على اللغة المطلوبة (افتراضي: english)
    if language not in template:
        language = "english"
    
    subject_template = template[language].get("subject", "")
    body_template = template[language].get("body", "")
    
    # معلومات العميل الافتراضية
    if client_info is None:
        client_info = {}
    
    # إعداد المتغيرات للاستبدال
    variables = {
        "company_name": client_info.get("company_name", "Valued Client"),
        "contact_person": client_info.get("contact_person", ""),
        "country": client_info.get("country", ""),
        "email": client_info.get("email", ""),
        "phone": client_info.get("phone", ""),
        "request_type": client_info.get("request_type", "inquiry"),
        "status": client_info.get("status", ""),
        "classification": client_info.get("classification", ""),
        "date": datetime.now().strftime("%d/%m/%Y"),
    }
    
    # استبدال المتغيرات
    subject = subject_template.format(**variables)
    body = body_template.format(**variables)
    
    # إضافة معلومات إضافية إذا كانت متوفرة
    if client_info.get("contact_person"):
        greeting = f"Dear {client_info['contact_person']}" if language == "english" else f"عزيزي {client_info['contact_person']}"
        if not body.startswith(greeting):
            # استبدال التحية إذا كانت موجودة
            body = body.replace(variables["company_name"], client_info["contact_person"], 1)
    
    return {
        "subject": subject,
        "body": body
    }


def get_all_templates(language: str = "english") -> Dict[str, Dict[str, str]]:
    """الحصول على جميع القوالب بلغة معينة"""
    templates = load_templates()
    result = {}
    
    for template_type, langs in templates.items():
        if language in langs:
            result[template_type] = langs[language]
    
    return result


def update_template(template_type: str, language: str, subject: str, body: str):
    """تحديث قالب معين"""
    templates = load_templates()
    
    if template_type not in templates:
        templates[template_type] = {}
    
    templates[template_type][language] = {
        "subject": subject,
        "body": body
    }
    
    save_templates(templates)


def create_custom_template(template_name: str, language: str, subject: str, body: str):
    """إنشاء قالب مخصص جديد"""
    templates = load_templates()
    
    if template_name not in templates:
        templates[template_name] = {}
    
    templates[template_name][language] = {
        "subject": subject,
        "body": body
    }
    
    save_templates(templates)


def delete_template(template_type: str):
    """حذف قالب معين"""
    templates = load_templates()
    
    if template_type in templates:
        del templates[template_type]
        save_templates(templates)


def get_saved_replies() -> List[Dict]:
    """الحصول على الردود المحفوظة كقوالب"""
    templates = load_templates()
    saved_replies = templates.get("saved_replies", [])
    return saved_replies


def save_reply_as_template(reply_subject: str, reply_body: str, template_name: str = None, language: str = "english"):
    """حفظ رد كقالب جديد"""
    templates = load_templates()
    
    if "saved_replies" not in templates:
        templates["saved_replies"] = []
    
    template_name = template_name or f"Custom Reply {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    
    saved_reply = {
        "name": template_name,
        "language": language,
        "subject": reply_subject,
        "body": reply_body,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "usage_count": 0
    }
    
    templates["saved_replies"].append(saved_reply)
    save_templates(templates)
    
    return saved_reply


def increment_template_usage(template_name: str):
    """زيادة عدد استخدامات القالب"""
    templates = load_templates()
    saved_replies = templates.get("saved_replies", [])
    
    for reply in saved_replies:
        if reply.get("name") == template_name:
            reply["usage_count"] = reply.get("usage_count", 0) + 1
            break
    
    save_templates(templates)


def detect_language(text: str) -> str:
    """
    اكتشاف لغة النص (بسيط)
    Returns: 'arabic', 'english', 'spanish', 'french', or 'unknown'
    """
    text_lower = text.lower()
    
    # كلمات عربية شائعة
    arabic_words = ["عزيزي", "شكرا", "شكراً", "مع", "التحيات", "يرجى", "في", "من", "إلى"]
    if any(word in text for word in arabic_words):
        return "arabic"
    
    # كلمات إسبانية شائعة
    spanish_words = ["estimado", "gracias", "saludos", "por favor", "consulta", "con respecto"]
    if any(word in text_lower for word in spanish_words):
        return "spanish"
    
    # كلمات فرنسية شائعة
    french_words = ["cher", "merci", "cordialement", "veuillez", "demande", "concernant"]
    if any(word in text_lower for word in french_words):
        return "french"
    
    # افتراضي: إنجليزي
    return "english"

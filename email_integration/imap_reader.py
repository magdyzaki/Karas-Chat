"""
قراءة الإيميلات من حسابات IMAP (cPanel)
Reading emails from IMAP accounts (cPanel)
"""
import imaplib
import email
from email.header import decode_header
from datetime import datetime
from typing import List, Dict, Optional
import ssl
import re


def read_messages_from_imap(imap_server: str, imap_port: int, username: str, password: str,
                           use_ssl: bool = True, folder: str = "INBOX", max_messages: Optional[int] = None) -> List[Dict]:
    """
    قراءة الرسائل من حساب IMAP
    
    Args:
        imap_server: عنوان خادم IMAP (مثل: mail.example.com)
        imap_port: منفذ IMAP (عادة 993 لـ SSL أو 143 لـ TLS)
        username: اسم المستخدم (البريد الإلكتروني أو اسم المستخدم)
        password: كلمة المرور
        use_ssl: استخدام SSL (True للبورت 993، False للبورت 143 مع TLS)
        folder: المجلد (افتراضي: INBOX)
        max_messages: الحد الأقصى لعدد الرسائل (None = جميع الرسائل)
    
    Returns:
        List of message dictionaries
    """
    messages = []
    
    try:
        # الاتصال بخادم IMAP
        if use_ssl:
            # SSL connection (port 993)
            mail = imaplib.IMAP4_SSL(imap_server, imap_port)
        else:
            # TLS connection (port 143)
            mail = imaplib.IMAP4(imap_server, imap_port)
            mail.starttls()
        
        # تسجيل الدخول
        mail.login(username, password)
        
        # اختيار المجلد
        status, messages_count = mail.select(folder)
        if status != "OK":
            raise Exception(f"Failed to select folder {folder}")
        
        # الحصول على عدد الرسائل
        num_messages = int(messages_count[0])
        if max_messages:
            num_messages = min(num_messages, max_messages)
        
        # البحث عن الرسائل (الحديثة أولاً)
        status, message_ids = mail.search(None, "ALL")
        if status != "OK":
            raise Exception("Failed to search messages")
        
        email_ids = message_ids[0].split()
        # أخذ آخر الرسائل (الأحدث)
        email_ids = email_ids[-num_messages:] if num_messages else email_ids
        
        # قراءة كل رسالة
        for email_id in email_ids:
            try:
                # جلب الرسالة
                status, msg_data = mail.fetch(email_id, "(RFC822)")
                if status != "OK":
                    continue
                
                # تحليل الرسالة
                email_body = msg_data[0][1]
                email_message = email.message_from_bytes(email_body)
                
                # استخراج المعلومات
                subject = _decode_header(email_message["Subject"])
                from_address = _decode_header(email_message["From"])
                to_address = _decode_header(email_message["To"])
                date_str = email_message["Date"]
                
                # تحويل التاريخ إلى تنسيق dd/mm/yyyy
                received_date = None
                actual_date_str = None
                try:
                    date_tuple = email.utils.parsedate_tz(date_str)
                    if date_tuple:
                        received_date = email.utils.mktime_tz(date_tuple)
                        date_obj = datetime.fromtimestamp(received_date)
                        actual_date_str = date_obj.strftime("%d/%m/%Y")
                        received_date = date_obj.isoformat()
                except:
                    received_date = date_str
                
                # استخراج البريد الإلكتروني من "From"
                sender_email = _extract_email(from_address)
                sender_name = _extract_name(from_address)
                
                # استخراج محتوى الرسالة
                body = _get_email_body(email_message)
                
                # تحويل إلى تنسيق مشابه لـ Microsoft Graph
                message_dict = {
                    "id": email_id.decode(),
                    "subject": subject or "",
                    "body": {
                        "content": body,
                        "contentType": "HTML" if _is_html(body) else "Text"
                    },
                    "from": {
                        "emailAddress": {
                            "name": sender_name or "",
                            "address": sender_email or ""
                        }
                    },
                    "receivedDateTime": received_date or "",
                    "date": actual_date_str or date_str,
                    "isRead": False
                }
                
                messages.append(message_dict)
                
            except Exception as e:
                print(f"Error reading message {email_id}: {str(e)}")
                continue
        
        # إغلاق الاتصال
        mail.close()
        mail.logout()
        
    except imaplib.IMAP4.error as e:
        raise Exception(f"IMAP error: {str(e)}")
    except Exception as e:
        raise Exception(f"Error reading IMAP messages: {str(e)}")
    
    return messages


def _decode_header(header):
    """فك تشفير رأس البريد الإلكتروني"""
    if not header:
        return ""
    
    decoded_parts = decode_header(header)
    decoded_str = ""
    
    for part, encoding in decoded_parts:
        if isinstance(part, bytes):
            if encoding:
                decoded_str += part.decode(encoding)
            else:
                decoded_str += part.decode('utf-8', errors='ignore')
        else:
            decoded_str += part
    
    return decoded_str.strip()


def _extract_email(address_string):
    """استخراج البريد الإلكتروني من سلسلة العنوان"""
    if not address_string:
        return ""
    
    # البحث عن نمط البريد الإلكتروني
    match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', address_string)
    if match:
        return match.group(0).lower()
    return ""


def _extract_name(address_string):
    """استخراج الاسم من سلسلة العنوان"""
    if not address_string:
        return ""
    
    # إذا كان العنوان يحتوي على <email@example.com>
    if '<' in address_string and '>' in address_string:
        name_part = address_string.split('<')[0].strip()
        # إزالة علامات الاقتباس
        name_part = name_part.strip('"').strip("'")
        return name_part
    
    return ""


def _get_email_body(email_message):
    """استخراج محتوى الرسالة (HTML أو نص عادي)"""
    body = ""
    
    if email_message.is_multipart():
        for part in email_message.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition"))
            
            # تخطي المرفقات
            if "attachment" in content_disposition:
                continue
            
            # محاولة استخراج النص أو HTML
            if content_type == "text/plain":
                try:
                    payload = part.get_payload(decode=True)
                    if payload:
                        charset = part.get_content_charset() or 'utf-8'
                        body = payload.decode(charset, errors='ignore')
                except:
                    pass
            elif content_type == "text/html" and not body:
                # استخدام HTML كبديل إذا لم يوجد نص عادي
                try:
                    payload = part.get_payload(decode=True)
                    if payload:
                        charset = part.get_content_charset() or 'utf-8'
                        body = payload.decode(charset, errors='ignore')
                except:
                    pass
    else:
        # رسالة بسيطة (ليست متعددة الأجزاء)
        try:
            payload = email_message.get_payload(decode=True)
            if payload:
                charset = email_message.get_content_charset() or 'utf-8'
                body = payload.decode(charset, errors='ignore')
        except:
            pass
    
    return body or ""


def _is_html(text):
    """التحقق مما إذا كان النص HTML"""
    if not text:
        return False
    # البحث عن علامات HTML شائعة
    html_tags = ['<html', '<body', '<div', '<p>', '<br', '<table']
    return any(tag in text.lower() for tag in html_tags)

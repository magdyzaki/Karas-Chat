"""
قراءة الإيميلات من cPanel باستخدام API Token
Reading emails from cPanel using API Token
"""
import requests
import json
import base64
from datetime import datetime
from typing import List, Dict, Optional
from email.utils import parsedate_tz, mktime_tz


def read_messages_from_cpanel_api(cpanel_host: str, cpanel_username: str, api_token: str,
                                  email_account: str, max_messages: Optional[int] = None) -> List[Dict]:
    """
    قراءة الرسائل من حساب cPanel باستخدام API Token أو Application Password
    
    ملاحظات مهمة:
    1. معظم استضافات cPanel لا تسمح باستخدام API Token مباشرة مع IMAP
    2. الحل الأفضل: استخدام Application Password (App Password) من cPanel
    3. كيفية الحصول على Application Password:
       - ادخل إلى cPanel → Email Accounts
       - اختر البريد الإلكتروني → Manage → App Passwords
       - أنشئ App Password جديد
       - استخدمه كـ "API Token" في هذا البرنامج
    
    Args:
        cpanel_host: عنوان خادم cPanel (مثل: example.com أو 192.168.1.1)
        cpanel_username: اسم مستخدم cPanel (المسؤول)
        api_token: API Token أو Application Password من cPanel
        email_account: البريد الإلكتروني المطلوب قراءة رسائله
        max_messages: الحد الأقصى لعدد الرسائل (None = جميع الرسائل)
    
    Returns:
        List of message dictionaries
    
    Raises:
        ValueError: إذا كانت البيانات غير صحيحة
        Exception: إذا فشل الاتصال
    """
    # التحقق من صحة البيانات المدخلة
    if not cpanel_host or not cpanel_host.strip():
        raise ValueError("عنوان خادم cPanel مطلوب")
    if not cpanel_username or not cpanel_username.strip():
        raise ValueError("اسم مستخدم cPanel مطلوب")
    if not api_token or not api_token.strip():
        raise ValueError("API Token مطلوب")
    if not email_account or not email_account.strip() or "@" not in email_account:
        raise ValueError("البريد الإلكتروني مطلوب ويجب أن يكون صحيحاً")
    
    messages = []
    
    try:
        # تنظيف عنوان الخادم (إزالة https:// أو http:// أو cpanel:// أو أي بروتوكول)
        host = cpanel_host.strip()
        # إزالة البروتوكولات
        for protocol in ["https://", "http://", "cpanel://", "cPanel://", "cPanel:", "cpanel:"]:
            if host.lower().startswith(protocol.lower()):
                host = host[len(protocol):].strip()
        
        # إزالة أي مسافات أو أحرف غير مرغوبة
        host = host.strip().strip('/').strip()
        
        # استخدام cPanel API v3
        api_url = f"https://{host}:2083/api/execute/Email/list_pops"
        
        # رؤوس الطلب
        headers = {
            "Authorization": f"cpanel {cpanel_username}:{api_token}",
            "Content-Type": "application/json"
        }
        
        # تعطيل تحذيرات SSL
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        
        # الحل الأفضل: استخدام cPanel API مباشرة لقراءة الرسائل بدون كلمة مرور
        # هذه الطريقة لا تحتاج كلمة مرور البريد، فقط API Token
        print("DEBUG: Attempting to read messages via cPanel API (no password required)...")
        
        # محاولة 1: استخدام Email::list_messages API (الطريقة المباشرة)
        messages_api_url = f"https://{host}:2083/api/execute/Email/list_messages"
        
        params = {
            "email": email_account,
            "mailbox": "INBOX"
        }
        
        try:
            response = requests.get(messages_api_url, headers=headers, params=params, timeout=30, verify=False)
            
            if response.status_code == 200:
                data = response.json()
                if "data" in data and data["data"]:
                    raw_messages = data["data"]
                    print(f"DEBUG: Found {len(raw_messages)} messages via cPanel API")
                    
                    for msg in raw_messages[:max_messages] if max_messages else raw_messages:
                        message_dict = _parse_cpanel_message(msg, email_account)
                        if message_dict:
                            messages.append(message_dict)
                    
                    if messages:
                        print(f"DEBUG: Successfully parsed {len(messages)} messages from cPanel API")
                        return messages
        except Exception as api_error:
            print(f"DEBUG: cPanel API list_messages failed: {str(api_error)}")
            # سنحاول طرق بديلة
        
        # محاولة 2: استخدام Email::fetch_messages API (إن كان متاحاً)
        try:
            fetch_api_url = f"https://{host}:2083/api/execute/Email/fetch_messages"
            fetch_params = {
                "email": email_account,
                "mailbox": "INBOX",
                "limit": max_messages or 50
            }
            
            response = requests.get(fetch_api_url, headers=headers, params=fetch_params, timeout=30, verify=False)
            
            if response.status_code == 200:
                data = response.json()
                if "data" in data and data["data"]:
                    raw_messages = data["data"]
                    print(f"DEBUG: Found {len(raw_messages)} messages via fetch_messages API")
                    
                    for msg in raw_messages:
                        message_dict = _parse_cpanel_message(msg, email_account)
                        if message_dict:
                            messages.append(message_dict)
                    
                    if messages:
                        print(f"DEBUG: Successfully parsed {len(messages)} messages from fetch_messages API")
                        return messages
        except Exception as fetch_error:
            print(f"DEBUG: cPanel API fetch_messages failed: {str(fetch_error)}")
        
        # محاولة 3: استخدام IMAP مع API Token (كحل بديل - قد لا يعمل في معظم الحالات)
        print("DEBUG: Attempting IMAP connection with API Token as fallback...")
        try:
            messages = _read_via_imap_with_cpanel(host, cpanel_username, api_token, email_account, max_messages)
            if messages:
                print(f"DEBUG: Successfully read {len(messages)} messages via IMAP")
                return messages
        except Exception as imap_error:
            print(f"DEBUG: IMAP connection failed: {str(imap_error)}")
            # سنستمر في المحاولة
        
        # إذا لم نحصل على رسائل من API بعد، نرفع خطأ واضح مع إرشادات
        if not messages:
            raise Exception(
                "فشل الاتصال بخادم cPanel باستخدام API Token.\n\n" +
                "🔍 الأسباب المحتملة:\n" +
                "1. API Token غير صحيح أو منتهي الصلاحية\n" +
                "2. API Token لا يحتوي على صلاحيات 'Email' أو 'Email::*'\n" +
                "3. إصدار cPanel لا يدعم قراءة الرسائل مباشرة من API\n" +
                "4. عنوان خادم cPanel غير صحيح\n\n" +
                "✅ الحلول الممكنة:\n\n" +
                "الحل 1: التحقق من API Token\n" +
                "1. ادخل إلى cPanel → API Tokens\n" +
                "2. تأكد من أن Token يحتوي على صلاحيات 'Email' أو 'Email::*'\n" +
                "3. إذا لم يكن كذلك، أنشئ Token جديد مع الصلاحيات المطلوبة\n\n" +
                "الحل 2: استخدام كلمة مرور البريد (إذا كان API لا يعمل)\n" +
                "1. استخدم نوع الحساب 'cPanel / IMAP'\n" +
                "2. أدخل كلمة مرور البريد العادية\n" +
                "3. ملاحظة: ستحتاج لتحديث كلمة المرور عند تغييرها\n\n" +
                "💡 ملاحظة:\n" +
                "- cPanel API Token يجب أن يحتوي على صلاحيات 'Email' لقراءة الرسائل\n" +
                "- بعض إصدارات cPanel لا تدعم قراءة الرسائل مباشرة من API\n" +
                "- في هذه الحالة، يجب استخدام IMAP مع كلمة مرور البريد"
            )
        
    except Exception as e:
        error_msg = str(e)
        # إزالة معلومات حساسة من رسالة الخطأ
        if "Failed to parse" in error_msg:
            error_msg = "عنوان خادم cPanel غير صحيح. تأكد من إدخال العنوان فقط (مثل: hierbasdelcielo.com) بدون https:// أو cPanel:"
        raise Exception(f"Error reading cPanel emails: {error_msg}")
    
    return messages


def _read_via_imap_with_cpanel(cpanel_host: str, cpanel_username: str, api_token: str,
                               email_account: str, max_messages: Optional[int]) -> List[Dict]:
    """
    قراءة الإيميلات عبر IMAP باستخدام Application Password
    
    ملاحظة: يجب استخدام Application Password (App Password) من cPanel وليس API Token العادي.
    Application Password يمكن الحصول عليه من:
    cPanel → Email Accounts → [اختر البريد] → Manage → App Passwords → Create
    """
    try:
        # الحصول على معلومات IMAP من cPanel
        # تنظيف عنوان الخادم (إزالة https:// أو http:// أو cpanel:// أو أي بروتوكول)
        host = cpanel_host.strip()
        # إزالة البروتوكولات
        for protocol in ["https://", "http://", "cpanel://", "cPanel://", "cPanel:", "cpanel:"]:
            if host.lower().startswith(protocol.lower()):
                host = host[len(protocol):].strip()
        
        # إزالة أي مسافات أو أحرف غير مرغوبة
        host = host.strip().strip('/').strip()
        
        # إذا كان العنوان يحتوي على "cPanel:" أو "cpanel:" في المنتصف، إزالتها
        if ":" in host and not host.count(":") == 1 and "2083" not in host:
            parts = host.split(":")
            host = parts[-1].strip() if parts else host
        
        from core.imap_reader import read_messages_from_imap
        
        # قائمة بمحاولات الاتصال المختلفة
        # ملاحظة: يجب استخدام Application Password (App Password) وليس API Token العادي
        connection_attempts = [
            # محاولة 1: استخدام Application Password مباشرة (الطريقة الأكثر شيوعاً)
            {
                "server": f"mail.{host}" if not host.startswith("mail.") else host,
                "port": 993,
                "username": email_account,
                "password": api_token,  # يجب أن يكون Application Password هنا
                "use_ssl": True,
                "description": "mail.{host}:993 with email as username"
            },
            # محاولة 2: استخدام التنسيق username|email (بعض الاستضافات)
            {
                "server": f"mail.{host}" if not host.startswith("mail.") else host,
                "port": 993,
                "username": f"{cpanel_username}|{email_account}",
                "password": api_token,
                "use_ssl": True,
                "description": "mail.{host}:993 with cpanel_username|email"
            },
            # محاولة 3: استخدام host كـ server مباشرة
            {
                "server": host,
                "port": 993,
                "username": email_account,
                "password": api_token,
                "use_ssl": True,
                "description": "{host}:993 direct"
            },
            # محاولة 4: استخدام imap.host
            {
                "server": f"imap.{host}",
                "port": 993,
                "username": email_account,
                "password": api_token,
                "use_ssl": True,
                "description": "imap.{host}:993"
            },
            # محاولة 5: استخدام البورت 143 مع TLS
            {
                "server": f"mail.{host}" if not host.startswith("mail.") else host,
                "port": 143,
                "username": email_account,
                "password": api_token,
                "use_ssl": False,
                "description": "mail.{host}:143 TLS"
            },
            # محاولة 6: استخدام البريد الكامل كاسم مستخدم (بعض الاستضافات)
            {
                "server": f"mail.{host}" if not host.startswith("mail.") else host,
                "port": 993,
                "username": f"{email_account}@{host}",
                "password": api_token,
                "use_ssl": True,
                "description": "mail.{host}:993 with full email as username"
            }
        ]
        
        last_error = None
        for attempt in connection_attempts:
            try:
                desc = attempt.get("description", f"{attempt['server']}:{attempt['port']}")
                print(f"DEBUG: Trying IMAP connection: {desc}")
                messages = read_messages_from_imap(
                    imap_server=attempt["server"],
                    imap_port=attempt["port"],
                    username=attempt["username"],
                    password=attempt["password"],
                    use_ssl=attempt["use_ssl"],
                    folder="INBOX",
                    max_messages=max_messages,
                    timeout=30
                )
                if messages:
                    print(f"DEBUG: Successfully connected using {desc}")
                    return messages
            except Exception as e:
                error_msg = str(e)
                # تسجيل الخطأ بدون معلومات حساسة
                if "password" in error_msg.lower() or "authentication" in error_msg.lower():
                    last_error = "فشل التحقق من الهوية - تأكد من استخدام Application Password وليس API Token"
                else:
                    last_error = error_msg
                print(f"DEBUG: Connection attempt failed: {error_msg}")
                continue
        
        # إذا فشلت جميع المحاولات، أرفع الخطأ الأخير
        if last_error:
            raise Exception(f"فشلت جميع محاولات الاتصال:\n{last_error}")
        
        return []
        
    except Exception as e:
        raise Exception(f"Error reading via IMAP with cPanel: {str(e)}")


def _parse_cpanel_message(msg_data: dict, email_account: str) -> Optional[Dict]:
    """تحليل رسالة من cPanel API"""
    try:
        subject = msg_data.get("subject", "")
        from_address = msg_data.get("from", "")
        date_str = msg_data.get("date", "")
        body = msg_data.get("body", "")
        
        # استخراج البريد الإلكتروني
        sender_email = _extract_email(from_address)
        sender_name = _extract_name(from_address)
        
        # تحويل التاريخ
        received_date = None
        try:
            date_tuple = parsedate_tz(date_str)
            if date_tuple:
                received_date = datetime.fromtimestamp(mktime_tz(date_tuple)).isoformat()
        except:
            received_date = date_str or datetime.now().isoformat()
        
        return {
            "id": msg_data.get("id", ""),
            "subject": subject or "",
            "body": {
                "content": body or "",
                "contentType": "HTML" if _is_html(body) else "Text"
            },
            "from": {
                "emailAddress": {
                    "name": sender_name or "",
                    "address": sender_email or ""
                }
            },
            "receivedDateTime": received_date,
            "isRead": msg_data.get("read", False)
        }
    except:
        return None


def _extract_email(address_string):
    """استخراج البريد الإلكتروني من سلسلة العنوان"""
    if not address_string:
        return ""
    
    import re
    match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', address_string)
    if match:
        return match.group(0).lower()
    return ""


def _extract_name(address_string):
    """استخراج الاسم من سلسلة العنوان"""
    if not address_string:
        return ""
    
    if '<' in address_string and '>' in address_string:
        name_part = address_string.split('<')[0].strip()
        name_part = name_part.strip('"').strip("'")
        return name_part
    
    return ""


def _is_html(text):
    """التحقق مما إذا كان النص HTML"""
    if not text:
        return False
    html_tags = ['<html', '<body', '<div', '<p>', '<br', '<table']
    return any(tag in text.lower() for tag in html_tags)
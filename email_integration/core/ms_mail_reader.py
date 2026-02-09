import requests

GRAPH_BASE = "https://graph.microsoft.com/v1.0"


def _headers(token):
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json"
    }


def _get_child_folders(token, parent_id):
    url = f"{GRAPH_BASE}/me/mailFolders/{parent_id}/childFolders"
    folders = []

    while url:
        r = requests.get(url, headers=_headers(token), timeout=30)
        r.raise_for_status()
        data = r.json()
        folders.extend(data.get("value", []))
        url = data.get("@odata.nextLink")

    return folders


def _find_folder_recursive(token, parent_id, target_name):
    children = _get_child_folders(token, parent_id)

    for f in children:
        if f.get("displayName", "").lower() == target_name.lower():
            return f.get("id")

        sub_id = _find_folder_recursive(token, f.get("id"), target_name)
        if sub_id:
            return sub_id

    return None


def get_folder_id(token, folder_name):
    folder_id = _find_folder_recursive(token, "inbox", folder_name)
    if not folder_id:
        raise RuntimeError(
            f"Folder '{folder_name}' not found under Inbox.\n"
            "Make sure it exists and contains at least one email."
        )
    return folder_id


def read_messages_from_folder(token, folder_name="EFM_Clients", top=None, max_messages=None, sender_email=None):
    """
    قراءة الرسائل من مجلد معين (يدعم pagination لقراءة جميع الرسائل)
    
    Args:
        token: رمز الوصول
        folder_name: اسم المجلد (إذا كان "Inbox" أو "inbox"، يقرأ من صندوق الوارد مباشرة)
        top: عدد الرسائل في كل صفحة (افتراضي: 100 - قيمة آمنة لتجنب مشاكل JSON)
        max_messages: الحد الأقصى لعدد الرسائل (None = جميع الرسائل)
        sender_email: تصفية الرسائل حسب بريد المرسل (اختياري)
    
    Returns:
        List of messages
    """
    # إذا كان المطلوب صندوق الوارد، استخدم مسار خاص
    # - في حالة وجود sender_email نقرأ من /me/messages (كل المجلدات)
    # - غير ذلك نستخدم مجلد Inbox فقط
    use_global_messages = sender_email is not None and folder_name.lower() == "inbox"

    if not use_global_messages:
        if folder_name.lower() == "inbox":
            folder_id = "inbox"
        else:
            folder_id = get_folder_id(token, folder_name)

    # استخدام 100 لكل صفحة (قيمة آمنة لتجنب مشاكل JSON parsing)
    page_size = top if top is not None else 100
    
    all_messages = []
    
    # بناء URL بدون فلتر (سنقوم بالتصفية محلياً)
    # السبب: Microsoft Graph API قد لا يدعم الفلاتر المعقدة بشكل موثوق
    query_params = [f"$top={page_size}", "$orderby=receivedDateTime desc"]
    
    # إذا كان هناك sender_email، نقرأ عدد أكبر من الرسائل للتصفية المحلية
    if sender_email:
        # زيادة عدد الرسائل للقراءة لتغطية احتمالية وجود رسائل في مجلدات مختلفة
        page_size = min(page_size * 2, 200)  # حتى 200 رسالة للبحث
        query_params[0] = f"$top={page_size}"
    
    if use_global_messages:
        # البحث في جميع الرسائل داخل الحساب (كل المجلدات)
        url = f"{GRAPH_BASE}/me/messages?{'&'.join(query_params)}"
    else:
        # البحث داخل مجلد محدد فقط
        url = (
            f"{GRAPH_BASE}/me/mailFolders/{folder_id}/messages"
            f"?{'&'.join(query_params)}"
        )

    # قراءة جميع الرسائل باستخدام pagination
    page_count = 0
    max_pages = 100  # حماية من الحلقات اللانهائية
    
    while url and page_count < max_pages:
        try:
            # timeout أقوى (30 ثانية) لتجنب التعليق
            r = requests.get(url, headers=_headers(token), timeout=30)
            r.raise_for_status()
            
            # استخدام response.text بدلاً من response.json() مباشرة لتجنب مشاكل JSON
            try:
                data = r.json()
            except Exception as json_error:
                # إذا فشل JSON parsing، جرب قراءة النص وتنظيفه
                print(f"DEBUG: JSON parsing error, trying to fix... Error: {str(json_error)}")
                import json
                text = r.text
                # محاولة إصلاح أحرف التحكم المشكلة
                text = text.encode('utf-8', errors='ignore').decode('utf-8')
                try:
                    data = json.loads(text)
                except:
                    # إذا فشل مرة أخرى، تخطي هذه الصفحة
                    print(f"DEBUG: Failed to parse JSON for page {page_count + 1}, skipping...")
                    break
            
            messages = data.get("value", [])
            if not messages:
                break
            
            # إذا كان هناك sender_email، نقوم بالتصفية محلياً
            if sender_email:
                sender_email_lower = sender_email.lower().strip()
                filtered_messages = []
                for msg in messages:
                    # التحقق من المرسل
                    from_addr = msg.get("from", {}).get("emailAddress", {}).get("address", "").lower()
                    # التحقق من المستلمين
                    to_recipients = msg.get("toRecipients", [])
                    to_addresses = [r.get("emailAddress", {}).get("address", "").lower() for r in to_recipients]
                    
                    # إذا كان البريد موجود في المرسل أو المستلمين
                    if from_addr == sender_email_lower or sender_email_lower in to_addresses:
                        filtered_messages.append(msg)
                
                all_messages.extend(filtered_messages)
            else:
                all_messages.extend(messages)
            
            page_count += 1
            
            # التحقق من الحد الأقصى
            if max_messages and len(all_messages) >= max_messages:
                all_messages = all_messages[:max_messages]
                break
            
            # إذا كنا نبحث عن sender_email ووجدنا رسائل كافية، نتوقف
            if sender_email and len(all_messages) >= (max_messages or 50):
                break
            
            # الحصول على رابط الصفحة التالية
            url = data.get("@odata.nextLink")
            
        except requests.exceptions.RequestException as e:
            print(f"DEBUG: Request error on page {page_count + 1}: {str(e)}")
            break
        except Exception as e:
            print(f"DEBUG: Unexpected error on page {page_count + 1}: {str(e)}")
            break
    
    return all_messages


def read_new_messages_from_inbox(token, since_datetime=None, top=50):
    """
    قراءة الرسائل الجديدة من صندوق الوارد
    
    Args:
        token: رمز الوصول
        since_datetime: تاريخ/وقت البدء (ISO format) - إذا كان None، يقرأ آخر 50 رسالة
        top: عدد الرسائل المطلوبة
    
    Returns:
        List of messages
    """
    url = f"{GRAPH_BASE}/me/mailFolders/inbox/messages"
    
    # بناء الاستعلام
    query_params = [f"$top={top}", "$orderby=receivedDateTime desc"]
    
    if since_datetime:
        query_params.append(f"$filter=receivedDateTime ge {since_datetime}")
    
    url += "?" + "&".join(query_params)
    
    r = requests.get(url, headers=_headers(token), timeout=30)
    r.raise_for_status()
    return r.json().get("value", [])

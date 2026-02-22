# Microsoft Graph Mail Reader
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
        try:
            r = requests.get(url, headers=_headers(token), timeout=30)
            r.raise_for_status()
            data = r.json()
            folders.extend(data.get("value", []))
            url = data.get("@odata.nextLink")
        except:
            break

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


def read_messages_from_folder(token, folder_name="Inbox", top=None, max_messages=None):
    """
    قراءة الرسائل من مجلد معين
    
    Args:
        token: رمز الوصول
        folder_name: اسم المجلد (إذا كان "Inbox" أو "inbox"، يقرأ من صندوق الوارد مباشرة)
        top: عدد الرسائل في كل صفحة (افتراضي: 100)
        max_messages: الحد الأقصى لعدد الرسائل (None = جميع الرسائل)
    
    Returns:
        List of messages
    """
    # إذا كان المطلوب صندوق الوارد، استخدم ID مباشرة
    if folder_name.lower() == "inbox":
        folder_id = "inbox"
    else:
        folder_id = get_folder_id(token, folder_name)

    # استخدام 100 لكل صفحة
    page_size = top if top is not None else 100
    
    all_messages = []
    url = (
        f"{GRAPH_BASE}/me/mailFolders/{folder_id}/messages"
        f"?$top={page_size}&$orderby=receivedDateTime desc"
    )

    # قراءة جميع الرسائل باستخدام pagination
    page_count = 0
    max_pages = 100  # حماية من الحلقات اللانهائية
    
    while url and page_count < max_pages:
        try:
            r = requests.get(url, headers=_headers(token), timeout=60)
            r.raise_for_status()
            
            try:
                data = r.json()
            except Exception as json_error:
                # محاولة إصلاح JSON
                import json
                text = r.text
                text = text.encode('utf-8', errors='ignore').decode('utf-8')
                try:
                    data = json.loads(text)
                except:
                    break
            
            messages = data.get("value", [])
            if not messages:
                break
            
            all_messages.extend(messages)
            page_count += 1
            
            # التحقق من الحد الأقصى
            if max_messages and len(all_messages) >= max_messages:
                all_messages = all_messages[:max_messages]
                break
            
            # الحصول على رابط الصفحة التالية
            url = data.get("@odata.nextLink")
            
        except requests.exceptions.RequestException as e:
            print(f"Request error on page {page_count + 1}: {str(e)}")
            break
        except Exception as e:
            print(f"Unexpected error on page {page_count + 1}: {str(e)}")
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
    
    try:
        r = requests.get(url, headers=_headers(token), timeout=30)
        r.raise_for_status()
        return r.json().get("value", [])
    except:
        return []

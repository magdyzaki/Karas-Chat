"""
إرسال المستندات عبر Outlook
Send Documents via Outlook
"""
import requests
import os
import base64


def create_draft_with_attachment(graph_token: str, to_email: str, subject: str, body: str, attachment_path: str):
    """
    إنشاء مسودة رسالة مع مرفق (الطريقة المفضلة)
    """
    if not os.path.exists(attachment_path):
        raise Exception(f"الملف غير موجود: {attachment_path}")
    
    file_name = os.path.basename(attachment_path)
    
    headers = {
        "Authorization": f"Bearer {graph_token}",
        "Content-Type": "application/json"
    }
    
    # إنشاء مسودة بدون مرفق أولاً
    message_url = "https://graph.microsoft.com/v1.0/me/messages"
    
    message_payload = {
        "subject": subject,
        "body": {
            "contentType": "HTML",
            "content": body.replace("\n", "<br>")
        },
        "toRecipients": [
            {
                "emailAddress": {
                    "address": to_email
                }
            }
        ]
    }
    
    response = requests.post(message_url, headers=headers, json=message_payload)
    
    if response.status_code not in (200, 201):
        raise Exception(f"فشل إنشاء المسودة: {response.status_code}\n{response.text}")
    
    draft_id = response.json().get("id")
    
    if not draft_id:
        raise Exception("لم يتم الحصول على معرف المسودة")
    
    # إضافة المرفق
    # قراءة الملف
    with open(attachment_path, 'rb') as f:
        file_content = f.read()
        file_content_b64 = base64.b64encode(file_content).decode('utf-8')
    
    file_size = len(file_content)
    
    # التحقق من حجم الملف (حد أقصى 3MB للمرفقات في Graph API)
    if file_size > 3 * 1024 * 1024:  # 3MB
        raise Exception(f"حجم الملف كبير جداً ({file_size / 1024 / 1024:.1f}MB). الحد الأقصى 3MB")
    
    # إضافة المرفق
    attachment_url = f"https://graph.microsoft.com/v1.0/me/messages/{draft_id}/attachments"
    
    attachment_payload = {
        "@odata.type": "#microsoft.graph.fileAttachment",
        "name": file_name,
        "contentType": "application/octet-stream",
        "contentBytes": file_content_b64
    }
    
    attach_response = requests.post(attachment_url, headers=headers, json=attachment_payload)
    
    if attach_response.status_code not in (200, 201):
        # إذا فشل إضافة المرفق، نترك المسودة بدون مرفق
        raise Exception(f"تم إنشاء المسودة، لكن تعذر إضافة المرفق تلقائياً. يرجى إضافة الملف '{file_name}' يدوياً في Outlook.")
    
    return draft_id

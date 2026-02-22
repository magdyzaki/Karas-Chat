"""
نظام التواصل المتقدم
Advanced Communication System for EFM
"""
from datetime import datetime
from typing import Dict, List, Optional
from enum import Enum

from .db import get_connection, get_client_by_id, add_message as db_add_message


# أنواع قنوات التواصل
class CommunicationChannel(str, Enum):
    EMAIL = "Email"
    OUTLOOK = "Outlook"
    WHATSAPP = "WhatsApp"
    LINKEDIN = "LinkedIn"
    TELEGRAM = "Telegram"
    PHONE = "Phone"
    SMS = "SMS"
    OTHER = "Other"


# حالة الرسالة
class MessageStatus(str, Enum):
    SENT = "sent"
    RECEIVED = "received"
    DRAFT = "draft"
    FAILED = "failed"
    PENDING = "pending"


def ensure_communication_columns():
    """تأكد من وجود الأعمدة المطلوبة في جدول الرسائل"""
    conn = get_connection()
    cur = conn.cursor()
    
    # إضافة عمود external_message_id إذا لم يكن موجوداً (للربط برسالة في النظام الخارجي)
    try:
        cur.execute("ALTER TABLE messages ADD COLUMN external_message_id TEXT")
    except Exception:
        pass
    
    # إضافة عمود message_status إذا لم يكن موجوداً
    try:
        cur.execute("ALTER TABLE messages ADD COLUMN message_status TEXT DEFAULT 'received'")
    except Exception:
        pass
    
    # إضافة عمود attachments إذا لم يكن موجوداً
    try:
        cur.execute("ALTER TABLE messages ADD COLUMN attachments TEXT")
    except Exception:
        pass
    
    conn.commit()
    conn.close()


def add_unified_message(
    client_id: int,
    channel: str,
    message_type: str,
    content: str,
    subject: str = None,
    external_message_id: str = None,
    status: str = "received",
    attachments: str = None,
    score_effect: int = 0
) -> int:
    """
    إضافة رسالة موحدة من أي قناة
    
    Args:
        client_id: معرف العميل
        channel: قناة التواصل (Email, WhatsApp, LinkedIn, Telegram, etc.)
        message_type: نوع الرسالة (Email, Message, Call, etc.)
        content: محتوى الرسالة
        subject: موضوع الرسالة (اختياري)
        external_message_id: معرف الرسالة في النظام الخارجي (اختياري)
        status: حالة الرسالة (sent, received, draft, failed, pending)
        attachments: معلومات المرفقات (JSON string)
        score_effect: تأثير على النقاط
    
    Returns:
        Message ID
    """
    ensure_communication_columns()
    
    data = {
        "client_id": client_id,
        "message_date": datetime.now().strftime("%d/%m/%Y"),
        "message_type": message_type,
        "channel": channel,
        "client_response": subject or "",
        "notes": content,
        "score_effect": score_effect
    }
    
    # إضافة الحقول الإضافية
    conn = get_connection()
    cur = conn.cursor()
    
    cur.execute("""
        INSERT INTO messages (
            client_id, message_date, message_type, channel,
            client_response, notes, score_effect,
            external_message_id, message_status, attachments
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        client_id,
        datetime.now().strftime("%d/%m/%Y"),
        message_type,
        channel,
        subject or "",
        content,
        score_effect,
        external_message_id,
        status,
        attachments
    ))
    
    message_id = cur.lastrowid
    
    # تحديث نقاط العميل
    if score_effect:
        cur.execute("""
            UPDATE clients
            SET seriousness_score = seriousness_score + ?
            WHERE id = ?
        """, (score_effect, client_id))
    
    conn.commit()
    conn.close()
    
    return message_id


def get_client_messages_unified(client_id: int, channel: str = None) -> List:
    """
    الحصول على جميع رسائل العميل (موحد)
    
    Args:
        client_id: معرف العميل
        channel: قناة محددة (اختياري)
    
    Returns:
        List of messages
    """
    ensure_communication_columns()
    conn = get_connection()
    cur = conn.cursor()
    
    if channel:
        query = """
            SELECT 
                id, message_date, message_type, channel,
                client_response, notes, score_effect,
                external_message_id, message_status, attachments
            FROM messages
            WHERE client_id = ? AND channel = ?
            ORDER BY message_date DESC, id DESC
        """
        cur.execute(query, (client_id, channel))
    else:
        query = """
            SELECT 
                id, message_date, message_type, channel,
                client_response, notes, score_effect,
                external_message_id, message_status, attachments
            FROM messages
            WHERE client_id = ?
            ORDER BY message_date DESC, id DESC
        """
        cur.execute(query, (client_id,))
    
    rows = cur.fetchall()
    conn.close()
    return rows


def get_messages_by_channel(channel: str) -> List:
    """الحصول على جميع الرسائل من قناة محددة"""
    ensure_communication_columns()
    conn = get_connection()
    cur = conn.cursor()
    
    cur.execute("""
        SELECT 
            m.id, m.client_id, c.company_name,
            m.message_date, m.message_type, m.channel,
            m.client_response, m.notes, m.score_effect,
            m.external_message_id, m.message_status
        FROM messages m
        LEFT JOIN clients c ON m.client_id = c.id
        WHERE m.channel = ?
        ORDER BY m.message_date DESC, m.id DESC
    """, (channel,))
    
    rows = cur.fetchall()
    conn.close()
    return rows


def get_communication_statistics(client_id: int = None) -> Dict:
    """الحصول على إحصائيات التواصل"""
    ensure_communication_columns()
    conn = get_connection()
    cur = conn.cursor()
    
    stats = {
        'by_channel': {},
        'total_messages': 0,
        'by_status': {}
    }
    
    if client_id:
        # إحصائيات عميل محدد
        cur.execute("""
            SELECT channel, COUNT(*) as count
            FROM messages
            WHERE client_id = ?
            GROUP BY channel
        """, (client_id,))
        
        for channel, count in cur.fetchall():
            stats['by_channel'][channel or 'Unknown'] = count
            stats['total_messages'] += count
        
        cur.execute("""
            SELECT message_status, COUNT(*) as count
            FROM messages
            WHERE client_id = ?
            GROUP BY message_status
        """, (client_id,))
        
        for status, count in cur.fetchall():
            stats['by_status'][status or 'received'] = count
    else:
        # إحصائيات عامة
        cur.execute("""
            SELECT channel, COUNT(*) as count
            FROM messages
            GROUP BY channel
        """)
        
        for channel, count in cur.fetchall():
            stats['by_channel'][channel or 'Unknown'] = count
            stats['total_messages'] += count
        
        cur.execute("""
            SELECT message_status, COUNT(*) as count
            FROM messages
            GROUP BY message_status
        """)
        
        for status, count in cur.fetchall():
            stats['by_status'][status or 'received'] = count
    
    conn.close()
    return stats


# =========================
# WhatsApp Integration (Basic)
# =========================
def save_whatsapp_message(client_id: int, message_text: str, phone_number: str = None, status: str = "received"):
    """
    حفظ رسالة WhatsApp
    
    Args:
        client_id: معرف العميل
        message_text: نص الرسالة
        phone_number: رقم الهاتف (اختياري)
        status: حالة الرسالة
    """
    subject = f"WhatsApp Message" + (f" - {phone_number}" if phone_number else "")
    
    return add_unified_message(
        client_id=client_id,
        channel=CommunicationChannel.WHATSAPP.value,
        message_type="Message",
        content=message_text,
        subject=subject,
        status=status
    )


# =========================
# LinkedIn Integration (Basic)
# =========================
def save_linkedin_message(client_id: int, message_text: str, conversation_id: str = None, status: str = "received"):
    """
    حفظ رسالة LinkedIn
    
    Args:
        client_id: معرف العميل
        message_text: نص الرسالة
        conversation_id: معرف المحادثة (اختياري)
        status: حالة الرسالة
    """
    subject = f"LinkedIn Message" + (f" - {conversation_id}" if conversation_id else "")
    
    return add_unified_message(
        client_id=client_id,
        channel=CommunicationChannel.LINKEDIN.value,
        message_type="Message",
        content=message_text,
        subject=subject,
        external_message_id=conversation_id,
        status=status
    )


# =========================
# Telegram Integration (Basic)
# =========================
def save_telegram_message(client_id: int, message_text: str, chat_id: str = None, status: str = "received"):
    """
    حفظ رسالة Telegram
    
    Args:
        client_id: معرف العميل
        message_text: نص الرسالة
        chat_id: معرف المحادثة (اختياري)
        status: حالة الرسالة
    """
    subject = f"Telegram Message" + (f" - Chat {chat_id}" if chat_id else "")
    
    return add_unified_message(
        client_id=client_id,
        channel=CommunicationChannel.TELEGRAM.value,
        message_type="Message",
        content=message_text,
        subject=subject,
        external_message_id=chat_id,
        status=status
    )

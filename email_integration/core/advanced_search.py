"""
نظام البحث المتقدم
Advanced Search System
"""
import sqlite3
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from .db import get_connection


def search_clients_advanced(
    search_text: str = "",
    classification: str = None,
    status: str = None,
    country: str = None,
    min_score: int = None,
    max_score: int = None,
    has_focus: Optional[bool] = None
) -> List[Tuple]:
    """
    بحث متقدم في العملاء
    
    Args:
        search_text: نص البحث (اسم الشركة، البريد، البلد، إلخ)
        classification: التصنيف
        status: الحالة
        country: البلد
        min_score: الحد الأدنى للنقاط
        max_score: الحد الأقصى للنقاط
        has_focus: Focus (True/False/None)
    
    Returns:
        قائمة من العملاء
    """
    conn = get_connection()
    cur = conn.cursor()
    
    query = """
        SELECT
            id, company_name, country, contact_person, email,
            phone, website, date_added, status, seriousness_score,
            classification, is_focus
        FROM clients
        WHERE 1=1
    """
    
    params = []
    
    # البحث النصي
    if search_text:
        search_pattern = f'%{search_text.lower()}%'
        query += """
            AND (
                LOWER(company_name) LIKE ? OR
                LOWER(country) LIKE ? OR
                LOWER(email) LIKE ? OR
                LOWER(contact_person) LIKE ? OR
                LOWER(phone) LIKE ? OR
                LOWER(website) LIKE ?
            )
        """
        params.extend([search_pattern] * 6)
    
    # الفلاتر
    if classification and classification != "All Classifications":
        query += " AND classification = ?"
        params.append(classification)
    
    if status and status != "All Status":
        query += " AND status = ?"
        params.append(status)
    
    if country:
        query += " AND LOWER(country) LIKE ?"
        params.append(f'%{country.lower()}%')
    
    if min_score is not None:
        query += " AND seriousness_score >= ?"
        params.append(min_score)
    
    if max_score is not None:
        query += " AND seriousness_score <= ?"
        params.append(max_score)
    
    if has_focus is not None:
        if has_focus:
            query += " AND is_focus = 1"
        else:
            query += " AND is_focus = 0"
    
    query += " ORDER BY is_focus DESC, seriousness_score DESC"
    
    cur.execute(query, tuple(params))
    rows = cur.fetchall()
    conn.close()
    
    return rows


def search_messages_advanced(
    search_text: str = "",
    client_id: int = None,
    channel: str = None,
    message_type: str = None,
    date_from: str = None,
    date_to: str = None
) -> List[Dict]:
    """
    بحث متقدم في الرسائل
    
    Args:
        search_text: نص البحث (في محتوى الرسالة أو الموضوع)
        client_id: معرف العميل
        channel: القناة (Email, WhatsApp, LinkedIn, etc.)
        message_type: نوع الرسالة
        date_from: تاريخ البداية (dd/mm/yyyy)
        date_to: تاريخ النهاية (dd/mm/yyyy)
    
    Returns:
        قائمة من الرسائل مع معلومات العميل
    """
    conn = get_connection()
    cur = conn.cursor()
    
    query = """
        SELECT
            m.id, m.client_id, c.company_name, m.message_date,
            m.message_type, m.channel, m.client_response,
            m.notes, m.score_effect
        FROM messages m
        LEFT JOIN clients c ON m.client_id = c.id
        WHERE 1=1
    """
    
    params = []
    
    # البحث النصي
    if search_text:
        search_pattern = f'%{search_text.lower()}%'
        query += """
            AND (
                LOWER(m.client_response) LIKE ? OR
                LOWER(m.notes) LIKE ?
            )
        """
        params.extend([search_pattern] * 2)
    
    # الفلاتر
    if client_id:
        query += " AND m.client_id = ?"
        params.append(client_id)
    
    if channel:
        query += " AND m.channel = ?"
        params.append(channel)
    
    if message_type:
        query += " AND m.message_type = ?"
        params.append(message_type)
    
    # البحث حسب التاريخ
    if date_from:
        try:
            # تحويل التاريخ إلى تنسيق قابل للمقارنة
            date_from_obj = datetime.strptime(date_from, "%d/%m/%Y")
            query += " AND m.message_date >= ?"
            params.append(date_from)
        except ValueError:
            pass
    
    if date_to:
        try:
            date_to_obj = datetime.strptime(date_to, "%d/%m/%Y")
            query += " AND m.message_date <= ?"
            params.append(date_to)
        except ValueError:
            pass
    
    query += " ORDER BY m.message_date DESC"
    
    cur.execute(query, tuple(params))
    rows = cur.fetchall()
    conn.close()
    
    # تحويل إلى Dictionary
    messages = []
    for row in rows:
        messages.append({
            'id': row[0],
            'client_id': row[1],
            'company_name': row[2],
            'message_date': row[3],
            'message_type': row[4],
            'channel': row[5],
            'client_response': row[6],
            'notes': row[7],
            'score_effect': row[8]
        })
    
    return messages


def search_requests_advanced(
    search_text: str = "",
    client_id: int = None,
    request_type: str = None,
    status: str = None,
    reply_status: str = None,
    date_from: str = None,
    date_to: str = None
) -> List[Dict]:
    """
    بحث متقدم في الطلبات
    
    Args:
        search_text: نص البحث
        client_id: معرف العميل
        request_type: نوع الطلب
        status: الحالة (open/closed)
        reply_status: حالة الرد (pending/replied)
        date_from: تاريخ البداية
        date_to: تاريخ النهاية
    
    Returns:
        قائمة من الطلبات
    """
    conn = get_connection()
    cur = conn.cursor()
    
    query = """
        SELECT
            r.id, r.client_id, c.company_name, r.client_email,
            r.request_type, r.status, r.reply_status,
            r.extracted_text, r.notes, r.created_at
        FROM requests r
        LEFT JOIN clients c ON r.client_id = c.id
        WHERE 1=1
    """
    
    params = []
    
    # البحث النصي
    if search_text:
        search_pattern = f'%{search_text.lower()}%'
        query += """
            AND (
                LOWER(r.request_type) LIKE ? OR
                LOWER(r.extracted_text) LIKE ? OR
                LOWER(r.notes) LIKE ? OR
                LOWER(r.client_email) LIKE ? OR
                LOWER(c.company_name) LIKE ?
            )
        """
        params.extend([search_pattern] * 5)
    
    # الفلاتر
    if client_id:
        query += " AND r.client_id = ?"
        params.append(client_id)
    
    if request_type:
        query += " AND r.request_type LIKE ?"
        params.append(f'%{request_type}%')
    
    if status:
        query += " AND r.status = ?"
        params.append(status)
    
    if reply_status:
        query += " AND r.reply_status = ?"
        params.append(reply_status)
    
    # البحث حسب التاريخ
    if date_from:
        query += " AND r.created_at >= ?"
        params.append(date_from)
    
    if date_to:
        query += " AND r.created_at <= ?"
        params.append(date_to)
    
    query += " ORDER BY r.created_at DESC"
    
    cur.execute(query, tuple(params))
    rows = cur.fetchall()
    conn.close()
    
    # تحويل إلى Dictionary
    requests = []
    for row in rows:
        requests.append({
            'id': row[0],
            'client_id': row[1],
            'company_name': row[2],
            'client_email': row[3],
            'request_type': row[4],
            'status': row[5],
            'reply_status': row[6],
            'extracted_text': row[7],
            'notes': row[8],
            'created_at': row[9]
        })
    
    return requests


def search_all_advanced(
    search_text: str = "",
    search_in: List[str] = None,
    **filters
) -> Dict:
    """
    بحث شامل في جميع الجداول
    
    Args:
        search_text: نص البحث
        search_in: قائمة الجداول للبحث فيها (['clients', 'messages', 'requests'])
        **filters: فلاتر إضافية
    
    Returns:
        Dictionary يحتوي على نتائج البحث من جميع الجداول
    """
    if search_in is None:
        search_in = ['clients', 'messages', 'requests']
    
    results = {}
    
    if 'clients' in search_in:
        results['clients'] = search_clients_advanced(
            search_text=search_text,
            classification=filters.get('classification'),
            status=filters.get('status'),
            country=filters.get('country'),
            min_score=filters.get('min_score'),
            max_score=filters.get('max_score'),
            has_focus=filters.get('has_focus')
        )
    
    if 'messages' in search_in:
        results['messages'] = search_messages_advanced(
            search_text=search_text,
            client_id=filters.get('client_id'),
            channel=filters.get('channel'),
            message_type=filters.get('message_type'),
            date_from=filters.get('date_from'),
            date_to=filters.get('date_to')
        )
    
    if 'requests' in search_in:
        results['requests'] = search_requests_advanced(
            search_text=search_text,
            client_id=filters.get('client_id'),
            request_type=filters.get('request_type'),
            status=filters.get('status'),
            reply_status=filters.get('reply_status'),
            date_from=filters.get('date_from'),
            date_to=filters.get('date_to')
        )
    
    return results

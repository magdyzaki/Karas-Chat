"""
نظام الإحصائيات
Statistics System for EFM
"""
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
from collections import defaultdict

from .db import get_connection, get_all_clients


def get_client_statistics() -> Dict:
    """
    الحصول على إحصائيات العملاء
    
    Returns:
        Dictionary containing various client statistics
    """
    clients = get_all_clients()
    
    stats = {
        'total': len(clients),
        'serious': 0,
        'potential': 0,
        'not_serious': 0,
        'focus': 0,
        'by_status': defaultdict(int),
        'by_country': defaultdict(int),
        'by_score_range': {
            '0-20': 0,
            '21-40': 0,
            '41-60': 0,
            '61-80': 0,
            '81-100': 0,
            '100+': 0
        }
    }
    
    for client in clients:
        (
            client_id, company, country, contact, email,
            phone, website, date_added, status, score,
            classification, is_focus
        ) = client
        
        # التصنيف
        classification = classification or ""
        if "🔥" in classification:
            stats['serious'] += 1
        elif "👍" in classification:
            stats['potential'] += 1
        else:
            stats['not_serious'] += 1
        
        # Focus
        if is_focus:
            stats['focus'] += 1
        
        # الحالة
        if status:
            stats['by_status'][status] += 1
        
        # البلد
        if country:
            stats['by_country'][country] += 1
        
        # النطاق النقاط
        score = score or 0
        if score <= 20:
            stats['by_score_range']['0-20'] += 1
        elif score <= 40:
            stats['by_score_range']['21-40'] += 1
        elif score <= 60:
            stats['by_score_range']['41-60'] += 1
        elif score <= 80:
            stats['by_score_range']['61-80'] += 1
        elif score <= 100:
            stats['by_score_range']['81-100'] += 1
        else:
            stats['by_score_range']['100+'] += 1
    
    return stats


def get_message_statistics() -> Dict:
    """
    الحصول على إحصائيات الرسائل
    
    Returns:
        Dictionary containing message statistics
    """
    conn = get_connection()
    cur = conn.cursor()
    
    stats = {
        'total': 0,
        'by_channel': defaultdict(int),
        'by_month': defaultdict(int),
        'by_type': defaultdict(int),
        'total_score_effect': 0
    }
    
    # إجمالي الرسائل
    cur.execute("SELECT COUNT(*) FROM messages")
    stats['total'] = cur.fetchone()[0]
    
    # حسب القناة
    cur.execute("SELECT channel, COUNT(*) FROM messages GROUP BY channel")
    for channel, count in cur.fetchall():
        stats['by_channel'][channel or 'Unknown'] = count
    
    # حسب النوع
    cur.execute("SELECT message_type, COUNT(*) FROM messages GROUP BY message_type")
    for msg_type, count in cur.fetchall():
        stats['by_type'][msg_type or 'Unknown'] = count
    
    # حسب الشهر (آخر 12 شهر)
    cur.execute("""
        SELECT 
            SUBSTR(message_date, 7, 4) || '-' || 
            SUBSTR(message_date, 4, 2) AS month,
            COUNT(*)
        FROM messages
        WHERE message_date IS NOT NULL
        GROUP BY month
        ORDER BY month DESC
        LIMIT 12
    """)
    
    for month, count in cur.fetchall():
        if month:
            stats['by_month'][month] = count
    
    # إجمالي تأثير النقاط
    cur.execute("SELECT SUM(score_effect) FROM messages")
    result = cur.fetchone()
    stats['total_score_effect'] = result[0] if result[0] else 0
    
    conn.close()
    return stats


def get_request_statistics() -> Dict:
    """
    الحصول على إحصائيات الطلبات
    
    Returns:
        Dictionary containing request statistics
    """
    conn = get_connection()
    cur = conn.cursor()
    
    stats = {
        'total': 0,
        'open': 0,
        'closed': 0,
        'pending_reply': 0,
        'replied': 0,
        'by_type': defaultdict(int),
        'by_month': defaultdict(int)
    }
    
    # إجمالي الطلبات
    cur.execute("SELECT COUNT(*) FROM requests")
    stats['total'] = cur.fetchone()[0]
    
    # حسب الحالة
    cur.execute("SELECT status, COUNT(*) FROM requests GROUP BY status")
    for status, count in cur.fetchall():
        if status == 'open':
            stats['open'] = count
        else:
            stats['closed'] += count
    
    # حسب حالة الرد
    cur.execute("SELECT reply_status, COUNT(*) FROM requests GROUP BY reply_status")
    for reply_status, count in cur.fetchall():
        if reply_status == 'pending':
            stats['pending_reply'] = count
        elif reply_status == 'replied':
            stats['replied'] = count
    
    # حسب النوع
    cur.execute("SELECT request_type, COUNT(*) FROM requests GROUP BY request_type")
    for req_type, count in cur.fetchall():
        if req_type:
            stats['by_type'][req_type] = count
    
    # حسب الشهر
    cur.execute("""
        SELECT 
            SUBSTR(created_at, 7, 4) || '-' || 
            SUBSTR(created_at, 4, 2) AS month,
            COUNT(*)
        FROM requests
        WHERE created_at IS NOT NULL
        GROUP BY month
        ORDER BY month DESC
        LIMIT 12
    """)
    
    for month, count in cur.fetchall():
        if month:
            stats['by_month'][month] = count
    
    conn.close()
    return stats


def get_client_growth_statistics() -> Dict:
    """
    الحصول على إحصائيات نمو العملاء
    
    Returns:
        Dictionary containing client growth statistics
    """
    clients = get_all_clients()
    
    growth = defaultdict(int)
    
    for client in clients:
        date_added = client[7]  # date_added
        if date_added:
            try:
                # تحويل من dd/mm/yyyy إلى yyyy-mm
                parts = date_added.split('/')
                if len(parts) == 3:
                    month_key = f"{parts[2]}-{parts[1].zfill(2)}"
                    growth[month_key] += 1
            except Exception:
                pass
    
    # ترتيب حسب التاريخ
    sorted_growth = dict(sorted(growth.items()))
    return sorted_growth


def get_comprehensive_statistics() -> Dict:
    """
    الحصول على إحصائيات شاملة
    
    Returns:
        Dictionary containing all statistics
    """
    return {
        'clients': get_client_statistics(),
        'messages': get_message_statistics(),
        'requests': get_request_statistics(),
        'growth': get_client_growth_statistics(),
        'generated_at': datetime.now().isoformat()
    }

"""
لوحة التحكم المحسّنة
Enhanced Dashboard Module
"""
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List
from .db import get_connection


def get_dashboard_stats() -> Dict:
    """
    الحصول على إحصائيات اللوحة الرئيسية
    
    Returns:
        Dictionary يحتوي على جميع الإحصائيات
    """
    conn = get_connection()
    cur = conn.cursor()
    
    stats = {}
    
    # إحصائيات العملاء
    cur.execute("SELECT COUNT(*) FROM clients")
    stats['total_clients'] = cur.fetchone()[0]
    
    cur.execute("SELECT COUNT(*) FROM clients WHERE classification LIKE '🔥%'")
    stats['serious_clients'] = cur.fetchone()[0]
    
    cur.execute("SELECT COUNT(*) FROM clients WHERE classification LIKE '👍%'")
    stats['potential_clients'] = cur.fetchone()[0]
    
    cur.execute("SELECT COUNT(*) FROM clients WHERE is_focus = 1")
    stats['focus_clients'] = cur.fetchone()[0]
    
    # إحصائيات الرسائل
    cur.execute("SELECT COUNT(*) FROM messages")
    stats['total_messages'] = cur.fetchone()[0]
    
    # إحصائيات الطلبات
    cur.execute("SELECT COUNT(*) FROM requests WHERE status = 'open'")
    stats['open_requests'] = cur.fetchone()[0]
    
    cur.execute("SELECT COUNT(*) FROM requests WHERE reply_status = 'pending'")
    stats['pending_requests'] = cur.fetchone()[0]
    
    # إحصائيات المهام
    try:
        cur.execute("SELECT COUNT(*) FROM tasks WHERE status = 'pending'")
        stats['pending_tasks'] = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(*) FROM tasks WHERE status = 'pending' AND due_date <= ?",
                   (datetime.now().strftime("%d/%m/%Y"),))
        stats['overdue_tasks'] = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(*) FROM tasks WHERE status = 'pending' AND due_date = ?",
                   (datetime.now().strftime("%d/%m/%Y"),))
        stats['tasks_due_today'] = cur.fetchone()[0]
    except Exception:
        stats['pending_tasks'] = 0
        stats['overdue_tasks'] = 0
        stats['tasks_due_today'] = 0
    
    # إحصائيات المبيعات
    try:
        cur.execute("SELECT COUNT(*) FROM sales_deals WHERE stage != 'closed_won' AND stage != 'closed_lost'")
        stats['active_deals'] = cur.fetchone()[0]
    except Exception:
        stats['active_deals'] = 0
    
    # إحصائيات النمو (آخر 30 يوم)
    thirty_days_ago = (datetime.now() - timedelta(days=30)).strftime("%d/%m/%Y")
    cur.execute("SELECT COUNT(*) FROM clients WHERE date_added >= ?", (thirty_days_ago,))
    stats['new_clients_30d'] = cur.fetchone()[0]
    
    conn.close()
    return stats


def get_actions_needed() -> List[Dict]:
    """
    الحصول على قائمة الإجراءات المطلوبة
    
    Returns:
        List of dictionaries containing actions needed
    """
    actions = []
    conn = get_connection()
    cur = conn.cursor()
    
    # 1. العملاء الذين يحتاجون متابعة
    try:
        from core.db import get_clients_needing_followup
        followup_clients = get_clients_needing_followup()
        for company in followup_clients[:5]:  # أول 5 فقط
            actions.append({
                'type': 'followup',
                'priority': 'medium',
                'title': f'متابعة مطلوبة: {company}',
                'description': f'العميل {company} يحتاج إلى متابعة',
                'icon': '📞',
                'color': '#FFD93D'
            })
    except Exception:
        pass
    
    # 2. الطلبات المعلقة
    try:
        cur.execute("""
            SELECT r.id, r.client_email, r.request_type, c.company_name
            FROM requests r
            LEFT JOIN clients c ON r.client_id = c.id
            WHERE r.reply_status = 'pending'
            ORDER BY r.created_at DESC
            LIMIT 5
        """)
        for row in cur.fetchall():
            req_id, email, req_type, company = row
            company = company or email or 'Unknown'
            actions.append({
                'type': 'request',
                'priority': 'high',
                'title': f'رد مطلوب على طلب: {req_type}',
                'description': f'العميل: {company}',
                'icon': '📋',
                'color': '#FF6B6B',
                'request_id': req_id
            })
    except Exception:
        pass
    
    # 3. المهام المتأخرة
    try:
        cur.execute("""
            SELECT t.id, t.title, t.due_date, c.company_name
            FROM tasks t
            JOIN clients c ON t.client_id = c.id
            WHERE t.status = 'pending' 
              AND t.due_date < ?
            ORDER BY t.due_date ASC
            LIMIT 5
        """, (datetime.now().strftime("%d/%m/%Y"),))
        for row in cur.fetchall():
            task_id, title, due_date, company = row
            actions.append({
                'type': 'task',
                'priority': 'urgent',
                'title': f'مهمة متأخرة: {title}',
                'description': f'العميل: {company} | تاريخ الاستحقاق: {due_date}',
                'icon': '⚠️',
                'color': '#E74C3C',
                'task_id': task_id
            })
    except Exception:
        pass
    
    # 4. المهام المستحقة اليوم
    try:
        cur.execute("""
            SELECT t.id, t.title, c.company_name
            FROM tasks t
            JOIN clients c ON t.client_id = c.id
            WHERE t.status = 'pending' 
              AND t.due_date = ?
            ORDER BY 
                CASE t.priority
                    WHEN 'urgent' THEN 1
                    WHEN 'high' THEN 2
                    WHEN 'medium' THEN 3
                    WHEN 'low' THEN 4
                END
            LIMIT 5
        """, (datetime.now().strftime("%d/%m/%Y"),))
        for row in cur.fetchall():
            task_id, title, company = row
            actions.append({
                'type': 'task',
                'priority': 'high',
                'title': f'مهمة مستحقة اليوم: {title}',
                'description': f'العميل: {company}',
                'icon': '📅',
                'color': '#FFD93D',
                'task_id': task_id
            })
    except Exception:
        pass
    
    conn.close()
    
    # ترتيب حسب الأولوية
    priority_order = {'urgent': 1, 'high': 2, 'medium': 3, 'low': 4}
    actions.sort(key=lambda x: priority_order.get(x.get('priority', 'low'), 4))
    
    return actions[:10]  # أول 10 إجراءات


def get_recent_activities(limit: int = 10) -> List[Dict]:
    """
    الحصول على آخر الأنشطة
    
    Args:
        limit: عدد الأنشطة المطلوبة
    
    Returns:
        List of recent activities
    """
    activities = []
    conn = get_connection()
    cur = conn.cursor()
    
    # آخر الرسائل
    try:
        cur.execute("""
            SELECT m.id, m.message_date, m.channel, m.message_type,
                   c.company_name, m.score_effect
            FROM messages m
            JOIN clients c ON m.client_id = c.id
            ORDER BY m.id DESC
            LIMIT ?
        """, (limit,))
        for row in cur.fetchall():
            msg_id, date, channel, msg_type, company, score = row
            activities.append({
                'type': 'message',
                'date': date,
                'title': f'رسالة جديدة من {company}',
                'description': f'{channel} - {msg_type}',
                'icon': '✉️',
                'color': '#4ECDC4',
                'message_id': msg_id,
                'score_effect': score or 0
            })
    except Exception:
        pass
    
    # آخر الطلبات
    try:
        cur.execute("""
            SELECT r.id, r.created_at, r.request_type, c.company_name
            FROM requests r
            LEFT JOIN clients c ON r.client_id = c.id
            ORDER BY r.id DESC
            LIMIT ?
        """, (limit // 2,))
        for row in cur.fetchall():
            req_id, date, req_type, company = row
            company = company or 'Unknown'
            activities.append({
                'type': 'request',
                'date': date or '',
                'title': f'طلب جديد: {req_type}',
                'description': f'العميل: {company}',
                'icon': '📋',
                'color': '#95E1D3',
                'request_id': req_id
            })
    except Exception:
        pass
    
    conn.close()
    
    # ترتيب حسب التاريخ (الأحدث أولاً)
    activities.sort(key=lambda x: x.get('date', ''), reverse=True)
    
    return activities[:limit]


def get_monthly_comparison() -> Dict:
    """
    الحصول على مقارنة شهرية
    
    Returns:
        Dictionary يحتوي على مقارنة الشهر الحالي مع الشهر الماضي
    """
    conn = get_connection()
    cur = conn.cursor()
    
    now = datetime.now()
    current_month_start = now.replace(day=1).strftime("%d/%m/%Y")
    
    # الشهر الماضي
    if now.month == 1:
        last_month_start = now.replace(year=now.year-1, month=12, day=1).strftime("%d/%m/%Y")
    else:
        last_month_start = now.replace(month=now.month-1, day=1).strftime("%d/%m/%Y")
    
    comparison = {}
    
    # عملاء جدد
    cur.execute("SELECT COUNT(*) FROM clients WHERE date_added >= ?", (current_month_start,))
    comparison['clients_this_month'] = cur.fetchone()[0]
    
    cur.execute("SELECT COUNT(*) FROM clients WHERE date_added >= ? AND date_added < ?",
               (last_month_start, current_month_start))
    comparison['clients_last_month'] = cur.fetchone()[0]
    
    # رسائل
    cur.execute("""
        SELECT COUNT(*) FROM messages 
        WHERE SUBSTR(message_date, 7, 4) || '-' || SUBSTR(message_date, 4, 2) = ?
    """, (f"{now.year}-{now.month:02d}",))
    comparison['messages_this_month'] = cur.fetchone()[0]
    
    last_month_year = now.year if now.month > 1 else now.year - 1
    last_month_num = now.month - 1 if now.month > 1 else 12
    
    cur.execute("""
        SELECT COUNT(*) FROM messages 
        WHERE SUBSTR(message_date, 7, 4) || '-' || SUBSTR(message_date, 4, 2) = ?
    """, (f"{last_month_year}-{last_month_num:02d}",))
    comparison['messages_last_month'] = cur.fetchone()[0]
    
    conn.close()
    
    # حساب التغيير
    if comparison['clients_last_month'] > 0:
        comparison['clients_change'] = ((comparison['clients_this_month'] - comparison['clients_last_month']) 
                                       / comparison['clients_last_month'] * 100)
    else:
        comparison['clients_change'] = 100 if comparison['clients_this_month'] > 0 else 0
    
    if comparison['messages_last_month'] > 0:
        comparison['messages_change'] = ((comparison['messages_this_month'] - comparison['messages_last_month']) 
                                        / comparison['messages_last_month'] * 100)
    else:
        comparison['messages_change'] = 100 if comparison['messages_this_month'] > 0 else 0
    
    return comparison

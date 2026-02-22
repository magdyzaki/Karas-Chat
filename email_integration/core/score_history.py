"""
نظام تتبع اتجاهات النقاط
Score History & Trends Tracking System
"""
import sqlite3
from datetime import datetime, timedelta
from typing import List, Dict, Tuple
from .db import get_connection


def init_score_history_table():
    """إنشاء جدول تتبع تاريخ النقاط"""
    conn = get_connection()
    cur = conn.cursor()
    
    cur.execute("""
    CREATE TABLE IF NOT EXISTS score_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        client_id INTEGER NOT NULL,
        date TEXT NOT NULL,
        score INTEGER NOT NULL,
        classification TEXT,
        change_reason TEXT,
        message_id INTEGER,
        FOREIGN KEY (client_id) REFERENCES clients(id),
        FOREIGN KEY (message_id) REFERENCES messages(id)
    )
    """)
    
    # إنشاء فهرس لتسريع الاستعلامات
    cur.execute("""
    CREATE INDEX IF NOT EXISTS idx_score_history_client_date 
    ON score_history(client_id, date DESC)
    """)
    
    conn.commit()
    conn.close()


def record_score_change(
    client_id: int,
    new_score: int,
    classification: str = None,
    change_reason: str = None,
    message_id: int = None
):
    """تسجيل تغيير في النقاط"""
    init_score_history_table()
    
    conn = get_connection()
    cur = conn.cursor()
    
    date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    cur.execute("""
    INSERT INTO score_history (
        client_id, date, score, classification,
        change_reason, message_id
    )
    VALUES (?, ?, ?, ?, ?, ?)
    """, (
        client_id,
        date_str,
        new_score,
        classification,
        change_reason,
        message_id
    ))
    
    conn.commit()
    conn.close()


def get_client_score_history(client_id: int, days: int = 30) -> List[Tuple]:
    """
    الحصول على تاريخ النقاط للعميل
    Returns: List of (date, score, classification, change_reason)
    """
    init_score_history_table()
    
    conn = get_connection()
    cur = conn.cursor()
    
    cutoff_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    
    cur.execute("""
    SELECT date, score, classification, change_reason
    FROM score_history
    WHERE client_id = ? AND date >= ?
    ORDER BY date DESC
    LIMIT 100
    """, (client_id, cutoff_date))
    
    rows = cur.fetchall()
    conn.close()
    return rows


def get_score_trend(client_id: int, days: int = 30) -> Dict:
    """
    تحليل اتجاه النقاط للعميل
    Returns: {
        'current_score': int,
        'previous_score': int,
        'change': int,
        'change_percent': float,
        'trend': str,  # 'up', 'down', 'stable'
        'points': List[Dict]  # [{date, score}]
    }
    """
    history = get_client_score_history(client_id, days)
    
    if not history:
        return {
            'current_score': 0,
            'previous_score': 0,
            'change': 0,
            'change_percent': 0.0,
            'trend': 'stable',
            'points': []
        }
    
    # أحدث نقطة
    current_score = history[0][1] if history else 0
    
    # نقطة سابقة (أول نقطة في الفترة)
    previous_score = history[-1][1] if len(history) > 1 else current_score
    
    change = current_score - previous_score
    change_percent = (change / previous_score * 100) if previous_score > 0 else 0.0
    
    # تحديد الاتجاه
    if change > 5:
        trend = 'up'
    elif change < -5:
        trend = 'down'
    else:
        trend = 'stable'
    
    # تحضير النقاط للرسم البياني
    points = [
        {
            'date': row[0],
            'score': row[1]
        }
        for row in reversed(history)  # عكس الترتيب (من الأقدم للأحدث)
    ]
    
    return {
        'current_score': current_score,
        'previous_score': previous_score,
        'change': change,
        'change_percent': change_percent,
        'trend': trend,
        'points': points
    }


def get_all_score_trends(days: int = 30) -> List[Dict]:
    """الحصول على اتجاهات النقاط لجميع العملاء"""
    from .db import get_all_clients
    
    clients = get_all_clients()
    trends = []
    
    for client in clients:
        client_id = client[0]
        company_name = client[1]
        current_score = client[10] or 0
        
        trend_data = get_score_trend(client_id, days)
        trend_data['client_id'] = client_id
        trend_data['company_name'] = company_name
        trends.append(trend_data)
    
    return trends


def get_classification_changes(client_id: int = None, days: int = 30) -> List[Dict]:
    """
    الحصول على تغييرات التصنيف
    Returns: List of {
        'client_id': int,
        'company_name': str,
        'date': str,
        'old_classification': str,
        'new_classification': str,
        'old_score': int,
        'new_score': int
    }
    """
    init_score_history_table()
    
    conn = get_connection()
    cur = conn.cursor()
    
    cutoff_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    
    # استعلام بسيط بدون window functions
    if client_id:
        cur.execute("""
        SELECT 
            sh.client_id,
            c.company_name,
            sh.date,
            sh.classification as new_classification,
            sh.score as new_score
        FROM score_history sh
        JOIN clients c ON sh.client_id = c.id
        WHERE sh.client_id = ? AND sh.date >= ?
        ORDER BY sh.date ASC
        """, (client_id, cutoff_date))
    else:
        cur.execute("""
        SELECT 
            sh.client_id,
            c.company_name,
            sh.date,
            sh.classification as new_classification,
            sh.score as new_score
        FROM score_history sh
        JOIN clients c ON sh.client_id = c.id
        WHERE sh.date >= ?
        ORDER BY sh.client_id, sh.date ASC
        """, (cutoff_date,))
    
    rows = cur.fetchall()
    conn.close()
    
    # معالجة البيانات يدوياً لتحديد التغييرات
    changes = []
    prev_data = {}  # {client_id: (classification, score)}
    
    for row in rows:
        c_id = row[0]
        company_name = row[1]
        date = row[2]
        new_class = row[3]
        new_score = row[4] or 0
        
        if c_id in prev_data:
            old_class, old_score = prev_data[c_id]
            
            # فقط إذا تغير التصنيف
            if old_class and old_class != new_class:
                changes.append({
                    'client_id': c_id,
                    'company_name': company_name,
                    'date': date,
                    'old_classification': old_class,
                    'new_classification': new_class,
                    'old_score': old_score,
                    'new_score': new_score
                })
        
        prev_data[c_id] = (new_class, new_score)
    
    # ترتيب حسب التاريخ (من الأحدث للأقدم)
    changes.sort(key=lambda x: x['date'], reverse=True)
    
    return changes

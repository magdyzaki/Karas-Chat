"""
نظام إدارة المهام والمتابعة
Tasks and Follow-up Management System
"""
import sqlite3
import calendar
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from .db import get_connection


# ===== Task Priorities =====
PRIORITY_LOW = "low"
PRIORITY_MEDIUM = "medium"
PRIORITY_HIGH = "high"
PRIORITY_URGENT = "urgent"

PRIORITIES = {
    PRIORITY_LOW: {"label": "Low", "color": "#95A5A6", "icon": "⚪"},
    PRIORITY_MEDIUM: {"label": "Medium", "color": "#4ECDC4", "icon": "🔵"},
    PRIORITY_HIGH: {"label": "High", "color": "#FFD93D", "icon": "🟡"},
    PRIORITY_URGENT: {"label": "Urgent", "color": "#FF6B6B", "icon": "🔴"}
}

# ===== Task Status =====
STATUS_PENDING = "pending"
STATUS_IN_PROGRESS = "in_progress"
STATUS_COMPLETED = "completed"
STATUS_CANCELLED = "cancelled"

TASK_STATUSES = {
    STATUS_PENDING: {"label": "Pending", "color": "#95A5A6"},
    STATUS_IN_PROGRESS: {"label": "In Progress", "color": "#4ECDC4"},
    STATUS_COMPLETED: {"label": "Completed", "color": "#2ECC71"},
    STATUS_CANCELLED: {"label": "Cancelled", "color": "#E74C3C"}
}

# ===== Task Types =====
TYPE_FOLLOWUP = "followup"
TYPE_CALL = "call"
TYPE_EMAIL = "email"
TYPE_MEETING = "meeting"
TYPE_SAMPLE_DELIVERY = "sample_delivery"
TYPE_QUOTATION = "quotation"
TYPE_OTHER = "other"

TASK_TYPES = {
    TYPE_FOLLOWUP: {"label": "Follow-up", "icon": "📞"},
    TYPE_CALL: {"label": "Call", "icon": "📱"},
    TYPE_EMAIL: {"label": "Email", "icon": "✉️"},
    TYPE_MEETING: {"label": "Meeting", "icon": "🤝"},
    TYPE_SAMPLE_DELIVERY: {"label": "Sample Delivery", "icon": "📦"},
    TYPE_QUOTATION: {"label": "Quotation", "icon": "💰"},
    TYPE_OTHER: {"label": "Other", "icon": "📋"}
}


def init_tasks_table():
    """إنشاء جدول المهام"""
    conn = get_connection()
    cur = conn.cursor()
    
    cur.execute("""
    CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        client_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        description TEXT,
        task_type TEXT DEFAULT 'followup',
        priority TEXT DEFAULT 'medium',
        status TEXT DEFAULT 'pending',
        due_date TEXT NOT NULL,
        reminder_date TEXT,
        completed_date TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT,
        notes TEXT,
        deal_id INTEGER,
        recurrence_pattern TEXT,
        recurrence_interval INTEGER,
        parent_task_id INTEGER,
        FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE,
        FOREIGN KEY (deal_id) REFERENCES sales_deals(id) ON DELETE SET NULL,
        FOREIGN KEY (parent_task_id) REFERENCES tasks(id) ON DELETE CASCADE
    )
    """)
    
    # إضافة أعمدة جديدة إن لم تكن موجودة
    for column, col_type in [
        ('deal_id', 'INTEGER'),
        ('recurrence_pattern', 'TEXT'),
        ('recurrence_interval', 'INTEGER'),
        ('parent_task_id', 'INTEGER')
    ]:
        try:
            cur.execute(f"ALTER TABLE tasks ADD COLUMN {column} {col_type}")
        except:
            pass  # العمود موجود بالفعل
    
    # إنشاء فهارس
    cur.execute("""
    CREATE INDEX IF NOT EXISTS idx_tasks_client_id 
    ON tasks(client_id)
    """)
    
    cur.execute("""
    CREATE INDEX IF NOT EXISTS idx_tasks_due_date 
    ON tasks(due_date)
    """)
    
    cur.execute("""
    CREATE INDEX IF NOT EXISTS idx_tasks_status 
    ON tasks(status)
    """)
    
    cur.execute("""
    CREATE INDEX IF NOT EXISTS idx_tasks_deal_id 
    ON tasks(deal_id)
    """)
    
    cur.execute("""
    CREATE INDEX IF NOT EXISTS idx_tasks_priority 
    ON tasks(priority)
    """)
    
    conn.commit()
    conn.close()


def create_task(
    client_id: int,
    title: str,
    description: str = "",
    task_type: str = TYPE_FOLLOWUP,
    priority: str = PRIORITY_MEDIUM,
    due_date: str = None,
    reminder_date: str = None,
    notes: str = "",
    deal_id: int = None,
    recurrence_pattern: str = None,
    recurrence_interval: int = None
) -> int:
    """
    إنشاء مهمة جديدة
    
    Returns: task_id
    """
    init_tasks_table()
    
    conn = get_connection()
    cur = conn.cursor()
    
    if due_date is None:
        due_date = (datetime.now() + timedelta(days=7)).strftime("%d/%m/%Y")
    
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # معالجة القيم الاختيارية
    final_deal_id = deal_id if deal_id else None
    final_recurrence_pattern = recurrence_pattern if recurrence_pattern and recurrence_pattern != "none" else None
    final_recurrence_interval = recurrence_interval if final_recurrence_pattern else None
    
    cur.execute("""
    INSERT INTO tasks (
        client_id, title, description, task_type,
        priority, status, due_date, reminder_date,
        created_at, notes, deal_id, recurrence_pattern, recurrence_interval
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        client_id,
        title,
        description,
        task_type,
        priority,
        STATUS_PENDING,
        due_date,
        reminder_date,
        created_at,
        notes,
        final_deal_id,
        final_recurrence_pattern,
        final_recurrence_interval
    ))
    
    task_id = cur.lastrowid
    conn.commit()
    conn.close()
    
    return task_id


def update_task(
    task_id: int,
    title: str = None,
    description: str = None,
    task_type: str = None,
    priority: str = None,
    status: str = None,
    due_date: str = None,
    reminder_date: str = None,
    notes: str = None,
    deal_id: int = None,
    recurrence_pattern: str = None,
    recurrence_interval: int = None
):
    """تحديث مهمة موجودة"""
    init_tasks_table()
    
    conn = get_connection()
    cur = conn.cursor()
    
    updates = []
    values = []
    
    if title is not None:
        updates.append("title = ?")
        values.append(title)
    
    if description is not None:
        updates.append("description = ?")
        values.append(description)
    
    if task_type is not None:
        updates.append("task_type = ?")
        values.append(task_type)
    
    if priority is not None:
        updates.append("priority = ?")
        values.append(priority)
    
    if status is not None:
        updates.append("status = ?")
        values.append(status)
        if status == STATUS_COMPLETED:
            updates.append("completed_date = ?")
            values.append(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    
    if due_date is not None:
        updates.append("due_date = ?")
        values.append(due_date)
    
    if reminder_date is not None:
        updates.append("reminder_date = ?")
        values.append(reminder_date)
    
    if notes is not None:
        updates.append("notes = ?")
        values.append(notes)
    
    if deal_id is not None:
        updates.append("deal_id = ?")
        values.append(deal_id if deal_id else None)
    
    if recurrence_pattern is not None:
        updates.append("recurrence_pattern = ?")
        values.append(recurrence_pattern if recurrence_pattern != "none" else None)
        if recurrence_pattern and recurrence_pattern != "none":
            updates.append("recurrence_interval = ?")
            values.append(recurrence_interval or 1)
        elif recurrence_pattern == "none":
            # إذا تم تعيين recurrence_pattern إلى "none"، يجب تعيين recurrence_interval إلى None
            updates.append("recurrence_interval = ?")
            values.append(None)
    
    updates.append("updated_at = ?")
    values.append(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    
    values.append(task_id)
    
    if updates:
        query = f"UPDATE tasks SET {', '.join(updates)} WHERE id = ?"
        cur.execute(query, tuple(values))
        conn.commit()
    
    conn.close()


def delete_task(task_id: int):
    """حذف مهمة"""
    init_tasks_table()
    
    conn = get_connection()
    cur = conn.cursor()
    
    cur.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    
    conn.commit()
    conn.close()


def get_task(task_id: int) -> Optional[Tuple]:
    """الحصول على مهمة واحدة"""
    init_tasks_table()
    
    conn = get_connection()
    cur = conn.cursor()
    
    cur.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
    row = cur.fetchone()
    conn.close()
    
    return row


def get_client_tasks(client_id: int, status: str = None) -> List[Dict]:
    """
    الحصول على مهام عميل معين
    
    Returns: List of task dictionaries
    """
    init_tasks_table()
    
    conn = get_connection()
    cur = conn.cursor()
    
    if status:
        cur.execute("""
        SELECT 
            t.id, t.client_id, t.title, t.description, t.task_type,
            t.priority, t.status, t.due_date, t.reminder_date,
            t.completed_date, t.created_at, t.updated_at, t.notes,
            t.deal_id, t.recurrence_pattern, t.recurrence_interval, t.parent_task_id,
            c.company_name
        FROM tasks t
        JOIN clients c ON t.client_id = c.id
        WHERE t.client_id = ? AND t.status = ?
        ORDER BY 
            CASE t.priority
                WHEN 'urgent' THEN 1
                WHEN 'high' THEN 2
                WHEN 'medium' THEN 3
                WHEN 'low' THEN 4
            END,
            t.due_date ASC
        """, (client_id, status))
    else:
        cur.execute("""
        SELECT 
            t.id, t.client_id, t.title, t.description, t.task_type,
            t.priority, t.status, t.due_date, t.reminder_date,
            t.completed_date, t.created_at, t.updated_at, t.notes,
            t.deal_id, t.recurrence_pattern, t.recurrence_interval, t.parent_task_id,
            c.company_name
        FROM tasks t
        JOIN clients c ON t.client_id = c.id
        WHERE t.client_id = ?
        ORDER BY 
            CASE t.priority
                WHEN 'urgent' THEN 1
                WHEN 'high' THEN 2
                WHEN 'medium' THEN 3
                WHEN 'low' THEN 4
            END,
            t.due_date ASC
        """, (client_id,))
    
    rows = cur.fetchall()
    conn.close()
    
    tasks = []
    for row in rows:
        task_dict = {
            'id': row[0],
            'client_id': row[1],
            'title': row[2],
            'description': row[3],
            'task_type': row[4],
            'priority': row[5],
            'status': row[6],
            'due_date': row[7],
            'reminder_date': row[8],
            'completed_date': row[9],
            'created_at': row[10],
            'updated_at': row[11],
            'notes': row[12],
            'company_name': row[17] if len(row) > 17 else 'Unknown'
        }
        
        # الحقول الجديدة
        if len(row) > 13:
            task_dict['deal_id'] = row[13]
        if len(row) > 14:
            task_dict['recurrence_pattern'] = row[14]
        if len(row) > 15:
            task_dict['recurrence_interval'] = row[15]
        if len(row) > 16:
            task_dict['parent_task_id'] = row[16]
        
        tasks.append(task_dict)
    
    return tasks


def get_all_tasks(status: str = None, priority: str = None, days_ahead: int = None) -> List[Dict]:
    """
    الحصول على جميع المهام مع فلاتر اختيارية
    
    Args:
        status: فلتر حسب الحالة
        priority: فلتر حسب الأولوية
        days_ahead: عدد الأيام القادمة (None = جميع المهام)
    """
    init_tasks_table()
    
    conn = get_connection()
    cur = conn.cursor()
    
    query = """
    SELECT 
        t.id, t.client_id, t.title, t.description, t.task_type,
        t.priority, t.status, t.due_date, t.reminder_date,
        t.completed_date, t.created_at, t.updated_at, t.notes,
        t.deal_id, t.recurrence_pattern, t.recurrence_interval, t.parent_task_id,
        c.company_name, c.email, c.phone
    FROM tasks t
    JOIN clients c ON t.client_id = c.id
    WHERE 1=1
    """
    
    params = []
    
    if status:
        query += " AND t.status = ?"
        params.append(status)
    
    if priority:
        query += " AND t.priority = ?"
        params.append(priority)
    
    if days_ahead is not None:
        today = datetime.now()
        end_date = (today + timedelta(days=days_ahead)).strftime("%d/%m/%Y")
        query += " AND t.due_date <= ?"
        params.append(end_date)
    
    query += """
    ORDER BY 
        CASE t.priority
            WHEN 'urgent' THEN 1
            WHEN 'high' THEN 2
            WHEN 'medium' THEN 3
            WHEN 'low' THEN 4
        END,
        t.due_date ASC
    """
    
    cur.execute(query, tuple(params))
    rows = cur.fetchall()
    conn.close()
    
    tasks = []
    for row in rows:
        tasks.append({
            'id': row[0],
            'client_id': row[1],
            'title': row[2],
            'description': row[3],
            'task_type': row[4],
            'priority': row[5],
            'status': row[6],
            'due_date': row[7],
            'reminder_date': row[8],
            'completed_date': row[9],
            'created_at': row[10],
            'updated_at': row[11],
            'notes': row[12],
            'company_name': row[13],
            'email': row[14],
            'phone': row[15]
        })
    
    return tasks


def get_upcoming_tasks(days: int = 7) -> List[Dict]:
    """الحصول على المهام القادمة في الأيام القادمة"""
    today = datetime.now()
    end_date = (today + timedelta(days=days)).strftime("%d/%m/%Y")
    
    return get_all_tasks(status=STATUS_PENDING, days_ahead=days)


def get_overdue_tasks() -> List[Dict]:
    """الحصول على المهام المتأخرة"""
    init_tasks_table()
    
    conn = get_connection()
    cur = conn.cursor()
    
    today_str = datetime.now().strftime("%d/%m/%Y")
    
    cur.execute("""
    SELECT 
        t.id, t.client_id, t.title, t.description, t.task_type,
        t.priority, t.status, t.due_date, t.reminder_date,
        t.completed_date, t.created_at, t.updated_at, t.notes,
        t.deal_id, t.recurrence_pattern, t.recurrence_interval, t.parent_task_id,
        c.company_name, c.email, c.phone
    FROM tasks t
    JOIN clients c ON t.client_id = c.id
    WHERE t.status = 'pending' AND t.due_date < ?
    ORDER BY t.due_date ASC
    """, (today_str,))
    
    rows = cur.fetchall()
    conn.close()
    
    tasks = []
    for row in rows:
        task_dict = {
            'id': row[0],
            'client_id': row[1],
            'title': row[2],
            'description': row[3],
            'task_type': row[4],
            'priority': row[5],
            'status': row[6],
            'due_date': row[7],
            'reminder_date': row[8],
            'completed_date': row[9],
            'created_at': row[10],
            'updated_at': row[11],
            'notes': row[12],
            'company_name': row[17] if len(row) > 17 else 'Unknown',
            'email': row[18] if len(row) > 18 else None,
            'phone': row[19] if len(row) > 19 else None
        }
        
        # الحقول الجديدة
        if len(row) > 13:
            task_dict['deal_id'] = row[13]
        if len(row) > 14:
            task_dict['recurrence_pattern'] = row[14]
        if len(row) > 15:
            task_dict['recurrence_interval'] = row[15]
        if len(row) > 16:
            task_dict['parent_task_id'] = row[16]
        
        tasks.append(task_dict)
    
    return tasks


def get_tasks_due_today() -> List[Dict]:
    """الحصول على المهام المستحقة اليوم"""
    today_str = datetime.now().strftime("%d/%m/%Y")
    
    init_tasks_table()
    
    conn = get_connection()
    cur = conn.cursor()
    
    cur.execute("""
    SELECT 
        t.id, t.client_id, t.title, t.description, t.task_type,
        t.priority, t.status, t.due_date, t.reminder_date,
        t.completed_date, t.created_at, t.updated_at, t.notes,
        t.deal_id, t.recurrence_pattern, t.recurrence_interval, t.parent_task_id,
        c.company_name, c.email, c.phone
    FROM tasks t
    JOIN clients c ON t.client_id = c.id
    WHERE t.status = 'pending' AND t.due_date = ?
    ORDER BY 
        CASE t.priority
            WHEN 'urgent' THEN 1
            WHEN 'high' THEN 2
            WHEN 'medium' THEN 3
            WHEN 'low' THEN 4
        END
    """, (today_str,))
    
    rows = cur.fetchall()
    conn.close()
    
    tasks = []
    for row in rows:
        task_dict = {
            'id': row[0],
            'client_id': row[1],
            'title': row[2],
            'description': row[3],
            'task_type': row[4],
            'priority': row[5],
            'status': row[6],
            'due_date': row[7],
            'reminder_date': row[8],
            'completed_date': row[9],
            'created_at': row[10],
            'updated_at': row[11],
            'notes': row[12],
            'company_name': row[17] if len(row) > 17 else 'Unknown',
            'email': row[18] if len(row) > 18 else None,
            'phone': row[19] if len(row) > 19 else None
        }
        
        # الحقول الجديدة
        if len(row) > 13:
            task_dict['deal_id'] = row[13]
        if len(row) > 14:
            task_dict['recurrence_pattern'] = row[14]
        if len(row) > 15:
            task_dict['recurrence_interval'] = row[15]
        if len(row) > 16:
            task_dict['parent_task_id'] = row[16]
        
        tasks.append(task_dict)
    
    return tasks


def get_reminders_due() -> List[Dict]:
    """الحصول على التذكيرات المستحقة"""
    init_tasks_table()
    
    conn = get_connection()
    cur = conn.cursor()
    
    today_str = datetime.now().strftime("%d/%m/%Y")
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    cur.execute("""
    SELECT 
        t.id, t.client_id, t.title, t.description, t.task_type,
        t.priority, t.status, t.due_date, t.reminder_date,
        t.completed_date, t.created_at, t.updated_at, t.notes,
        c.company_name, c.email, c.phone
    FROM tasks t
    JOIN clients c ON t.client_id = c.id
    WHERE t.status = 'pending' 
      AND t.reminder_date IS NOT NULL 
      AND (t.reminder_date <= ? OR t.reminder_date <= ?)
    ORDER BY t.reminder_date ASC
    """, (today_str, now_str))
    
    rows = cur.fetchall()
    conn.close()
    
    tasks = []
    for row in rows:
        tasks.append({
            'id': row[0],
            'client_id': row[1],
            'title': row[2],
            'description': row[3],
            'task_type': row[4],
            'priority': row[5],
            'status': row[6],
            'due_date': row[7],
            'reminder_date': row[8],
            'completed_date': row[9],
            'created_at': row[10],
            'updated_at': row[11],
            'notes': row[12],
            'company_name': row[13],
            'email': row[14],
            'phone': row[15]
        })
    
    return tasks


def complete_task(task_id: int):
    """إكمال مهمة"""
    update_task(task_id, status=STATUS_COMPLETED)


def get_task_statistics() -> Dict:
    """الحصول على إحصائيات المهام"""
    init_tasks_table()
    
    conn = get_connection()
    cur = conn.cursor()
    
    stats = {
        'total': 0,
        'pending': 0,
        'in_progress': 0,
        'completed': 0,
        'cancelled': 0,
        'overdue': 0,
        'due_today': 0,
        'upcoming_7_days': 0,
        'by_priority': {
            'urgent': 0,
            'high': 0,
            'medium': 0,
            'low': 0
        },
        'by_type': {}
    }
    
    # إحصائيات عامة
    cur.execute("SELECT status, COUNT(*) FROM tasks GROUP BY status")
    for status, count in cur.fetchall():
        stats['total'] += count
        if status in stats:
            stats[status] = count
    
    # إحصائيات الأولوية
    cur.execute("SELECT priority, COUNT(*) FROM tasks WHERE status != 'completed' GROUP BY priority")
    for priority, count in cur.fetchall():
        if priority in stats['by_priority']:
            stats['by_priority'][priority] = count
    
    # إحصائيات النوع
    cur.execute("SELECT task_type, COUNT(*) FROM tasks WHERE status != 'completed' GROUP BY task_type")
    for task_type, count in cur.fetchall():
        stats['by_type'][task_type] = count
    
    # المهام المتأخرة
    overdue = get_overdue_tasks()
    stats['overdue'] = len(overdue)
    
    # المهام المستحقة اليوم
    due_today = get_tasks_due_today()
    stats['due_today'] = len(due_today)
    
    # المهام القادمة في 7 أيام
    upcoming = get_upcoming_tasks(7)
    stats['upcoming_7_days'] = len(upcoming)
    
    conn.close()
    
    return stats


def calculate_next_recurrence_date(current_date: datetime, pattern: str, interval: int) -> datetime:
    """
    حساب تاريخ التكرار التالي بناءً على النمط والفترة
    
    Args:
        current_date: التاريخ الحالي
        pattern: نمط التكرار (daily/weekly/monthly)
        interval: فترة التكرار (عدد الأيام/الأسابيع/الأشهر)
    
    Returns:
        datetime: التاريخ الجديد
    """
    if pattern == "daily":
        return current_date + timedelta(days=interval)
    
    elif pattern == "weekly":
        return current_date + timedelta(weeks=interval)
    
    elif pattern == "monthly":
        # إضافة عدد الأشهر
        month = current_date.month + interval
        year = current_date.year
        
        # معالجة تجاوز السنة
        while month > 12:
            month -= 12
            year += 1
        
        # الحصول على آخر يوم في الشهر الجديد
        last_day = calendar.monthrange(year, month)[1]
        day = min(current_date.day, last_day)
        
        return datetime(year, month, day)
    
    else:
        # افتراضي: يومي
        return current_date + timedelta(days=interval)


def create_recurring_task_occurrences():
    """
    إنشاء المهام المتكررة تلقائياً
    يتم استدعاؤها بشكل دوري لإنشاء المهام الجديدة بناءً على المهام المتكررة المكتملة
    """
    init_tasks_table()
    conn = get_connection()
    cur = conn.cursor()
    
    # البحث عن المهام المتكررة المكتملة التي تحتاج إلى إنشاء مهمة جديدة
    cur.execute("""
        SELECT id, client_id, title, description, task_type, priority,
               due_date, reminder_date, notes, deal_id, recurrence_pattern, recurrence_interval
        FROM tasks
        WHERE status = ?
          AND recurrence_pattern IS NOT NULL
          AND recurrence_pattern != 'none'
          AND parent_task_id IS NULL
    """, (STATUS_COMPLETED,))
    
    completed_recurring_tasks = cur.fetchall()
    created_count = 0
    
    for task in completed_recurring_tasks:
        task_id, client_id, title, description, task_type, priority, \
        due_date_str, reminder_date_str, notes, deal_id, recurrence_pattern, recurrence_interval = task
        
        try:
            # تحويل تاريخ الاستحقاق
            due_date = datetime.strptime(due_date_str, "%d/%m/%Y")
            
            # حساب التاريخ الجديد بناءً على نمط التكرار
            new_due_date = calculate_next_recurrence_date(
                due_date, recurrence_pattern, recurrence_interval or 1
            )
            
            # حساب تاريخ التذكير الجديد (نفس الفترة قبل التاريخ الجديد)
            new_reminder_date = None
            if reminder_date_str:
                try:
                    reminder_date = datetime.strptime(reminder_date_str, "%d/%m/%Y")
                    days_before = (due_date - reminder_date).days
                    new_reminder_date = new_due_date - timedelta(days=days_before)
                except:
                    pass
            
            # إنشاء المهمة الجديدة
            new_task_id = create_task(
                client_id=client_id,
                title=title,
                description=description,
                task_type=task_type,
                priority=priority,
                due_date=new_due_date.strftime("%d/%m/%Y"),
                reminder_date=new_reminder_date.strftime("%d/%m/%Y") if new_reminder_date else None,
                notes=notes,
                deal_id=deal_id,
                recurrence_pattern=recurrence_pattern,
                recurrence_interval=recurrence_interval
            )
            
            # ربط المهمة الجديدة بالمهمة الأصلية
            cur.execute("UPDATE tasks SET parent_task_id = ? WHERE id = ?", (task_id, new_task_id))
            
            created_count += 1
            
        except Exception as e:
            print(f"Error creating recurring task for task {task_id}: {str(e)}")
            continue
    
    conn.commit()
    conn.close()
    
    return created_count

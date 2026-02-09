"""
منطق إنشاء المهام المتكررة تلقائياً
Recurring Tasks Auto-Creation Logic
"""
from datetime import datetime, timedelta
import calendar
from core.tasks import (
    create_task, STATUS_COMPLETED, init_tasks_table
)
from core.db import get_connection


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

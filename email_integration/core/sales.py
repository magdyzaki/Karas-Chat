"""
نظام إدارة المبيعات
Sales Management System for EFM
"""
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from collections import defaultdict

from .db import get_connection


# مراحل المبيعات (Pipeline Stages)
SALES_STAGES = [
    "Lead",           # عميل محتمل
    "Qualified",      # مؤهل
    "Proposal",       # عرض
    "Negotiation",    # مفاوضات
    "Closed Won",     # مكتمل - مكسب
    "Closed Lost"     # مكتمل - خسارة
]

# احتمالات التحويل لكل مرحلة
STAGE_PROBABILITY = {
    "Lead": 0.1,
    "Qualified": 0.25,
    "Proposal": 0.50,
    "Negotiation": 0.75,
    "Closed Won": 1.0,
    "Closed Lost": 0.0
}


def init_sales_table():
    """تهيئة جدول الصفقات/المبيعات"""
    conn = get_connection()
    cur = conn.cursor()
    
    cur.execute("""
        CREATE TABLE IF NOT EXISTS sales_deals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER NOT NULL,
            deal_name TEXT NOT NULL,
            product_name TEXT,
            stage TEXT DEFAULT 'Lead',
            value REAL DEFAULT 0,
            currency TEXT DEFAULT 'USD',
            probability REAL DEFAULT 0.1,
            expected_close_date TEXT,
            actual_close_date TEXT,
            status TEXT DEFAULT 'active',
            notes TEXT,
            created_date TEXT,
            updated_date TEXT,
            created_by TEXT,
            FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE
        )
    """)
    
    # إضافة عمود product_name إن لم يكن موجوداً
    try:
        cur.execute("ALTER TABLE sales_deals ADD COLUMN product_name TEXT")
    except:
        pass  # العمود موجود بالفعل
    
    # جدول تاريخ تغيير المراحل
    cur.execute("""
        CREATE TABLE IF NOT EXISTS deal_stage_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            deal_id INTEGER NOT NULL,
            from_stage TEXT,
            to_stage TEXT,
            changed_date TEXT,
            changed_by TEXT,
            notes TEXT,
            FOREIGN KEY (deal_id) REFERENCES sales_deals(id) ON DELETE CASCADE
        )
    """)
    
    conn.commit()
    conn.close()


def add_sale_deal(data: dict) -> int:
    """
    إضافة صفقة جديدة
    
    Args:
        data: Dictionary containing deal data
    
    Returns:
        Deal ID
    """
    init_sales_table()
    conn = get_connection()
    cur = conn.cursor()
    
    stage = data.get("stage", "Lead")
    probability = data.get("probability", STAGE_PROBABILITY.get(stage, 0.1))
    
    cur.execute("""
        INSERT INTO sales_deals (
            client_id, deal_name, product_name, stage, value, currency,
            probability, expected_close_date, actual_close_date,
            status, notes, created_date, updated_date, created_by
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data["client_id"],
        data["deal_name"],
        data.get("product_name"),
        stage,
        data.get("value", 0),
        data.get("currency", "USD"),
        probability,
        data.get("expected_close_date"),
        data.get("actual_close_date"),
        data.get("status", "active"),
        data.get("notes"),
        datetime.now().strftime("%d/%m/%Y %H:%M"),
        datetime.now().strftime("%d/%m/%Y %H:%M"),
        data.get("created_by", "User")
    ))
    
    deal_id = cur.lastrowid
    
    # تسجيل المرحلة الأولية في التاريخ
    cur.execute("""
        INSERT INTO deal_stage_history (
            deal_id, from_stage, to_stage, changed_date, changed_by
        )
        VALUES (?, ?, ?, ?, ?)
    """, (
        deal_id,
        None,
        stage,
        datetime.now().strftime("%d/%m/%Y %H:%M"),
        data.get("created_by", "User")
    ))
    
    conn.commit()
    conn.close()
    return deal_id


def update_sale_deal(deal_id: int, data: dict):
    """تحديث صفقة"""
    init_sales_table()
    conn = get_connection()
    cur = conn.cursor()
    
    # الحصول على المرحلة القديمة
    cur.execute("SELECT stage FROM sales_deals WHERE id=?", (deal_id,))
    old_stage_result = cur.fetchone()
    old_stage = old_stage_result[0] if old_stage_result else None
    
    new_stage = data.get("stage")
    probability = data.get("probability")
    
    # إذا تغيرت المرحلة، تحديث الاحتمالية تلقائياً
    if new_stage and new_stage != old_stage:
        if probability is None:
            probability = STAGE_PROBABILITY.get(new_stage, 0.1)
        
        # تسجيل التغيير في التاريخ
        cur.execute("""
            INSERT INTO deal_stage_history (
                deal_id, from_stage, to_stage, changed_date, changed_by, notes
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            deal_id,
            old_stage,
            new_stage,
            datetime.now().strftime("%d/%m/%Y %H:%M"),
            data.get("updated_by", "User"),
            data.get("stage_change_notes")
        ))
    
    # تحديث البيانات
    updates = []
    values = []
    
    if "deal_name" in data:
        updates.append("deal_name = ?")
        values.append(data["deal_name"])
    
    if "product_name" in data:
        updates.append("product_name = ?")
        values.append(data["product_name"])
    
    if "stage" in data:
        updates.append("stage = ?")
        values.append(new_stage)
    
    if "value" in data:
        updates.append("value = ?")
        values.append(data["value"])
    
    if "currency" in data:
        updates.append("currency = ?")
        values.append(data["currency"])
    
    if "probability" in data or new_stage:
        updates.append("probability = ?")
        values.append(probability)
    
    if "expected_close_date" in data:
        updates.append("expected_close_date = ?")
        values.append(data["expected_close_date"])
    
    if "actual_close_date" in data:
        updates.append("actual_close_date = ?")
        values.append(data["actual_close_date"])
    
    if "status" in data:
        updates.append("status = ?")
        values.append(data["status"])
    
    if "notes" in data:
        updates.append("notes = ?")
        values.append(data["notes"])
    
    updates.append("updated_date = ?")
    values.append(datetime.now().strftime("%d/%m/%Y %H:%M"))
    values.append(deal_id)
    
    if updates:
        query = f"UPDATE sales_deals SET {', '.join(updates)} WHERE id = ?"
        cur.execute(query, values)
    
    conn.commit()
    conn.close()


def get_deal_by_id(deal_id: int):
    """الحصول على صفقة بواسطة ID"""
    init_sales_table()
    conn = get_connection()
    cur = conn.cursor()
    
    cur.execute("""
        SELECT 
            d.id, d.client_id, c.company_name, d.deal_name, d.product_name,
            d.stage, d.value, d.currency, d.probability,
            d.expected_close_date, d.actual_close_date,
            d.status, d.notes, d.created_date, d.updated_date
        FROM sales_deals d
        LEFT JOIN clients c ON d.client_id = c.id
        WHERE d.id = ?
    """, (deal_id,))
    
    row = cur.fetchone()
    conn.close()
    return row


def get_all_deals(status: str = "active"):
    """الحصول على جميع الصفقات"""
    init_sales_table()
    conn = get_connection()
    cur = conn.cursor()
    
    query = """
        SELECT 
            d.id, d.client_id, c.company_name, d.deal_name, d.product_name,
            d.stage, d.value, d.currency, d.probability,
            d.expected_close_date, d.actual_close_date,
            d.status, d.notes, d.created_date, d.updated_date
        FROM sales_deals d
        LEFT JOIN clients c ON d.client_id = c.id
    """
    
    if status:
        query += " WHERE d.status = ?"
        cur.execute(query, (status,))
    else:
        query += " ORDER BY d.created_date DESC"
        cur.execute(query)
    
    rows = cur.fetchall()
    conn.close()
    return rows


def get_deals_by_stage(stage: str):
    """الحصول على الصفقات حسب المرحلة"""
    init_sales_table()
    conn = get_connection()
    cur = conn.cursor()
    
    cur.execute("""
        SELECT 
            d.id, d.client_id, c.company_name, d.deal_name, d.product_name,
            d.stage, d.value, d.currency, d.probability,
            d.expected_close_date, d.actual_close_date,
            d.status
        FROM sales_deals d
        LEFT JOIN clients c ON d.client_id = c.id
        WHERE d.stage = ? AND d.status = 'active'
        ORDER BY d.value DESC
    """, (stage,))
    
    rows = cur.fetchall()
    conn.close()
    return rows


def get_pipeline_statistics() -> Dict:
    """الحصول على إحصائيات Pipeline"""
    init_sales_table()
    conn = get_connection()
    cur = conn.cursor()
    
    stats = {
        'by_stage': {},
        'total_value': 0,
        'weighted_value': 0,  # القيمة المرجحة (value * probability)
        'total_deals': 0
    }
    
    for stage in SALES_STAGES:
        cur.execute("""
            SELECT COUNT(*), COALESCE(SUM(value), 0), COALESCE(SUM(value * probability), 0)
            FROM sales_deals
            WHERE stage = ? AND status = 'active'
        """, (stage,))
        
        count, total_value, weighted_value = cur.fetchone()
        stats['by_stage'][stage] = {
            'count': count,
            'total_value': total_value or 0,
            'weighted_value': weighted_value or 0
        }
        stats['total_value'] += total_value or 0
        stats['weighted_value'] += weighted_value or 0
        stats['total_deals'] += count
    
    conn.close()
    return stats


def get_sales_revenue_forecast(months: int = 12) -> Dict:
    """
    توقع الإيرادات
    
    Args:
        months: عدد الأشهر للتنبؤ
    
    Returns:
        Dictionary containing revenue forecast
    """
    init_sales_table()
    conn = get_connection()
    cur = conn.cursor()
    
    forecast = {
        'by_month': defaultdict(float),
        'total_forecast': 0,
        'weighted_forecast': 0
    }
    
    # الصفقات المكتملة (Closed Won) حسب الشهر
    cur.execute("""
        SELECT 
            SUBSTR(actual_close_date, 7, 4) || '-' || 
            SUBSTR(actual_close_date, 4, 2) AS month,
            SUM(value) AS total
        FROM sales_deals
        WHERE status = 'active' AND stage = 'Closed Won' 
          AND actual_close_date IS NOT NULL
        GROUP BY month
        ORDER BY month DESC
        LIMIT ?
    """, (months,))
    
    for month, total in cur.fetchall():
        if month:
            forecast['by_month'][month] = total or 0
            forecast['total_forecast'] += total or 0
    
    # الصفقات المتوقعة حسب expected_close_date
    cur.execute("""
        SELECT 
            SUBSTR(expected_close_date, 7, 4) || '-' || 
            SUBSTR(expected_close_date, 4, 2) AS month,
            SUM(value) AS total,
            SUM(value * probability) AS weighted
        FROM sales_deals
        WHERE status = 'active' 
          AND stage != 'Closed Won' 
          AND stage != 'Closed Lost'
          AND expected_close_date IS NOT NULL
        GROUP BY month
        ORDER BY month DESC
        LIMIT ?
    """, (months,))
    
    for month, total, weighted in cur.fetchall():
        if month:
            forecast['by_month'][month] = forecast['by_month'].get(month, 0) + (total or 0)
            forecast['total_forecast'] += total or 0
            forecast['weighted_forecast'] += weighted or 0
    
    conn.close()
    return forecast


def get_sales_reports(period: str = "monthly") -> Dict:
    """
    تقارير المبيعات
    
    Args:
        period: 'monthly' or 'yearly'
    
    Returns:
        Dictionary containing sales reports
    """
    init_sales_table()
    conn = get_connection()
    cur = conn.cursor()
    
    reports = {
        'period': period,
        'by_period': {},
        'total_revenue': 0,
        'total_deals': 0,
        'won_deals': 0,
        'lost_deals': 0,
        'conversion_rate': 0
    }
    
    if period == "monthly":
        date_format = "SUBSTR(actual_close_date, 7, 4) || '-' || SUBSTR(actual_close_date, 4, 2)"
    else:  # yearly
        date_format = "SUBSTR(actual_close_date, 7, 4)"
    
    # الصفقات المكتملة
    cur.execute(f"""
        SELECT 
            {date_format} AS period,
            COUNT(*) AS count,
            SUM(value) AS revenue
        FROM sales_deals
        WHERE stage = 'Closed Won' 
          AND actual_close_date IS NOT NULL
          AND status = 'active'
        GROUP BY period
        ORDER BY period DESC
        LIMIT 24
    """)
    
    for period_key, count, revenue in cur.fetchall():
        if period_key:
            reports['by_period'][period_key] = {
                'revenue': revenue or 0,
                'deals': count
            }
            reports['total_revenue'] += revenue or 0
            reports['total_deals'] += count
            reports['won_deals'] += count
    
    # الصفقات الخاسرة
    cur.execute(f"""
        SELECT 
            {date_format} AS period,
            COUNT(*) AS count
        FROM sales_deals
        WHERE stage = 'Closed Lost'
          AND actual_close_date IS NOT NULL
          AND status = 'active'
        GROUP BY period
        ORDER BY period DESC
        LIMIT 24
    """)
    
    for period_key, count in cur.fetchall():
        if period_key:
            if period_key not in reports['by_period']:
                reports['by_period'][period_key] = {'revenue': 0, 'deals': 0}
            reports['by_period'][period_key]['lost'] = count
            reports['lost_deals'] += count
    
    # معدل التحويل
    if reports['won_deals'] + reports['lost_deals'] > 0:
        reports['conversion_rate'] = (reports['won_deals'] / (reports['won_deals'] + reports['lost_deals'])) * 100
    
    conn.close()
    return reports


def get_conversion_analysis() -> Dict:
    """
    تحليل معدل التحويل
    
    Returns:
        Dictionary containing conversion analysis
    """
    init_sales_table()
    conn = get_connection()
    cur = conn.cursor()
    
    analysis = {
        'stage_conversion': {},
        'overall_conversion': 0,
        'average_time_per_stage': {},
        'win_rate': 0,
        'loss_rate': 0
    }
    
    # عدد الصفقات في كل مرحلة
    stage_counts = {}
    for stage in SALES_STAGES:
        cur.execute("""
            SELECT COUNT(*) FROM sales_deals
            WHERE stage = ? AND status = 'active'
        """, (stage,))
        stage_counts[stage] = cur.fetchone()[0]
    
    # حساب معدل التحويل بين المراحل
    for i in range(len(SALES_STAGES) - 1):
        current_stage = SALES_STAGES[i]
        next_stage = SALES_STAGES[i + 1]
        
        current_count = stage_counts[current_stage]
        next_count = stage_counts[next_stage]
        
        if current_count > 0:
            conversion_rate = (next_count / current_count) * 100
            analysis['stage_conversion'][f"{current_stage} -> {next_stage}"] = conversion_rate
    
    # معدل التحويل الإجمالي (من Lead إلى Closed Won)
    total_leads = stage_counts.get("Lead", 0)
    total_won = stage_counts.get("Closed Won", 0)
    
    if total_leads > 0:
        analysis['overall_conversion'] = (total_won / total_leads) * 100
    
    # Win Rate و Loss Rate
    total_closed = stage_counts.get("Closed Won", 0) + stage_counts.get("Closed Lost", 0)
    if total_closed > 0:
        analysis['win_rate'] = (stage_counts.get("Closed Won", 0) / total_closed) * 100
        analysis['loss_rate'] = (stage_counts.get("Closed Lost", 0) / total_closed) * 100
    
    conn.close()
    return analysis


def delete_deal(deal_id: int):
    """حذف صفقة"""
    init_sales_table()
    conn = get_connection()
    cur = conn.cursor()
    
    cur.execute("DELETE FROM deal_stage_history WHERE deal_id = ?", (deal_id,))
    cur.execute("DELETE FROM sales_deals WHERE id = ?", (deal_id,))
    
    conn.commit()
    conn.close()

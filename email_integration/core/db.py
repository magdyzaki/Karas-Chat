import sqlite3
import os
import re
from datetime import datetime

# استخدام قاعدة بيانات CRM الحالية بدلاً من efm.db
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
DB_PATH = os.path.join(BASE_DIR, "database", "crm.db")


# =========================
# Connection
# =========================
def get_connection():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    return sqlite3.connect(DB_PATH)


# =========================
# Init & Migration
# =========================
def init_db():
    conn = get_connection()
    cur = conn.cursor()

    # استخدام جدول customers الموجود في CRM بدلاً من إنشاء جدول clients جديد
    # إذا لم يكن جدول customers موجوداً، ننشئ جدول clients
    cur.execute("""
    CREATE TABLE IF NOT EXISTS clients (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        company_name TEXT NOT NULL,
        country TEXT,
        contact_person TEXT,
        email TEXT,
        phone TEXT,
        website TEXT,
        date_added TEXT,
        status TEXT,
        seriousness_score INTEGER DEFAULT 0,
        classification TEXT,
        is_focus INTEGER DEFAULT 0
    )
    """)
    
    # إنشاء جدول mapping للربط بين clients و customers إذا لزم الأمر
    cur.execute("""
    CREATE TABLE IF NOT EXISTS client_customer_mapping (
        client_id INTEGER,
        customer_id INTEGER,
        PRIMARY KEY (client_id, customer_id),
        FOREIGN KEY (client_id) REFERENCES clients(id),
        FOREIGN KEY (customer_id) REFERENCES customers(id)
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        client_id INTEGER,
        message_date TEXT,
        message_type TEXT,
        channel TEXT,
        client_response TEXT,
        notes TEXT,
        score_effect INTEGER DEFAULT 0,
        FOREIGN KEY (client_id) REFERENCES clients(id)
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS requests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        client_id INTEGER,
        client_email TEXT,
        request_type TEXT,
        extracted_text TEXT,
        notes TEXT,
        status TEXT DEFAULT 'open',
        reply_status TEXT DEFAULT 'pending',
        created_at TEXT,
        FOREIGN KEY (client_id) REFERENCES clients(id)

    )
    """)

    # جدول حسابات Outlook
    cur.execute("""
    CREATE TABLE IF NOT EXISTS outlook_accounts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        account_name TEXT NOT NULL UNIQUE,
        email TEXT,
        token_cache_path TEXT,
        is_active INTEGER DEFAULT 1,
        created_at TEXT,
        last_sync TEXT
    )
    """)

    conn.commit()
    conn.close()

    # 👇👇👇 أضف الثلاثة أسطر دول فقط
    ensure_focus_column()
    ensure_requests_email_column()
    ensure_requests_reply_status_column()
    
    # التأكد من وجود حقول حسابات IMAP
    ensure_account_type_columns()
    
    # التأكد من وجود حقل actual_date للرسائل
    ensure_actual_date_column()
    # التأكد من وجود أعمدة الرسائل الأساسية (قد تكون قاعدة البيانات قديمة)
    ensure_messages_columns()
    
    # إضافة حساب Outlook ثابت (contact@el-raee.com)
    ensure_default_outlook_account()
    
    # تهيئة جداول نظام التقييم المتقدم
    try:
        from core.score_history import init_score_history_table
        init_score_history_table()
    except Exception:
        pass
    
    # تهيئة جدول المهام
    try:
        from core.tasks import init_tasks_table
        init_tasks_table()
    except Exception:
        pass
    
    # تهيئة جدول المستندات
    try:
        init_documents_table()
    except Exception:
        pass
    
    # تهيئة جداول المنتجات والعروض
    try:
        init_products_table()
        init_quotes_table()
    except Exception:
        pass
    
    # تهيئة جدول المبيعات
    try:
        from core.sales import init_sales_table
        init_sales_table()
    except Exception:
        pass
    
    # تهيئة أعمدة التواصل المتقدم
    try:
        from core.communication import ensure_communication_columns
        ensure_communication_columns()
    except Exception:
        pass
    
    # تحسينات الأداء - إنشاء الفهارس
    try:
        from core.performance import create_performance_indexes
        create_performance_indexes()
    except Exception:
        pass

    # تهيئة جدول المزامنة المخصصة (مستقل عن جدول clients)
    try:
        ensure_custom_sync_clients_table()
    except Exception:
        pass


def ensure_custom_sync_clients_table():
    """
    جدول مستقل لعملاء/أهداف المزامنة المخصصة.
    - لا يؤثر على جدول clients الرئيسي.
    - الحذف/الإضافة هنا لا تمس البيانات الرئيسية.
    """
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS custom_sync_clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_name TEXT,
            country TEXT,
            contact_person TEXT,
            email TEXT,
            phone TEXT,
            website TEXT,
            date_added TEXT
        )
    """)

    # منع تكرار البريد الإلكتروني (بشكل غير حساس لحالة الأحرف) مع السماح بالقيم الفارغة
    try:
        cur.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS idx_custom_sync_clients_email_lower
            ON custom_sync_clients(LOWER(email))
            WHERE email IS NOT NULL AND email != ''
        """)
    except Exception:
        pass

    conn.commit()
    conn.close()


# =========================
# Custom Sync Clients (Independent)
# =========================
def get_custom_sync_clients():
    ensure_custom_sync_clients_table()
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT
            id,
            company_name,
            country,
            contact_person,
            email,
            phone,
            website,
            date_added
        FROM custom_sync_clients
        ORDER BY id DESC
    """)
    rows = cur.fetchall()
    conn.close()
    return rows


def find_custom_sync_client_by_email(email: str):
    ensure_custom_sync_clients_table()
    if not email:
        return None
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT * FROM custom_sync_clients WHERE LOWER(email)=?",
        (email.lower(),)
    )
    row = cur.fetchone()
    conn.close()
    return row


def add_custom_sync_client(data: dict):
    """
    data keys:
      company_name, country, contact_person, email, phone, website, date_added
    """
    ensure_custom_sync_clients_table()
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO custom_sync_clients (
            company_name, country, contact_person,
            email, phone, website, date_added
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        data.get("company_name"),
        data.get("country"),
        data.get("contact_person"),
        data.get("email"),
        data.get("phone"),
        data.get("website"),
        data.get("date_added"),
    ))
    conn.commit()
    conn.close()


def delete_custom_sync_client(custom_id: int):
    ensure_custom_sync_clients_table()
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM custom_sync_clients WHERE id = ?", (custom_id,))
    conn.commit()
    conn.close()


def ensure_focus_column():
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("ALTER TABLE clients ADD COLUMN is_focus INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        pass
    conn.commit()
    conn.close()


def ensure_requests_email_column():
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("ALTER TABLE requests ADD COLUMN client_email TEXT")
    except sqlite3.OperationalError:
        pass
    conn.commit()
    conn.close()


# =========================
# Clients
# =========================
def add_client(data: dict):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
    INSERT INTO clients (
        company_name, country, contact_person,
        email, phone, website,
        date_added, status,
        seriousness_score, classification, is_focus
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data["company_name"],
        data.get("country"),
        data.get("contact_person"),
        data.get("email"),
        data.get("phone"),
        data.get("website"),
        data["date_added"],
        data["status"],
        data["seriousness_score"],
        data["classification"],
        data.get("is_focus", 0)
    ))
    conn.commit()
    conn.close()


def update_client(client_id: int, data: dict):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
    UPDATE clients SET
        company_name = ?,
        country = ?,
        contact_person = ?,
        email = ?,
        phone = ?,
        website = ?,
        status = ?,
        seriousness_score = ?,
        classification = ?,
        is_focus = ?
    WHERE id = ?
    """, (
        data["company_name"],
        data.get("country"),
        data.get("contact_person"),
        data.get("email"),
        data.get("phone"),
        data.get("website"),
        data.get("status"),
        data.get("seriousness_score"),
        data.get("classification"),
        data.get("is_focus", 0),
        client_id
    ))
    conn.commit()
    conn.close()


def delete_client(client_id: int):
    """
    حذف عميل مع جميع رسائله وطلباته
    """
    conn = get_connection()
    cur = conn.cursor()
    
    try:
        # حساب عدد الرسائل قبل الحذف
        cur.execute("SELECT COUNT(*) FROM messages WHERE client_id=?", (client_id,))
        messages_count_before = cur.fetchone()[0] or 0
        
        # حساب عدد الطلبات قبل الحذف
        cur.execute("SELECT COUNT(*) FROM requests WHERE client_id=?", (client_id,))
        requests_count_before = cur.fetchone()[0] or 0
        
        # تعطيل DEBUG prints لتحسين الأداء (يمكن تفعيلها إذا لزم الأمر)
        # print(f"DEBUG: Deleting client {client_id}: {messages_count_before} messages, {requests_count_before} requests")
        
        # الحصول على جميع message_id المرتبطة بهذا العميل
        cur.execute("SELECT id FROM messages WHERE client_id=?", (client_id,))
        message_ids = [row[0] for row in cur.fetchall()]
        # print(f"DEBUG: Found {len(message_ids)} message IDs to delete")
        
        # حذف سجلات score_history المرتبطة بالرسائل أولاً (إذا كان الجدول موجود)
        if message_ids:
            try:
                placeholders = ','.join('?' * len(message_ids))
                cur.execute(f"DELETE FROM score_history WHERE message_id IN ({placeholders})", message_ids)
                score_history_deleted = cur.rowcount
                # print(f"DEBUG: Deleted {score_history_deleted} score_history records")
            except Exception as e:
                pass  # قد لا يكون جدول score_history موجود
        
        # حذف جميع الرسائل المرتبطة - استخدام حلقة للتأكد من حذف جميع الرسائل
        messages_deleted = 0
        max_iterations = 50  # حماية من الحلقات اللانهائية
        iteration = 0
        
        while iteration < max_iterations:
            # التحقق من عدد الرسائل المتبقية
            cur.execute("SELECT COUNT(*) FROM messages WHERE client_id=?", (client_id,))
            remaining_count = cur.fetchone()[0] or 0
            
            if remaining_count == 0:
                # print(f"DEBUG: All messages deleted after {iteration} iterations")
                break  # لا توجد رسائل متبقية
            
            # حذف جميع الرسائل دفعة واحدة
            cur.execute("DELETE FROM messages WHERE client_id = ?", (client_id,))
            deleted_count = cur.rowcount
            messages_deleted += deleted_count
            
            # print(f"DEBUG: Iteration {iteration + 1}: Deleted {deleted_count} messages, {remaining_count - deleted_count} remaining")
            
            iteration += 1
        
        # التحقق النهائي
        cur.execute("SELECT COUNT(*) FROM messages WHERE client_id=?", (client_id,))
        final_remaining = cur.fetchone()[0] or 0
        if final_remaining > 0:
            # محاولة حذف نهائية باستخدام message_ids مباشرة
            if message_ids:
                placeholders = ','.join('?' * len(message_ids))
                cur.execute(f"DELETE FROM messages WHERE id IN ({placeholders})", message_ids)
                final_deleted = cur.rowcount
                messages_deleted += final_deleted
        
        # استخدام messages_count_before كعدد الرسائل المحذوفة إذا كان rowcount غير موثوق
        if messages_count_before > 0 and messages_deleted == 0:
            messages_deleted = messages_count_before
        
        # حذف جميع الطلبات المرتبطة دفعة واحدة
        cur.execute("DELETE FROM requests WHERE client_id = ?", (client_id,))
        # استخدام requests_count_before كعدد الطلبات المحذوفة لأن rowcount قد لا يعمل بشكل صحيح في SQLite
        requests_deleted = requests_count_before
        
        # التحقق من أن جميع الطلبات تم حذفها
        cur.execute("SELECT COUNT(*) FROM requests WHERE client_id=?", (client_id,))
        remaining_requests = cur.fetchone()[0] or 0
        if remaining_requests > 0:
            cur.execute("DELETE FROM requests WHERE client_id = ?", (client_id,))
        
        # حذف المهام المرتبطة (إن وجدت)
        tasks_deleted = 0
        try:
            cur.execute("SELECT COUNT(*) FROM tasks WHERE client_id=?", (client_id,))
            tasks_count_before = cur.fetchone()[0] or 0
            cur.execute("DELETE FROM tasks WHERE client_id = ?", (client_id,))
            tasks_deleted = cur.rowcount
            if tasks_count_before > 0 and tasks_deleted == 0:
                tasks_deleted = tasks_count_before
        except:
            pass  # قد لا يكون جدول المهام موجود
        
        # حذف المستندات المرتبطة (إن وجدت)
        documents_deleted = 0
        try:
            cur.execute("SELECT COUNT(*) FROM documents WHERE client_id=?", (client_id,))
            documents_count_before = cur.fetchone()[0] or 0
            cur.execute("DELETE FROM documents WHERE client_id = ?", (client_id,))
            documents_deleted = cur.rowcount
            if documents_count_before > 0 and documents_deleted == 0:
                documents_deleted = documents_count_before
        except:
            pass  # قد لا يكون جدول المستندات موجود
        
        # حذف الصفقات المرتبطة (إن وجدت)
        deals_deleted = 0
        try:
            cur.execute("SELECT COUNT(*) FROM sales_deals WHERE client_id=?", (client_id,))
            deals_count_before = cur.fetchone()[0] or 0
            cur.execute("DELETE FROM sales_deals WHERE client_id = ?", (client_id,))
            deals_deleted = cur.rowcount
            if deals_count_before > 0 and deals_deleted == 0:
                deals_deleted = deals_count_before
        except:
            pass  # قد لا يكون جدول الصفقات موجود
        
        # حذف العميل
        cur.execute("DELETE FROM clients WHERE id = ?", (client_id,))
        client_deleted = cur.rowcount
        
        # print(f"DEBUG: Deleted: {messages_deleted} messages, {requests_deleted} requests, {tasks_deleted} tasks, {documents_deleted} documents, {deals_deleted} deals, {client_deleted} client")
        
        conn.commit()
        
        return {
            'success': True,
            'messages_deleted': messages_deleted,
            'requests_deleted': requests_deleted,
            'tasks_deleted': tasks_deleted,
            'documents_deleted': documents_deleted,
            'deals_deleted': deals_deleted,
            'messages_count_before': messages_count_before,
            'requests_count_before': requests_count_before
        }
    
    except Exception as e:
        conn.rollback()
        import traceback
        error_msg = f"{str(e)}\n\n{traceback.format_exc()}"
        # print(f"DEBUG ERROR in delete_client: {error_msg}")
        raise e
    
    finally:
        conn.close()


def get_all_clients():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            id,
            company_name,
            country,
            contact_person,
            email,
            phone,
            website,
            date_added,
            status,
            seriousness_score,
            COALESCE(classification, 'Unclassified') AS classification,
            is_focus
        FROM clients
        ORDER BY is_focus DESC, seriousness_score DESC
    """)

    rows = cur.fetchall()
    conn.close()
    return rows


def get_client_by_id(client_id: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM clients WHERE id=?", (client_id,))
    row = cur.fetchone()
    conn.close()
    return row


def find_client_by_email(email: str):
    if not email:
        return None
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM clients WHERE LOWER(email)=?", (email.lower(),))
    row = cur.fetchone()
    conn.close()
    return row


def find_client_by_domain(domain: str):
    if not domain:
        return None
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT * FROM clients WHERE LOWER(email) LIKE ?",
        (f"%@{domain.lower()}",)
    )
    row = cur.fetchone()
    conn.close()
    return row


def get_focus_emails():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT email FROM clients WHERE is_focus=1")
    emails = [r[0].lower() for r in cur.fetchall()]
    conn.close()
    return emails


# =========================
# Messages
# =========================
def add_message(data: dict):
    # تأكد أن الأعمدة المطلوبة موجودة قبل الإدخال (خاصة بعد ترحيل قاعدة بيانات قديمة)
    try:
        ensure_messages_columns()
    except Exception:
        pass

    conn = get_connection()
    cur = conn.cursor()

    # فحص التكرار: التحقق من وجود رسالة مكررة
    # نفحص بناءً على: client_id, actual_date/message_date, client_response (الموضوع)
    actual_date = data.get("actual_date")
    message_date = data.get("message_date")
    client_response = data.get("client_response") or ""
    notes = data.get("notes") or ""
    
    # استخدام التاريخ الفعلي إن وجد، وإلا استخدام message_date
    check_date = actual_date or message_date
    
    if check_date:
        # فحص التكرار بناءً على التاريخ والموضوع
        cur.execute("""
            SELECT id FROM messages
            WHERE client_id = ? 
            AND (actual_date = ? OR (actual_date IS NULL AND message_date = ?))
            AND client_response = ?
            LIMIT 1
        """, (data["client_id"], check_date, check_date, client_response))
        
        existing = cur.fetchone()
        if existing:
            # رسالة مكررة موجودة بالفعل
            conn.close()
            return existing[0]  # إرجاع ID الرسالة الموجودة
    
    # إذا لم يكن هناك تكرار، نفحص أيضاً بناءً على جزء من المحتوى (أول 100 حرف)
    if notes:
        notes_preview = notes[:100] if len(notes) > 100 else notes
        cur.execute("""
            SELECT id FROM messages
            WHERE client_id = ? 
            AND client_response = ?
            AND (notes LIKE ? OR notes = ?)
            LIMIT 1
        """, (data["client_id"], client_response, f"{notes_preview}%", notes))
        
        existing = cur.fetchone()
        if existing:
            # رسالة مكررة موجودة بالفعل
            conn.close()
            return existing[0]  # إرجاع ID الرسالة الموجودة

    # الحصول على النقاط الحالية للعميل قبل التحديث
    cur.execute("SELECT seriousness_score, classification FROM clients WHERE id = ?", (data["client_id"],))
    old_data = cur.fetchone()
    old_score = old_data[0] if old_data else 0
    old_classification = old_data[1] if old_data else ""

    # إضافة الرسالة
    cur.execute("""
    INSERT INTO messages (
        client_id, message_date, actual_date,
        message_type, channel,
        client_response, notes,
        score_effect
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data["client_id"],
        data["message_date"],
        actual_date,  # التاريخ الفعلي للرسالة من البريد
        data["message_type"],
        data["channel"],
        client_response,
        notes,
        data["score_effect"]
    ))
    
    message_id = cur.lastrowid

    # تحديث النقاط
    cur.execute("""
        UPDATE clients
        SET seriousness_score = seriousness_score + ?
        WHERE id = ?
    """, (data["score_effect"], data["client_id"]))

    # الحصول على النقاط الجديدة والتصنيف الجديد
    cur.execute("SELECT seriousness_score FROM clients WHERE id = ?", (data["client_id"],))
    new_data = cur.fetchone()
    new_score = new_data[0] if new_data else old_score

    # تصنيف العميل بناءً على النقاط الجديدة
    from core.models import classify_client
    new_classification = classify_client(new_score)

    # تحديث التصنيف
    cur.execute("""
        UPDATE clients
        SET classification = ?
        WHERE id = ?
    """, (new_classification, data["client_id"]))

    conn.commit()
    conn.close()

    # تسجيل تغيير النقاط في السجل (إذا كان التتبع مفعّل)
    try:
        from core.score_history import record_score_change
        from core.scoring_config import is_trend_analysis_enabled
        
        if is_trend_analysis_enabled():
            change_reason = f"رسالة: {data.get('message_type', 'Unknown')} - {data.get('notes', '')}"
            record_score_change(
                client_id=data["client_id"],
                new_score=new_score,
                classification=new_classification,
                change_reason=change_reason[:200],  # حد أقصى 200 حرف
                message_id=message_id
            )
    except Exception:
        pass  # إذا فشل التسجيل، لا نوقف العملية

    # التحقق من تغيير التصنيف وإرسال تنبيه
    try:
        from core.classification_alerts import check_classification_change
        from core.scoring_config import is_trend_analysis_enabled
        
        if old_classification != new_classification and is_trend_analysis_enabled():
            check_classification_change(
                client_id=data["client_id"],
                old_score=old_score,
                new_score=new_score,
                old_classification=old_classification or "❌ Not Serious",
                new_classification=new_classification,
                change_reason=f"رسالة: {data.get('message_type', 'Unknown')}",
                message_id=message_id,
                show_alert=False  # سنعرض التنبيه من واجهة المستخدم
            )
    except Exception:
        pass


def get_client_messages(client_id: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT message_date, actual_date, message_type, channel,
               client_response, notes, score_effect
        FROM messages
        WHERE client_id=?
        ORDER BY COALESCE(actual_date, message_date) DESC, id DESC
    """, (client_id,))
    rows = cur.fetchall()
    conn.close()
    
    # إزالة التكرارات من النتائج (بناءً على التاريخ والموضوع)
    seen = set()
    unique_rows = []
    for row in rows:
        (message_date, actual_date, message_type, channel, 
         client_response, notes, score_effect) = row
        
        # استخدام التاريخ الفعلي إن وجد
        date_key = actual_date or message_date or ""
        subject_key = client_response or ""
        
        # إنشاء مفتاح فريد للرسالة
        message_key = (date_key, subject_key)
        
        if message_key not in seen:
            seen.add(message_key)
            unique_rows.append(row)
    
    return unique_rows


def remove_duplicate_messages(client_id: int = None):
    """
    إزالة الرسائل المكررة من قاعدة البيانات
    إذا تم تمرير client_id، يتم إزالة التكرارات لهذا العميل فقط
    إذا لم يتم تمرير client_id، يتم إزالة التكرارات لجميع العملاء
    """
    conn = get_connection()
    cur = conn.cursor()
    
    try:
        if client_id:
            # إزالة التكرارات لعميل محدد
            # نحتفظ بأحدث رسالة (أكبر id) لكل مجموعة مكررة
            cur.execute("""
                DELETE FROM messages
                WHERE id NOT IN (
                    SELECT MAX(id)
                    FROM messages
                    WHERE client_id = ?
                    GROUP BY 
                        client_id,
                        COALESCE(actual_date, message_date),
                        client_response
                )
                AND client_id = ?
            """, (client_id, client_id))
        else:
            # إزالة التكرارات لجميع العملاء
            cur.execute("""
                DELETE FROM messages
                WHERE id NOT IN (
                    SELECT MAX(id)
                    FROM messages
                    GROUP BY 
                        client_id,
                        COALESCE(actual_date, message_date),
                        client_response
                )
            """)
        
        deleted_count = cur.rowcount
        conn.commit()
        conn.close()
        return deleted_count
    except Exception as e:
        conn.rollback()
        conn.close()
        raise e


# =========================
# Follow-Up
# =========================
def get_clients_needing_followup():
    from core.models import followup_days

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            c.id,
            c.company_name,
            c.status,
            c.classification,
            MAX(m.message_date)
        FROM clients c
        LEFT JOIN messages m ON c.id = m.client_id
        GROUP BY c.id
    """)
    rows = cur.fetchall()
    conn.close()

    today = datetime.now()
    due = []

    for cid, company, status, classification, last_date in rows:
        if last_date:
            try:
                last_dt = datetime.strptime(last_date, "%d/%m/%Y")
                days = (today - last_dt).days
            except ValueError:
                days = 999
        else:
            days = 999

        wait = followup_days(status if status else classification)
        if days >= wait:
            due.append(company)

    return due


# =========================
# Requests
# =========================
def resolve_client_id_by_email(email: str):
    if not email:
        return None
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id FROM clients WHERE LOWER(email)=?", (email.lower(),))
    row = cur.fetchone()
    conn.close()
    return row[0] if row else None


def auto_link_requests_by_email():
    ensure_requests_email_column()
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        UPDATE requests
        SET client_id = (
            SELECT c.id
            FROM clients c
            WHERE LOWER(c.email)=LOWER(requests.client_email)
        )
        WHERE (client_id IS NULL OR client_id = 0)
          AND client_email IS NOT NULL
          AND client_email != ''
    """)
    conn.commit()
    conn.close()


def heal_request_email_from_client():
    ensure_requests_email_column()
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        UPDATE requests
        SET client_email = (
            SELECT email FROM clients
            WHERE clients.id = requests.client_id
        )
        WHERE (client_email IS NULL OR client_email = '')
          AND client_id IS NOT NULL
    """)
    conn.commit()
    conn.close()


def get_request_reply_email(request_id: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT r.client_email, c.email
        FROM requests r
        LEFT JOIN clients c ON r.client_id = c.id
        WHERE r.id = ?
    """, (request_id,))
    row = cur.fetchone()
    conn.close()

    if not row:
        return None

    request_email, client_email = row
    return request_email or client_email


def save_request(client_email, request_type, extracted_text, notes=""):
    ensure_requests_email_column()

    conn = get_connection()
    cur = conn.cursor()

    # 🔒 منع تكرار نفس الطلب المفتوح لنفس الإيميل
    cur.execute("""
        SELECT id
        FROM requests
        WHERE LOWER(client_email)=?
          AND request_type=?
          AND status='open'
    """, (client_email.lower(), request_type))

    exists = cur.fetchone()
    if exists:
        conn.close()
        return  # الطلب موجود بالفعل → لا نضيفه مرة أخرى

    # 🔗 ربط الطلب بالعميل إن وُجد
    client_id = resolve_client_id_by_email(client_email)

    # 🆕 إنشاء الطلب
    cur.execute("""
        INSERT INTO requests (
            client_id,
            client_email,
            request_type,
            extracted_text,
            notes,
            status,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        client_id,
        client_email,
        request_type,
        extracted_text,
        notes,
        "open",
        datetime.now().strftime("%d/%m/%Y %H:%M")
    ))

    # 🎯 تحديث حالة العميل تلقائيًا حسب نوع الطلب
    if client_id:
        rt = request_type.lower()
        if "price" in rt:
            cur.execute(
                "UPDATE clients SET status='Requested Price' WHERE id=?",
                (client_id,)
            )
        elif "sample" in rt:
            cur.execute(
                "UPDATE clients SET status='Samples Requested' WHERE id=?",
                (client_id,)
            )
        elif "spec" in rt:
            cur.execute(
                "UPDATE clients SET status='Specs Requested' WHERE id=?",
                (client_id,)
            )

    conn.commit()
    conn.close()



def update_request_reply_status(request_id: int, reply_status: str):
    """
    reply_status: 'pending' | 'replied'
    """
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        UPDATE requests
        SET reply_status = ?
        WHERE id = ?
    """, (reply_status, request_id))

    conn.commit()
    conn.close()



def sync_request_from_client(client_id: int):
    if not client_id:
        return

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        UPDATE requests
        SET client_email = (
            SELECT email FROM clients WHERE clients.id = ?
        )
        WHERE client_id = ?
    """, (client_id, client_id))

    conn.commit()
    conn.close()


# =========================
# AUTO RESOLUTION ENGINE
# =========================
def extract_email_from_text(text: str):
    if not text:
        return None
    match = re.search(
        r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
        text
    )
    return match.group(0).lower() if match else None


def extract_domain_from_text(text: str):
    if not text:
        return None
    match = re.search(
        r"\b[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b",
        text
    )
    return match.group(0).lower() if match else None


def sync_all_requests_from_clients():
    """
    FULL AUTO SYNC + AUTO CLIENT HEALING
    """

    ensure_requests_email_column()

    conn = get_connection()
    cur = conn.cursor()

    # 1) unlink orphan client_id
    cur.execute("""
        UPDATE requests
        SET client_id = NULL
        WHERE client_id IS NOT NULL
          AND client_id NOT IN (SELECT id FROM clients)
    """)

    # 2) link requests by email
    cur.execute("""
        UPDATE requests
        SET client_id = (
            SELECT id FROM clients
            WHERE LOWER(clients.email) = LOWER(requests.client_email)
        )
        WHERE client_id IS NULL
          AND client_email IS NOT NULL
          AND client_email != ''
    """)

    # 3) heal missing request email from client
    cur.execute("""
        UPDATE requests
        SET client_email = (
            SELECT email FROM clients
            WHERE clients.id = requests.client_id
        )
        WHERE client_id IS NOT NULL
          AND (client_email IS NULL OR client_email = '')
    """)

    # 4) auto-create client from extracted text
    cur.execute("""
        SELECT id, extracted_text
        FROM requests
        WHERE client_id IS NULL
    """)
    rows = cur.fetchall()

    for req_id, text in rows:
        email = extract_email_from_text(text)
        domain = extract_domain_from_text(text)

        if email:
            cur.execute("""
                INSERT INTO clients (
                    company_name, email, date_added, status
                )
                VALUES (?, ?, ?, ?)
            """, (
                email.split("@")[1],
                email,
                datetime.now().strftime("%d/%m/%Y"),
                "auto"
            ))

            cur.execute("""
                UPDATE requests
                SET client_id = (
                    SELECT id FROM clients WHERE email = ?
                ),
                client_email = ?
                WHERE id = ?
            """, (email, email, req_id))

        elif domain:
            cur.execute("""
                INSERT INTO clients (
                    company_name, date_added, status
                )
                VALUES (?, ?, ?)
            """, (
                domain,
                datetime.now().strftime("%d/%m/%Y"),
                "auto"
            ))

            cur.execute("""
                UPDATE requests
                SET client_id = (
                    SELECT id FROM clients WHERE company_name = ?
                )
                WHERE id = ?
            """, (domain, req_id))

    conn.commit()
    conn.close()

# =========================
# Compatibility Helpers (REQUIRED by UI)
# =========================

def get_clients_needing_followup():
    """
    Return list of company names that require follow-up
    (safe wrapper – never crashes UI)
    """
    try:
        from core.models import followup_days
    except Exception:
        return []

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            c.company_name,
            c.status,
            c.classification,
            MAX(m.message_date)
        FROM clients c
        LEFT JOIN messages m ON c.id = m.client_id
        GROUP BY c.id
    """)
    rows = cur.fetchall()
    conn.close()

    today = datetime.now()
    due = []

    for company, status, classification, last_date in rows:
        if last_date:
            try:
                last_dt = datetime.strptime(last_date, "%d/%m/%Y")
                days = (today - last_dt).days
            except Exception:
                days = 999
        else:
            days = 999

        wait = followup_days(status or classification)
        if days >= wait:
            due.append(company)

    return due


def find_client_by_domain(domain: str):
    """
    Find client by email domain (safe)
    """
    if not domain:
        return None

    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT * FROM clients WHERE LOWER(email) LIKE ?",
        (f"%@{domain.lower()}",)
    )
    row = cur.fetchone()
    conn.close()
    return row

def request_exists(client_email: str, request_type: str):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT id
        FROM requests
        WHERE LOWER(client_email)=?
          AND request_type=?
          AND status='open'
    """, (client_email.lower(), request_type))
    row = cur.fetchone()
    conn.close()
    return row is not None

def ensure_requests_reply_status_column():
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            ALTER TABLE requests
            ADD COLUMN reply_status TEXT DEFAULT 'pending'
        """)
    except sqlite3.OperationalError:
        pass
    conn.commit()
    conn.close()


def ensure_actual_date_column():
    """إضافة حقل actual_date إلى جدول messages للتاريخ الفعلي للرسالة"""
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("ALTER TABLE messages ADD COLUMN actual_date TEXT")
    except sqlite3.OperationalError:
        pass
    conn.commit()
    conn.close()


def _table_has_column(cur, table: str, column: str) -> bool:
    cur.execute(f"PRAGMA table_info({table})")
    cols = [r[1] for r in cur.fetchall()]  # (cid, name, type, notnull, dflt_value, pk)
    return column in cols


def ensure_messages_columns():
    """
    بعض قواعد البيانات القديمة قد تحتوي جدول messages بدون أعمدة لازمة للـ Email Integration.
    نضيف الأعمدة الناقصة بشكل آمن بدون حذف/تعديل البيانات.
    """
    conn = get_connection()
    cur = conn.cursor()

    # إذا الجدول غير موجود، سيتم إنشاؤه عبر init_db (CREATE TABLE IF NOT EXISTS)
    # هنا نركز على إضافة الأعمدة المفقودة فقط.
    columns_to_add = [
        ("actual_date", "TEXT"),
        ("message_type", "TEXT"),
        ("channel", "TEXT"),
        ("client_response", "TEXT"),
        ("notes", "TEXT"),
        ("score_effect", "INTEGER DEFAULT 0"),
    ]

    for col_name, col_def in columns_to_add:
        try:
            if not _table_has_column(cur, "messages", col_name):
                cur.execute(f"ALTER TABLE messages ADD COLUMN {col_name} {col_def}")
        except sqlite3.OperationalError:
            # في حال كانت هناك مشكلة في PRAGMA أو ALTER (مثلاً الجدول غير موجود)
            pass

    conn.commit()
    conn.close()


def ensure_account_type_columns():
    """إضافة حقول جديدة لجدول outlook_accounts لدعم حسابات IMAP"""
    conn = get_connection()
    cur = conn.cursor()
    
    columns_to_add = [
        ("account_type", "TEXT DEFAULT 'outlook'"),
        ("imap_server", "TEXT"),
        ("imap_port", "INTEGER DEFAULT 993"),
        ("imap_username", "TEXT"),
        ("imap_password", "TEXT"),
        ("use_ssl", "INTEGER DEFAULT 1"),
        ("cpanel_host", "TEXT"),
        ("cpanel_username", "TEXT"),
        ("cpanel_api_token", "TEXT"),
        ("use_cpanel_api", "INTEGER DEFAULT 0")
    ]
    
    for column_name, column_def in columns_to_add:
        try:
            cur.execute(f"ALTER TABLE outlook_accounts ADD COLUMN {column_name} {column_def}")
        except sqlite3.OperationalError:
            pass  # العمود موجود بالفعل
    
    conn.commit()
    conn.close()


def ensure_default_outlook_account():
    """إضافة حساب Outlook ثابت (contact@el-raee.com) إذا لم يكن موجوداً"""
    conn = get_connection()
    cur = conn.cursor()
    
    # التحقق من وجود الحساب
    cur.execute("SELECT id FROM outlook_accounts WHERE account_name = ?", ("contact@el-raee.com",))
    if cur.fetchone():
        conn.close()
        return  # الحساب موجود بالفعل
    
    # إضافة الحساب
    try:
        token_cache_path = "database/ms_token_cache_contact_el-raee_com.bin"
        cur.execute("""
            INSERT INTO outlook_accounts 
            (account_name, email, token_cache_path, account_type, is_active, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            "contact@el-raee.com",
            "contact@el-raee.com",
            token_cache_path,
            "outlook",
            1,
            datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        ))
        conn.commit()
    except sqlite3.IntegrityError:
        pass  # الحساب موجود بالفعل (race condition)
    finally:
        conn.close()


# =========================
# Documents Management
# =========================
def init_documents_table():
    """تهيئة جدول المستندات"""
    conn = get_connection()
    cur = conn.cursor()
    
    cur.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER NOT NULL,
            file_name TEXT NOT NULL,
            file_path TEXT NOT NULL,
            file_type TEXT,
            file_size INTEGER,
            document_type TEXT,
            description TEXT,
            uploaded_date TEXT,
            uploaded_by TEXT,
            FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE
        )
    """)
    
    conn.commit()
    conn.close()


def add_document(data: dict):
    """إضافة مستند جديد"""
    conn = get_connection()
    cur = conn.cursor()
    
    cur.execute("""
        INSERT INTO documents (
            client_id, file_name, file_path, file_type,
            file_size, document_type, description,
            uploaded_date, uploaded_by
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data["client_id"],
        data["file_name"],
        data["file_path"],
        data.get("file_type"),
        data.get("file_size"),
        data.get("document_type"),
        data.get("description"),
        data["uploaded_date"],
        data.get("uploaded_by")
    ))
    
    conn.commit()
    doc_id = cur.lastrowid
    conn.close()
    return doc_id


def get_client_documents(client_id: int):
    """الحصول على جميع مستندات العميل"""
    conn = get_connection()
    cur = conn.cursor()
    
    cur.execute("""
        SELECT *
        FROM documents
        WHERE client_id = ?
        ORDER BY uploaded_date DESC
    """, (client_id,))
    
    results = cur.fetchall()
    conn.close()
    return results


def get_document_by_id(doc_id: int):
    """الحصول على مستند بواسطة ID"""
    conn = get_connection()
    cur = conn.cursor()
    
    cur.execute("SELECT * FROM documents WHERE id=?", (doc_id,))
    result = cur.fetchone()
    conn.close()
    return result


def delete_document(doc_id: int):
    """حذف مستند"""
    conn = get_connection()
    cur = conn.cursor()
    
    # الحصول على مسار الملف قبل الحذف
    cur.execute("SELECT file_path FROM documents WHERE id=?", (doc_id,))
    result = cur.fetchone()
    
    if result:
        file_path = result[0]
        # حذف الملف من القرص
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception as e:
            print(f"خطأ في حذف الملف: {e}")
    
    # حذف السجل من قاعدة البيانات
    cur.execute("DELETE FROM documents WHERE id=?", (doc_id,))
    
    conn.commit()
    conn.close()


def search_documents(search_text: str, client_id: int = None):
    """البحث في المستندات"""
    conn = get_connection()
    cur = conn.cursor()
    
    search_pattern = f'%{search_text.lower()}%'
    
    if client_id:
        query = """
            SELECT *
            FROM documents
            WHERE client_id = ?
              AND (LOWER(file_name) LIKE ?
                OR LOWER(description) LIKE ?
                OR LOWER(document_type) LIKE ?)
            ORDER BY uploaded_date DESC
        """
        cur.execute(query, (client_id, search_pattern, search_pattern, search_pattern))
    else:
        query = """
            SELECT *
            FROM documents
            WHERE LOWER(file_name) LIKE ?
               OR LOWER(description) LIKE ?
               OR LOWER(document_type) LIKE ?
            ORDER BY uploaded_date DESC
        """
        cur.execute(query, (search_pattern, search_pattern, search_pattern))
    
    results = cur.fetchall()
    conn.close()
    return results


# =========================
# Products Management
# =========================
def init_products_table():
    """تهيئة جدول المنتجات"""
    conn = get_connection()
    cur = conn.cursor()
    
    cur.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_name TEXT NOT NULL,
            product_code TEXT,
            category TEXT,
            unit TEXT,
            unit_price REAL DEFAULT 0,
            cost_price REAL DEFAULT 0,
            description TEXT,
            specifications TEXT,
            active INTEGER DEFAULT 1,
            created_date TEXT
        )
    """)
    
    conn.commit()
    conn.close()


def add_product(data: dict):
    """إضافة منتج جديد"""
    conn = get_connection()
    cur = conn.cursor()
    
    cur.execute("""
        INSERT INTO products (
            product_name, product_code, category, unit,
            unit_price, cost_price, description, specifications,
            active, created_date
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data["product_name"],
        data.get("product_code"),
        data.get("category"),
        data.get("unit"),
        data.get("unit_price", 0),
        data.get("cost_price", 0),
        data.get("description"),
        data.get("specifications"),
        data.get("active", 1),
        datetime.now().strftime("%d/%m/%Y")
    ))
    
    conn.commit()
    product_id = cur.lastrowid
    conn.close()
    return product_id


def get_all_products(active_only=True):
    """الحصول على جميع المنتجات"""
    conn = get_connection()
    cur = conn.cursor()
    
    if active_only:
        cur.execute("SELECT * FROM products WHERE active=1 ORDER BY product_name")
    else:
        cur.execute("SELECT * FROM products ORDER BY product_name")
    
    results = cur.fetchall()
    conn.close()
    return results


def get_product_by_id(product_id: int):
    """الحصول على منتج بواسطة ID"""
    conn = get_connection()
    cur = conn.cursor()
    
    cur.execute("SELECT * FROM products WHERE id=?", (product_id,))
    result = cur.fetchone()
    conn.close()
    return result


def update_product(product_id: int, data: dict):
    """تحديث منتج"""
    conn = get_connection()
    cur = conn.cursor()
    
    cur.execute("""
        UPDATE products
        SET product_name=?, product_code=?, category=?, unit=?,
            unit_price=?, cost_price=?, description=?, specifications=?,
            active=?
        WHERE id=?
    """, (
        data["product_name"],
        data.get("product_code"),
        data.get("category"),
        data.get("unit"),
        data.get("unit_price", 0),
        data.get("cost_price", 0),
        data.get("description"),
        data.get("specifications"),
        data.get("active", 1),
        product_id
    ))
    
    conn.commit()
    conn.close()


def delete_product(product_id: int):
    """حذف منتج (soft delete)"""
    conn = get_connection()
    cur = conn.cursor()
    
    cur.execute("UPDATE products SET active=0 WHERE id=?", (product_id,))
    
    conn.commit()
    conn.close()


# =========================
# Quotes/Offers Management
# =========================
def init_quotes_table():
    """تهيئة جدول العروض والاقتباسات"""
    conn = get_connection()
    cur = conn.cursor()
    
    cur.execute("""
        CREATE TABLE IF NOT EXISTS quotes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            quote_number TEXT UNIQUE,
            client_id INTEGER NOT NULL,
            quote_date TEXT NOT NULL,
            valid_until TEXT,
            status TEXT DEFAULT 'draft',
            total_amount REAL DEFAULT 0,
            currency TEXT DEFAULT 'USD',
            discount REAL DEFAULT 0,
            tax_rate REAL DEFAULT 0,
            notes TEXT,
            terms_conditions TEXT,
            created_date TEXT,
            created_by TEXT,
            FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE
        )
    """)
    
    # جدول تفاصيل العروض (المنتجات في كل عرض)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS quote_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            quote_id INTEGER NOT NULL,
            product_id INTEGER,
            product_name TEXT NOT NULL,
            quantity REAL NOT NULL,
            unit_price REAL NOT NULL,
            discount REAL DEFAULT 0,
            total_price REAL NOT NULL,
            FOREIGN KEY (quote_id) REFERENCES quotes(id) ON DELETE CASCADE,
            FOREIGN KEY (product_id) REFERENCES products(id)
        )
    """)
    
    conn.commit()
    conn.close()


def add_quote(data: dict):
    """إضافة عرض جديد"""
    conn = get_connection()
    cur = conn.cursor()
    
    # توليد رقم العرض
    if not data.get("quote_number"):
        cur.execute("SELECT COUNT(*) FROM quotes")
        count = cur.fetchone()[0]
        quote_number = f"QT-{datetime.now().strftime('%Y%m%d')}-{count + 1:04d}"
    else:
        quote_number = data["quote_number"]
    
    cur.execute("""
        INSERT INTO quotes (
            quote_number, client_id, quote_date, valid_until,
            status, total_amount, currency, discount, tax_rate,
            notes, terms_conditions, created_date, created_by
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        quote_number,
        data["client_id"],
        data["quote_date"],
        data.get("valid_until"),
        data.get("status", "draft"),
        data.get("total_amount", 0),
        data.get("currency", "USD"),
        data.get("discount", 0),
        data.get("tax_rate", 0),
        data.get("notes"),
        data.get("terms_conditions"),
        datetime.now().strftime("%d/%m/%Y %H:%M"),
        data.get("created_by", "User")
    ))
    
    quote_id = cur.lastrowid
    
    # إضافة عناصر العرض
    if "items" in data:
        for item in data["items"]:
            cur.execute("""
                INSERT INTO quote_items (
                    quote_id, product_id, product_name, quantity,
                    unit_price, discount, total_price
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                quote_id,
                item.get("product_id"),
                item["product_name"],
                item["quantity"],
                item["unit_price"],
                item.get("discount", 0),
                item["total_price"]
            ))
    
    conn.commit()
    conn.close()
    return quote_id


def get_quote_by_id(quote_id: int):
    """الحصول على عرض بواسطة ID"""
    conn = get_connection()
    cur = conn.cursor()
    
    cur.execute("SELECT * FROM quotes WHERE id=?", (quote_id,))
    quote = cur.fetchone()
    
    if quote:
        cur.execute("SELECT * FROM quote_items WHERE quote_id=?", (quote_id,))
        items = cur.fetchall()
        conn.close()
        return quote, items
    else:
        conn.close()
        return None, []


def get_client_quotes(client_id: int):
    """الحصول على جميع عروض العميل"""
    conn = get_connection()
    cur = conn.cursor()
    
    cur.execute("""
        SELECT * FROM quotes
        WHERE client_id = ?
        ORDER BY quote_date DESC
    """, (client_id,))
    
    results = cur.fetchall()
    conn.close()
    return results


def get_all_quotes(status_filter=None):
    """الحصول على جميع العروض"""
    conn = get_connection()
    cur = conn.cursor()
    
    if status_filter:
        cur.execute("""
            SELECT * FROM quotes
            WHERE status = ?
            ORDER BY quote_date DESC
        """, (status_filter,))
    else:
        cur.execute("SELECT * FROM quotes ORDER BY quote_date DESC")
    
    results = cur.fetchall()
    conn.close()
    return results


def update_quote_status(quote_id: int, status: str):
    """تحديث حالة العرض"""
    conn = get_connection()
    cur = conn.cursor()
    
    cur.execute("UPDATE quotes SET status=? WHERE id=?", (status, quote_id))
    
    conn.commit()
    conn.close()


def calculate_quote_profitability(quote_id: int):
    """حساب الربحية للعرض"""
    conn = get_connection()
    cur = conn.cursor()
    
    # الحصول على عناصر العرض
    cur.execute("""
        SELECT qi.quantity, qi.unit_price, qi.total_price, qi.product_id,
               p.cost_price
        FROM quote_items qi
        LEFT JOIN products p ON qi.product_id = p.id
        WHERE qi.quote_id = ?
    """, (quote_id,))
    
    items = cur.fetchall()
    
    total_revenue = 0
    total_cost = 0
    
    for item in items:
        quantity, unit_price, total_price, product_id, cost_price = item
        total_revenue += total_price or 0
        
        if cost_price:
            total_cost += (cost_price * quantity)
        else:
            # إذا لم يكن هناك سعر تكلفة، نقدره بـ 60% من السعر
            total_cost += (unit_price * 0.6 * quantity)
    
    # الحصول على خصم العرض
    cur.execute("SELECT discount, tax_rate FROM quotes WHERE id=?", (quote_id,))
    result = cur.fetchone()
    discount = result[0] if result else 0
    tax_rate = result[1] if result else 0
    
    # حساب الربح
    revenue_after_discount = total_revenue - discount
    profit = revenue_after_discount - total_cost
    profit_margin = (profit / revenue_after_discount * 100) if revenue_after_discount > 0 else 0
    
    conn.close()
    
    return {
        "total_revenue": total_revenue,
        "total_cost": total_cost,
        "discount": discount,
        "revenue_after_discount": revenue_after_discount,
        "profit": profit,
        "profit_margin": profit_margin
    }


def delete_quote(quote_id: int):
    """حذف عرض"""
    conn = get_connection()
    cur = conn.cursor()
    
    # حذف عناصر العرض أولاً (بسبب FOREIGN KEY)
    cur.execute("DELETE FROM quote_items WHERE quote_id=?", (quote_id,))
    
    # حذف العرض
    cur.execute("DELETE FROM quotes WHERE id=?", (quote_id,))
    
    conn.commit()
    conn.close()


# =========================
# Product Buyer Search
# =========================
def search_buyers_by_product(product_name: str, countries: list = None):
    """
    البحث عن العملاء (المشترين) حسب المنتج والدول
    
    Args:
        product_name: اسم المنتج (مثل "Dehydrated Onion")
        countries: قائمة الدول (مثل ["Germany", "France", "USA"])
    
    Returns:
        قائمة من العملاء الذين لديهم طلبات/رسائل متعلقة بالمنتج في الدول المحددة
    """
    conn = get_connection()
    cur = conn.cursor()
    
    product_pattern = f'%{product_name.lower()}%'
    
    # بناء شروط البحث عن الدول
    if not countries or len(countries) == 0:
        # إذا لم يتم تحديد دول، استخدم جميع دول الاتحاد الأوروبي وأمريكا
        countries = [
            "Austria", "Belgium", "Bulgaria", "Croatia", "Cyprus", "Czech Republic",
            "Denmark", "Estonia", "Finland", "France", "Germany", "Greece", "Hungary",
            "Ireland", "Italy", "Latvia", "Lithuania", "Luxembourg", "Malta",
            "Netherlands", "Poland", "Portugal", "Romania", "Slovakia", "Slovenia",
            "Spain", "Sweden", "United Kingdom", "UK", "England",
            "USA", "United States", "US", "America"
        ]
    
    # بناء شرط الدول - استخدام LIKE للبحث المرن
    country_conditions = " OR ".join(["c.country LIKE ?" for _ in countries])
    country_params = [f'%{c}%' for c in countries]
    
    all_results = {}
    
    # 1. البحث في الطلبات
    query1 = f"""
        SELECT DISTINCT c.*
        FROM clients c
        INNER JOIN requests r ON c.id = r.client_id
        WHERE (
            LOWER(r.extracted_text) LIKE ? 
            OR LOWER(r.notes) LIKE ?
            OR LOWER(r.request_type) LIKE ?
        )
        AND ({country_conditions})
    """
    
    params1 = [product_pattern, product_pattern, product_pattern] + country_params
    cur.execute(query1, params1)
    for row in cur.fetchall():
        all_results[row[0]] = row
    
    # 2. البحث في الرسائل
    found_ids = list(all_results.keys())
    if found_ids:
        ids_condition = " AND c.id NOT IN (" + ",".join(["?" for _ in found_ids]) + ")"
        params2_base = found_ids
    else:
        ids_condition = ""
        params2_base = []
    
    query2 = f"""
        SELECT DISTINCT c.*
        FROM clients c
        INNER JOIN messages m ON c.id = m.client_id
        WHERE (
            LOWER(m.notes) LIKE ?
            OR LOWER(m.client_response) LIKE ?
        )
        AND ({country_conditions}){ids_condition}
    """
    
    params2 = [product_pattern, product_pattern] + country_params + params2_base
    cur.execute(query2, params2)
    for row in cur.fetchall():
        all_results[row[0]] = row
    
    # 3. البحث المباشر في جدول العملاء (في حالة عدم وجود طلبات أو رسائل)
    # البحث في اسم الشركة، البريد الإلكتروني، الموقع الإلكتروني
    found_ids = list(all_results.keys())
    if found_ids:
        ids_condition = " AND c.id NOT IN (" + ",".join(["?" for _ in found_ids]) + ")"
        params3_base = found_ids
    else:
        ids_condition = ""
        params3_base = []
    
    query3 = f"""
        SELECT DISTINCT c.*
        FROM clients c
        WHERE (
            LOWER(c.company_name) LIKE ?
            OR LOWER(c.email) LIKE ?
            OR LOWER(c.website) LIKE ?
        )
        AND ({country_conditions}){ids_condition}
    """
    
    params3 = [product_pattern, product_pattern, product_pattern] + country_params + params3_base
    cur.execute(query3, params3)
    for row in cur.fetchall():
        all_results[row[0]] = row


# =========================
# Outlook Accounts Management
# =========================
def add_outlook_account(account_name, email=None, token_cache_path=None, account_type="outlook",
                        imap_server=None, imap_port=993, imap_username=None, imap_password=None, use_ssl=1,
                        cpanel_host=None, cpanel_username=None, cpanel_api_token=None, use_cpanel_api=0):
    """إضافة حساب جديد (Outlook أو IMAP أو cPanel API)"""
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO outlook_accounts 
            (account_name, email, token_cache_path, account_type, created_at,
             imap_server, imap_port, imap_username, imap_password, use_ssl,
             cpanel_host, cpanel_username, cpanel_api_token, use_cpanel_api)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            account_name, email, token_cache_path, account_type,
            datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            imap_server, imap_port, imap_username, imap_password, use_ssl,
            cpanel_host, cpanel_username, cpanel_api_token, use_cpanel_api
        ))
        conn.commit()
        account_id = cur.lastrowid
        conn.close()
        return account_id
    except sqlite3.IntegrityError:
        conn.close()
        raise ValueError(f"Account name '{account_name}' already exists")


def get_all_outlook_accounts():
    """الحصول على جميع الحسابات (Outlook و IMAP و cPanel API)"""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, account_name, email, token_cache_path, is_active, created_at, last_sync,
               account_type, imap_server, imap_port, imap_username, imap_password, use_ssl,
               cpanel_host, cpanel_username, cpanel_api_token, use_cpanel_api
        FROM outlook_accounts
        ORDER BY account_name
    """)
    accounts = cur.fetchall()
    conn.close()
    return accounts


def get_outlook_account_by_id(account_id):
    """الحصول على حساب بواسطة ID (Outlook أو IMAP أو cPanel API)"""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, account_name, email, token_cache_path, is_active, created_at, last_sync,
               account_type, imap_server, imap_port, imap_username, imap_password, use_ssl,
               cpanel_host, cpanel_username, cpanel_api_token, use_cpanel_api
        FROM outlook_accounts
        WHERE id = ?
    """, (account_id,))
    account = cur.fetchone()
    conn.close()
    return account


def get_outlook_account_by_name(account_name):
    """الحصول على حساب Outlook بواسطة الاسم"""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, account_name, email, token_cache_path, is_active, created_at, last_sync
        FROM outlook_accounts
        WHERE account_name = ?
    """, (account_name,))
    account = cur.fetchone()
    conn.close()
    return account


def update_outlook_account(account_id, account_name=None, email=None, token_cache_path=None, is_active=None,
                           account_type=None, imap_server=None, imap_port=None, imap_username=None,
                           imap_password=None, use_ssl=None, cpanel_host=None, cpanel_username=None,
                           cpanel_api_token=None, use_cpanel_api=None):
    """تحديث حساب (Outlook أو IMAP)"""
    conn = get_connection()
    cur = conn.cursor()
    updates = []
    params = []
    
    if account_name is not None:
        updates.append("account_name = ?")
        params.append(account_name)
    if email is not None:
        updates.append("email = ?")
        params.append(email)
    if token_cache_path is not None:
        updates.append("token_cache_path = ?")
        params.append(token_cache_path)
    if is_active is not None:
        updates.append("is_active = ?")
        params.append(is_active)
    if account_type is not None:
        updates.append("account_type = ?")
        params.append(account_type)
    if imap_server is not None:
        updates.append("imap_server = ?")
        params.append(imap_server)
    if imap_port is not None:
        updates.append("imap_port = ?")
        params.append(imap_port)
    if imap_username is not None:
        updates.append("imap_username = ?")
        params.append(imap_username)
    if imap_password is not None:
        updates.append("imap_password = ?")
        params.append(imap_password)
    if use_ssl is not None:
        updates.append("use_ssl = ?")
        params.append(use_ssl)
    if cpanel_host is not None:
        updates.append("cpanel_host = ?")
        params.append(cpanel_host)
    if cpanel_username is not None:
        updates.append("cpanel_username = ?")
        params.append(cpanel_username)
    if cpanel_api_token is not None:
        updates.append("cpanel_api_token = ?")
        params.append(cpanel_api_token)
    if use_cpanel_api is not None:
        updates.append("use_cpanel_api = ?")
        params.append(use_cpanel_api)
    
    if updates:
        params.append(account_id)
        cur.execute(f"""
            UPDATE outlook_accounts
            SET {', '.join(updates)}
            WHERE id = ?
        """, params)
        conn.commit()
    conn.close()


def delete_outlook_account(account_id):
    """حذف حساب Outlook"""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM outlook_accounts WHERE id = ?", (account_id,))
    conn.commit()
    conn.close()


def update_account_last_sync(account_id):
    """تحديث تاريخ آخر مزامنة للحساب"""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        UPDATE outlook_accounts
        SET last_sync = ?
        WHERE id = ?
    """, (datetime.now().strftime("%d/%m/%Y %H:%M:%S"), account_id))
    conn.commit()
    conn.close()

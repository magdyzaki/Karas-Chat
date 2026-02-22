# 🔧 fix_ids_and_tables.py
# يقوم بفحص كل الجداول في قاعدة البيانات crm.db
# ويعيد ترتيب IDs المفقودة تلقائياً مرة واحدة فقط عند التشغيل

import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "database", "crm.db")

def reconnect_db():
    """يفتح الاتصال بقاعدة البيانات."""
    return sqlite3.connect(DB_PATH)

def fix_table_ids(conn, table_name):
    """
    يعيد ترتيب IDs داخل الجدول المحدد بدون حذف البيانات.
    """
    cursor = conn.cursor()
    print(f"🧩 فحص الجدول: {table_name}")

    # تحقق من وجود عمود id
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [col[1] for col in cursor.fetchall()]
    if "id" not in columns:
        print(f"⚠️  الجدول {table_name} لا يحتوي على عمود id، تم تخطيه.")
        return

    # قراءة كل الصفوف بالترتيب
    cursor.execute(f"SELECT * FROM {table_name} ORDER BY id")
    rows = cursor.fetchall()

    if not rows:
        print(f"🔹 الجدول {table_name} فارغ.")
        return

    # تحديث القيم
    for new_id, row in enumerate(rows, start=1):
        old_id = row[0]
        if new_id != old_id:
            cursor.execute(f"UPDATE {table_name} SET id = ? WHERE id = ?", (new_id, old_id))
            print(f"🔄 إعادة ترقيم من {old_id} إلى {new_id}")

    # إعادة ضبط الـ AUTOINCREMENT
    cursor.execute(f"DELETE FROM sqlite_sequence WHERE name='{table_name}'")
    cursor.execute(f"UPDATE sqlite_sequence SET seq = (SELECT MAX(id) FROM {table_name}) WHERE name='{table_name}'")
    conn.commit()
    print(f"✅ تم إصلاح IDs في الجدول {table_name}.\n")

def main():
    if not os.path.exists(DB_PATH):
        print("❌ قاعدة البيانات غير موجودة.")
        return

    conn = reconnect_db()
    cursor = conn.cursor()

    # الحصول على أسماء الجداول
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [t[0] for t in cursor.fetchall() if t[0] != 'sqlite_sequence']

    print("🚀 بدء فحص الجداول...")
    for table in tables:
        fix_table_ids(conn, table)

    conn.commit()
    conn.close()
    print("🎯 تمت المراجعة الكاملة بنجاح ✅")

if __name__ == "__main__":
    main()
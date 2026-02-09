import sqlite3, os

print("🔍 Checking and updating sales table structure...")

# تحديد المسار الصحيح لقاعدة البيانات داخل مجلد المشروع
DB = os.path.join(os.path.dirname(__file__), "database", "crm.db")

if not os.path.exists(DB):
    print("❌ Database file not found!")
    exit()

try:
    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    # جلب أسماء الأعمدة الموجودة حاليًا
    cur.execute("PRAGMA table_info(sales)")
    columns = [col[1] for col in cur.fetchall()]

    added = []

    # إضافة الأعمدة لو مش موجودة
    if "customer_address" not in columns:
        cur.execute("ALTER TABLE sales ADD COLUMN customer_address TEXT;")
        added.append("customer_address")

    if "customer_phone" not in columns:
        cur.execute("ALTER TABLE sales ADD COLUMN customer_phone TEXT;")
        added.append("customer_phone")

    conn.commit()
    conn.close()

    if added:
        print(f"✅ Added missing columns: {', '.join(added)}")
    else:
        print("✅ All required columns already exist. No changes made.")

    print("\n🎉 Database structure updated successfully!")

except Exception as e:
    print(f"❌ Error while updating database: {e}")
# setup_db.py
# إعداد قاعدة البيانات وإنشاء جميع الجداول الأساسية + جدول الإعدادات
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "database", "crm.db")

def ensure_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # 🔹 جدول العملاء
    c.execute("""
    CREATE TABLE IF NOT EXISTS customers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        country TEXT DEFAULT '',
        company TEXT DEFAULT '',
        email TEXT DEFAULT '',
        phone TEXT DEFAULT '',
        address TEXT DEFAULT '',
        rating TEXT DEFAULT '',
        created_at TEXT DEFAULT ''
    )
    """)
    
    # التأكد من وجود جميع الأعمدة المطلوبة
    columns_to_add = {
        "country": "TEXT DEFAULT ''",
        "rating": "TEXT DEFAULT ''",
        "created_at": "TEXT DEFAULT ''",
        "address": "TEXT DEFAULT ''"  # إضافة عمود address
    }
    
    for col_name, col_type in columns_to_add.items():
        try:
            c.execute(f"ALTER TABLE customers ADD COLUMN {col_name} {col_type}")
        except:
            pass

    # 🔹 جدول المنتجات
    c.execute("""
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_code TEXT UNIQUE,
        code TEXT DEFAULT '',
        name TEXT NOT NULL,
        description TEXT DEFAULT '',
        quantity REAL DEFAULT 0,
        unit TEXT DEFAULT '',
        price_egp REAL DEFAULT 0,
        price_usd REAL DEFAULT 0,
        buy_price REAL DEFAULT 0,
        category TEXT DEFAULT ''
    )
    """)
    
    # التأكد من وجود الأعمدة الإضافية
    try:
        c.execute("ALTER TABLE products ADD COLUMN code TEXT DEFAULT ''")
    except:
        pass
    try:
        c.execute("ALTER TABLE products ADD COLUMN buy_price REAL DEFAULT 0")
    except:
        pass

    # 🔹 جدول المبيعات
    c.execute("""
    CREATE TABLE IF NOT EXISTS sales (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id INTEGER,
        customer_name TEXT DEFAULT '',
        product_id INTEGER,
        product_name TEXT DEFAULT '',
        product_code TEXT DEFAULT '',
        unit TEXT DEFAULT '',
        quantity REAL DEFAULT 0,
        price_egp REAL DEFAULT 0,
        price_usd REAL DEFAULT 0,
        exchange_rate REAL DEFAULT 0,
        total_egp REAL DEFAULT 0,
        total_usd REAL DEFAULT 0,
        return_qty REAL DEFAULT 0,
        sale_date TEXT DEFAULT '',
        FOREIGN KEY(customer_id) REFERENCES customers(id)
    )
    """)

    # 🔹 جدول الفواتير (مبسط)
    c.execute("""
    CREATE TABLE IF NOT EXISTS invoices (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id INTEGER,
        date TEXT DEFAULT '',
        total REAL DEFAULT 0,
        status TEXT DEFAULT '',
        invoice_number TEXT DEFAULT '',
        paid REAL DEFAULT 0
    )
    """)

    # 🔹 جدول الإعدادات العامة (لحفظ شروط الدفع ومعلومات البنك)
    c.execute("""
    CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY,
        value TEXT
    )
    """)
    
    # 🔹 جدول متابعة الصادرات (Export Follow-Up)
    c.execute("""
    CREATE TABLE IF NOT EXISTS export_followup (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_name TEXT NOT NULL,
        invoice_number TEXT,
        product_name TEXT,
        quantity REAL DEFAULT 0,
        unit TEXT DEFAULT '',
        export_date TEXT,
        shipping_date TEXT,
        expected_arrival TEXT,
        actual_arrival TEXT,
        status TEXT DEFAULT 'قيد المعالجة',
        port TEXT DEFAULT '',
        container_number TEXT DEFAULT '',
        shipping_line TEXT DEFAULT '',
        bl_number TEXT DEFAULT '',
        payment_status TEXT DEFAULT 'غير مدفوع',
        notes TEXT DEFAULT '',
        created_at TEXT DEFAULT '',
        updated_at TEXT DEFAULT ''
    )
    """)

    # ✅ التأكد من وجود بيانات افتراضية
    default_settings = {
        "payment_terms": "Payment due within 30 days.",
        "bank_details": "Bank:\nAccount:\nIBAN:\nSWIFT:"
    }

    for k, v in default_settings.items():
        c.execute("SELECT 1 FROM settings WHERE key=?", (k,))
        if not c.fetchone():
            c.execute("INSERT INTO settings (key, value) VALUES (?, ?)", (k, v))

    conn.commit()
    conn.close()
    print("✅ Database setup completed successfully at:", DB_PATH)

if __name__ == '__main__':
    ensure_db()
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
        phone TEXT DEFAULT '',
        email TEXT DEFAULT '',
        company TEXT DEFAULT '',
        address TEXT DEFAULT '',
        rating INTEGER DEFAULT 0
    )
    """)

    # 🔹 جدول المنتجات
    c.execute("""
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_code TEXT UNIQUE,
        name TEXT NOT NULL,
        description TEXT DEFAULT '',
        quantity REAL DEFAULT 0,
        unit TEXT DEFAULT '',
        price_egp REAL DEFAULT 0,
        price_usd REAL DEFAULT 0,
        category TEXT DEFAULT ''
    )
    """)

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
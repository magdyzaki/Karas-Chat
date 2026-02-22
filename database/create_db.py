import sqlite3
import os

DB = os.path.join(os.path.dirname(__file__), "crm.db")

conn = sqlite3.connect(DB)
cur = conn.cursor()

# -------------------------------------------------------------------
# جدول العملاء
# -------------------------------------------------------------------
cur.execute("""
CREATE TABLE IF NOT EXISTS customers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    country TEXT,
    company TEXT,
    email TEXT,
    phone TEXT,
    category TEXT,
    status TEXT,
    notes TEXT,
    created_at TEXT
)
""")

# -------------------------------------------------------------------
# جدول المنتجات
# -------------------------------------------------------------------
cur.execute("""
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    quantity REAL,
    unit TEXT
)
""")

# -------------------------------------------------------------------
# جدول المبيعات
# -------------------------------------------------------------------
cur.execute("""
CREATE TABLE IF NOT EXISTS sales (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER,
    product_name TEXT,
    quantity REAL,
    unit TEXT,
    date TEXT
)
""")

conn.commit()
conn.close()

print("✓ Database initialized successfully")

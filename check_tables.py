import sqlite3, os

DB_PATH = os.path.join(os.path.dirname(__file__), "database", "crm.db")
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

tables = ["customers", "products", "sales"]
for t in tables:
    cursor.execute(f"PRAGMA table_info({t})")
    print(f"\n📋 Table: {t}")
    for col in cursor.fetchall():
        print(f"  - {col[1]}")

conn.close()
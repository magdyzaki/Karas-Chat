import sqlite3
import os

DB = os.path.join("database", "crm.db")

conn = sqlite3.connect(DB)
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS payments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sale_id INTEGER NOT NULL,
    amount REAL NOT NULL,
    method TEXT NOT NULL,
    note TEXT DEFAULT '',
    date TEXT NOT NULL
)
""")

conn.commit()
conn.close()

print(">>> Table payments created successfully!")
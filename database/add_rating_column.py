import sqlite3
import os

DB = os.path.join(os.path.dirname(__file__), "crm.db")

conn = sqlite3.connect(DB)
cur = conn.cursor()

try:
    cur.execute("ALTER TABLE customers ADD COLUMN rating TEXT")
    print("✓ Column 'rating' added successfully")
except Exception as e:
    print("• Column already exists or error:", e)

conn.commit()
conn.close()

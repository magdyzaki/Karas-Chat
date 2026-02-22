import sqlite3
import os

DB = os.path.join(os.path.dirname(__file__), "crm.db")

conn = sqlite3.connect(DB)
cur = conn.cursor()

# إضافة عمود product_code
try:
    cur.execute("ALTER TABLE products ADD COLUMN product_code TEXT")
    print("✓ Added column: product_code")
except:
    print("• Column product_code already exists")

# إضافة عمود price_egp
try:
    cur.execute("ALTER TABLE products ADD COLUMN price_egp REAL")
    print("✓ Added column: price_egp")
except:
    print("• Column price_egp already exists")

# إضافة عمود price_usd
try:
    cur.execute("ALTER TABLE products ADD COLUMN price_usd REAL")
    print("✓ Added column: price_usd")
except:
    print("• Column price_usd already exists")

conn.commit()
conn.close()

print("\n✓ Database updated successfully")

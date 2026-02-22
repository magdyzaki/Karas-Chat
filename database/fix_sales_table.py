import sqlite3
import os

DB = os.path.join(os.path.dirname(__file__), "crm.db")

conn = sqlite3.connect(DB)
cur = conn.cursor()

def add_column(col, dtype):
    try:
        cur.execute(f"ALTER TABLE sales ADD COLUMN {col} {dtype}")
        print(f"✓ Added column: {col}")
    except sqlite3.OperationalError:
        print(f"• Column exists: {col}")

print("\n--- Fixing sales table ---\n")

add_column("customer_id", "INTEGER")
add_column("customer_name", "TEXT")

add_column("product_id", "INTEGER")
add_column("product_name", "TEXT")
add_column("product_code", "TEXT")

add_column("unit", "TEXT")
add_column("quantity", "REAL")

add_column("price_egp", "REAL")
add_column("price_usd", "REAL")
add_column("exchange_rate", "REAL")

add_column("total_egp", "REAL")
add_column("total_usd", "REAL")

add_column("return_qty", "REAL")
add_column("sale_date", "TEXT")

conn.commit()
conn.close()

print("\n✓ Sales table is now fully compatible with SalesPage.py")

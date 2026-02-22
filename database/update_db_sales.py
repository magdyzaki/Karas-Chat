import sqlite3
import os

DB = os.path.join(os.path.dirname(__file__), "crm.db")

conn = sqlite3.connect(DB)
cur = conn.cursor()


def add_column(table, column, dtype):
    try:
        cur.execute(f"ALTER TABLE {table} ADD COLUMN {column} {dtype}")
        print(f"✓ Added column: {column}")
    except:
        print(f"• Column {column} already exists")


print("Updating sales table...\n")

# الأعمدة التي تحتاجها SalesPage
add_column("sales", "customer_id", "INTEGER")
add_column("sales", "customer_name", "TEXT")
add_column("sales", "price_egp", "REAL")
add_column("sales", "price_usd", "REAL")
add_column("sales", "total_price_egp", "REAL")
add_column("sales", "total_price_usd", "REAL")

conn.commit()
conn.close()

print("\n✓ Sales table updated successfully!")

# add_test_data.py
# سكريبت لإضافة بيانات تجريبية للبرنامج
import sqlite3
import os
from datetime import datetime

DB = os.path.join(os.path.dirname(__file__), "database", "crm.db")

def ensure_db():
    """التأكد من وجود قاعدة البيانات والجداول"""
    os.makedirs(os.path.dirname(DB), exist_ok=True)
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    
    # جدول العملاء
    cur.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            country TEXT DEFAULT '',
            company TEXT DEFAULT '',
            email TEXT DEFAULT '',
            phone TEXT DEFAULT '',
            rating TEXT DEFAULT '',
            created_at TEXT DEFAULT ''
        )
    """)
    
    # جدول المنتجات
    cur.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_code TEXT,
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
    
    # جدول المبيعات
    cur.execute("""
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
            sale_date TEXT DEFAULT ''
        )
    """)
    
    # جدول الموردين
    cur.execute("""
        CREATE TABLE IF NOT EXISTS suppliers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            phone TEXT DEFAULT '',
            address TEXT DEFAULT '',
            notes TEXT DEFAULT ''
        )
    """)
    
    # جدول المشتريات
    cur.execute("""
        CREATE TABLE IF NOT EXISTS purchases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            supplier TEXT,
            invoice_no TEXT,
            date TEXT,
            subtotal REAL DEFAULT 0,
            total REAL DEFAULT 0,
            note TEXT DEFAULT '',
            created_at TEXT
        )
    """)
    
    # جدول عناصر المشتريات
    cur.execute("""
        CREATE TABLE IF NOT EXISTS purchase_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            purchase_id INTEGER,
            product_id TEXT,
            product_code TEXT,
            product_name TEXT,
            unit TEXT,
            quantity REAL DEFAULT 0,
            unit_price REAL DEFAULT 0,
            line_total REAL DEFAULT 0,
            FOREIGN KEY(purchase_id) REFERENCES purchases(id)
        )
    """)
    
    # جدول الفواتير
    cur.execute("""
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
    
    # جدول المدفوعات
    cur.execute("""
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_name TEXT,
            sale_ids TEXT,
            sale_id TEXT,
            amount REAL,
            remaining REAL,
            receipt TEXT,
            method TEXT,
            created_at TEXT,
            note TEXT
        )
    """)
    
    conn.commit()
    conn.close()

def add_test_data():
    """إضافة البيانات التجريبية"""
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # 1. إضافة عميلين
    print("إضافة عملاء...")
    customers = [
        ("أحمد محمد", "مصر", "شركة النور للتجارة", "ahmed@example.com", "+20 100 123 4567", "Hot", now),
        ("سارة علي", "السعودية", "مؤسسة الخير", "sara@example.com", "+966 50 987 6543", "Warm", now)
    ]
    
    customer_ids = []
    for cust in customers:
        cur.execute("""
            INSERT INTO customers (name, country, company, email, phone, rating, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, cust)
        customer_ids.append(cur.lastrowid)
        print(f"   تم إضافة العميل: {cust[0]}")
    
    # 2. إضافة منتجين بكمية 100 طن لكل منهما
    print("\nإضافة منتجات...")
    products = [
        ("P-001", "P-001", "قمح", "قمح عالي الجودة", 100.0, "طن", 5000.0, 250.0, 200.0, "حبوب"),
        ("P-002", "P-002", "ذرة", "ذرة صفراء ممتازة", 100.0, "طن", 4500.0, 220.0, 180.0, "حبوب")
    ]
    
    product_ids = []
    for prod in products:
        # محاولة إدراج مع جميع الأعمدة
        try:
            cur.execute("""
                INSERT INTO products (product_code, code, name, description, quantity, unit, 
                                     price_egp, price_usd, buy_price, category)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, prod)
        except:
            # إذا فشل، نستخدم الأعمدة الأساسية فقط
            try:
                cur.execute("""
                    INSERT INTO products (product_code, name, description, quantity, unit, 
                                         price_egp, price_usd, category)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (prod[0], prod[2], prod[3], prod[4], prod[5], prod[6], prod[7], prod[9]))
            except:
                cur.execute("""
                    INSERT INTO products (name, quantity, unit, price_egp, price_usd)
                    VALUES (?, ?, ?, ?, ?)
                """, (prod[2], prod[4], prod[5], prod[6], prod[7]))
        product_ids.append(cur.lastrowid)
        print(f"   تم إضافة المنتج: {prod[2]} - الكمية: {prod[4]} {prod[5]}")
    
    # 3. إضافة مبيعين (50 طن من كل منتج)
    print("\nإضافة مبيعات...")
    sales_data = [
        (customer_ids[0], "أحمد محمد", product_ids[0], "قمح", "P-001", "طن", 50.0, 
         5000.0, 250.0, 50.0, 250000.0, 12500.0, 0.0, now),
        (customer_ids[1], "سارة علي", product_ids[1], "ذرة", "P-002", "طن", 50.0,
         4500.0, 220.0, 50.0, 225000.0, 11000.0, 0.0, now)
    ]
    
    sale_ids = []
    for sale in sales_data:
        cur.execute("""
            INSERT INTO sales (customer_id, customer_name, product_id, product_name, product_code,
                              unit, quantity, price_egp, price_usd, exchange_rate,
                              total_egp, total_usd, return_qty, sale_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, sale)
        sale_ids.append(cur.lastrowid)
        print(f"   تم إضافة بيع: {sale[3]} - الكمية: {sale[6]} {sale[5]}")
    
    # 4. إضافة مرتجع 10 طن من أول منتج
    print("\nإضافة مرتجع...")
    cur.execute("""
        UPDATE sales 
        SET return_qty = 10.0,
            total_egp = ?,
            total_usd = ?
        WHERE id = ?
    """, (
        40.0 * 5000.0,  # الكمية الصافية × السعر
        40.0 * 250.0,
        sale_ids[0]
    ))
    print(f"   تم إضافة مرتجع: 10 طن من قمح")
    
    # 5. إضافة موردين
    print("\nإضافة موردين...")
    suppliers = [
        ("شركة المزارع الحديثة", "+20 100 111 2222", "القاهرة - مصر", "مورد رئيسي للحبوب"),
        ("مؤسسة الأغذية المتحدة", "+966 50 222 3333", "الرياض - السعودية", "مورد موثوق للمنتجات الزراعية")
    ]
    
    supplier_ids = []
    for supp in suppliers:
        cur.execute("""
            INSERT INTO suppliers (name, phone, address, notes)
            VALUES (?, ?, ?, ?)
        """, supp)
        supplier_ids.append(cur.lastrowid)
        print(f"   تم إضافة المورد: {supp[0]}")
    
    # 6. إضافة مشتريات
    print("\nإضافة مشتريات...")
    
    # مشتريات من المورد الأول
    purchase_date1 = datetime.now().strftime("%Y-%m-%d")
    cur.execute("""
        INSERT INTO purchases (supplier, invoice_no, date, subtotal, total, note, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        suppliers[0][0],
        "INV-001",
        purchase_date1,
        20000.0,  # 100 طن × 200 جنيه
        20000.0,
        "شراء قمح",
        now
    ))
    purchase_id1 = cur.lastrowid
    
    # عناصر المشتريات الأولى
    cur.execute("""
        INSERT INTO purchase_items (purchase_id, product_code, product_name, unit, quantity, unit_price, line_total)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        purchase_id1,
        "P-001",
        "قمح",
        "طن",
        100.0,
        200.0,
        20000.0
    ))
    print(f"   تم إضافة مشتريات: 100 طن قمح من {suppliers[0][0]}")
    
    # مشتريات من المورد الثاني
    purchase_date2 = datetime.now().strftime("%Y-%m-%d")
    cur.execute("""
        INSERT INTO purchases (supplier, invoice_no, date, subtotal, total, note, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        suppliers[1][0],
        "INV-002",
        purchase_date2,
        18000.0,  # 100 طن × 180 جنيه
        18000.0,
        "شراء ذرة",
        now
    ))
    purchase_id2 = cur.lastrowid
    
    # عناصر المشتريات الثانية
    cur.execute("""
        INSERT INTO purchase_items (purchase_id, product_code, product_name, unit, quantity, unit_price, line_total)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        purchase_id2,
        "P-002",
        "ذرة",
        "طن",
        100.0,
        180.0,
        18000.0
    ))
    print(f"   تم إضافة مشتريات: 100 طن ذرة من {suppliers[1][0]}")
    
    # 7. إضافة فواتير
    print("\nإضافة فواتير...")
    
    # فاتورة للعميل الأول (أحمد محمد)
    invoice_date1 = datetime.now().strftime("%Y-%m-%d")
    invoice_total1 = 12500.0  # إجمالي المبيعات بالدولار
    cur.execute("""
        INSERT INTO invoices (customer_id, date, total, status, invoice_number, paid)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        customer_ids[0],
        invoice_date1,
        invoice_total1,
        "مدفوعة جزئياً",
        "INV-2024-001",
        5000.0  # تم دفع 5000 دولار
    ))
    invoice_id1 = cur.lastrowid
    print(f"   تم إضافة فاتورة: INV-2024-001 للعميل أحمد محمد - الإجمالي: ${invoice_total1:.2f}")
    
    # فاتورة للعميل الثاني (سارة علي)
    invoice_date2 = datetime.now().strftime("%Y-%m-%d")
    invoice_total2 = 11000.0  # إجمالي المبيعات بالدولار
    cur.execute("""
        INSERT INTO invoices (customer_id, date, total, status, invoice_number, paid)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        customer_ids[1],
        invoice_date2,
        invoice_total2,
        "مدفوعة",
        "INV-2024-002",
        11000.0  # تم دفع المبلغ كاملاً
    ))
    invoice_id2 = cur.lastrowid
    print(f"   تم إضافة فاتورة: INV-2024-002 للعميل سارة علي - الإجمالي: ${invoice_total2:.2f}")
    
    # 8. إضافة تحصيل مدفوعات
    print("\nإضافة تحصيل مدفوعات...")
    
    # دفعة أولى من العميل الأول (5000 دولار)
    payment_date1 = datetime.now().strftime("%Y-%m-%d")
    cur.execute("""
        INSERT INTO payments (customer_name, sale_ids, sale_id, amount, remaining, receipt, method, created_at, note)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        "أحمد محمد",
        str(sale_ids[0]),  # sale_ids
        str(sale_ids[0]),  # sale_id
        5000.0,  # amount
        7500.0,  # remaining (12500 - 5000)
        "REC-001",
        "Bank Transfer",
        payment_date1,
        "دفعة أولى - 40% من إجمالي الفاتورة"
    ))
    print(f"   تم إضافة دفعة: 5000 USD من أحمد محمد - المتبقي: 7500 USD")
    
    # دفعة كاملة من العميل الثاني (11000 دولار)
    payment_date2 = datetime.now().strftime("%Y-%m-%d")
    cur.execute("""
        INSERT INTO payments (customer_name, sale_ids, sale_id, amount, remaining, receipt, method, created_at, note)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        "سارة علي",
        str(sale_ids[1]),  # sale_ids
        str(sale_ids[1]),  # sale_id
        11000.0,  # amount
        0.0,  # remaining (مدفوعة بالكامل)
        "REC-002",
        "Cash",
        payment_date2,
        "دفعة كاملة - تم السداد"
    ))
    print(f"   تم إضافة دفعة: 11000 USD من سارة علي - مدفوعة بالكامل")
    
    # دفعة ثانية من العميل الأول (2500 دولار)
    payment_date3 = datetime.now().strftime("%Y-%m-%d")
    cur.execute("""
        INSERT INTO payments (customer_name, sale_ids, sale_id, amount, remaining, receipt, method, created_at, note)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        "أحمد محمد",
        str(sale_ids[0]),  # sale_ids
        str(sale_ids[0]),  # sale_id
        2500.0,  # amount
        5000.0,  # remaining (7500 - 2500)
        "REC-003",
        "Cheque",
        payment_date3,
        "دفعة ثانية - 20% من إجمالي الفاتورة"
    ))
    print(f"   تم إضافة دفعة: 2500 USD من أحمد محمد - المتبقي: 5000 USD")
    
    conn.commit()
    conn.close()
    
    print("\nتمت إضافة جميع البيانات التجريبية بنجاح!")
    print(f"\nملخص البيانات:")
    print(f"   - عدد العملاء: 2")
    print(f"   - عدد المنتجات: 2 (100 طن لكل منتج)")
    print(f"   - عدد المبيعات: 2 (50 طن لكل منتج)")
    print(f"   - المرتجعات: 10 طن من قمح")
    print(f"   - عدد الموردين: 2")
    print(f"   - عدد المشتريات: 2")
    print(f"   - عدد الفواتير: 2")
    print(f"   - عدد المدفوعات: 3")
    print(f"   - المخزون المتبقي: قمح 50 طن، ذرة 50 طن")

if __name__ == "__main__":
    ensure_db()
    add_test_data()

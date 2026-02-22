"""
تحسينات الأداء لقاعدة البيانات
Database Performance Optimizations
"""
from .db import get_connection


def create_performance_indexes():
    """إنشاء فهارس لتحسين أداء قاعدة البيانات"""
    conn = get_connection()
    cur = conn.cursor()
    
    try:
        # فهارس على جدول clients
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_clients_email 
            ON clients(email)
        """)
        
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_clients_classification 
            ON clients(classification)
        """)
        
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_clients_status 
            ON clients(status)
        """)
        
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_clients_score 
            ON clients(seriousness_score)
        """)
        
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_clients_focus 
            ON clients(is_focus)
        """)
        
        # فهارس على جدول messages
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_messages_client_id 
            ON messages(client_id)
        """)
        
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_messages_date 
            ON messages(message_date)
        """)
        
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_messages_channel 
            ON messages(channel)
        """)
        
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_messages_type 
            ON messages(message_type)
        """)
        
        # فهارس على جدول requests
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_requests_client_id 
            ON requests(client_id)
        """)
        
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_requests_status 
            ON requests(status)
        """)
        
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_requests_reply_status 
            ON requests(reply_status)
        """)
        
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_requests_type 
            ON requests(request_type)
        """)
        
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_requests_created 
            ON requests(created_at)
        """)
        
        # فهارس على جدول sales_deals
        try:
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_deals_client_id 
                ON sales_deals(client_id)
            """)
            
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_deals_stage 
                ON sales_deals(stage)
            """)
            
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_deals_status 
                ON sales_deals(status)
            """)
        except:
            pass  # الجدول قد لا يكون موجوداً
        
        conn.commit()
        return True
        
    except Exception as e:
        print(f"Error creating performance indexes: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


def optimize_database():
    """تحسين قاعدة البيانات (VACUUM, ANALYZE)"""
    conn = get_connection()
    cur = conn.cursor()
    
    try:
        # VACUUM - إعادة تنظيم قاعدة البيانات
        cur.execute("VACUUM")
        
        # ANALYZE - تحديث إحصائيات الاستعلام
        cur.execute("ANALYZE")
        
        conn.commit()
        return True
    except Exception as e:
        print(f"Error optimizing database: {e}")
        return False
    finally:
        conn.close()

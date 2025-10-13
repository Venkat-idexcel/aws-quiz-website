"""
Simple script to test database connectivity and table existence
"""
import psycopg2
from config import Config

def test_database():
    config = Config()
    
    try:
        print("Connecting to database...")
        conn = psycopg2.connect(
            host=config.DB_HOST,
            port=config.DB_PORT,
            database=config.DB_NAME,
            user=config.DB_USER,
            password=config.DB_PASSWORD,
            connect_timeout=5
        )
        
        cur = conn.cursor()
        
        # Check tables
        cur.execute("""
            SELECT table_name FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
            ORDER BY table_name
        """)
        tables = [row[0] for row in cur.fetchall()]
        
        print(f"\n✅ Connected to: {config.DB_NAME}")
        print(f"   Host: {config.DB_HOST}:{config.DB_PORT}")
        print(f"\nTables found: {len(tables)}")
        for table in tables:
            print(f"  - {table}")
        
        # Count records
        if 'users' in tables:
            cur.execute("SELECT COUNT(*) FROM users")
            print(f"\nUsers: {cur.fetchone()[0]}")
        
        if 'questions' in tables:
            cur.execute("SELECT COUNT(*) FROM questions")
            print(f"Questions: {cur.fetchone()[0]}")
        
        cur.close()
        conn.close()
        
        print("\n✅ Database test successful!")
        return True
        
    except Exception as e:
        print(f"\n❌ Database test failed: {e}")
        return False

if __name__ == '__main__':
    test_database()

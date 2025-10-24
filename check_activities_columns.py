import psycopg2
from config import Config

def check_activities_columns():
    """Check what columns exist in the user_activities table"""
    try:
        conn = psycopg2.connect(
            dbname=Config.DB_NAME,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            host=Config.DB_HOST,
            port=Config.DB_PORT
        )
        
        cur = conn.cursor()
        cur.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'user_activities'
            ORDER BY ordinal_position
        """)
        columns = cur.fetchall()
        
        print("=== User Activities Table Columns ===")
        for col in columns:
            print(f"  - {col[0]}: {col[1]}")
        
        conn.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_activities_columns()

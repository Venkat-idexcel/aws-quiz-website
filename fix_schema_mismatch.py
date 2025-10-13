"""
Fix schema mismatch - Add missing columns and update existing data
"""
import psycopg2
from config import Config

conn = psycopg2.connect(
    host=Config.DB_HOST,
    port=Config.DB_PORT,
    database=Config.DB_NAME,
    user=Config.DB_USER,
    password=Config.DB_PASSWORD
)

cur = conn.cursor()

try:
    print("Adding started_at and completed_at columns...")
    
    # Add started_at column (copy from start_time)
    cur.execute("""
        ALTER TABLE quiz_sessions 
        ADD COLUMN IF NOT EXISTS started_at TIMESTAMP WITH TIME ZONE
    """)
    
    # Add completed_at column (copy from end_time)
    cur.execute("""
        ALTER TABLE quiz_sessions 
        ADD COLUMN IF NOT EXISTS completed_at TIMESTAMP WITH TIME ZONE
    """)
    
    # Add time_taken_minutes column
    cur.execute("""
        ALTER TABLE quiz_sessions 
        ADD COLUMN IF NOT EXISTS time_taken_minutes INTEGER
    """)
    
    # Copy existing data
    cur.execute("""
        UPDATE quiz_sessions 
        SET started_at = start_time,
            completed_at = end_time,
            time_taken_minutes = EXTRACT(EPOCH FROM (end_time - start_time)) / 60
        WHERE started_at IS NULL
    """)
    
    conn.commit()
    print("✅ Schema updated successfully!")
    
    # Verify
    cur.execute("""
        SELECT COUNT(*) FROM quiz_sessions 
        WHERE started_at IS NOT NULL
    """)
    count = cur.fetchone()[0]
    print(f"✅ {count} quiz sessions have started_at set")
    
    cur.execute("""
        SELECT COUNT(*) FROM quiz_sessions 
        WHERE completed_at IS NOT NULL
    """)
    count = cur.fetchone()[0]
    print(f"✅ {count} quiz sessions have completed_at set")
    
except Exception as e:
    print(f"❌ Error: {e}")
    conn.rollback()
finally:
    cur.close()
    conn.close()

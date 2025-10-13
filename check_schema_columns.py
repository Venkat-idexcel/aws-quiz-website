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

print("\n=== quiz_sessions table columns ===")
cur.execute("""
    SELECT column_name, data_type 
    FROM information_schema.columns 
    WHERE table_name = 'quiz_sessions' 
    ORDER BY ordinal_position
""")

for row in cur.fetchall():
    print(f"{row[0]}: {row[1]}")

cur.close()
conn.close()

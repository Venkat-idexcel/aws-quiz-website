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

cur.execute("SELECT column_name, data_type, is_nullable FROM information_schema.columns WHERE table_name = 'questions' ORDER BY ordinal_position")

print('Database schema for questions table:')
for row in cur.fetchall():
    print(f'  {row[0]}: {row[1]} (nullable: {row[2]})')

conn.close()
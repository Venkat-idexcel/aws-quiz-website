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

# Get questions table schema
cur.execute("""
    SELECT column_name, data_type, character_maximum_length, is_nullable 
    FROM information_schema.columns 
    WHERE table_name='questions' 
    ORDER BY ordinal_position
""")

print("\n📋 Questions Table Schema:")
print("="*80)
for col_name, data_type, max_len, nullable in cur.fetchall():
    max_len_str = str(max_len) if max_len else "unlimited"
    print(f"  {col_name:20} {data_type:15}({max_len_str:10}) {'NULL' if nullable == 'YES' else 'NOT NULL'}")

# Check current question count
cur.execute("SELECT COUNT(*) FROM questions WHERE category = 'Cloud Practitioner Practice Test'")
count = cur.fetchone()[0]
print(f"\n📊 Current Cloud Practitioner Practice Test questions: {count}")

# Check latest question ID
cur.execute("""
    SELECT question_id FROM questions 
    WHERE category = 'Cloud Practitioner Practice Test' 
    AND question_id LIKE 'CP_%' 
    ORDER BY question_id DESC 
    LIMIT 1
""")
result = cur.fetchone()
latest_id = result[0] if result else "None"
print(f"📝 Latest question ID: {latest_id}")

conn.close()

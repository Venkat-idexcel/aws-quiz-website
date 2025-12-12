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

cur.execute("SELECT COUNT(*) FROM questions WHERE category = 'Cloud Practitioner Practice Test'")
count = cur.fetchone()[0]
print(f'Total Cloud Practitioner Practice Test questions: {count}')

# Get sample questions to verify
cur.execute("SELECT question_id, question, correct_answer FROM questions WHERE category = 'Cloud Practitioner Practice Test' LIMIT 3")
samples = cur.fetchall()

print("\nSample questions:")
for i, sample in enumerate(samples, 1):
    print(f"{i}. ID: {sample[0]}")
    print(f"   Q: {sample[1][:80]}...")
    print(f"   Answer: {sample[2]}")

conn.close()
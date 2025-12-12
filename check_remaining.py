"""
Check the remaining 9 issues
"""
import psycopg2
from config import Config

config = Config()
conn = psycopg2.connect(
    host=config.DB_HOST,
    port=config.DB_PORT,
    database=config.DB_NAME,
    user=config.DB_USER,
    password=config.DB_PASSWORD
)
cur = conn.cursor()

# Check for answers ending with ,E
cur.execute("""
    SELECT question_id, question, correct_answer
    FROM questions 
    WHERE category = 'Cloud Practitioner Practice Test' 
    AND correct_answer LIKE '%,E'
    ORDER BY question_id
""")

results = cur.fetchall()
print(f"Found {len(results)} questions with bad correct_answer format:\n")

for q_id, question, answer in results:
    print(f"{q_id}: {answer}")
    print(f"  Question: {question[:80]}...")
    print()

cur.close()
conn.close()

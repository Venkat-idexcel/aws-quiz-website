"""
Direct fix for CP_0780 and similar questions
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

# Check all multi-select questions across entire database
cur.execute("""
    SELECT question_id, question, correct_answer
    FROM questions 
    WHERE category = 'Cloud Practitioner Practice Test' 
    AND (question LIKE '%Choose two%' OR question LIKE '%Choose TWO%' OR question LIKE '%Select 2%' 
         OR question LIKE '%(Choose two)%' OR question LIKE '%choose two%' OR question LIKE '%Select TWO%'
         OR question LIKE '%select 2%' OR question LIKE '%Select TWO%')
    AND correct_answer NOT LIKE '%,%'
    ORDER BY question_id
""")

results = cur.fetchall()
print(f"Total multi-select questions with only one answer: {len(results)}\n")

for q_id, question, answer in results[:20]:  # Show first 20
    print(f"{q_id}: {answer}")
    print(f"  Q: {question[:80]}...")
    print()

cur.close()
conn.close()

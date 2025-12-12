"""
Check multi-select questions with only one answer
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

cur.execute("""
    SELECT question_id, question, correct_answer, option_a, option_b, option_c, option_d
    FROM questions 
    WHERE category = 'Cloud Practitioner Practice Test' 
    AND (question LIKE '%Choose two%' OR question LIKE '%Choose TWO%' OR question LIKE '%Select 2%' 
         OR question LIKE '%(Choose two)%' OR question LIKE '%choose two%')
    AND correct_answer NOT LIKE '%,%'
    ORDER BY question_id
    LIMIT 10
""")

results = cur.fetchall()
print(f"Found {cur.rowcount} multi-select questions with only one answer\n")
print("Sample questions:\n")

for q_id, question, answer, opt_a, opt_b, opt_c, opt_d in results:
    print(f"{q_id}: Answer = {answer}")
    print(f"  Q: {question[:100]}...")
    print(f"  A: {opt_a[:50] if opt_a else 'N/A'}")
    print(f"  B: {opt_b[:50] if opt_b else 'N/A'}")
    print(f"  C: {opt_c[:50] if opt_c else 'N/A'}")
    print(f"  D: {opt_d[:50] if opt_d else 'N/A'}")
    print()

cur.close()
conn.close()

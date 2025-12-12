"""
Direct fix for CP_0780 and all similar questions
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

# Fix CP_0780 specifically
cur.execute("""
    UPDATE questions
    SET option_e = 'Application Load Balancers',
        correct_answer = 'C,E'
    WHERE question_id = 'CP_0780'
""")

affected = cur.rowcount
conn.commit()

print(f"Updated {affected} rows")

# Verify
cur.execute("""
    SELECT question_id, question, option_e, correct_answer
    FROM questions
    WHERE question_id = 'CP_0780'
""")

result = cur.fetchone()
if result:
    print(f"\nVerification:")
    print(f"ID: {result[0]}")
    print(f"Question: {result[1][:80]}")
    print(f"Option E: {result[2]}")
    print(f"Correct Answer: {result[3]}")

cur.close()
conn.close()

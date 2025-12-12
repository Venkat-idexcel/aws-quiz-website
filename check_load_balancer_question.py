"""
Check the specific question about load balancers
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
    AND question LIKE '%load balancer types are available%'
""")

result = cur.fetchone()
if result:
    q_id, question, answer, opt_a, opt_b, opt_c, opt_d = result
    print(f"Question ID: {q_id}")
    print(f"Question: {question}")
    print(f"Correct Answer: '{answer}'")
    print(f"Answer length: {len(answer)}")
    print(f"Contains comma: {', ' in answer or ',' in answer}")
    
    # Count answers
    answers = [x.strip() for x in answer.split(',') if x.strip()]
    print(f"Answer parts: {answers}")
    print(f"Answer count: {len(answers)}")
    
    print(f"\nOptions:")
    print(f"A: {opt_a}")
    print(f"B: {opt_b}")
    print(f"C: {opt_c}")
    print(f"D: {opt_d}")
else:
    print("Question not found")

cur.close()
conn.close()

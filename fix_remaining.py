"""
Fix the remaining 9 questions - these are multi-select questions where E is a valid second answer
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

# Get the 9 remaining questions
cur.execute("""
    SELECT question_id, question, correct_answer
    FROM questions 
    WHERE category = 'Cloud Practitioner Practice Test' 
    AND correct_answer LIKE '%,E'
    ORDER BY question_id
""")

results = cur.fetchall()
print(f"Checking {len(results)} questions:\n")

fixed = 0
for q_id, question, answer in results:
    # Check if these are multi-select questions
    is_multi_select = any(x in question for x in ["Choose two", "Choose TWO", "Select 2", "(Choose two)", "choose two"])
    
    if is_multi_select:
        # This is correct - they should have 2 answers
        print(f"{q_id}: {answer} - OK (multi-select question)")
    else:
        # Single select - remove the ,E
        new_answer = answer.split(',')[0]
        print(f"{q_id}: {answer} -> {new_answer} (single-select, fixing...)")
        
        cur.execute("""
            UPDATE questions
            SET correct_answer = %s
            WHERE question_id = %s
        """, (new_answer, q_id))
        fixed += 1

if fixed > 0:
    conn.commit()
    print(f"\nFixed {fixed} questions")
else:
    print("\nAll 9 questions are multi-select - answers are correct!")

cur.close()
conn.close()

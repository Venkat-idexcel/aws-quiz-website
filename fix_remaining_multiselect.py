"""
Fix remaining multi-select questions from aws_practicetest_20 JSON files
"""
import psycopg2
import json
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

# Load the practicetest JSON
with open('data/aws_practicetest_20_questions_cleaned.json', 'r', encoding='utf-8') as f:
    json_questions = json.load(f)

print(f"Loaded {len(json_questions)} questions from practicetest JSON")

# Get multi-select questions that still only have one answer (likely CP_05xx to CP_08xx range)
cur.execute("""
    SELECT question_id, question, correct_answer
    FROM questions 
    WHERE category = 'Cloud Practitioner Practice Test' 
    AND question_id >= 'CP_0500'
    AND (question LIKE '%Choose two%' OR question LIKE '%Choose TWO%' OR question LIKE '%Select 2%' 
         OR question LIKE '%(Choose two)%' OR question LIKE '%choose two%' OR question LIKE '%Select TWO%')
    AND correct_answer NOT LIKE '%,%'
    ORDER BY question_id
""")

db_questions = cur.fetchall()
print(f"Found {len(db_questions)} multi-select questions with only one answer (CP_0500+)\n")

# Create a mapping by normalizing question text
question_map = {}
for q in json_questions:
    q_text_norm = q['question'].strip().lower().replace('\n', ' ')[:100]
    # Clean the answer - remove duplicate ,E and explanation text
    answer = q['answer'].strip()
    # If answer has ,E,E pattern, convert to ,E
    if ',E,E' in answer:
        answer = answer.replace(',E,E', ',E')
    question_map[q_text_norm] = answer

fixed = 0
for q_id, question, current_answer in db_questions:
    q_norm = question.strip().lower().replace('\n', ' ')[:100]
    
    if q_norm in question_map:
        correct_answer = question_map[q_norm]
        
        # Only update if it has multiple answers
        if ',' in correct_answer:
            print(f"Fixing {q_id}: '{current_answer}' -> '{correct_answer}'")
            
            cur.execute("""
                UPDATE questions
                SET correct_answer = %s
                WHERE question_id = %s
            """, (correct_answer, q_id))
            fixed += 1
    else:
        print(f"Not found: {q_id} - {question[:60]}...")

conn.commit()
print(f"\nFixed {fixed} questions")

cur.close()
conn.close()

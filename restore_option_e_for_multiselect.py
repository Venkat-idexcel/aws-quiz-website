"""
Restore option_e for multi-select questions from original JSON files
Many multi-select questions need option_e to have two valid choices
"""
import psycopg2
import json
import re
from config import Config

def clean_option(text):
    """Extract just the option text before 'Correct Answer:'"""
    if not text:
        return None
    # Remove explanation text
    if "Correct Answer:" in text:
        text = text.split("Correct Answer:")[0].strip()
    return text if text else None

config = Config()
conn = psycopg2.connect(
    host=config.DB_HOST,
    port=config.DB_PORT,
    database=config.DB_NAME,
    user=config.DB_USER,
    password=config.DB_PASSWORD
)
cur = conn.cursor()

# Load both JSON files
json_data = []

# Load aws_practitioner_questions.json (CP_0001 to CP_0499)
with open('data/aws_practitioner_questions.json', 'r', encoding='utf-8') as f:
    data1 = json.load(f)
    for q in data1:
        json_data.append({
            'id': q['question_id'],
            'option_e': q.get('option_e', ''),
            'answer': q.get('correct_answer', '')
        })

# Load aws_practicetest_20_questions_cleaned.json (CP_0500+)
with open('data/aws_practicetest_20_questions_cleaned.json', 'r', encoding='utf-8') as f:
    data2 = json.load(f)
    # Map by question text since these don't have question_id
    for i, q in enumerate(data2):
        # Try to estimate question_id based on position
        q_id = f"CP_{500 + i:04d}"
        option_e_raw = q['options'].get('E', '')
        answer_raw = q.get('answer', '')
        
        # Clean option_e
        option_e_clean = clean_option(option_e_raw)
        
        # Clean answer - remove duplicate E
        answer_clean = answer_raw.replace(',E,E', ',E').strip()
        
        json_data.append({
            'id': q_id,
            'option_e': option_e_clean,
            'answer': answer_clean,
            'question': q['question'][:80]
        })

print(f"Loaded {len(json_data)} questions from JSON files\n")

# Get multi-select questions from database
cur.execute("""
    SELECT question_id, question, option_e, correct_answer
    FROM questions 
    WHERE category = 'Cloud Practitioner Practice Test' 
    AND (question LIKE '%Choose two%' OR question LIKE '%Choose TWO%' OR question LIKE '%Select 2%' 
         OR question LIKE '%(Choose two)%' OR question LIKE '%choose two%' OR question LIKE '%Select TWO%'
         OR question LIKE '%select 2%' OR question LIKE '%Select TWO%' OR question LIKE '%(choose two)%')
    ORDER BY question_id
""")

db_questions = cur.fetchall()
print(f"Found {len(db_questions)} multi-select questions in database\n")

# Create lookup by question_id
json_lookup = {item['id']: item for item in json_data}

fixed_count = 0
restored_option_e = 0
fixed_answers = 0

for q_id, question, current_option_e, current_answer in db_questions:
    if q_id in json_lookup:
        json_q = json_lookup[q_id]
        needs_update = False
        new_option_e = current_option_e
        new_answer = current_answer
        
        # Restore option_e if it's missing but should exist
        if (not current_option_e or current_option_e.strip() == '') and json_q['option_e']:
            new_option_e = json_q['option_e']
            needs_update = True
            restored_option_e += 1
            print(f"Restoring option_e for {q_id}")
            print(f"  E: {new_option_e[:60]}...")
        
        # Fix answer if it only has one value but should have two
        if ',' not in current_answer and ',' in json_q['answer']:
            new_answer = json_q['answer']
            needs_update = True
            fixed_answers += 1
            print(f"Fixing answer for {q_id}: '{current_answer}' -> '{new_answer}'")
        
        if needs_update:
            cur.execute("""
                UPDATE questions
                SET option_e = %s, correct_answer = %s
                WHERE question_id = %s
            """, (new_option_e, new_answer, q_id))
            fixed_count += 1

conn.commit()
print(f"\n=== Summary ===")
print(f"Total questions updated: {fixed_count}")
print(f"Option_e restored: {restored_option_e}")
print(f"Answers fixed: {fixed_answers}")

cur.close()
conn.close()

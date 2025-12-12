"""
Restore correct answers for multi-select questions from original JSON file
"""
import psycopg2
import json
from config import Config

def restore_multi_select_answers():
    # Load original JSON data - this file has the correct answers
    with open("data/aws_practitioner_questions.json", "r", encoding="utf-8") as f:
        json_questions = json.load(f)
    
    print(f"Loaded {len(json_questions)} questions from JSON file")
    
    # Create a mapping of question_id to correct answer
    question_answers = {}
    for q in json_questions:
        q_id = q["question_id"]
        answer = q["correct_answer"]
        question_answers[q_id] = answer
    
    print(f"Created answer mapping for {len(question_answers)} questions")
    
    # Connect to database
    config = Config()
    conn = psycopg2.connect(
        host=config.DB_HOST,
        port=config.DB_PORT,
        database=config.DB_NAME,
        user=config.DB_USER,
        password=config.DB_PASSWORD
    )
    cur = conn.cursor()
    
    # Get multi-select questions with only one answer
    cur.execute("""
        SELECT question_id, question, correct_answer
        FROM questions 
        WHERE category = 'Cloud Practitioner Practice Test' 
        AND (question LIKE '%Choose two%' OR question LIKE '%Choose TWO%' OR question LIKE '%Select 2%' 
             OR question LIKE '%(Choose two)%' OR question LIKE '%choose two%' OR question LIKE '%Select TWO%')
        AND correct_answer NOT LIKE '%,%'
        ORDER BY question_id
    """)
    
    db_questions = cur.fetchall()
    print(f"\nFound {len(db_questions)} multi-select questions with only one answer")
    
    fixed = 0
    not_found = 0
    
    for q_id, question, current_answer in db_questions:
        # Try to find match in JSON by question_id
        if q_id in question_answers:
            correct_answer = question_answers[q_id]
            
            # Only update if it's different and has multiple answers
            if ',' in correct_answer and correct_answer != current_answer:
                cur.execute("""
                    UPDATE questions
                    SET correct_answer = %s
                    WHERE question_id = %s
                """, (correct_answer, q_id))
                print(f"Fixed {q_id}: {current_answer} -> {correct_answer}")
                fixed += 1
        else:
            not_found += 1
            print(f"Not found: {q_id} - {question[:60]}...")
    
    conn.commit()
    print(f"\nFixed {fixed} multi-select questions")
    print(f"Not found in JSON: {not_found}")
    
    cur.close()
    conn.close()

if __name__ == '__main__':
    restore_multi_select_answers()

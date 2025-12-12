#!/usr/bin/env python3
"""
Import remaining questions in small batches to avoid interruption
"""

import json
import psycopg2
from config import Config
import sys

def get_current_count():
    config = Config()
    conn = psycopg2.connect(
        host=config.DB_HOST,
        port=config.DB_PORT,
        database=config.DB_NAME,
        user=config.DB_USER,
        password=config.DB_PASSWORD
    )
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM questions WHERE category = 'Cloud Practitioner Practice Test'")
    count = cur.fetchone()[0]
    conn.close()
    return count

def import_batch(start_index, batch_size=10):
    """Import a small batch of questions"""
    try:
        # Load questions
        with open("data/aws_practicetest_20_questions_cleaned.json", "r", encoding="utf-8") as f:
            all_questions = json.load(f)
        
        # Calculate which questions to import
        # We've already imported 55 questions (5 test + 50 from batch)
        # So we need to start from index 55 in our JSON
        questions_to_import = all_questions[55 + start_index:55 + start_index + batch_size]
        
        if not questions_to_import:
            print("No more questions to import")
            return 0
            
        print(f"Importing batch starting at index {start_index}, {len(questions_to_import)} questions...")
        
        # Connect to database
        config = Config()
        conn = psycopg2.connect(
            host=config.DB_HOST,
            port=config.DB_PORT,
            database=config.DB_NAME,
            user=config.DB_USER,
            password=config.DB_PASSWORD
        )
        
        cursor = conn.cursor()
        
        # Get current count for ID generation
        current_count = get_current_count()
        next_num = current_count + 1
        
        imported = 0
        for i, question_data in enumerate(questions_to_import):
            question_id = f"CP_{next_num + i:04d}"
            
            cursor.execute("""
                INSERT INTO questions (
                    question_id, question, option_a, option_b, option_c, option_d, option_e,
                    correct_answer, explanation, category, difficulty_level
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
            """, (
                question_id,
                question_data["question"],
                question_data["options"].get('A', ''),
                question_data["options"].get('B', ''),
                question_data["options"].get('C', ''),
                question_data["options"].get('D', ''),
                question_data["options"].get('E', ''),
                question_data["answer"],
                '',
                'Cloud Practitioner Practice Test',
                'Intermediate'
            ))
            
            imported += 1
            print(f"  ✅ {question_id}: {question_data['question'][:50]}...")
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print(f"✅ Batch completed: {imported} questions imported")
        return imported
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return 0

if __name__ == "__main__":
    # Check how many we need to import
    current = get_current_count()
    target = 991  # 499 original + 492 new
    remaining = target - current
    
    print(f"Current: {current}, Target: {target}, Remaining: {remaining}")
    
    if remaining <= 0:
        print("✅ All questions already imported!")
        sys.exit(0)
    
    # Import in batches of 10
    batch_size = 10
    start_index = 0
    
    while remaining > 0:
        imported = import_batch(start_index, min(batch_size, remaining))
        if imported == 0:
            break
            
        remaining -= imported
        start_index += imported
        
        current = get_current_count()
        print(f"Progress: {current}/{target} ({target-current} remaining)\n")
    
    final_count = get_current_count()
    print(f"🎉 Final count: {final_count} Cloud Practitioner questions")
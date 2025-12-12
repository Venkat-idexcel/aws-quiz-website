#!/usr/bin/env python3
"""
Continue importing - runs multiple small batches automatically
"""

import json
import psycopg2
from config import Config
import time

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

def import_next_batch():
    """Import next batch of 20 questions"""
    try:
        # Load questions
        with open("data/aws_practicetest_20_questions_cleaned.json", "r", encoding="utf-8") as f:
            all_questions = json.load(f)
        
        # Calculate current progress
        current_count = get_current_count()
        original_count = 499  # Original questions before import
        imported_so_far = current_count - original_count
        
        # Get next batch (20 questions)
        start_index = imported_so_far
        end_index = min(start_index + 20, len(all_questions))
        questions_to_import = all_questions[start_index:end_index]
        
        if not questions_to_import:
            print("✅ All questions have been imported!")
            return 0
        
        print(f"Importing questions {start_index + 1} to {end_index} from Practice Test 20...")
        
        # Connect and import
        config = Config()
        conn = psycopg2.connect(
            host=config.DB_HOST,
            port=config.DB_PORT,
            database=config.DB_NAME,
            user=config.DB_USER,
            password=config.DB_PASSWORD
        )
        
        cursor = conn.cursor()
        next_id_num = current_count + 1
        
        for i, question_data in enumerate(questions_to_import):
            question_id = f"CP_{next_id_num + i:04d}"
            
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
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print(f"✅ Successfully imported {len(questions_to_import)} questions")
        return len(questions_to_import)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return 0

# Run multiple batches
if __name__ == "__main__":
    total_target = 492  # Total questions to import
    batches_to_run = 5  # Run 5 batches of 20 questions each
    
    for batch_num in range(1, batches_to_run + 1):
        print(f"\n--- Batch {batch_num} ---")
        
        current = get_current_count()
        imported_so_far = current - 499
        remaining = total_target - imported_so_far
        
        print(f"Progress: {imported_so_far}/{total_target} imported, {remaining} remaining")
        
        if remaining <= 0:
            print("✅ All questions imported!")
            break
        
        imported = import_next_batch()
        if imported == 0:
            break
            
        # Brief pause between batches
        time.sleep(1)
    
    final_count = get_current_count()
    final_imported = final_count - 499
    print(f"\n🎉 Session complete!")
    print(f"📊 Total Cloud Practitioner questions: {final_count}")
    print(f"📈 Questions imported from Practice Test 20: {final_imported}/{total_target}")
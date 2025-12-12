#!/usr/bin/env python3
"""
Import remaining AWS Practice Test 20 Questions
Starts from question 6 (index 5) since we already imported the first 5
"""

import json
import psycopg2
from config import Config

def import_remaining_questions():
    try:
        # Load questions
        with open("data/aws_practicetest_20_questions_cleaned.json", "r", encoding="utf-8") as f:
            all_questions = json.load(f)
        
        # Skip the first 5 questions we already imported
        questions = all_questions[5:]
        print(f"Importing remaining {len(questions)} questions (skipping first 5 already imported)...")
        
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
        
        # Get current count
        cursor.execute("SELECT COUNT(*) FROM questions WHERE category = 'Cloud Practitioner Practice Test'")
        current_count = cursor.fetchone()[0]
        next_num = current_count + 1
        
        print(f"Current count: {current_count}, starting at CP_{next_num:04d}")
        
        successful_imports = 0
        failed_imports = 0
        
        # Import questions in batches
        batch_size = 50
        total_questions = len(questions)
        
        for batch_start in range(0, total_questions, batch_size):
            batch_end = min(batch_start + batch_size, total_questions)
            batch_questions = questions[batch_start:batch_end]
            
            print(f"\nProcessing batch {batch_start//batch_size + 1}: questions {batch_start + 1} to {batch_end}")
            
            try:
                # Start transaction for this batch
                for i, question_data in enumerate(batch_questions):
                    question_index = batch_start + i
                    question_id = f"CP_{next_num + question_index:04d}"
                    
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
                    
                    successful_imports += 1
                
                # Commit this batch
                conn.commit()
                print(f"  ✅ Batch completed: {len(batch_questions)} questions imported")
                
            except Exception as e:
                print(f"  ❌ Batch failed: {e}")
                conn.rollback()
                failed_imports += len(batch_questions)
                successful_imports -= len(batch_questions)  # Rollback the count
        
        print(f"\n🎉 Import completed!")
        print(f"✅ Successfully imported: {successful_imports} questions")
        if failed_imports > 0:
            print(f"❌ Failed to import: {failed_imports} questions")
        
        # Final count check
        cursor.execute("SELECT COUNT(*) FROM questions WHERE category = 'Cloud Practitioner Practice Test'")
        final_count = cursor.fetchone()[0]
        print(f"📊 Total Cloud Practitioner questions: {final_count}")
        
        cursor.close()
        conn.close()
        
        return successful_imports
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 0

if __name__ == "__main__":
    import_remaining_questions()
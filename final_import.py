#!/usr/bin/env python3
"""
Complete the import in one final push
"""

import json
import psycopg2
from config import Config

def complete_import():
    try:
        # Load questions
        with open("data/aws_practicetest_20_questions_cleaned.json", "r", encoding="utf-8") as f:
            all_questions = json.load(f)
        
        # Get current state
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
        current_count = cur.fetchone()[0]
        
        original_count = 499
        imported_so_far = current_count - original_count
        
        print(f"Current status:")
        print(f"  Total Cloud Practitioner questions: {current_count}")
        print(f"  Questions imported from Practice Test 20: {imported_so_far}/492")
        print(f"  Remaining to import: {492 - imported_so_far}")
        
        # Get remaining questions to import
        remaining_questions = all_questions[imported_so_far:]
        
        if not remaining_questions:
            print("✅ All questions already imported!")
            return
        
        print(f"\n🚀 Importing final {len(remaining_questions)} questions...")
        
        # Import in chunks of 50
        chunk_size = 50
        total_imported = 0
        
        for chunk_start in range(0, len(remaining_questions), chunk_size):
            chunk_end = min(chunk_start + chunk_size, len(remaining_questions))
            chunk = remaining_questions[chunk_start:chunk_end]
            
            print(f"Processing chunk {chunk_start//chunk_size + 1}: {len(chunk)} questions...")
            
            # Get fresh count for ID generation
            cur.execute("SELECT COUNT(*) FROM questions WHERE category = 'Cloud Practitioner Practice Test'")
            fresh_count = cur.fetchone()[0]
            next_id_num = fresh_count + 1
            
            for i, question_data in enumerate(chunk):
                question_id = f"CP_{next_id_num + i:04d}"
                
                cur.execute("""
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
            
            # Commit this chunk
            conn.commit()
            total_imported += len(chunk)
            
            print(f"  ✅ Chunk completed: {len(chunk)} questions imported")
            print(f"  Progress: {total_imported}/{len(remaining_questions)} remaining questions imported")
        
        # Final verification
        cur.execute("SELECT COUNT(*) FROM questions WHERE category = 'Cloud Practitioner Practice Test'")
        final_count = cur.fetchone()[0]
        final_imported = final_count - original_count
        
        print(f"\n🎉 Import completed successfully!")
        print(f"📊 Final statistics:")
        print(f"  Total Cloud Practitioner questions: {final_count}")
        print(f"  Original questions: {original_count}")
        print(f"  Questions added from Practice Test 20: {final_imported}")
        print(f"  Import success rate: {final_imported}/492 ({(final_imported/492)*100:.1f}%)")
        
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    complete_import()
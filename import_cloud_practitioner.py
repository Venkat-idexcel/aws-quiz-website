#!/usr/bin/env python3
"""
Import Cloud Practitioner Practice Test questions automatically
"""

import json
import psycopg2
import psycopg2.extras
from config import Config

def get_db_connection():
    """Get database connection"""
    try:
        conn = psycopg2.connect(
            host=Config.DB_HOST,
            port=Config.DB_PORT,
            database=Config.DB_NAME,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD
        )
        return conn
    except Exception as e:
        print(f"Database connection error: {e}")
        return None

def import_questions_to_db():
    """Import questions from JSON to database"""
    
    # Load questions from JSON file
    try:
        with open('data/aws_practitioner_questions.json', 'r', encoding='utf-8') as f:
            questions = json.load(f)
        print(f"✅ Loaded {len(questions)} questions from JSON file")
    except Exception as e:
        print(f"❌ Error loading JSON file: {e}")
        return False
    
    conn = get_db_connection()
    if not conn:
        print("Failed to connect to database")
        return False
    
    try:
        cur = conn.cursor()
        
        # Delete existing Cloud Practitioner Practice Test questions
        print("🗑️ Deleting existing Cloud Practitioner Practice Test questions...")
        cur.execute("DELETE FROM questions WHERE category = %s", ('Cloud Practitioner Practice Test',))
        deleted_count = cur.rowcount
        print(f"Deleted {deleted_count} existing questions")
        
        # Insert new questions
        insert_query = """
        INSERT INTO questions (
            question_id, question, option_a, option_b, option_c, option_d, option_e,
            correct_answer, explanation, category, difficulty_level
        ) VALUES (
            %(question_id)s, %(question)s, %(option_a)s, %(option_b)s, %(option_c)s, %(option_d)s, %(option_e)s,
            %(correct_answer)s, %(explanation)s, 'Cloud Practitioner Practice Test', 'intermediate'
        )
        """
        
        successful_imports = 0
        for i, question in enumerate(questions):
            try:
                # Add question_id if not present
                if 'question_id' not in question:
                    question['question_id'] = f'CP_{i+1:04d}'
                
                cur.execute(insert_query, question)
                successful_imports += 1
                if (i + 1) % 100 == 0:
                    print(f"Imported {i + 1} questions...")
            except Exception as e:
                print(f"Error importing question {i + 1}: {e}")
                continue
        
        conn.commit()
        print(f"✅ Successfully imported {successful_imports} out of {len(questions)} questions")
        
        # Verify import
        cur.execute("SELECT COUNT(*) FROM questions WHERE category = 'Cloud Practitioner Practice Test'")
        total_count = cur.fetchone()[0]
        print(f"📊 Total Cloud Practitioner Practice Test questions in database: {total_count}")
        
        return True
        
    except Exception as e:
        print(f"Database error: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def main():
    print("🚀 Starting Cloud Practitioner Practice Test import...")
    
    if import_questions_to_db():
        print("✅ Questions successfully imported to database!")
        print("🎯 Quiz category 'Cloud Practitioner Practice Test' is ready!")
    else:
        print("❌ Failed to import questions to database")

if __name__ == "__main__":
    main()
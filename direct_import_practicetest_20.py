#!/usr/bin/env python3
"""
Direct Database Import Script for AWS Practice Test 20 Questions
Uses direct database connection without Flask app context
"""

import json
import psycopg2
import os
from config import Config

def load_questions():
    """Load questions from the JSON file created by the extraction script"""
    try:
        with open("data/aws_practicetest_20_questions_improved.json", "r", encoding="utf-8") as f:
            questions = json.load(f)
        return questions
    except FileNotFoundError:
        print("❌ Questions file not found. Please run the extraction script first.")
        return None

def get_db_connection():
    """Get direct database connection"""
    try:
        config = Config()
        
        # Create connection string
        connection_params = {
            'host': config.DB_HOST,
            'port': config.DB_PORT,
            'database': config.DB_NAME,
            'user': config.DB_USER,
            'password': config.DB_PASSWORD,
            'connect_timeout': 10
        }
        
        conn = psycopg2.connect(**connection_params)
        return conn
    except Exception as e:
        print(f"❌ Database connection error: {e}")
        return None

def get_next_question_id():
    """Get the next available question ID for Cloud Practitioner Practice Test"""
    conn = get_db_connection()
    if not conn:
        return None
    
    cursor = conn.cursor()
    
    try:
        # Find the highest existing CP_ question ID
        cursor.execute("""
            SELECT question_id FROM questions 
            WHERE category = 'Cloud Practitioner Practice Test' 
            AND question_id LIKE 'CP_%' 
            ORDER BY question_id DESC 
            LIMIT 1
        """)
        
        result = cursor.fetchone()
        if result:
            last_id = result[0]  # e.g., 'CP_0499'
            next_num = int(last_id.split('_')[1]) + 1
        else:
            next_num = 1
            
        return next_num
    except Exception as e:
        print(f"❌ Error getting next question ID: {e}")
        return None
    finally:
        cursor.close()
        conn.close()

def import_questions(questions):
    """Import questions to the database"""
    if not questions:
        print("❌ No questions to import")
        return 0
    
    conn = get_db_connection()
    if not conn:
        print("❌ Could not connect to database")
        return 0
    
    cursor = conn.cursor()
    next_num = get_next_question_id()
    
    if next_num is None:
        print("❌ Could not determine next question ID")
        conn.close()
        return 0
    
    successful_imports = 0
    failed_imports = 0
    
    print(f"📊 Starting import of {len(questions)} questions...")
    print(f"🏷️ Next question ID will be: CP_{next_num:04d}")
    
    try:
        for i, q in enumerate(questions):
            try:
                question_id = f"CP_{next_num:04d}"
                
                # Ensure all options are present (fill missing with empty string)
                option_a = q['options'].get('A', '')
                option_b = q['options'].get('B', '')
                option_c = q['options'].get('C', '')
                option_d = q['options'].get('D', '')
                option_e = q['options'].get('E', '')
                
                # Insert into database
                cursor.execute("""
                    INSERT INTO questions (
                        question_id, question, option_a, option_b, option_c, option_d, option_e,
                        correct_answer, category, explanation
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    question_id,
                    q['question'],
                    option_a,
                    option_b,
                    option_c,
                    option_d,
                    option_e,
                    q['answer'],
                    'Cloud Practitioner Practice Test',
                    ''  # No explanation provided in this format
                ))
                
                successful_imports += 1
                next_num += 1  # Increment for next question
                
                # Print progress every 50 questions
                if successful_imports % 50 == 0:
                    print(f"✅ Imported {successful_imports} questions...")
                
            except Exception as e:
                failed_imports += 1
                print(f"❌ Failed to import question {q.get('number', i+1)}: {e}")
                continue
        
        # Commit all changes
        conn.commit()
        print(f"✅ Committed all changes to database")
        
    except Exception as e:
        print(f"❌ Database error: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()
    
    print(f"\n📊 Import Summary:")
    print(f"✅ Successful imports: {successful_imports}")
    print(f"❌ Failed imports: {failed_imports}")
    print(f"📝 Total questions processed: {len(questions)}")
    
    return successful_imports

def main():
    """Main import process"""
    print("🚀 Starting AWS Practice Test 20 database import...")
    
    # Load questions from JSON file
    questions = load_questions()
    if not questions:
        return
    
    print(f"📖 Loaded {len(questions)} questions from file")
    
    # Show sample question
    sample = questions[0]
    print(f"\n📝 Sample question:")
    print(f"Question {sample['number']}: {sample['question'][:100]}...")
    print(f"Answer: {sample['answer']}")
    
    # Test database connection
    print(f"\n🔌 Testing database connection...")
    next_id = get_next_question_id()
    if next_id is None:
        print("❌ Cannot connect to database. Check your configuration.")
        return
    
    print(f"✅ Database connection successful. Next question ID: CP_{next_id:04d}")
    
    # Proceed with import
    print(f"\n🚀 Proceeding with import of {len(questions)} questions...")
    
    imported_count = import_questions(questions)
    
    if imported_count > 0:
        print(f"\n🎉 Successfully added {imported_count} new questions!")
        
        # Get total count
        final_next_id = get_next_question_id()
        if final_next_id:
            print(f"📊 Total questions now in Cloud Practitioner Practice Test: {final_next_id - 1}")
    else:
        print("\n❌ No questions were imported.")

if __name__ == "__main__":
    main()
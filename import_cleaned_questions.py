#!/usr/bin/env python3
"""
Direct Database Import Script for Cleaned AWS Practice Test 20 Questions
Uses the cleaned questions file with fixed answer lengths
"""

import json
import psycopg2
import os
from config import Config

def load_questions():
    """Load questions from the cleaned JSON file"""
    try:
        with open("data/aws_practicetest_20_questions_cleaned.json", "r", encoding="utf-8") as f:
            questions = json.load(f)
        return questions
    except FileNotFoundError:
        print("❌ Cleaned questions file not found. Please run fix_questions.py first.")
        return None

def get_db_connection():
    """Get direct database connection"""
    try:
        config = Config()
        
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
    
    print(f"📊 Starting import of {len(questions)} cleaned questions...")
    print(f"🏷️ Next question ID will be: CP_{next_num:04d}")
    
    try:
        for i, question_data in enumerate(questions):
            question_id = f"CP_{next_num + i:04d}"
            
            try:
                # Prepare question text and options
                question_text = question_data["question"]
                options = question_data["options"]
                correct_answer = question_data["answer"]
                
                # Insert the question
                cursor.execute("""
                    INSERT INTO questions (
                        question_id, question, option_a, option_b, option_c, option_d, option_e,
                        correct_answer, explanation, category, difficulty_level
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    )
                """, (
                    question_id,
                    question_text,
                    options.get('A', ''),
                    options.get('B', ''),
                    options.get('C', ''),
                    options.get('D', ''),
                    options.get('E', ''),  # Some questions have option E
                    correct_answer,
                    '',  # No explanation provided in this format
                    'Cloud Practitioner Practice Test',
                    'Intermediate'
                ))
                
                successful_imports += 1
                
                # Progress indicator
                if (i + 1) % 50 == 0:
                    print(f"✅ Imported {i + 1}/{len(questions)} questions...")
                    
            except psycopg2.Error as e:
                print(f"❌ Failed to import question {i + 1}: {e}")
                failed_imports += 1
                # Continue with next question instead of stopping
                continue
        
        # Commit the transaction
        conn.commit()
        print(f"\n🎉 Import completed!")
        print(f"✅ Successfully imported: {successful_imports} questions")
        if failed_imports > 0:
            print(f"❌ Failed to import: {failed_imports} questions")
        
        return successful_imports
        
    except Exception as e:
        print(f"❌ Import error: {e}")
        conn.rollback()
        return 0
    finally:
        cursor.close()
        conn.close()

def main():
    print("🚀 AWS Practice Test 20 - Cleaned Questions Import")
    print("=" * 50)
    
    # Test database connection
    conn = get_db_connection()
    if not conn:
        print("❌ Cannot connect to database. Please check your configuration.")
        return
    
    # Check current count
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM questions WHERE category = 'Cloud Practitioner Practice Test'")
    current_count = cursor.fetchone()[0]
    cursor.close()
    conn.close()
    
    print(f"📊 Current Cloud Practitioner questions: {current_count}")
    
    # Load questions
    questions = load_questions()
    if not questions:
        return
    
    print(f"📖 Loaded {len(questions)} questions from cleaned file")
    
    # Auto-confirm import for this session
    print(f"\n🚀 Proceeding with import of {len(questions)} new questions to the database...")
    
    # Import questions
    imported_count = import_questions(questions)
    
    if imported_count > 0:
        print(f"\n🎯 Final result: {imported_count} questions imported successfully!")
        print(f"📈 Total Cloud Practitioner questions: {current_count + imported_count}")
    else:
        print("❌ Import failed.")

if __name__ == "__main__":
    main()
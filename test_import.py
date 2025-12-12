#!/usr/bin/env python3
"""
Test import script - imports just 5 questions to test the format
"""

import json
import psycopg2
from config import Config

def test_import():
    try:
        # Load questions
        with open("data/aws_practicetest_20_questions_cleaned.json", "r", encoding="utf-8") as f:
            all_questions = json.load(f)
        
        # Test with just first 5 questions
        questions = all_questions[:5]
        print(f"Testing with {len(questions)} questions...")
        
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
        
        # Test insert each question
        for i, question_data in enumerate(questions):
            question_id = f"CP_{next_num + i:04d}"
            
            print(f"\nTesting question {i+1}:")
            print(f"  ID: {question_id}")
            print(f"  Question: {question_data['question'][:50]}...")
            print(f"  Answer: '{question_data['answer']}' (length: {len(question_data['answer'])})")
            
            # Check all field lengths
            question_text = question_data["question"]
            options = question_data["options"]
            correct_answer = question_data["answer"]
            
            print(f"  Field lengths:")
            print(f"    question_id: {len(question_id)}")
            print(f"    question: {len(question_text)}")
            print(f"    correct_answer: {len(correct_answer)}")
            print(f"    category: {len('Cloud Practitioner Practice Test')}")
            print(f"    option_a: {len(options.get('A', ''))}")
            print(f"    option_b: {len(options.get('B', ''))}")
            print(f"    option_c: {len(options.get('C', ''))}")
            print(f"    option_d: {len(options.get('D', ''))}")
            print(f"    option_e: {len(options.get('E', ''))}")
            
            try:
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
                    options.get('E', ''),
                    correct_answer,
                    '',
                    'Cloud Practitioner Practice Test',
                    'Intermediate'
                ))
                
                print(f"  ✅ Successfully prepared for insert")
                
            except Exception as e:
                print(f"  ❌ Insert failed: {e}")
                conn.rollback()
                break
        
        # If we get here, commit the test inserts
        conn.commit()
        print(f"\n🎉 Test completed successfully! All {len(questions)} questions inserted.")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_import()
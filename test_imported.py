#!/usr/bin/env python3
"""
Test newly imported questions to ensure they work correctly
"""

import psycopg2
from config import Config
import json
import random

def test_imported_questions():
    try:
        config = Config()
        conn = psycopg2.connect(
            host=config.DB_HOST,
            port=config.DB_PORT,
            database=config.DB_NAME,
            user=config.DB_USER,
            password=config.DB_PASSWORD
        )
        
        cur = conn.cursor()
        
        # Get some newly imported questions (questions with IDs >= CP_0500)
        cur.execute("""
            SELECT question_id, question, option_a, option_b, option_c, option_d, option_e, correct_answer
            FROM questions 
            WHERE category = 'Cloud Practitioner Practice Test' 
            AND question_id >= 'CP_0500'
            ORDER BY question_id
            LIMIT 5
        """)
        
        sample_questions = cur.fetchall()
        
        print("🧪 Testing newly imported questions:")
        print("=" * 60)
        
        for i, (qid, question, opt_a, opt_b, opt_c, opt_d, opt_e, correct) in enumerate(sample_questions, 1):
            print(f"\n📝 Test Question {i} (ID: {qid}):")
            print(f"Q: {question}")
            print(f"A) {opt_a}")
            print(f"B) {opt_b}")
            print(f"C) {opt_c}")
            print(f"D) {opt_d}")
            if opt_e:
                print(f"E) {opt_e}")
            print(f"✅ Correct Answer: {correct}")
            
            # Validate answer format
            if len(correct) > 10:
                print(f"❌ WARNING: Answer '{correct}' is {len(correct)} chars (exceeds 10-char limit)")
            else:
                print(f"✅ Answer length OK: {len(correct)} chars")
        
        # Get count summary
        cur.execute("SELECT COUNT(*) FROM questions WHERE category = 'Cloud Practitioner Practice Test'")
        total_count = cur.fetchone()[0]
        
        cur.execute("""
            SELECT COUNT(*) FROM questions 
            WHERE category = 'Cloud Practitioner Practice Test' 
            AND question_id >= 'CP_0500'
        """)
        new_count = cur.fetchone()[0]
        
        print(f"\n📊 Import Summary:")
        print(f"  Total Cloud Practitioner questions: {total_count}")
        print(f"  Original questions: 499")
        print(f"  Newly imported questions: {new_count}")
        print(f"  Import progress: {new_count}/492 ({(new_count/492)*100:.1f}%)")
        
        # Test answer distribution
        cur.execute("""
            SELECT correct_answer, COUNT(*) 
            FROM questions 
            WHERE category = 'Cloud Practitioner Practice Test' 
            AND question_id >= 'CP_0500'
            GROUP BY correct_answer 
            ORDER BY COUNT(*) DESC
            LIMIT 10
        """)
        
        answer_dist = cur.fetchall()
        print(f"\n📈 Answer distribution for new questions:")
        for answer, count in answer_dist:
            print(f"  {answer}: {count} questions")
        
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_imported_questions()
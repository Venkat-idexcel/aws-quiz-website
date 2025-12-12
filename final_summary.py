#!/usr/bin/env python3
"""
Final Summary - Check completion status of AWS Practice Test 20 import
"""

import psycopg2
from config import Config

def main():
    try:
        print("🎯 AWS Practice Test 20 Import - Final Summary")
        print("=" * 55)
        
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
        
        # Get total count
        cur.execute("SELECT COUNT(*) FROM questions WHERE category = 'Cloud Practitioner Practice Test'")
        total_count = cur.fetchone()[0]
        
        # Original count was 499
        original_count = 499
        imported_count = total_count - original_count
        
        # Target was to import 492 new questions
        target_import = 492
        remaining = max(0, target_import - imported_count)
        
        print(f"📊 Question Counts:")
        print(f"  Original questions: {original_count}")
        print(f"  Target new questions: {target_import}")
        print(f"  Actually imported: {imported_count}")
        print(f"  Current total: {total_count}")
        print(f"  Remaining to import: {remaining}")
        
        # Calculate progress
        progress_pct = (imported_count / target_import) * 100
        print(f"\n📈 Progress: {imported_count}/{target_import} ({progress_pct:.1f}%)")
        
        # Check if complete
        if remaining == 0:
            print("\n🎉 IMPORT COMPLETED SUCCESSFULLY!")
            print("✅ All 492 questions from AWS Practice Test 20 have been imported.")
        else:
            print(f"\n⏳ Import in progress... {remaining} questions remaining")
        
        # Test a few questions to verify quality
        cur.execute("""
            SELECT question_id, question, correct_answer 
            FROM questions 
            WHERE category = 'Cloud Practitioner Practice Test' 
            AND question_id >= 'CP_0500'
            ORDER BY question_id 
            LIMIT 3
        """)
        
        sample_questions = cur.fetchall()
        
        print(f"\n📝 Sample imported questions:")
        for qid, question, answer in sample_questions:
            short_q = question[:60] + "..." if len(question) > 60 else question
            print(f"  {qid}: {short_q} (Answer: {answer})")
        
        # Check answer length compliance
        cur.execute("""
            SELECT COUNT(*) FROM questions 
            WHERE category = 'Cloud Practitioner Practice Test' 
            AND LENGTH(correct_answer) > 10
        """)
        
        long_answers = cur.fetchone()[0]
        
        if long_answers > 0:
            print(f"\n⚠️ WARNING: {long_answers} questions have answers longer than 10 characters")
        else:
            print(f"\n✅ All answers comply with 10-character database constraint")
        
        # Check latest question ID
        cur.execute("""
            SELECT question_id FROM questions 
            WHERE category = 'Cloud Practitioner Practice Test'
            ORDER BY question_id DESC 
            LIMIT 1
        """)
        
        latest_id = cur.fetchone()[0]
        print(f"\n🏷️ Latest question ID: {latest_id}")
        
        cur.close()
        conn.close()
        
        print(f"\n" + "=" * 55)
        
        if remaining == 0:
            print("🚀 Ready to test the quiz with new questions!")
            print("   Visit: http://localhost:5000")
        else:
            print("💡 To complete import, run: python final_import.py")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
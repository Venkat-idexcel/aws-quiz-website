#!/usr/bin/env python3
"""
Comprehensive test to check AWS Data Engineer quiz flow
"""

import psycopg2
import psycopg2.extras

def test_data_engineer_questions():
    """Test if AWS Data Engineer questions are accessible"""
    
    print("🔍 Testing AWS Data Engineer Quiz Questions...")
    print("=" * 50)
    
    # Database connection
    try:
        conn = psycopg2.connect(
            host='los-dev-psql-rdsclstr-new.cj6duvm27hk9.us-east-1.rds.amazonaws.com',
            port=3306,
            database='cretificate_quiz_db',
            user='postgres',
            password='poc2*&(SRWSjnjkn@#@#'
        )
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        print("✅ Database connection successful")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return
    
    # Test 1: Check if AWS Data Engineer questions exist
    cur.execute("SELECT COUNT(*) FROM aws_questions WHERE category ILIKE 'AWS Data Engineer'")
    de_count = cur.fetchone()[0]
    print(f"✅ Found {de_count} AWS Data Engineer questions in database")
    
    # Test 2: Test the exact query used in the application
    query = """
        SELECT id, question, option_a, option_b, option_c, option_d, option_e, 
               correct_answer, explanation,
               COALESCE(is_multiselect, CASE WHEN LENGTH(TRIM(correct_answer)) > 1 THEN true ELSE false END) as is_multiselect
        FROM aws_questions 
        WHERE category ILIKE 'AWS Data Engineer'
        ORDER BY RANDOM() 
        LIMIT 3
    """
    
    cur.execute(query)
    questions = cur.fetchall()
    
    if questions:
        print(f"✅ Successfully fetched {len(questions)} questions using app query")
        print("\n📋 Sample questions:")
        for i, q in enumerate(questions, 1):
            print(f"\n{i}. Question ID: {q['id']}")
            print(f"   Text: {q['question'][:100]}...")
            print(f"   Option A: {q['option_a']}")
            print(f"   Option B: {q['option_b']}")
            print(f"   Correct: {q['correct_answer']}")
            print(f"   Multi-select: {q['is_multiselect']}")
    else:
        print("❌ No questions returned by app query!")
    
    # Test 3: Check for any NULL or empty values that might cause issues
    cur.execute("""
        SELECT COUNT(*) as total,
               COUNT(CASE WHEN question IS NULL OR TRIM(question) = '' THEN 1 END) as empty_questions,
               COUNT(CASE WHEN option_a IS NULL OR TRIM(option_a) = '' THEN 1 END) as empty_option_a,
               COUNT(CASE WHEN correct_answer IS NULL OR TRIM(correct_answer) = '' THEN 1 END) as empty_answers
        FROM aws_questions 
        WHERE category ILIKE 'AWS Data Engineer'
    """)
    
    stats = cur.fetchone()
    print(f"\n📊 Data Quality Check:")
    print(f"   Total questions: {stats['total']}")
    print(f"   Empty questions: {stats['empty_questions']}")
    print(f"   Empty option_a: {stats['empty_option_a']}")
    print(f"   Empty answers: {stats['empty_answers']}")
    
    if stats['empty_questions'] > 0 or stats['empty_option_a'] > 0 or stats['empty_answers'] > 0:
        print("⚠️  Found data quality issues that might prevent questions from displaying")
    else:
        print("✅ All data quality checks passed")
    
    # Test 4: Check specific columns that might be missing
    cur.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'aws_questions' 
        ORDER BY column_name
    """)
    columns = [row[0] for row in cur.fetchall()]
    
    required_columns = ['id', 'question', 'option_a', 'option_b', 'option_c', 'option_d', 'correct_answer']
    missing_columns = [col for col in required_columns if col not in columns]
    
    print(f"\n🔍 Column Check:")
    print(f"   Available columns: {columns}")
    if missing_columns:
        print(f"❌ Missing required columns: {missing_columns}")
    else:
        print("✅ All required columns present")
    
    conn.close()
    
    print("\n" + "=" * 50)
    if de_count > 0 and questions and not missing_columns:
        print("🎉 AWS Data Engineer questions should work correctly!")
        print("💡 If questions aren't displaying in the web app:")
        print("   1. Check if user is logged in")
        print("   2. Check browser console for JavaScript errors")
        print("   3. Check Flask app logs for errors")
        print("   4. Verify the quiz type parameter is 'aws-data-engineer'")
    else:
        print("❌ There are issues that need to be fixed")

if __name__ == "__main__":
    test_data_engineer_questions()
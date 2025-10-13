import psycopg2

# Database credentials
DB_CONFIG = {
    'host': 'los-dev-psql-rdsclstr-new.cj6duvm27hk9.us-east-1.rds.amazonaws.com',
    'port': 3306,
    'database': 'cretificate_quiz_db',
    'user': 'postgres',
    'password': 'poc2*&(SRWSjnjkn@#@#'
}

try:
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    print('Testing database connection...')

    # Test 1: Check total questions
    cur.execute('SELECT COUNT(*) FROM aws_questions')
    total = cur.fetchone()[0]
    print(f'Total questions: {total}')

    # Test 2: Check AWS Data Engineer questions (exact match)
    cur.execute("SELECT COUNT(*) FROM aws_questions WHERE category = 'AWS Data Engineer'")
    de_exact = cur.fetchone()[0]
    print(f'AWS Data Engineer (exact match): {de_exact}')

    # Test 3: Check AWS Data Engineer questions (ILIKE match)
    cur.execute("SELECT COUNT(*) FROM aws_questions WHERE category ILIKE '%AWS Data Engineer%'")
    de_ilike = cur.fetchone()[0]
    print(f'AWS Data Engineer (ILIKE match): {de_ilike}')

    # Test 4: Show sample categories
    cur.execute('SELECT DISTINCT category FROM aws_questions WHERE category IS NOT NULL LIMIT 10')
    categories = cur.fetchall()
    print('Sample categories:')
    for cat in categories:
        print(f'  "{cat[0]}"')

    # Test 5: Show sample questions with AWS Data Engineer category
    cur.execute("SELECT id, question, category FROM aws_questions WHERE category ILIKE '%AWS Data Engineer%' LIMIT 3")
    sample_questions = cur.fetchall()
    print('Sample AWS Data Engineer questions:')
    for q in sample_questions:
        print(f'  ID: {q[0]}, Category: "{q[2]}", Question: {q[1][:50]}...')

    cur.close()
    conn.close()
    print('SUCCESS: Database test completed')

except Exception as e:
    print(f'ERROR: {e}')
    import traceback
    traceback.print_exc()

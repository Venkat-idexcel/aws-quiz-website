import psycopg2

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

    # Check total questions
    cur.execute('SELECT COUNT(*) FROM aws_questions')
    total = cur.fetchone()[0]
    print(f'Total questions: {total}')

    # Check AWS Data Engineer questions
    cur.execute("SELECT COUNT(*) FROM aws_questions WHERE category ILIKE '%AWS Data Engineer%'")
    de_count = cur.fetchone()[0]
    print(f'AWS Data Engineer questions: {de_count}')

    # Show categories
    cur.execute('SELECT category, COUNT(*) FROM aws_questions WHERE category IS NOT NULL GROUP BY category')
    categories = cur.fetchall()
    print('Categories:')
    for cat, count in categories:
        print(f'  {cat}: {count}')

    cur.close()
    conn.close()
    print('SUCCESS: Database check completed')

except Exception as e:
    print(f'ERROR: {e}')

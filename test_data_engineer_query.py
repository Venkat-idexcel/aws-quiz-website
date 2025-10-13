import psycopg2
import psycopg2.extras

conn = psycopg2.connect(
    host='los-dev-psql-rdsclstr-new.cj6duvm27hk9.us-east-1.rds.amazonaws.com',
    port=3306,
    database='cretificate_quiz_db',
    user='postgres',
    password='poc2*&(SRWSjnjkn@#@#'
)

cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

# Test the exact query used in the app for AWS Data Engineer
query = """
    SELECT id, question, option_a, option_b, option_c, option_d, option_e, correct_answer, explanation,
           COALESCE(is_multiselect, CASE WHEN LENGTH(TRIM(correct_answer)) > 1 THEN true ELSE false END) as is_multiselect
    FROM aws_questions 
    WHERE category ILIKE 'AWS Data Engineer'
    ORDER BY RANDOM() 
    LIMIT 5
"""

print('Testing AWS Data Engineer query...')
print('Query:', query)
cur.execute(query)
questions = cur.fetchall()

print(f'Found {len(questions)} questions')
if questions:
    for i, q in enumerate(questions, 1):
        print(f'{i}. ID: {q["id"]}, Question: {q["question"][:50]}...')
        print(f'   Options: A={q["option_a"]} B={q["option_b"]}')
        print(f'   Correct: {q["correct_answer"]}')
        print()
else:
    print('No questions returned!')

conn.close()
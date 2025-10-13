import psycopg2

# Database Configuration (same as Flask app)
DB_CONFIG = {
    'host': 'los-dev-psql-rdsclstr-new.cj6duvm27hk9.us-east-1.rds.amazonaws.com',
    'port': 3306,
    'database': 'cretificate_quiz_db',
    'user': 'postgres',
    'password': 'poc2*&(SRWSjnjkn@#@#'
}

def test_quiz_query():
    """Test the same query logic used in the Flask app"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()

        print("Testing quiz query logic...")

        # Test AWS Cloud Practitioner query (should work)
        print("\n=== Testing AWS Cloud Practitioner Query ===")
        cloud_practitioner_query = """
            SELECT id, question, option_a, option_b, option_c, option_d, option_e, correct_answer, explanation,
                   COALESCE(is_multiselect, CASE WHEN LENGTH(TRIM(correct_answer)) > 1 THEN true ELSE false END) as is_multiselect
            FROM aws_questions
            WHERE category IS NULL OR category = '' OR category NOT ILIKE 'AWS Data Engineer'
            ORDER BY RANDOM()
            LIMIT 5
        """

        cur.execute(cloud_practitioner_query)
        cp_questions = cur.fetchall()
        print(f"Cloud Practitioner questions found: {len(cp_questions)}")
        for q in cp_questions:
            print(f"  ID: {q[0]}, Category: '{q[8]}', Question: {q[1][:50]}...")

        # Test AWS Data Engineer query (this is what should work now)
        print("\n=== Testing AWS Data Engineer Query ===")
        data_engineer_query = """
            SELECT id, question, option_a, option_b, option_c, option_d, option_e, correct_answer, explanation,
                   COALESCE(is_multiselect, CASE WHEN LENGTH(TRIM(correct_answer)) > 1 THEN true ELSE false END) as is_multiselect
            FROM aws_questions
            WHERE category ILIKE 'AWS Data Engineer'
            ORDER BY RANDOM()
            LIMIT 5
        """

        cur.execute(data_engineer_query)
        de_questions = cur.fetchall()
        print(f"AWS Data Engineer questions found: {len(de_questions)}")
        for q in de_questions:
            print(f"  ID: {q[0]}, Category: '{q[8]}', Question: {q[1][:50]}...")

        # Test the exact query from the app
        print("\n=== Testing Exact App Query for AWS Data Engineer ===")
        quiz_type = 'aws-data-engineer'
        num_questions = 10

        query = ""
        if quiz_type == 'aws-cloud-practitioner':
            query = """
                SELECT id, question, option_a, option_b, option_c, option_d, option_e, correct_answer, explanation,
                       COALESCE(is_multiselect, CASE WHEN LENGTH(TRIM(correct_answer)) > 1 THEN true ELSE false END) as is_multiselect
                FROM aws_questions
                WHERE category IS NULL OR category = '' OR category NOT ILIKE 'AWS Data Engineer'
                ORDER BY RANDOM()
                LIMIT %s
            """
        elif quiz_type == 'aws-data-engineer':
            query = """
                SELECT id, question, option_a, option_b, option_c, option_d, option_e, correct_answer, explanation,
                       COALESCE(is_multiselect, CASE WHEN LENGTH(TRIM(correct_answer)) > 1 THEN true ELSE false END) as is_multiselect
                FROM aws_questions
                WHERE category ILIKE 'AWS Data Engineer'
                ORDER BY RANDOM()
                LIMIT %s
            """

        print(f"Executing query for quiz_type: {quiz_type}")
        cur.execute(query, (num_questions,))
        questions = cur.fetchall()

        print(f"Query returned {len(questions)} questions")

        if not questions:
            print("ERROR: No questions found for AWS Data Engineer quiz type!")
        else:
            print("SUCCESS: Questions found for AWS Data Engineer quiz type!")
            for i, q in enumerate(questions[:3]):  # Show first 3
                print(f"  Question {i+1}: {q[1][:60]}... (Category: '{q[8]}')")

        cur.close()
        conn.close()
        print("\nSUCCESS: Query test completed")

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_quiz_query()

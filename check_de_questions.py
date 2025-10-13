import psycopg2

# Database credentials
DB_HOST = 'los-dev-psql-rdsclstr-new.cj6duvm27hk9.us-east-1.rds.amazonaws.com'
DB_PORT = 3306  # Custom PostgreSQL port (AWS RDS configured on non-standard port)
DB_NAME = 'cretificate_quiz_db'  # Keep existing database name
DB_USER = 'postgres'
DB_PASSWORD = 'poc2*&(SRWSjnjkn@#@#'

def check_questions():
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            connect_timeout=10
        )

        cur = conn.cursor()

        # Check total questions
        cur.execute("SELECT COUNT(*) FROM aws_questions")
        total = cur.fetchone()[0]
        print(f"Total questions in database: {total}")

        # Check AWS Data Engineer questions count
        cur.execute("SELECT COUNT(*) FROM aws_questions WHERE category ILIKE '%AWS Data Engineer%'")
        de_count = cur.fetchone()[0]
        print(f"AWS Data Engineer questions in database: {de_count}")

        # Check categories
        cur.execute("SELECT category, COUNT(*) FROM aws_questions GROUP BY category ORDER BY COUNT(*) DESC")
        categories = cur.fetchall()
        print("Categories:")
        for cat, count in categories:
            print(f"  '{cat}': {count} questions")

        cur.close()
        conn.close()
        print("Database connection successful!")

    except Exception as e:
        print(f"Database error: {e}")

if __name__ == '__main__':
    check_questions()

import psycopg2

# Database credentials
DB_HOST = 'los-dev-psql-rdsclstr-new.cj6duvm27hk9.us-east-1.rds.amazonaws.com'
DB_PORT = 3306  # Custom PostgreSQL port (AWS RDS configured on non-standard port)
DB_NAME = 'cretificate_quiz_db'  # Keep existing database name
DB_USER = 'postgres'
DB_PASSWORD = 'poc2*&(SRWSjnjkn@#@#'

def debug_database():
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
        
        # Check categories
        cur.execute("SELECT category, COUNT(*) FROM aws_questions GROUP BY category ORDER BY COUNT(*) DESC")
        categories = cur.fetchall()
        print("\nCategories:")
        for cat, count in categories:
            print(f"  '{cat}': {count} questions")
        
        # Test Cloud Practitioner query
        cur.execute("""
            SELECT COUNT(*) FROM aws_questions 
            WHERE category IS NULL OR category = '' OR category NOT ILIKE 'AWS Data Engineer'
        """)
        cp_count = cur.fetchone()[0]
        print(f"\nCloud Practitioner questions available: {cp_count}")
        
        # Test Data Engineer query
        cur.execute("""
            SELECT COUNT(*) FROM aws_questions 
            WHERE category ILIKE 'AWS Data Engineer'
        """)
        de_count = cur.fetchone()[0]
        print(f"Data Engineer questions available: {de_count}")
        
        # Check if required columns exist
        cur.execute("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name = 'aws_questions' 
            ORDER BY column_name
        """)
        columns = [row[0] for row in cur.fetchall()]
        print(f"\nTable columns: {columns}")
        
        cur.close()
        conn.close()
        print("\n✅ Database connection successful!")
        
    except Exception as e:
        print(f"❌ Database error: {e}")

if __name__ == '__main__':
    debug_database()
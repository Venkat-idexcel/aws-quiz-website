import psycopg2

# Database credentials
DB_HOST = 'los-dev-psql-rdsclstr-new.cj6duvm27hk9.us-east-1.rds.amazonaws.com'
DB_PORT = 3306
DB_NAME = 'cretificate_quiz_db'
DB_USER = 'postgres'
DB_PASSWORD = 'poc2*&(SRWSjnjkn@#@#'

def quick_fix():
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
        
        # Add missing columns if they don't exist
        print("Adding missing columns...")
        
        try:
            cur.execute("ALTER TABLE aws_questions ADD COLUMN IF NOT EXISTS explanation TEXT")
            print("✓ Added explanation column")
        except Exception as e:
            print(f"Explanation column: {e}")
            
        try:
            cur.execute("ALTER TABLE aws_questions ADD COLUMN IF NOT EXISTS category VARCHAR(255)")
            print("✓ Added category column")
        except Exception as e:
            print(f"Category column: {e}")
            
        try:
            cur.execute("ALTER TABLE aws_questions ADD COLUMN IF NOT EXISTS option_e TEXT")
            print("✓ Added option_e column")
        except Exception as e:
            print(f"Option_e column: {e}")
            
        try:
            cur.execute("ALTER TABLE aws_questions ADD COLUMN IF NOT EXISTS is_multiselect BOOLEAN DEFAULT FALSE")
            print("✓ Added is_multiselect column")
        except Exception as e:
            print(f"is_multiselect column: {e}")
        
        conn.commit()
        
        # Check counts after fix
        cur.execute("SELECT COUNT(*) FROM aws_questions")
        total = cur.fetchone()[0]
        print(f"\nTotal questions: {total}")
        
        # Test both queries
        cur.execute("""
            SELECT COUNT(*) FROM aws_questions 
            WHERE category IS NULL OR category = '' OR category NOT ILIKE 'AWS Data Engineer'
        """)
        cp_count = cur.fetchone()[0]
        print(f"Cloud Practitioner questions: {cp_count}")
        
        cur.execute("""
            SELECT COUNT(*) FROM aws_questions 
            WHERE category ILIKE 'AWS Data Engineer'
        """)
        de_count = cur.fetchone()[0]
        print(f"Data Engineer questions: {de_count}")
        
        cur.close()
        conn.close()
        print("\n✅ Quick fix completed!")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == '__main__':
    quick_fix()
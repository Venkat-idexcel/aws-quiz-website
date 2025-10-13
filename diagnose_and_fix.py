"""
Comprehensive diagnostic and fix script for the quiz application
"""
import psycopg2
import psycopg2.extras
from config import Config

def diagnose_and_fix():
    """Check database state and fix issues"""
    config = Config()
    
    print("=" * 60)
    print("QUIZ APPLICATION DIAGNOSTIC AND FIX")
    print("=" * 60)
    
    try:
        conn = psycopg2.connect(
            host=config.DB_HOST,
            port=config.DB_PORT,
            database=config.DB_NAME,
            user=config.DB_USER,
            password=config.DB_PASSWORD,
            connect_timeout=10
        )
        
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        print(f"\n✅ Connected to database: {config.DB_NAME}")
        print(f"   Host: {config.DB_HOST}:{config.DB_PORT}")
        
        # Check tables
        print("\n" + "=" * 60)
        print("CHECKING TABLES")
        print("=" * 60)
        
        cur.execute("""
            SELECT table_name FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
            ORDER BY table_name
        """)
        tables = [row[0] for row in cur.fetchall()]
        print(f"\nTables in database: {', '.join(tables)}")
        
        # Check users table
        print("\n" + "=" * 60)
        print("USERS TABLE")
        print("=" * 60)
        
        if 'users' in tables:
            cur.execute("SELECT COUNT(*) FROM users")
            user_count = cur.fetchone()[0]
            print(f"Total users: {user_count}")
            
            if user_count > 0:
                cur.execute("SELECT id, username, email, is_active, created_at FROM users ORDER BY id DESC LIMIT 5")
                print("\nRecent users:")
                for row in cur.fetchall():
                    print(f"  ID: {row['id']}, Username: {row['username']}, Email: {row['email']}, Active: {row['is_active']}")
            else:
                print("⚠️  No users found in database!")
        else:
            print("❌ Users table does not exist!")
        
        # Check questions table
        print("\n" + "=" * 60)
        print("QUESTIONS TABLE")
        print("=" * 60)
        
        questions_table = None
        if 'questions' in tables:
            questions_table = 'questions'
        elif 'aws_questions' in tables:
            questions_table = 'aws_questions'
            print("⚠️  Using legacy table name: aws_questions")
        
        if questions_table:
            cur.execute(f"SELECT COUNT(*) FROM {questions_table}")
            q_count = cur.fetchone()[0]
            print(f"Total questions: {q_count}")
            
            if q_count > 0:
                cur.execute(f"SELECT DISTINCT category, COUNT(*) FROM {questions_table} GROUP BY category ORDER BY COUNT(*) DESC")
                print("\nCategories:")
                for row in cur.fetchall():
                    print(f"  '{row[0]}': {row[1]} questions")
                    
                # Check column names
                cur.execute(f"""
                    SELECT column_name FROM information_schema.columns 
                    WHERE table_name = '{questions_table}' 
                    ORDER BY ordinal_position
                """)
                columns = [row[0] for row in cur.fetchall()]
                print(f"\nColumns: {', '.join(columns)}")
            else:
                print("❌ No questions found in database!")
        else:
            print("❌ No questions table found!")
        
        # Check quiz_sessions
        print("\n" + "=" * 60)
        print("QUIZ SESSIONS TABLE")
        print("=" * 60)
        
        if 'quiz_sessions' in tables:
            cur.execute("SELECT COUNT(*) FROM quiz_sessions")
            session_count = cur.fetchone()[0]
            print(f"Total quiz sessions: {session_count}")
        else:
            print("⚠️  quiz_sessions table does not exist")
        
        # FIXES
        print("\n" + "=" * 60)
        print("APPLYING FIXES")
        print("=" * 60)
        
        fixes_applied = []
        
        # Fix 1: Ensure users table has required columns
        if 'users' in tables:
            cur.execute("""
                SELECT column_name FROM information_schema.columns 
                WHERE table_name = 'users' 
            """)
            user_columns = [row[0] for row in cur.fetchall()]
            
            required_columns = {
                'password_hash': 'VARCHAR(255)',
                'is_active': 'BOOLEAN DEFAULT TRUE',
                'is_admin': 'BOOLEAN DEFAULT FALSE',
                'last_login': 'TIMESTAMP'
            }
            
            for col, col_type in required_columns.items():
                if col not in user_columns:
                    try:
                        if col == 'password_hash':
                            cur.execute(f"ALTER TABLE users ADD COLUMN {col} {col_type}")
                        else:
                            cur.execute(f"ALTER TABLE users ADD COLUMN IF NOT EXISTS {col} {col_type}")
                        conn.commit()
                        fixes_applied.append(f"Added {col} column to users table")
                    except Exception as e:
                        print(f"  Note: Could not add {col}: {e}")
        
        # Fix 2: If using aws_questions but app expects questions, create view or notify
        if 'aws_questions' in tables and 'questions' not in tables:
            print("\n⚠️  IMPORTANT: Application uses 'questions' table but only 'aws_questions' exists!")
            print("   You need to either:")
            print("   1. Rename aws_questions to questions, OR")
            print("   2. Update app.py to use aws_questions consistently")
            fixes_applied.append("Identified table name mismatch")
        
        if fixes_applied:
            print("\nFixes applied:")
            for fix in fixes_applied:
                print(f"  ✅ {fix}")
        else:
            print("\nNo fixes needed.")
        
        conn.commit()
        cur.close()
        conn.close()
        
        print("\n" + "=" * 60)
        print("DIAGNOSTIC COMPLETE")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    diagnose_and_fix()

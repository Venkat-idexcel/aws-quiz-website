import psycopg2
import psycopg2.extras
from config import Config

def test_admin_users_query():
    """Test the admin users page query"""
    try:
        conn = psycopg2.connect(
            dbname=Config.DB_NAME,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            host=Config.DB_HOST,
            port=Config.DB_PORT
        )
        print("✓ Database connection successful")
        
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        # Test the current query
        print("\n=== Testing Admin Users Query ===")
        try:
            cur.execute("""
                SELECT u.id, u.username, u.email, u.first_name, u.last_name, 
                       u.created_at, u.last_login, u.is_active,
                       ups.total_quizzes, ups.average_score, ups.best_score,
                       ups.total_time_spent_minutes, ups.last_quiz_date
                FROM users u
                LEFT JOIN user_performance_summary ups ON u.id = ups.user_id
                WHERE u.is_admin = FALSE
                ORDER BY u.created_at DESC
            """)
            users = cur.fetchall()
            print(f"✓ Query successful! Found {len(users)} users")
        except Exception as e:
            print(f"✗ Query failed: {e}")
            
            # Try without last_login and user_performance_summary
            print("\n=== Testing Simplified Query (without last_login and performance table) ===")
            try:
                cur.execute("""
                    SELECT u.id, u.username, u.email, u.first_name, u.last_name, 
                           u.created_at, u.is_active
                    FROM users u
                    WHERE u.is_admin = FALSE
                    ORDER BY u.created_at DESC
                """)
                users = cur.fetchall()
                print(f"✓ Simplified query successful! Found {len(users)} users")
                for user in users[:3]:
                    print(f"  - {user['first_name']} {user['last_name']} ({user['email']})")
            except Exception as e2:
                print(f"✗ Simplified query also failed: {e2}")
        
        # Check if user_performance_summary table exists
        print("\n=== Checking if user_performance_summary table exists ===")
        cur.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'user_performance_summary'
            )
        """)
        table_exists = cur.fetchone()[0]
        print(f"user_performance_summary table exists: {table_exists}")
        
        conn.close()
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_admin_users_query()

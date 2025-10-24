import psycopg2
import psycopg2.extras
from config import Config

def test_fixed_admin_users_query():
    """Test the fixed admin users page query"""
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
        
        # Test the fixed query
        print("\n=== Testing Fixed Admin Users Query ===")
        cur.execute("""
            SELECT u.id, u.username, u.email, u.first_name, u.last_name, 
                   u.created_at, u.is_active,
                   COUNT(DISTINCT qs.id) as total_quizzes,
                   ROUND(AVG(qs.score_percentage), 1) as average_score,
                   MAX(qs.score_percentage) as best_score,
                   SUM(qs.time_taken_minutes) as total_time_spent_minutes,
                   MAX(qs.completed_at) as last_quiz_date
            FROM users u
            LEFT JOIN quiz_sessions qs ON u.id = qs.user_id AND qs.completed_at IS NOT NULL
            WHERE u.is_admin = FALSE
            GROUP BY u.id, u.username, u.email, u.first_name, u.last_name, u.created_at, u.is_active
            ORDER BY u.created_at DESC
        """)
        users = cur.fetchall()
        print(f"✓ Query successful! Found {len(users)} users\n")
        
        # Show first 5 users
        print("First 5 users:")
        for user in users[:5]:
            print(f"  - {user['first_name']} {user['last_name']} ({user['email']})")
            print(f"    Quizzes: {user['total_quizzes']}, Avg Score: {user['average_score']}%, Best: {user['best_score']}%")
        
        print("\n=== Testing User Detail Query ===")
        if users:
            user_id = users[0]['id']
            cur.execute("""
                SELECT u.*,
                       COUNT(DISTINCT qs.id) as total_quizzes,
                       ROUND(AVG(qs.score_percentage), 1) as average_score,
                       MAX(qs.score_percentage) as best_score,
                       SUM(qs.time_taken_minutes) as total_time_spent_minutes,
                       MAX(qs.completed_at) as last_quiz_date
                FROM users u
                LEFT JOIN quiz_sessions qs ON u.id = qs.user_id AND qs.completed_at IS NOT NULL
                WHERE u.id = %s AND u.is_admin = FALSE
                GROUP BY u.id
            """, (user_id,))
            user = cur.fetchone()
            print(f"✓ User detail query successful for user ID {user_id}")
            
            # Test activities query
            cur.execute("""
                SELECT activity_type, description, created_at, ip_address
                FROM user_activities
                WHERE user_id = %s
                ORDER BY created_at DESC
                LIMIT 50
            """, (user_id,))
            activities = cur.fetchall()
            print(f"✓ Activities query successful! Found {len(activities)} activities")
        
        print("\n✓ All queries passed successfully!")
        
        conn.close()
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_fixed_admin_users_query()

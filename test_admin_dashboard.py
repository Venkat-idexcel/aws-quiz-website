import psycopg2
import psycopg2.extras
from config import Config

def test_admin_dashboard():
    """Test the admin dashboard queries"""
    try:
        # Connect to database
        conn = psycopg2.connect(
            dbname=Config.DB_NAME,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            host=Config.DB_HOST,
            port=Config.DB_PORT
        )
        print("✓ Database connection successful")
        
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        # Test user statistics query
        print("\n=== Testing User Statistics Query ===")
        cur.execute("""
            SELECT 
                COUNT(*) as total_users,
                COUNT(*) FILTER (WHERE is_active = TRUE) as active_users,
                COUNT(*) FILTER (WHERE created_at >= NOW() - INTERVAL '30 days') as new_users_30_days
            FROM users WHERE is_admin = FALSE
        """)
        user_stats = cur.fetchone()
        print(f"User Stats: {dict(user_stats)}")
        
        # Test quiz statistics query
        print("\n=== Testing Quiz Statistics Query ===")
        cur.execute("""
            SELECT 
                COUNT(*) as total_quizzes,
                COUNT(DISTINCT user_id) as unique_users_took_quiz,
                ROUND(AVG(score_percentage), 1) as average_score,
                COUNT(*) FILTER (WHERE completed_at >= NOW() - INTERVAL '7 days') as quizzes_last_7_days
            FROM quiz_sessions WHERE completed_at IS NOT NULL
        """)
        quiz_stats = cur.fetchone()
        print(f"Quiz Stats: {dict(quiz_stats)}")
        
        # Test top performers query
        print("\n=== Testing Top Performers Query ===")
        cur.execute("""
            SELECT u.first_name, u.last_name, u.email, 
                   COUNT(qs.id) as quiz_count,
                   ROUND(AVG(qs.score_percentage), 1) as avg_score,
                   MAX(qs.score_percentage) as best_score
            FROM users u 
            JOIN quiz_sessions qs ON u.id = qs.user_id
            WHERE qs.completed_at >= NOW() - INTERVAL '30 days'
              AND u.is_admin = FALSE
            GROUP BY u.id, u.first_name, u.last_name, u.email
            ORDER BY avg_score DESC, quiz_count DESC
            LIMIT 10
        """)
        top_performers = cur.fetchall()
        print(f"Top Performers Count: {len(top_performers)}")
        for p in top_performers:
            print(f"  - {p['first_name']} {p['last_name']}: {p['avg_score']}% avg, {p['quiz_count']} quizzes")
        
        # Test recent activities query
        print("\n=== Testing Recent Activities Query ===")
        cur.execute("""
            SELECT ua.activity_type, ua.description, ua.created_at,
                   u.first_name, u.last_name, u.email
            FROM user_activities ua
            JOIN users u ON ua.user_id = u.id
            WHERE u.is_admin = FALSE
            ORDER BY ua.created_at DESC
            LIMIT 20
        """)
        recent_activities = cur.fetchall()
        print(f"Recent Activities Count: {len(recent_activities)}")
        for act in recent_activities[:5]:  # Show first 5
            print(f"  - {act['activity_type']}: {act['description']} by {act['first_name']} {act['last_name']}")
        
        print("\n✓ All admin dashboard queries executed successfully!")
        
        conn.close()
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_admin_dashboard()

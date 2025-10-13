"""
Complete Database Setup Script
This script will:
1. Create all required tables if they don't exist
2. Verify data integrity
3. Fix common issues
"""
import psycopg2
import psycopg2.extras
from werkzeug.security import generate_password_hash
from config import Config

def setup_database():
    """Complete database setup"""
    config = Config()
    
    print("=" * 70)
    print("QUIZ APPLICATION - DATABASE SETUP")
    print("=" * 70)
    
    try:
        conn = psycopg2.connect(
            host=config.DB_HOST,
            port=config.DB_PORT,
            database=config.DB_NAME,
            user=config.DB_USER,
            password=config.DB_PASSWORD,
            connect_timeout=10
        )
        
        cur = conn.cursor()
        
        print(f"\n✅ Connected to: {config.DB_NAME} at {config.DB_HOST}:{config.DB_PORT}\n")
        
        # 1. Create users table
        print("Creating users table...")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(100) UNIQUE NOT NULL,
                email VARCHAR(200) UNIQUE NOT NULL,
                password_hash VARCHAR(255),
                first_name VARCHAR(100),
                last_name VARCHAR(100),
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP,
                is_active BOOLEAN DEFAULT TRUE,
                is_admin BOOLEAN DEFAULT FALSE,
                oauth_provider VARCHAR(50),
                oauth_id VARCHAR(255),
                profile_picture_url VARCHAR(500),
                reset_token VARCHAR(100),
                reset_token_expires TIMESTAMP
            )
        """)
        print("✅ Users table ready")
        
        # 2. Create questions table (new schema)
        print("\nCreating questions table...")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS questions (
                id SERIAL PRIMARY KEY,
                question_id VARCHAR(50) UNIQUE NOT NULL,
                question TEXT NOT NULL,
                option_a TEXT NOT NULL,
                option_b TEXT NOT NULL,
                option_c TEXT NOT NULL,
                option_d TEXT NOT NULL,
                option_e TEXT,
                correct_answer VARCHAR(10) NOT NULL,
                explanation TEXT,
                category VARCHAR(100) NOT NULL,
                difficulty_level VARCHAR(50),
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cur.execute("CREATE INDEX IF NOT EXISTS idx_questions_category ON questions(category)")
        print("✅ Questions table ready")
        
        # 3. Create quiz_sessions table
        print("\nCreating quiz_sessions table...")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS quiz_sessions (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                category VARCHAR(100) NOT NULL,
                start_time TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                end_time TIMESTAMP WITH TIME ZONE,
                completed_at TIMESTAMP,
                total_questions INTEGER DEFAULT 0,
                correct_answers INTEGER DEFAULT 0,
                score_percentage DECIMAL(5, 2),
                time_taken_minutes INTEGER,
                is_completed BOOLEAN DEFAULT FALSE,
                quiz_data JSONB
            )
        """)
        cur.execute("CREATE INDEX IF NOT EXISTS idx_quiz_sessions_user_id ON quiz_sessions(user_id)")
        print("✅ Quiz sessions table ready")
        
        # 4. Create user_answers table
        print("\nCreating user_answers table...")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS user_answers (
                id SERIAL PRIMARY KEY,
                session_id INTEGER NOT NULL REFERENCES quiz_sessions(id) ON DELETE CASCADE,
                question_id VARCHAR(50) NOT NULL,
                user_answer VARCHAR(10),
                is_correct BOOLEAN,
                answered_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cur.execute("CREATE INDEX IF NOT EXISTS idx_user_answers_session_id ON user_answers(session_id)")
        print("✅ User answers table ready")
        
        # 5. Create badges table
        print("\nCreating badges table...")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS badges (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) UNIQUE NOT NULL,
                description TEXT,
                icon VARCHAR(50),
                color VARCHAR(20),
                criteria_type VARCHAR(50) NOT NULL,
                criteria_value INTEGER,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("✅ Badges table ready")
        
        # 6. Create user_badges table
        print("\nCreating user_badges table...")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS user_badges (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                badge_id INTEGER NOT NULL REFERENCES badges(id) ON DELETE CASCADE,
                awarded_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, badge_id)
            )
        """)
        cur.execute("CREATE INDEX IF NOT EXISTS idx_user_badges_user_id ON user_badges(user_id)")
        print("✅ User badges table ready")
        
        # 7. Create user_activities table
        print("\nCreating user_activities table...")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS user_activities (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id),
                activity_type VARCHAR(50) NOT NULL,
                activity_description TEXT,
                ip_address VARCHAR(45),
                user_agent TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("✅ User activities table ready")
        
        # 8. Insert default badges
        print("\nInserting default badges...")
        default_badges = [
            ('First Steps', 'Complete your first quiz', '🎯', '#28a745', 'quiz_count', 1),
            ('Quiz Master', 'Complete 5 quizzes', '🏆', '#ffc107', 'quiz_count', 5),
            ('Dedicated Learner', 'Complete 10 quizzes', '📚', '#17a2b8', 'quiz_count', 10),
            ('High Achiever', 'Score 90% or higher', '⭐', '#fd7e14', 'high_score', 90),
            ('Perfect Score', 'Get 100% on a quiz', '💯', '#dc3545', 'perfect_score', 100),
            ('Consistent Performer', 'Maintain 80% average over 5 quizzes', '🎖️', '#20c997', 'average_score', 80)
        ]
        
        for name, desc, icon, color, ctype, cval in default_badges:
            cur.execute("""
                INSERT INTO badges (name, description, icon, color, criteria_type, criteria_value)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (name) DO NOTHING
            """, (name, desc, icon, color, ctype, cval))
        print("✅ Default badges inserted")
        
        # Commit all changes
        conn.commit()
        
        # Check current state
        print("\n" + "=" * 70)
        print("DATABASE STATUS")
        print("=" * 70)
        
        cur.execute("SELECT COUNT(*) FROM users")
        user_count = cur.fetchone()[0]
        print(f"\nUsers: {user_count}")
        
        cur.execute("SELECT COUNT(*) FROM questions")
        q_count = cur.fetchone()[0]
        print(f"Questions: {q_count}")
        
        if q_count > 0:
            cur.execute("SELECT DISTINCT category, COUNT(*) FROM questions GROUP BY category")
            print("\nCategories:")
            for row in cur.fetchall():
                print(f"  - {row[0]}: {row[1]} questions")
        
        cur.execute("SELECT COUNT(*) FROM quiz_sessions")
        session_count = cur.fetchone()[0]
        print(f"\nQuiz Sessions: {session_count}")
        
        cur.execute("SELECT COUNT(*) FROM badges")
        badge_count = cur.fetchone()[0]
        print(f"Badges: {badge_count}")
        
        cur.close()
        conn.close()
        
        print("\n" + "=" * 70)
        print("✅ DATABASE SETUP COMPLETE")
        print("=" * 70)
        
        if user_count == 0:
            print("\n⚠️  No users in database. Please register a new account.")
        
        if q_count == 0:
            print("\n⚠️  No questions in database. Please import questions.")
            print("   Run: python import_csv_data.py")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    setup_database()

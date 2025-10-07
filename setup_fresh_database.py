#!/usr/bin/env python3
"""
Fresh Database Setup Script
Creates a new database on AWS RDS and initializes all required tables
"""

import psycopg2
import psycopg2.extras
from datetime import datetime
import sys
import os

# New Database Configuration (AWS RDS)
NEW_DB_CONFIG = {
    'host': 'los-dev-psql-rdsclstr-new.cj6duvm27hk9.us-east-1.rds.amazonaws.com',
    'port': 3306,
    'database': 'cretificate_quiz_db',
    'user': 'postgres',
    'password': 'poc2*&(SRWSjnjkn@#@#'
}

# Default database for initial connection (without specifying database name)
DEFAULT_DB_CONFIG = NEW_DB_CONFIG.copy()
DEFAULT_DB_CONFIG['database'] = 'postgres'  # Connect to default postgres database

def test_connection(db_config, db_name="database"):
    """Test database connection"""
    try:
        conn = psycopg2.connect(**db_config)
        conn.close()
        print(f"✅ Successfully connected to {db_name}")
        return True
    except Exception as e:
        print(f"❌ Failed to connect to {db_name}: {e}")
        return False

def create_database():
    """Create the database if it doesn't exist"""
    try:
        # Connect to default postgres database
        conn = psycopg2.connect(**DEFAULT_DB_CONFIG)
        conn.autocommit = True
        cur = conn.cursor()
        
        # Check if database exists
        cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (NEW_DB_CONFIG['database'],))
        exists = cur.fetchone()
        
        if exists:
            print(f"✅ Database '{NEW_DB_CONFIG['database']}' already exists")
        else:
            # Create database
            cur.execute(f"CREATE DATABASE {NEW_DB_CONFIG['database']}")
            print(f"✅ Created database '{NEW_DB_CONFIG['database']}'")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error creating database: {e}")
        return False

def initialize_tables():
    """Initialize all required tables"""
    try:
        conn = psycopg2.connect(**NEW_DB_CONFIG)
        cur = conn.cursor()
        
        print("🔄 Creating database tables...")
        
        # Create users table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                email VARCHAR(100) UNIQUE NOT NULL,
                password_hash VARCHAR(255),
                first_name VARCHAR(50) NOT NULL,
                last_name VARCHAR(50) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP,
                is_active BOOLEAN DEFAULT TRUE,
                is_admin BOOLEAN DEFAULT FALSE,
                reset_token VARCHAR(100),
                reset_token_expires TIMESTAMP,
                oauth_provider VARCHAR(50),
                oauth_id VARCHAR(255),
                profile_picture_url VARCHAR(500)
            )
        """)
        print("✅ Created users table")
        
        # Create aws_questions table (if you have questions data)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS aws_questions (
                id SERIAL PRIMARY KEY,
                question TEXT NOT NULL,
                option_a TEXT,
                option_b TEXT,
                option_c TEXT,
                option_d TEXT,
                option_e TEXT,
                correct_answer VARCHAR(10) NOT NULL,
                explanation TEXT,
                category VARCHAR(100),
                difficulty_level VARCHAR(20),
                is_multiselect BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("✅ Created aws_questions table")
        
        # Create quiz_sessions table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS quiz_sessions (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id),
                started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP,
                total_questions INTEGER,
                correct_answers INTEGER,
                score_percentage DECIMAL(5,2),
                time_taken_minutes INTEGER,
                quiz_data JSONB
            )
        """)
        print("✅ Created quiz_sessions table")
        
        # Create quiz_answers table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS quiz_answers (
                id SERIAL PRIMARY KEY,
                session_id INTEGER REFERENCES quiz_sessions(id),
                question_id INTEGER REFERENCES aws_questions(id),
                user_answer VARCHAR(10),
                correct_answer VARCHAR(10),
                is_correct BOOLEAN,
                answered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("✅ Created quiz_answers table")
        
        # Create user_activities table
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
        print("✅ Created user_activities table")
        
        # Create badges table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS badges (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL UNIQUE,
                description TEXT,
                icon VARCHAR(50),
                color VARCHAR(20),
                criteria_type VARCHAR(50) NOT NULL,
                criteria_value INTEGER,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("✅ Created badges table")
        
        # Create user_badges table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS user_badges (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                badge_id INTEGER REFERENCES badges(id) ON DELETE CASCADE,
                awarded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, badge_id)
            )
        """)
        print("✅ Created user_badges table")
        
        # Create achievements table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS achievements (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                achievement_type VARCHAR(50) NOT NULL,
                achievement_data JSONB,
                achieved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("✅ Created achievements table")
        
        # Create user_performance_summary table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS user_performance_summary (
                user_id INTEGER PRIMARY KEY REFERENCES users(id),
                total_quizzes INTEGER DEFAULT 0,
                total_questions_answered INTEGER DEFAULT 0,
                total_correct_answers INTEGER DEFAULT 0,
                average_score DECIMAL(5,2) DEFAULT 0,
                best_score DECIMAL(5,2) DEFAULT 0,
                worst_score DECIMAL(5,2) DEFAULT 0,
                total_time_spent_minutes INTEGER DEFAULT 0,
                last_quiz_date TIMESTAMP,
                first_quiz_date TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("✅ Created user_performance_summary table")
        
        # Create leaderboard_cache table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS leaderboard_cache (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                total_score INTEGER DEFAULT 0,
                quiz_count INTEGER DEFAULT 0,
                average_score DECIMAL(5,2) DEFAULT 0,
                badges_count INTEGER DEFAULT 0,
                rank_position INTEGER,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("✅ Created leaderboard_cache table")
        
        # Insert default badges
        print("🏆 Adding default badges...")
        default_badges = [
            ('First Steps', 'Complete your first quiz', '🎯', '#28a745', 'quiz_count', 1),
            ('Quiz Master', 'Complete 5 quizzes', '🏆', '#ffc107', 'quiz_count', 5),
            ('Dedicated Learner', 'Complete 10 quizzes', '📚', '#17a2b8', 'quiz_count', 10),
            ('AWS Explorer', 'Complete 25 quizzes', '🚀', '#6f42c1', 'quiz_count', 25),
            ('High Achiever', 'Score 90% or higher', '⭐', '#fd7e14', 'high_score', 90),
            ('Perfect Score', 'Get 100% on a quiz', '💯', '#dc3545', 'perfect_score', 100),
            ('Consistent Performer', 'Maintain 80% average over 5 quizzes', '🎖️', '#20c997', 'average_score', 80),
            ('Quick Learner', 'Complete a quiz in under 5 minutes', '⚡', '#e83e8c', 'quick_completion', 5),
            ('Knowledge Seeker', 'Answer 100 questions correctly', '🧠', '#4ecdc4', 'correct_answers', 100)
        ]
        
        for name, description, icon, color, criteria_type, criteria_value in default_badges:
            cur.execute("""
                INSERT INTO badges (name, description, icon, color, criteria_type, criteria_value)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (name) DO NOTHING
            """, (name, description, icon, color, criteria_type, criteria_value))
        
        print("✅ Added default badges")
        
        # Create indexes for better performance
        print("📊 Creating database indexes...")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_quiz_sessions_user_id ON quiz_sessions(user_id)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_quiz_answers_session_id ON quiz_answers(session_id)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_user_activities_user_id ON user_activities(user_id)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_achievements_user_type ON achievements(user_id, achievement_type)")
        print("✅ Created database indexes")
        
        conn.commit()
        conn.close()
        
        print("\n🎉 Database initialization completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error initializing tables: {e}")
        return False

def setup_fresh_database():
    """Main setup function"""
    print("🚀 Setting up fresh database...")
    print("=" * 50)
    
    # Test connection to AWS RDS
    print("🔍 Testing AWS RDS connection...")
    if not test_connection(DEFAULT_DB_CONFIG, "AWS RDS"):
        print("❌ Cannot connect to AWS RDS. Setup aborted.")
        print("Please check your database credentials and network connectivity.")
        return False
    
    # Create database
    print("\n📝 Creating database...")
    if not create_database():
        return False
    
    # Test connection to the specific database
    print("\n🔍 Testing connection to quiz database...")
    if not test_connection(NEW_DB_CONFIG, "quiz database"):
        print("❌ Cannot connect to quiz database. Setup aborted.")
        return False
    
    # Initialize tables
    print("\n🏗️ Initializing database tables...")
    if not initialize_tables():
        return False
    
    print("\n✅ Fresh database setup completed!")
    print("=" * 50)
    print("Your new database is ready to use!")
    print(f"Database: {NEW_DB_CONFIG['database']}")
    print(f"Host: {NEW_DB_CONFIG['host']}")
    print(f"Port: {NEW_DB_CONFIG['port']}")
    
    return True

if __name__ == "__main__":
    print("Fresh Database Setup Tool")
    print("=" * 50)
    print("This will create a fresh database on AWS RDS with all required tables")
    print(f"Target: {NEW_DB_CONFIG['host']}:{NEW_DB_CONFIG['port']}")
    print()
    
    response = input("Do you want to proceed with fresh database setup? (yes/no): ").lower()
    
    if response in ['yes', 'y']:
        success = setup_fresh_database()
        if success:
            print("\n🎉 Setup completed! You can now run your application.")
            print("Run: python app.py")
        else:
            print("\n❌ Setup failed. Please check the errors above.")
    else:
        print("Setup cancelled.")
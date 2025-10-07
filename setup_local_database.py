#!/usr/bin/env python3
"""
Local PostgreSQL Database Setup Script for AWS Quiz Website
This script initializes the local PostgreSQL database and loads initial data
"""

import psycopg2
import sys
import os
from pathlib import Path

# Add the application directory to Python path
app_dir = Path(__file__).parent.absolute()
sys.path.insert(0, str(app_dir))

from config import Config

def create_database():
    """Create the database if it doesn't exist"""
    print("🗄️ Creating database...")
    
    # Connect to postgres database first to create our database
    try:
        conn = psycopg2.connect(
            host=Config.DB_HOST,
            port=Config.DB_PORT,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            database='postgres'  # Connect to default postgres database
        )
        conn.autocommit = True
        cur = conn.cursor()
        
        # Check if database exists
        cur.execute("SELECT 1 FROM pg_catalog.pg_database WHERE datname = %s", (Config.DB_NAME,))
        exists = cur.fetchone()
        
        if not exists:
            cur.execute(f'CREATE DATABASE "{Config.DB_NAME}"')
            print(f"✅ Database '{Config.DB_NAME}' created successfully")
        else:
            print(f"✅ Database '{Config.DB_NAME}' already exists")
            
        conn.close()
    except Exception as e:
        print(f"❌ Error creating database: {e}")
        return False
    
    return True

def create_tables():
    """Create the required tables"""
    print("🏗️ Creating database tables...")
    
    try:
        conn = psycopg2.connect(
            host=Config.DB_HOST,
            port=Config.DB_PORT,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            database=Config.DB_NAME
        )
        cur = conn.cursor()
        
        # Users table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(80) UNIQUE NOT NULL,
                email VARCHAR(120) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                first_name VARCHAR(100),
                last_name VARCHAR(100),
                is_admin BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP
            )
        """)
        
        # AWS Questions table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS aws_questions (
                id SERIAL PRIMARY KEY,
                question TEXT NOT NULL,
                option_a TEXT NOT NULL,
                option_b TEXT NOT NULL,
                option_c TEXT NOT NULL,
                option_d TEXT NOT NULL,
                option_e TEXT,
                correct_answer VARCHAR(10) NOT NULL,
                explanation TEXT,
                category VARCHAR(100) DEFAULT 'AWS Cloud Practitioner',
                difficulty VARCHAR(20) DEFAULT 'medium',
                is_multiselect BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Quiz Sessions table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS quiz_sessions (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id),
                total_questions INTEGER NOT NULL,
                correct_answers INTEGER DEFAULT 0,
                score_percentage DECIMAL(5,2),
                time_taken INTEGER,
                quiz_data JSONB,
                completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # User Quiz Answers table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS user_quiz_answers (
                id SERIAL PRIMARY KEY,
                quiz_session_id INTEGER REFERENCES quiz_sessions(id),
                question_id INTEGER REFERENCES aws_questions(id),
                user_answer TEXT,
                is_correct BOOLEAN,
                time_spent INTEGER,
                answered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create indexes for better performance
        cur.execute("CREATE INDEX IF NOT EXISTS idx_aws_questions_category ON aws_questions(category)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_quiz_sessions_user_id ON quiz_sessions(user_id)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_user_quiz_answers_session_id ON user_quiz_answers(quiz_session_id)")
        
        conn.commit()
        print("✅ Database tables created successfully")
        
        # Show table info
        cur.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            ORDER BY table_name
        """)
        tables = cur.fetchall()
        print(f"📋 Created tables: {[t[0] for t in tables]}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        import traceback
        traceback.print_exc()
        return False

def create_admin_user():
    """Create a default admin user"""
    print("👤 Creating default admin user...")
    
    try:
        conn = psycopg2.connect(
            host=Config.DB_HOST,
            port=Config.DB_PORT,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            database=Config.DB_NAME
        )
        cur = conn.cursor()
        
        # Check if admin user exists
        cur.execute("SELECT id FROM users WHERE username = 'admin'")
        if cur.fetchone():
            print("✅ Admin user already exists")
            conn.close()
            return True
        
        # Create admin user (password: admin123)
        from werkzeug.security import generate_password_hash
        password_hash = generate_password_hash('admin123')
        
        cur.execute("""
            INSERT INTO users (username, email, password_hash, first_name, last_name, is_admin)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, ('admin', 'admin@quiz.local', password_hash, 'Admin', 'User', True))
        
        conn.commit()
        print("✅ Admin user created (username: admin, password: admin123)")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error creating admin user: {e}")
        return False

def load_sample_questions():
    """Load some sample questions"""
    print("📚 Loading sample questions...")
    
    try:
        conn = psycopg2.connect(
            host=Config.DB_HOST,
            port=Config.DB_PORT,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            database=Config.DB_NAME
        )
        cur = conn.cursor()
        
        # Check if questions already exist
        cur.execute("SELECT COUNT(*) FROM aws_questions")
        count = cur.fetchone()[0]
        
        if count > 0:
            print(f"✅ Questions already loaded ({count} questions)")
            conn.close()
            return True
        
        # Sample AWS Cloud Practitioner questions
        sample_questions = [
            {
                'question': 'What does AWS stand for?',
                'option_a': 'Amazon Web Services',
                'option_b': 'Amazon Website Services', 
                'option_c': 'Automated Web Services',
                'option_d': 'Amazon World Services',
                'option_e': 'Amazon Wireless Services',
                'correct_answer': 'A',
                'explanation': 'AWS stands for Amazon Web Services, which is Amazon\'s cloud computing platform.',
                'category': 'AWS Cloud Practitioner'
            },
            {
                'question': 'Which AWS service is used for object storage?',
                'option_a': 'EC2',
                'option_b': 'RDS',
                'option_c': 'S3',
                'option_d': 'Lambda',
                'option_e': 'VPC',
                'correct_answer': 'C',
                'explanation': 'Amazon S3 (Simple Storage Service) is AWS\'s object storage service.',
                'category': 'AWS Cloud Practitioner'
            },
            {
                'question': 'What is the AWS service for virtual servers?',
                'option_a': 'S3',
                'option_b': 'EC2', 
                'option_c': 'RDS',
                'option_d': 'Lambda',
                'option_e': 'CloudFront',
                'correct_answer': 'B',
                'explanation': 'Amazon EC2 (Elastic Compute Cloud) provides virtual servers in the AWS cloud.',
                'category': 'AWS Cloud Practitioner'
            }
        ]
        
        for q in sample_questions:
            cur.execute("""
                INSERT INTO aws_questions 
                (question, option_a, option_b, option_c, option_d, option_e, 
                 correct_answer, explanation, category)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (q['question'], q['option_a'], q['option_b'], q['option_c'], 
                  q['option_d'], q['option_e'], q['correct_answer'], 
                  q['explanation'], q['category']))
        
        conn.commit()
        print(f"✅ Loaded {len(sample_questions)} sample questions")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error loading sample questions: {e}")
        return False

def main():
    """Main setup function"""
    print("🚀 Setting up Local PostgreSQL Database for AWS Quiz Website")
    print("=" * 60)
    
    # Test database connection
    try:
        print("🔍 Testing PostgreSQL connection...")
        conn = psycopg2.connect(
            host=Config.DB_HOST,
            port=Config.DB_PORT,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            database='postgres'
        )
        cur = conn.cursor()
        cur.execute('SELECT version()')
        version = cur.fetchone()[0]
        print(f"✅ PostgreSQL connection successful: {version[:50]}...")
        conn.close()
    except Exception as e:
        print(f"❌ PostgreSQL connection failed: {e}")
        print("\n🔧 Make sure PostgreSQL is running:")
        print("   sudo systemctl start postgresql")
        print("   sudo systemctl status postgresql")
        return False
    
    # Setup steps
    steps = [
        ("Create Database", create_database),
        ("Create Tables", create_tables), 
        ("Create Admin User", create_admin_user),
        ("Load Sample Questions", load_sample_questions)
    ]
    
    for step_name, step_func in steps:
        print(f"\n{step_name}...")
        if not step_func():
            print(f"❌ Failed at step: {step_name}")
            return False
    
    print("\n" + "=" * 60)
    print("🎉 Database setup complete!")
    print("\n📋 Database Information:")
    print(f"   Host: {Config.DB_HOST}")
    print(f"   Port: {Config.DB_PORT}")
    print(f"   Database: {Config.DB_NAME}")
    print(f"   User: {Config.DB_USER}")
    print("\n👤 Admin Login:")
    print("   Username: admin")
    print("   Password: admin123")
    print("\n📚 Next steps:")
    print("   1. Load more questions using load_data_engineer_simple.py")
    print("   2. Start the application with ./deploy_ec2.sh")
    print("   3. Access the website and login as admin")
    
    return True

if __name__ == "__main__":
    main()
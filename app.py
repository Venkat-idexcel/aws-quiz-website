from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, g
import psycopg2
import psycopg2.extras
from psycopg2 import pool
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import secrets
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import random
import json
import re
from functools import wraps
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from authlib.integrations.flask_client import OAuth
import requests
from config import Config, DevelopmentConfig, ProductionConfig
import os
import logging
import time

# Create config dictionary for the app
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

# --- Logging Configuration (stdout friendly for containers / LB) ---
logging.basicConfig(
    level=os.getenv('LOG_LEVEL', 'INFO').upper(),
    format='%(asctime)s %(levelname)s %(message)s'
)
logger = logging.getLogger("quiz_app")

# Initialize extensions (must be before create_app)
oauth = OAuth()
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["1000 per hour", "100 per minute"]
)

# Simple request timing middleware
from flask import Response

def register_request_timing(app):
    @app.before_request
    def _start_timer():
        g._req_start = time.perf_counter()

    @app.after_request
    def _log_request(resp: Response):
        try:
            duration = (time.perf_counter() - getattr(g, '_req_start', time.perf_counter())) * 1000
            logger.info(
                "request", extra={
                    'path': request.path,
                    'method': request.method,
                    'status': resp.status_code,
                    'duration_ms': round(duration, 2),
                    'remote_ip': request.remote_addr
                }
            )
        except Exception:
            pass
        return resp


def create_app(config_name='production'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # Initialize extensions with app
    oauth.init_app(app)
    limiter.init_app(app)

    # Register OAuth providers from config
    oauth.register(
        name='google',
        client_id=app.config.get('GOOGLE_CLIENT_ID'),
        client_secret=app.config.get('GOOGLE_CLIENT_SECRET'),
        server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
        client_kwargs={'scope': 'openid email profile'}
    )
    oauth.register(
        name='github',
        client_id=app.config.get('GITHUB_CLIENT_ID'),
        client_secret=app.config.get('GITHUB_CLIENT_SECRET'),
        authorize_url='https://github.com/login/oauth/authorize',
        access_token_url='https://github.com/login/oauth/access_token',
        client_kwargs={'scope': 'user:email'}
    )
    oauth.register(
        name='microsoft',
        client_id=app.config.get('MICROSOFT_CLIENT_ID'),
        client_secret=app.config.get('MICROSOFT_CLIENT_SECRET'),
        server_metadata_url='https://login.microsoftonline.com/common/v2.0/.well-known/openid_configuration',
        client_kwargs={'scope': 'openid email profile'}
    )

    # Register CLI commands
    @app.cli.command("init-db")
    def init_db_command():
        """Creates the database tables."""
        from app import init_database
        init_database()
        print("Initialized the database.")

    @app.cli.command("create-indexes")
    def create_indexes_command():
        """Create helpful database indexes (idempotent)."""
        conn = get_db_connection()
        if not conn:
            print("Cannot obtain DB connection")
            return
        try:
            cur = conn.cursor()
            statements = [
                # Users
                "CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)",
                "CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)",
                # Quiz sessions
                "CREATE INDEX IF NOT EXISTS idx_quiz_sessions_user ON quiz_sessions(user_id)",
                "CREATE INDEX IF NOT EXISTS idx_quiz_sessions_completed ON quiz_sessions(completed_at)",
                # Activity
                "CREATE INDEX IF NOT EXISTS idx_user_activity_user ON user_activities(user_id)",
                # Badges link
                "CREATE INDEX IF NOT EXISTS idx_user_badges_user ON user_badges(user_id)"
            ]
            for stmt in statements:
                try:
                    cur.execute(stmt)
                except Exception as e:
                    print(f"Index statement failed ({stmt}): {e}")
            conn.commit()
            print("✅ Index creation completed")
        finally:
            return_db_connection(conn)

    return app

app = create_app(os.getenv('FLASK_ENV', 'default'))

# Email Configuration
# To use Gmail: 
# 1. Enable 2-Factor Authentication on your Google account
# 2. Generate App Password: Google Account → Security → App passwords
# 3. Replace the values below with your Gmail credentials

# EMAIL_HOST = 'smtp.gmail.com' # Now handled by config
# EMAIL_PORT = 587
# EMAIL_HOST_USER = 'your-gmail@gmail.com'  # Replace with your Gmail address
# EMAIL_HOST_PASSWORD = 'your-16-char-app-password'  # Replace with Gmail App Password
# EMAIL_USE_TLS = True
# app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)

# Database configuration (matching your existing setup)
# DB_CONFIG = { # Now handled by config
#     'host': 'localhost',
#     'port': 5480,
#     'database': 'cretificate_quiz_db',
#     'user': 'psql_master',
#     'password': 'LaS%J`ea&>7V2CR8C+P`'
# }

def get_db_connection():
    """Get database connection from pool with error handling"""
    if 'db_conn' in g and g.db_conn and not g.db_conn.closed:
        return g.db_conn

    try:
        # Use app context to get config
        conn = psycopg2.connect(
            host=app.config['DB_HOST'],
            port=app.config['DB_PORT'],
            database=app.config['DB_NAME'],
            user=app.config['DB_USER'],
            password=app.config['DB_PASSWORD'],
            connect_timeout=5
        )
        g.db_conn = conn
        return conn
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        # Optionally, flash a message or handle it
        # flash('Database connection is currently unavailable. Please try again later.', 'error')
        return None

def return_db_connection(conn):
    """Return connection to pool or close if not using pool"""
    # This function is simplified as we are not using a pool in this version.
    if conn and not conn.closed:
        conn.close()

# Application teardown
@app.teardown_appcontext
def close_db(error):
    """Close database connection on request end"""
    if hasattr(g, 'db_conn'):
        return_db_connection(g.db_conn)

def clean_text(text):
    """Clean text by removing PDF stamps and unwanted content"""
    if not text:
        return text
    
    # Remove IT Exam Dumps stamp variations
    text = re.sub(r'IT Exam Dumps.*?VCEup\.com', '', text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r'IT Exam Dumps.*?Learn Anything.*?VCEup\.com', '', text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r'Learn Anything.*?VCEup\.com', '', text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r'VCEup\.com', '', text, flags=re.IGNORECASE)
    
    # Remove other common PDF stamps
    text = re.sub(r'www\..*?\.com', '', text, flags=re.IGNORECASE)
    text = re.sub(r'https?://[^\s]+', '', text, flags=re.IGNORECASE)
    
    # Clean up extra whitespace and newlines
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()
    
    return text

# Badge System Functions
def check_and_award_badges(user_id):
    """Check and award badges for a user based on their achievements - OPTIMIZED"""
    conn = get_db_connection()
    if not conn:
        return []
    
    newly_awarded = []
    
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        # Get user's current stats with a single optimized query
        cur.execute("""
            SELECT 
                COUNT(qs.id) as quiz_count,
                COUNT(CASE WHEN qs.score_percentage >= 90 THEN 1 END) as high_score_count,
                COUNT(CASE WHEN qs.score_percentage = 100 THEN 1 END) as perfect_score_count,
                COALESCE(AVG(qs.score_percentage), 0) as avg_score,
                COALESCE(SUM(qs.correct_answers), 0) as total_correct_answers,
                COALESCE(MIN(qs.time_taken_minutes), 999) as fastest_time
            FROM quiz_sessions qs
            WHERE qs.user_id = %s AND qs.completed_at IS NOT NULL
        """, (user_id,))
        
        user_stats = cur.fetchone()
        if not user_stats or user_stats['quiz_count'] == 0:
            return newly_awarded
        
        # Get badges user doesn't have yet with a single query
        cur.execute("""
            SELECT b.* FROM badges b
            WHERE b.is_active = TRUE 
            AND b.id NOT IN (
                SELECT ub.badge_id FROM user_badges ub WHERE ub.user_id = %s
            )
        """, (user_id,))
        available_badges = cur.fetchall()
        
        # Check each badge criteria (much faster now with pre-fetched data)
        badges_to_award = []
        for badge in available_badges:
            should_award = False
            
            # Fast criteria checking
            if badge['criteria_type'] == 'quiz_count':
                should_award = user_stats['quiz_count'] >= badge['criteria_value']
            elif badge['criteria_type'] == 'high_score':
                should_award = user_stats['high_score_count'] > 0
            elif badge['criteria_type'] == 'perfect_score':
                should_award = user_stats['perfect_score_count'] > 0
            elif badge['criteria_type'] == 'average_score':
                should_award = user_stats['avg_score'] >= badge['criteria_value'] and user_stats['quiz_count'] >= 5
            elif badge['criteria_type'] == 'correct_answers':
                should_award = user_stats['total_correct_answers'] >= badge['criteria_value']
            elif badge['criteria_type'] == 'quick_completion':
                should_award = user_stats['fastest_time'] <= badge['criteria_value']
            
            if should_award:
                badges_to_award.append(badge)
        
        # Batch award badges if any qualify
        if badges_to_award:
            badge_values = [(user_id, badge['id']) for badge in badges_to_award]
            cur.executemany("""
                INSERT INTO user_badges (user_id, badge_id)
                VALUES (%s, %s)
                ON CONFLICT (user_id, badge_id) DO NOTHING
            """, badge_values)
            
            # Add to newly awarded list
            for badge in badges_to_award:
                newly_awarded.append({
                    'name': badge['name'],
                    'description': badge['description'],
                    'icon': badge['icon'],
                    'color': badge['color']
                })
        
        conn.commit()
        return newly_awarded
        
    except Exception as e:
        print(f"Error checking badges: {e}")
        conn.rollback()
        return newly_awarded
    finally:
        conn.close()

def get_user_badges(user_id):
    """Get all badges for a user"""
    conn = get_db_connection()
    if not conn:
        return []
    
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("""
            SELECT b.*, ub.awarded_at
            FROM badges b
            JOIN user_badges ub ON b.id = ub.badge_id
            WHERE ub.user_id = %s
            ORDER BY ub.awarded_at DESC
        """, (user_id,))
        
        return cur.fetchall()
        
    except Exception as e:
        print(f"Error getting user badges: {e}")
        return []
    finally:
        conn.close()

def get_leaderboard(limit=10):
    """Get top performers for leaderboard"""
    conn = get_db_connection()
    if not conn:
        return []
    
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        # Calculate leaderboard with comprehensive scoring
        cur.execute("""
            SELECT 
                u.id,
                u.first_name,
                u.last_name,
                u.username,
                COUNT(qs.id) as total_quizzes,
                COALESCE(AVG(qs.score_percentage), 0) as avg_score,
                COALESCE(MAX(qs.score_percentage), 0) as best_score,
                COUNT(ub.badge_id) as badges_count,
                -- Comprehensive score calculation
                (COALESCE(AVG(qs.score_percentage), 0) * 0.4 + 
                 COUNT(qs.id) * 2 + 
                 COUNT(ub.badge_id) * 5 + 
                 COALESCE(MAX(qs.score_percentage), 0) * 0.1) as leaderboard_score
            FROM users u
            LEFT JOIN quiz_sessions qs ON u.id = qs.user_id AND qs.completed_at IS NOT NULL
            LEFT JOIN user_badges ub ON u.id = ub.user_id
            WHERE u.is_active = TRUE
            GROUP BY u.id, u.first_name, u.last_name, u.username
            HAVING COUNT(qs.id) > 0
            ORDER BY leaderboard_score DESC
            LIMIT %s
        """, (limit,))
        
        return cur.fetchall()
        
    except Exception as e:
        print(f"Error getting leaderboard: {e}")
        return []
    finally:
        conn.close()

def update_achievements(user_id, achievement_type, achievement_data=None):
    """Record user achievements"""
    conn = get_db_connection()
    if not conn:
        return
    
    try:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO achievements (user_id, achievement_type, achievement_data)
            VALUES (%s, %s, %s)
        """, (user_id, achievement_type, json.dumps(achievement_data) if achievement_data else None))
        
        conn.commit()
        
    except Exception as e:
        print(f"Error updating achievements: {e}")
        conn.rollback()
    finally:
        conn.close()

def admin_required(f):
    """Decorator to require admin authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('login'))
        
        # Check if user is admin
        conn = get_db_connection()
        if not conn:
            flash('Database connection error.', 'error')
            return redirect(url_for('dashboard'))
        
        try:
            cur = conn.cursor()
            # Check if is_admin column exists
            cur.execute("""
                SELECT column_name FROM information_schema.columns 
                WHERE table_name = 'users' AND column_name = 'is_admin'
            """)
            admin_column_exists = cur.fetchone()
            
            if admin_column_exists:
                cur.execute("SELECT is_admin FROM users WHERE id = %s", (session['user_id'],))
                result = cur.fetchone()
                is_admin = result[0] if result else False
            else:
                # If is_admin column doesn't exist, no one is admin yet
                is_admin = False
            
            if not is_admin:
                flash('Access denied. Admin privileges required.', 'error')
                return redirect(url_for('dashboard'))
                
        except Exception as e:
            print(f"Admin check error: {e}")
            flash('Authentication error.', 'error')
            return redirect(url_for('dashboard'))
        finally:
            conn.close()
            
        return f(*args, **kwargs)
    return decorated_function

def log_user_activity(user_id, activity_type, description, ip_address=None, user_agent=None):
    """Log user activity for admin tracking"""
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO user_activities (user_id, activity_type, activity_description, ip_address, user_agent)
            VALUES (%s, %s, %s, %s, %s)
        """, (user_id, activity_type, description, ip_address, user_agent))
        conn.commit()
        return True
    except Exception as e:
        print(f"Activity logging error: {e}")
        return False
    finally:
        conn.close()

def get_user_performance_summary(user_id):
    """Get cached user performance summary"""
    conn = get_db_connection()
    if not conn:
        return None
    
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT 
                total_quizzes, total_questions_answered, total_correct_answers,
                average_score_percentage, best_score_percentage, worst_score_percentage,
                total_time_minutes, first_quiz_date, last_quiz_date
            FROM user_performance_summary 
            WHERE user_id = %s
        """, (user_id,))
        
        result = cur.fetchone()
        return result
    except Exception as e:
        print(f"Error getting user performance: {e}")
        return None
    finally:
        return_db_connection(conn)

def update_user_performance_summary(user_id):
    """Update user performance summary for admin dashboard"""
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        cur = conn.cursor()
        
        # Calculate performance metrics
        cur.execute("""
            SELECT 
                COUNT(*) as total_quizzes,
                COALESCE(SUM(total_questions), 0) as total_questions,
                COALESCE(SUM(correct_answers), 0) as total_correct,
                COALESCE(AVG(score_percentage), 0) as avg_score,
                COALESCE(MAX(score_percentage), 0) as best_score,
                COALESCE(MIN(score_percentage), 0) as worst_score,
                COALESCE(SUM(time_taken_minutes), 0) as total_time,
                MIN(completed_at) as first_quiz,
                MAX(completed_at) as last_quiz
            FROM quiz_sessions 
            WHERE user_id = %s AND completed_at IS NOT NULL
        """, (user_id,))
        
        stats = cur.fetchone()
        
        if stats and stats[0] > 0:  # If user has taken quizzes
            cur.execute("""
                INSERT INTO user_performance_summary 
                (user_id, total_quizzes, total_questions_answered, total_correct_answers,
                 average_score, best_score, worst_score, total_time_spent_minutes,
                 first_quiz_date, last_quiz_date, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (user_id) DO UPDATE SET
                    total_quizzes = EXCLUDED.total_quizzes,
                    total_questions_answered = EXCLUDED.total_questions_answered,
                    total_correct_answers = EXCLUDED.total_correct_answers,
                    average_score = EXCLUDED.average_score,
                    best_score = EXCLUDED.best_score,
                    worst_score = EXCLUDED.worst_score,
                    total_time_spent_minutes = EXCLUDED.total_time_spent_minutes,
                    first_quiz_date = EXCLUDED.first_quiz_date,
                    last_quiz_date = EXCLUDED.last_quiz_date,
                    updated_at = EXCLUDED.updated_at
            """, (user_id, stats[0], stats[1], stats[2], stats[3], stats[4], 
                  stats[5] if stats[5] > 0 else stats[4], stats[6], stats[7], stats[8], datetime.now()))
            conn.commit()
            
            # Note: Cache invalidation is handled automatically by cache timeout
            
        return True
    except Exception as e:
        print(f"Performance summary update error: {e}")
        return False
    finally:
        return_db_connection(conn)

def create_admin_user(username, email, password, first_name, last_name):
    """Create an admin user programmatically"""
    conn = get_db_connection()
    if not conn:
        return False, "Database connection error"
    
    try:
        cur = conn.cursor()
        
        # Ensure is_admin column exists
        try:
            cur.execute("""
                SELECT column_name FROM information_schema.columns 
                WHERE table_name = 'users' AND column_name = 'is_admin'
            """)
            admin_column_exists = cur.fetchone()
            
            if not admin_column_exists:
                cur.execute("ALTER TABLE users ADD COLUMN is_admin BOOLEAN DEFAULT FALSE")
                conn.commit()
        except Exception as col_error:
            print(f"Column check error: {col_error}")
        
        # Check if user already exists
        cur.execute("SELECT id FROM users WHERE username = %s OR email = %s", (username, email))
        if cur.fetchone():
            return False, "Username or email already exists"
        
        # Create admin user
        password_hash = generate_password_hash(password)
        cur.execute("""
            INSERT INTO users (username, email, password_hash, first_name, last_name, is_admin)
            VALUES (%s, %s, %s, %s, %s, TRUE)
            RETURNING id
        """, (username, email, password_hash, first_name, last_name))
        
        admin_id = cur.fetchone()[0]
        conn.commit()
        
        # Log activity (optional - don't fail if it doesn't work)
        try:
            log_user_activity(admin_id, 'ADMIN_CREATED', f'Admin user {username} created')
        except Exception as log_error:
            print(f"Activity logging failed (non-critical): {log_error}")
        
        return True, f"Admin user {username} created successfully with ID {admin_id}"
        
    except Exception as e:
        print(f"Admin creation error: {e}")
        conn.rollback()
        return False, f"Error creating admin user: {e}"
    finally:
        conn.close()

def send_reset_email(email, reset_token):
    """Send password reset email"""
    try:
        # Create message
        msg = MIMEMultipart()
        msg['From'] = app.config['EMAIL_HOST_USER']
        msg['To'] = email
        msg['Subject'] = 'Password Reset - Idexcel Quiz Platform'
        
        # Create reset URL (change the domain to your actual domain)
        reset_url = f"http://127.0.0.1:5000/reset-password/{reset_token}"
        
        # Email body
        body = f"""
        Hello,
        
        You have requested to reset your password for the Idexcel Quiz Platform.
        
        Click the link below to reset your password:
        {reset_url}
        
        This link will expire in 1 hour.
        
        If you didn't request this password reset, please ignore this email.
        
        Best regards,
        Idexcel Quiz Platform Team
        """
        
        msg.attach(MIMEText(body, 'plain'))
        
        # Connect to SMTP server and send email
        server = smtplib.SMTP(app.config['EMAIL_HOST'], app.config['EMAIL_PORT'])
        if app.config['EMAIL_USE_TLS']:
            server.starttls()
        server.login(app.config['EMAIL_HOST_USER'], app.config['EMAIL_HOST_PASSWORD'])
        text = msg.as_string()
        server.sendmail(app.config['EMAIL_HOST_USER'], email, text)
        server.quit()
        
        print(f"Password reset email sent to {email}")
        return True
        
    except Exception as e:
        print(f"Failed to send email to {email}: {e}")
        return False

def init_database():
    """Initialize database tables for users"""
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        cur = conn.cursor()
        
        # Create users table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                email VARCHAR(100) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                first_name VARCHAR(50) NOT NULL,
                last_name VARCHAR(50) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP,
                is_active BOOLEAN DEFAULT TRUE,
                is_admin BOOLEAN DEFAULT FALSE,
                reset_token VARCHAR(100),
                reset_token_expires TIMESTAMP
            )
        """)
        
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
        
        # Create user_activities table for admin tracking
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
        
        # Create user_performance_summary table for quick admin access
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
        
        # Create badges table for badge system
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
        
        # Create user_badges table for awarded badges
        cur.execute("""
            CREATE TABLE IF NOT EXISTS user_badges (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                badge_id INTEGER REFERENCES badges(id) ON DELETE CASCADE,
                awarded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, badge_id)
            )
        """)
        
        # Create achievements table for tracking user milestones
        cur.execute("""
            CREATE TABLE IF NOT EXISTS achievements (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                achievement_type VARCHAR(50) NOT NULL,
                achievement_data JSONB,
                achieved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create index for achievements
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_achievements_user_type 
            ON achievements(user_id, achievement_type)
        """)
        
        # Create leaderboard_cache table for performance
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

        
        # Insert default badges if they don't exist
        default_badges = [
            ('First Steps', 'Complete your first quiz', '🎯', '#28a745', 'quiz_count', 1),
            ('Quiz Master', 'Complete 5 quizzes', '🏆', '#ffc107', 'quiz_count', 5),
            ('Dedicated Learner', 'Complete 10 quizzes', '📚', '#17a2b8', 'quiz_count', 10),
            ('AWS Explorer', 'Complete 25 quizzes', '🚀', '#6f42c1', 'quiz_count', 25),
            ('High Achiever', 'Score 90% or higher', '⭐', '#fd7e14', 'high_score', 90),
            ('Perfect Score', 'Get 100% on a quiz', '💯', '#dc3545', 'perfect_score', 100),
            ('Consistent Performer', 'Maintain 80% average over 5 quizzes', '🎖️', '#20c997', 'average_score', 80),
            ('Quick Learner', 'Complete a quiz in under 5 minutes', '⚡', '#e83e8c', 'quick_completion', 5),
            ('Streak Master', 'Complete quizzes on 7 consecutive days', '🔥', '#ff6b6b', 'streak_days', 7),
            ('Knowledge Seeker', 'Answer 100 questions correctly', '🧠', '#4ecdc4', 'correct_answers', 100)
        ]
        
        for name, description, icon, color, criteria_type, criteria_value in default_badges:
            try:
                cur.execute("""
                    INSERT INTO badges (name, description, icon, color, criteria_type, criteria_value)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (name) DO NOTHING
                """, (name, description, icon, color, criteria_type, criteria_value))
            except Exception as e:
                print(f"Note: Could not insert badge {name}: {e}")

        # Add is_admin column to existing users if it doesn't exist
        try:
            cur.execute("""
                ALTER TABLE users ADD COLUMN IF NOT EXISTS is_admin BOOLEAN DEFAULT FALSE;
            """)
        except Exception as e:
            print(f"Note: Could not add is_admin column: {e}")

        # Add OAuth columns to existing users if they don't exist
        try:
            cur.execute("""
                ALTER TABLE users ADD COLUMN IF NOT EXISTS oauth_provider VARCHAR(50);
            """)
            cur.execute("""
                ALTER TABLE users ADD COLUMN IF NOT EXISTS oauth_id VARCHAR(255);
            """)
            cur.execute("""
                ALTER TABLE users ADD COLUMN IF NOT EXISTS profile_picture_url VARCHAR(500);
            """)
            cur.execute("""
                ALTER TABLE users 
                ALTER COLUMN password_hash DROP NOT NULL;
            """)
            print("✅ OAuth columns added successfully!")
        except Exception as e:
            print(f"Note: Could not add OAuth columns: {e}")
        
        # Add is_multiselect column to aws_questions table if it doesn't exist
        try:
            cur.execute("""
                ALTER TABLE aws_questions ADD COLUMN IF NOT EXISTS is_multiselect BOOLEAN DEFAULT false;
            """)
            
            # Update existing records to set is_multiselect based on correct_answer length
            cur.execute("""
                UPDATE aws_questions 
                SET is_multiselect = CASE 
                    WHEN LENGTH(TRIM(correct_answer)) > 1 THEN true 
                    ELSE false 
                END
                WHERE is_multiselect IS NULL OR is_multiselect = false;
            """)
        except Exception as e:
            print(f"Note: Could not add/update is_multiselect column: {e}")
        
        conn.commit()
        print("✅ User database tables created successfully!")
        return True
        
    except Exception as e:
        print(f"Error creating database tables: {e}")
        conn.rollback()
        return False
    finally:
        if conn:
            conn.close()

@app.route('/')
def index():
    """Home page - redirect to login if not authenticated"""
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
@limiter.limit("10 per minute", methods=["POST"])  # Rate limit login attempts
def login():
    """Login page"""
    if request.method == 'POST':
        email = request.form['email'].strip().lower()
        password = request.form['password']
        
        conn = get_db_connection()
        if not conn:
            flash('Database connection error. Please try again.', 'error')
            return render_template('auth/login.html')
        
        try:
            cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            cur.execute("SELECT * FROM users WHERE email = %s AND is_active = TRUE", (email,))
            user = cur.fetchone()
            
            if user and check_password_hash(user['password_hash'], password):
                # Update last login
                cur.execute("UPDATE users SET last_login = %s WHERE id = %s", 
                           (datetime.now(), user['id']))
                conn.commit()
                
                # Set session
                session.permanent = True  # Make session permanent
                session['user_id'] = user['id']
                session['username'] = user['username']
                session['first_name'] = user['first_name']
                session['last_name'] = user['last_name']
                
                # Check if is_admin column exists and set admin status
                try:
                    session['is_admin'] = user.get('is_admin', False) or False
                except (KeyError, TypeError):
                    session['is_admin'] = False
                
                # Log activity (only if activity logging is available)
                try:
                    log_user_activity(user['id'], 'LOGIN', f'User {user["username"]} logged in', 
                                    request.remote_addr, request.headers.get('User-Agent'))
                except Exception as log_error:
                    print(f"Activity logging error: {log_error}")
                
                flash(f'Welcome back, {user["first_name"]}!', 'success')
                
                # Redirect to admin dashboard if admin user
                if session.get('is_admin', False):
                    return redirect(url_for('admin_dashboard'))
                else:
                    return redirect(url_for('dashboard'))
            else:
                flash('Invalid email or password.', 'error')
                
        except Exception as e:
            print(f"Login error: {e}")
            flash('An error occurred during login.', 'error')
        finally:
            return_db_connection(conn)
    
    return render_template('auth/login.html')

# OAuth Routes
@app.route('/auth/<provider>')
def oauth_login(provider):
    """Initiate OAuth login with the specified provider"""
    try:
        print(f"🔑 OAuth login initiated for provider: {provider}")
        
        if provider not in ['google', 'github', 'microsoft']:
            print(f"❌ Unsupported OAuth provider: {provider}")
            flash('Unsupported OAuth provider.', 'error')
            return redirect(url_for('login'))
        
        client = oauth.create_client(provider)
        if not client:
            print(f"❌ OAuth client not configured for {provider}")
            flash(f'{provider.title()} OAuth is not configured. Please check the setup guide.', 'warning')
            return redirect(url_for('login'))
        
        redirect_uri = url_for('oauth_callback', provider=provider, _external=True)
        print(f"📍 Redirect URI for {provider}: {redirect_uri}")
        
        # For demo purposes, if using placeholder credentials, show success message
        if app.config.get(f'{provider.upper()}_CLIENT_ID', '').startswith('your-'):
             flash(f'🎉 OAuth button works! {provider.title()} OAuth initiated successfully. In production, you would be redirected to {provider.title()} for authentication.', 'success')
             return redirect(url_for('login'))
        
        return client.authorize_redirect(redirect_uri)
        
    except Exception as e:
        print(f"❌ OAuth login error for {provider}: {str(e)}")
        flash(f'Error initiating {provider.title()} login: {str(e)}', 'error')
        return redirect(url_for('login'))

@app.route('/auth/<provider>/callback')
def oauth_callback(provider):
    """Handle OAuth callback and create/login user"""
    try:
        if provider not in ['google', 'github', 'microsoft']:
            flash('Unsupported OAuth provider.', 'error')
            return redirect(url_for('login'))
        
        client = oauth.create_client(provider)
        if not client:
            flash(f'{provider.title()} OAuth is not configured.', 'error')
            return redirect(url_for('login'))

        # For demo purposes, if using placeholder credentials, show success message
        if app.config.get(f'{provider.upper()}_CLIENT_ID', '').startswith('your-'):
             flash(f'🎉 OAuth button works! {provider.title()} OAuth initiated successfully. In production, you would be redirected to {provider.title()} for authentication.', 'success')
             return redirect(url_for('login'))

        token = client.authorize_access_token()
        user_info = token.get('userinfo')
        if not user_info:
             if provider == 'github':
                 # GitHub doesn't use OIDC userinfo, fetch user from API
                 resp = client.get('user', token=token)
                 profile = resp.json()
                 user_info = {
                     'sub': profile['id'],
                     'name': profile.get('name', profile.get('login')),
                     'email': profile.get('email'),
                     'picture': profile.get('avatar_url')
                 }
             else:
                 flash(f'Failed to fetch user information from {provider.title()}.', 'error')
                 return redirect(url_for('login'))
        
        # Create or update user
        user = create_or_update_oauth_user(user_info, provider)
        if not user:
            flash('Failed to create or update user account.', 'error')
            return redirect(url_for('login'))
        
        # Log in the user
        session['user_id'] = user['id']
        session['username'] = user['username']
        session['email'] = user['email']
        session['first_name'] = user['first_name']
        session['last_name'] = user['last_name']
        session['is_admin'] = user.get('is_admin', False)
        
        flash(f'Successfully signed in with {provider.title()}!', 'success')
        
        # Redirect to appropriate dashboard
        if session.get('is_admin', False):
            return redirect(url_for('admin_dashboard'))
        else:
            return redirect(url_for('dashboard'))
            
    except Exception as e:
        print(f"OAuth callback error for {provider}: {e}")
        flash(f'Error completing {provider.title()} sign-in.', 'error')
        return redirect(url_for('login'))

def get_oauth_user_info(provider, token):
    """Get user information from OAuth provider"""
    try:
        if provider == 'google':
            client = oauth.create_client('google')
            user_info = client.get('https://www.googleapis.com/oauth2/v2/userinfo', token=token).json()
            return {
                'oauth_id': user_info.get('id'),
                'email': user_info.get('email'),
                'first_name': user_info.get('given_name', ''),
                'last_name': user_info.get('family_name', ''),
                'profile_picture': user_info.get('picture'),
                'provider': 'google'
            }
        elif provider == 'github':
            # GitHub requires separate API calls for user info
            user_response = requests.get('https://api.github.com/user', 
                                       headers={'Authorization': f'token {token["access_token"]}'})
            if user_response.status_code != 200:
                return None
            
            user_data = user_response.json()
            
            # Get user email (GitHub may have private emails)
            email_response = requests.get('https://api.github.com/user/emails',
                                        headers={'Authorization': f'token {token["access_token"]}'})
            emails = email_response.json() if email_response.status_code == 200 else []
            primary_email = next((e['email'] for e in emails if e['primary']), user_data.get('email'))
            
            # Parse name
            full_name = user_data.get('name', '').split(' ', 1)
            first_name = full_name[0] if full_name else user_data.get('login', '')
            last_name = full_name[1] if len(full_name) > 1 else ''
            
            return {
                'oauth_id': str(user_data.get('id')),
                'email': primary_email,
                'first_name': first_name,
                'last_name': last_name,
                'profile_picture': user_data.get('avatar_url'),
                'provider': 'github'
            }
        elif provider == 'microsoft':
            client = oauth.create_client('microsoft')
            user_info = client.get('https://graph.microsoft.com/v1.0/me', token=token).json()
            return {
                'oauth_id': user_info.get('id'),
                'email': user_info.get('mail') or user_info.get('userPrincipalName'),
                'first_name': user_info.get('givenName', ''),
                'last_name': user_info.get('surname', ''),
                'profile_picture': None,  # Would need additional Graph API call
                'provider': 'microsoft'
            }
    except Exception as e:
        print(f"Error getting user info from {provider}: {e}")
        return None

def create_or_update_oauth_user(user_info, provider):
    """Create new user or update existing user from OAuth info"""
    conn = get_db_connection()
    if not conn:
        return None
    
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        # Check if user already exists by OAuth ID
        cur.execute("""
            SELECT * FROM users 
            WHERE oauth_provider = %s AND oauth_id = %s
        """, (provider, user_info['oauth_id']))
        
        existing_user = cur.fetchone()
        
        if existing_user:
            # Update existing OAuth user
            cur.execute("""
                UPDATE users SET 
                    email = %s,
                    first_name = %s,
                    last_name = %s,
                    profile_picture_url = %s,
                    last_login = CURRENT_TIMESTAMP
                WHERE oauth_provider = %s AND oauth_id = %s
                RETURNING *
            """, (
                user_info['email'],
                user_info['first_name'],
                user_info['last_name'],
                user_info.get('profile_picture'),
                provider,
                user_info['oauth_id']
            ))
        else:
            # Check if user exists by email
            cur.execute("SELECT * FROM users WHERE email = %s", (user_info['email'],))
            email_user = cur.fetchone()
            
            if email_user:
                # Link existing email account with OAuth
                cur.execute("""
                    UPDATE users SET 
                        oauth_provider = %s,
                        oauth_id = %s,
                        profile_picture_url = %s,
                        last_login = CURRENT_TIMESTAMP
                    WHERE email = %s
                    RETURNING *
                """, (
                    provider,
                    user_info['oauth_id'],
                    user_info.get('profile_picture'),
                    user_info['email']
                ))
            else:
                # Create new user
                username = user_info['email'].split('@')[0]  # Use email prefix as username
                # Ensure unique username
                counter = 1
                original_username = username
                while True:
                    cur.execute("SELECT id FROM users WHERE username = %s", (username,))
                    if not cur.fetchone():
                        break
                    username = f"{original_username}{counter}"
                    counter += 1
                
                cur.execute("""
                    INSERT INTO users (
                        username, email, first_name, last_name, 
                        oauth_provider, oauth_id, profile_picture_url,
                        password_hash, created_at, last_login
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
                    ) RETURNING *
                """, (
                    username,
                    user_info['email'],
                    user_info['first_name'],
                    user_info['last_name'],
                    provider,
                    user_info['oauth_id'],
                    user_info.get('profile_picture'),
                    None  # No password for OAuth users
                ))
        
        user = cur.fetchone()
        conn.commit()
        return dict(user) if user else None
        
    except Exception as e:
        print(f"Error creating/updating OAuth user: {e}")
        conn.rollback()
        return None
    finally:
        return_db_connection(conn)

@app.route('/register', methods=['GET', 'POST'])
@limiter.limit("5 per minute", methods=["POST"])  # Rate limit registration attempts
def register():
    """Registration page"""
    if request.method == 'POST':
        # Get form data
        username = request.form['username'].strip()
        email = request.form['email'].strip().lower()
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        first_name = request.form['first_name'].strip()
        last_name = request.form['last_name'].strip()
        
        # Validation
        if not all([username, email, password, first_name, last_name]):
            flash('All fields are required.', 'error')
            return render_template('auth/register.html')
        
        if password != confirm_password:
            flash('Passwords do not match.', 'error')
            return render_template('auth/register.html')
        
        if len(password) < 6:
            flash('Password must be at least 6 characters long.', 'error')
            return render_template('auth/register.html')
        
        conn = get_db_connection()
        if not conn:
            flash('Database connection error. Please try again.', 'error')
            return render_template('auth/register.html')
        
        try:
            cur = conn.cursor()
            
            # Check if username or email already exists
            cur.execute("SELECT id FROM users WHERE username = %s OR email = %s", (username, email))
            if cur.fetchone():
                flash('Username or email already exists.', 'error')
                return render_template('auth/register.html')
            
            # Create new user
            password_hash = generate_password_hash(password)
            cur.execute("""
                INSERT INTO users (username, email, password_hash, first_name, last_name)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id
            """, (username, email, password_hash, first_name, last_name))
            
            user_id = cur.fetchone()[0]
            conn.commit()
            
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))
            
        except Exception as e:
            print(f"Registration error: {e}")
            flash('An error occurred during registration.', 'error')
            conn.rollback()
        finally:
            conn.close()
    
    return render_template('auth/register.html')

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Forgot password page"""
    if request.method == 'POST':
        email = request.form['email'].strip().lower()
        
        conn = get_db_connection()
        if not conn:
            flash('Database connection error. Please try again.', 'error')
            return render_template('auth/forgot_password.html')
        
        try:
            cur = conn.cursor()
            cur.execute("SELECT id FROM users WHERE email = %s AND is_active = TRUE", (email,))
            user = cur.fetchone()
            
            if user:
                # Generate reset token
                reset_token = secrets.token_urlsafe(32)
                expires = datetime.now() + timedelta(hours=1)
                
                cur.execute("""
                    UPDATE users 
                    SET reset_token = %s, reset_token_expires = %s 
                    WHERE email = %s
                """, (reset_token, expires, email))
                conn.commit()
                
                # Send password reset email
                email_sent = False
                try:
                    email_sent = send_reset_email(email, reset_token)
                except:
                    email_sent = False
                
                if email_sent:
                    flash(f'Password reset instructions have been sent to {email}. Please check your email.', 'info')
                else:
                    # Development mode: show token and clickable link
                    reset_url = f"http://127.0.0.1:5000/reset-password/{reset_token}"
                    flash(f'Email service unavailable. Use this link to reset password: <a href="{reset_url}" target="_blank">Reset Password</a>', 'warning')
            else:
                # Don't reveal if email exists or not
                flash(f'If an account with {email} exists, password reset instructions have been sent.', 'info')
                
        except Exception as e:
            print(f"Forgot password error: {e}")
            flash('An error occurred. Please try again.', 'error')
        finally:
            conn.close()
    
    return render_template('auth/forgot_password.html')

@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """Reset password with token"""
    conn = get_db_connection()
    if not conn:
        flash('Database connection error. Please try again.', 'error')
        return redirect(url_for('forgot_password'))
    
    try:
        cur = conn.cursor()
        # Check if token is valid and not expired
        cur.execute("""
            SELECT id, email FROM users 
            WHERE reset_token = %s AND reset_token_expires > %s AND is_active = TRUE
        """, (token, datetime.now()))
        user = cur.fetchone()
        
        if not user:
            flash('Invalid or expired reset token. Please request a new password reset.', 'error')
            return redirect(url_for('forgot_password'))
        
        if request.method == 'POST':
            password = request.form.get('password', '').strip()
            confirm_password = request.form.get('confirm_password', '').strip()
            
            if not password or len(password) < 6:
                flash('Password must be at least 6 characters long.', 'error')
                return render_template('auth/reset_password.html', token=token)
            
            if password != confirm_password:
                flash('Passwords do not match.', 'error')
                return render_template('auth/reset_password.html', token=token)
            
            # Update password and clear reset token
            password_hash = generate_password_hash(password)
            cur.execute("""
                UPDATE users 
                SET password_hash = %s, reset_token = NULL, reset_token_expires = NULL 
                WHERE id = %s
            """, (password_hash, user[0]))
            conn.commit()
            
            flash('Password has been reset successfully! Please log in with your new password.', 'success')
            return redirect(url_for('login'))
        
        return render_template('auth/reset_password.html', token=token)
        
    except Exception as e:
        print(f"Reset password error: {e}")
        flash('An error occurred. Please try again.', 'error')
        return redirect(url_for('forgot_password'))
    finally:
        conn.close()

@app.route('/dashboard')
def dashboard():
    """Main dashboard - requires authentication"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    # Get user's quiz statistics
    conn = get_db_connection()
    stats = {
        'total_quizzes': 0,
        'average_score': 0,
        'best_score': 0,
        'total_questions_answered': 0
    }
    
    if conn:
        try:
            cur = conn.cursor()
            cur.execute("""
                SELECT 
                    COUNT(*) as total_quizzes,
                    COALESCE(AVG(score_percentage), 0) as avg_score,
                    COALESCE(MAX(score_percentage), 0) as best_score,
                    COALESCE(SUM(total_questions), 0) as total_questions
                FROM quiz_sessions 
                WHERE user_id = %s AND completed_at IS NOT NULL
            """, (session['user_id'],))
            
            result = cur.fetchone()
            if result:
                stats = {
                    'total_quizzes': result[0],
                    'average_score': round(result[1], 1),
                    'best_score': round(result[2], 1),
                    'total_questions_answered': result[3]
                }
        except Exception as e:
            print(f"Dashboard stats error: {e}")
        finally:
            return_db_connection(conn)
    
    return render_template('dashboard/home.html', stats=stats)

@app.route('/quiz')
@limiter.limit("20 per minute")  # Rate limit quiz access
def quiz():
    """Start a new quiz"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    return render_template('quiz/start.html')

@app.route('/quiz/start/<quiz_type>')
@limiter.limit("10 per minute")  # Rate limit quiz starts
def take_quiz_direct(quiz_type):
    """Direct quiz start without modal"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Default to 20 questions for direct start
    num_questions = 20
    
    # Validate quiz type and handle unavailable options
    if quiz_type not in ['aws-cloud-practitioner', 'aws-data-engineer']:
        flash(f'Quiz type {quiz_type} is not available yet. Please check back later!', 'error')
        return redirect(url_for('quiz'))
    
    # Store quiz type in session for tracking
    session['current_quiz_type'] = quiz_type
    
    conn = get_db_connection()
    if not conn:
        # Use sample questions when database is not available
        sample_questions = [
            {
                'id': 1,
                'question_text': 'Which AWS service is used for object storage?',
                'option_a': 'EC2',
                'option_b': 'S3',
                'option_c': 'RDS',
                'option_d': 'Lambda',
                'option_e': '',
                'correct_answer': 'B',
                'is_multi_select': False
            }
        ]
        
        # Shuffle and limit questions
        import random
        random.shuffle(sample_questions)
        questions = sample_questions[:num_questions]
        
        session['quiz_questions'] = [q['id'] for q in questions]
        session['current_question'] = 0
        session['quiz_answers'] = {}
        session['quiz_start_time'] = datetime.now().isoformat()
        
        return render_template('quiz/question.html', 
                             question=questions[0], 
                             question_num=1, 
                             total_questions=len(questions),
                             quiz_type=quiz_type)
    
    try:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        # Get questions for the quiz type
        query = ""
        if quiz_type == 'aws-cloud-practitioner':
            query = """
                SELECT id, question, option_a, option_b, option_c, option_d, option_e, 
                       correct_answer, explanation, is_multiselect
                FROM aws_questions 
                WHERE category IS NULL OR category = '' OR category NOT ILIKE 'AWS Data Engineer'
                ORDER BY RANDOM() 
                LIMIT %s
            """
        elif quiz_type == 'aws-data-engineer':
            query = """
                SELECT id, question, option_a, option_b, option_c, option_d, option_e, 
                       correct_answer, explanation, is_multiselect
                FROM aws_questions 
                WHERE category ILIKE 'AWS Data Engineer'
                ORDER BY RANDOM() 
                LIMIT %s
            """

        if query:
            print(f"DEBUG: Executing query for {quiz_type}: {query}")
        cursor.execute(query, (num_questions,))
        
        questions = cursor.fetchall()
        print(f"DEBUG: Found {len(questions) if questions else 0} questions for {quiz_type}")
        
        if not questions:
            flash('No questions available for this quiz type. Please try again later.', 'error')
            return redirect(url_for('quiz'))
        
        # Store quiz session data
        session['quiz_question_ids'] = [q['id'] for q in questions]
        session['quiz_questions'] = [dict(q) for q in questions]
        session['quiz_current'] = 0
        session['quiz_answers'] = {}
        session['quiz_start_time'] = datetime.now().isoformat()
        session['quiz_total'] = len(questions)
        
        return render_template('quiz/question.html', 
                             question=questions[0], 
                             question_num=1, 
                             total_questions=len(questions),
                             quiz_type=quiz_type)
        
    except Exception as e:
        print(f"Database error: {e}")
        flash('Unable to start quiz. Please try again later.', 'error')
        return redirect(url_for('quiz'))
    
    finally:
        return_db_connection(conn)

@app.route('/quiz/take', methods=['POST'])
@limiter.limit("10 per minute")  # Rate limit quiz starts
def take_quiz():
    """Take quiz with selected parameters"""
    if 'user_id' not in session:
        print("DEBUG: No user_id in session for take_quiz")
        return redirect(url_for('login'))
    
    num_questions = int(request.form.get('num_questions', 20))
    quiz_type = request.form.get('quiz_type', 'aws-cloud-practitioner')
    
    print(f"DEBUG: take_quiz called with quiz_type={quiz_type}, num_questions={num_questions}")
    
    # Validate quiz type and handle unavailable options
    if quiz_type not in ['aws-cloud-practitioner', 'aws-data-engineer']:
        print(f"DEBUG: Invalid quiz type: {quiz_type}")
        flash(f'Quiz type {quiz_type} is not available yet. Please check back later!', 'error')
        return redirect(url_for('quiz'))
    
    # Store quiz type in session for tracking
    session['current_quiz_type'] = quiz_type
    
    conn = get_db_connection()
    if not conn:
        # Fallback to sample questions when database is not available
        sample_questions = [
            {
                'id': 1,
                'question_text': 'Which AWS service is used for object storage?',
                'option_a': 'EC2',
                'option_b': 'S3',
                'option_c': 'RDS',
                'option_d': 'Lambda',
                'option_e': '',
                'correct_answer': 'B',
                'is_multi_select': False
            },
            {
                'id': 2,
                'question_text': 'Which are compute services? (Select two)',
                'option_a': 'EC2',
                'option_b': 'S3',
                'option_c': 'Lambda',
                'option_d': 'RDS',
                'option_e': '',
                'correct_answer': 'AC',
                'is_multi_select': True
            },
            {
                'id': 3,
                'question_text': 'What does EC2 stand for?',
                'option_a': 'Elastic Compute Cloud',
                'option_b': 'Elastic Container Cloud',
                'option_c': 'Enterprise Compute Cloud',
                'option_d': 'Extended Compute Cloud',
                'option_e': '',
                'correct_answer': 'A',
                'is_multi_select': False
            },
            {
                'id': 4,
                'question_text': 'Which AWS service provides DNS?',
                'option_a': 'CloudFront',
                'option_b': 'Route 53',
                'option_c': 'ELB',
                'option_d': 'VPC',
                'option_e': '',
                'correct_answer': 'B',
                'is_multi_select': False
            },
            {
                'id': 5,
                'question_text': 'Which are database services? (Select two)',
                'option_a': 'RDS',
                'option_b': 'S3',
                'option_c': 'DynamoDB',
                'option_d': 'EC2',
                'option_e': '',
                'correct_answer': 'AC',
                'is_multi_select': True
            },
            {
                'id': 6,
                'question_text': 'What is Amazon VPC?',
                'option_a': 'Virtual Private Cloud',
                'option_b': 'Virtual Public Cloud',
                'option_c': 'Virtual Protected Cloud',
                'option_d': 'Virtual Private Connection',
                'option_e': '',
                'correct_answer': 'A',
                'is_multi_select': False
            },
            {
                'id': 7,
                'question_text': 'Which provide content delivery? (Select two)',
                'option_a': 'CloudFront',
                'option_b': 'S3',
                'option_c': 'Global Accelerator',
                'option_d': 'RDS',
                'option_e': '',
                'correct_answer': 'AC',
                'is_multi_select': True
            },
            {
                'id': 8,
                'question_text': 'What is AWS IAM?',
                'option_a': 'Identity and Access Management',
                'option_b': 'Internet Access Management',
                'option_c': 'Infrastructure Access Management',
                'option_d': 'Internal Application Management',
                'option_e': '',
                'correct_answer': 'A',
                'is_multi_select': False
            },
            {
                'id': 9,
                'question_text': 'Which are monitoring services? (Select two)',
                'option_a': 'CloudWatch',
                'option_b': 'S3',
                'option_c': 'X-Ray',
                'option_d': 'EC2',
                'option_e': '',
                'correct_answer': 'AC',
                'is_multi_select': True
            },
            {
                'id': 10,
                'question_text': 'What is AWS Lambda?',
                'option_a': 'Virtual Machine Service',
                'option_b': 'Serverless Compute Service',
                'option_c': 'Database Service',
                'option_d': 'Storage Service',
                'option_e': '',
                'correct_answer': 'B',
                'is_multi_select': False
            },
            # Adding more sample questions to support 20+ questions when DB is offline
            {
                'id': 11,
                'question_text': 'Which AWS service is used for content delivery network (CDN)?',
                'option_a': 'S3',
                'option_b': 'CloudFront',
                'option_c': 'Route 53',
                'option_d': 'ELB',
                'option_e': '',
                'correct_answer': 'B',
                'is_multi_select': False
            },
            {
                'id': 12,
                'question_text': 'Which are valid AWS storage services? (Select two)',
                'option_a': 'S3',
                'option_b': 'EC2',
                'option_c': 'EBS',
                'option_d': 'Lambda',
                'option_e': '',
                'correct_answer': 'AC',
                'is_multi_select': True
            },
            {
                'id': 13,
                'question_text': 'What is AWS EBS?',
                'option_a': 'Elastic Block Store',
                'option_b': 'Elastic Bean Stalk',
                'option_c': 'Elastic Backup Service',
                'option_d': 'Enterprise Backup System',
                'option_e': '',
                'correct_answer': 'A',
                'is_multi_select': False
            },
            {
                'id': 14,
                'question_text': 'Which AWS service provides managed database?',
                'option_a': 'EC2',
                'option_b': 'S3',
                'option_c': 'RDS',
                'option_d': 'Lambda',
                'option_e': '',
                'correct_answer': 'C',
                'is_multi_select': False
            },
            {
                'id': 15,
                'question_text': 'Which are NoSQL database services? (Select two)',
                'option_a': 'RDS',
                'option_b': 'DynamoDB',
                'option_c': 'DocumentDB',
                'option_d': 'S3',
                'option_e': '',
                'correct_answer': 'BC',
                'is_multi_select': True
            },
            {
                'id': 16,
                'question_text': 'What is AWS Auto Scaling?',
                'option_a': 'Automatic storage scaling',
                'option_b': 'Automatic compute scaling',
                'option_c': 'Automatic network scaling',
                'option_d': 'Automatic backup scaling',
                'option_e': '',
                'correct_answer': 'B',
                'is_multi_select': False
            },
            {
                'id': 17,
                'question_text': 'Which services help with high availability? (Select two)',
                'option_a': 'ELB',
                'option_b': 'S3',
                'option_c': 'Auto Scaling',
                'option_d': 'Lambda',
                'option_e': '',
                'correct_answer': 'AC',
                'is_multi_select': True
            },
            {
                'id': 18,
                'question_text': 'What is AWS ELB?',
                'option_a': 'Elastic Load Balancer',
                'option_b': 'Elastic Logging Buffer',
                'option_c': 'Enterprise Load Balancer',
                'option_d': 'Extended Load Balancer',
                'option_e': '',
                'correct_answer': 'A',
                'is_multi_select': False
            },
            {
                'id': 19,
                'question_text': 'Which AWS service provides messaging?',
                'option_a': 'S3',
                'option_b': 'SQS',
                'option_c': 'EC2',
                'option_d': 'RDS',
                'option_e': '',
                'correct_answer': 'B',
                'is_multi_select': False
            },
            {
                'id': 20,
                'question_text': 'Which are valid messaging services? (Select two)',
                'option_a': 'SQS',
                'option_b': 'EC2',
                'option_c': 'SNS',
                'option_d': 'S3',
                'option_e': '',
                'correct_answer': 'AC',
                'is_multi_select': True
            },
            {
                'id': 21,
                'question_text': 'What is AWS SNS?',
                'option_a': 'Simple Notification Service',
                'option_b': 'Simple Network Service',
                'option_c': 'Secure Notification System',
                'option_d': 'Standard Network Service',
                'option_e': '',
                'correct_answer': 'A',
                'is_multi_select': False
            },
            {
                'id': 22,
                'question_text': 'Which services provide security? (Select two)',
                'option_a': 'IAM',
                'option_b': 'S3',
                'option_c': 'KMS',
                'option_d': 'EC2',
                'option_e': '',
                'correct_answer': 'AC',
                'is_multi_select': True
            },
            {
                'id': 23,
                'question_text': 'What is AWS KMS?',
                'option_a': 'Key Management Service',
                'option_b': 'Kernel Management System',
                'option_c': 'Knowledge Management Service',
                'option_d': 'Keystore Management System',
                'option_e': '',
                'correct_answer': 'A',
                'is_multi_select': False
            },
            {
                'id': 24,
                'question_text': 'Which AWS service provides API management?',
                'option_a': 'Lambda',
                'option_b': 'API Gateway',
                'option_c': 'EC2',
                'option_d': 'S3',
                'option_e': '',
                'correct_answer': 'B',
                'is_multi_select': False
            },
            {
                'id': 25,
                'question_text': 'Which are serverless services? (Select two)',
                'option_a': 'Lambda',
                'option_b': 'EC2',
                'option_c': 'API Gateway',
                'option_d': 'RDS',
                'option_e': '',
                'correct_answer': 'AC',
                'is_multi_select': True
            },
            {
                'id': 26,
                'question_text': 'What is AWS Step Functions?',
                'option_a': 'Workflow orchestration',
                'option_b': 'Load balancing',
                'option_c': 'Data storage',
                'option_d': 'Network routing',
                'option_e': '',
                'correct_answer': 'A',
                'is_multi_select': False
            },
            {
                'id': 27,
                'question_text': 'Which services help with DevOps? (Select two)',
                'option_a': 'CodePipeline',
                'option_b': 'S3',
                'option_c': 'CodeDeploy',
                'option_d': 'EC2',
                'option_e': '',
                'correct_answer': 'AC',
                'is_multi_select': True
            },
            {
                'id': 28,
                'question_text': 'What is AWS CodePipeline?',
                'option_a': 'Data pipeline service',
                'option_b': 'CI/CD pipeline service',
                'option_c': 'Network pipeline service',
                'option_d': 'Storage pipeline service',
                'option_e': '',
                'correct_answer': 'B',
                'is_multi_select': False
            },
            {
                'id': 29,
                'question_text': 'Which AWS service provides container orchestration?',
                'option_a': 'EC2',
                'option_b': 'ECS',
                'option_c': 'S3',
                'option_d': 'Lambda',
                'option_e': '',
                'correct_answer': 'B',
                'is_multi_select': False
            },
            {
                'id': 30,
                'question_text': 'Which are container services? (Select two)',
                'option_a': 'ECS',
                'option_b': 'S3',
                'option_c': 'EKS',
                'option_d': 'RDS',
                'option_e': '',
                'correct_answer': 'AC',
                'is_multi_select': True
            }
        ]
        
        # Allow repeating questions if we need more than available sample questions
        if num_questions <= len(sample_questions):
            questions = random.sample(sample_questions, num_questions)
        else:
            # If requested more questions than available samples, repeat some randomly
            questions = sample_questions[:]  # Start with all questions
            remaining_needed = num_questions - len(sample_questions)
            additional_questions = random.choices(sample_questions, k=remaining_needed)
            questions.extend(additional_questions)
            random.shuffle(questions)  # Shuffle the final list
        
        print(f"DEBUG: Using {len(questions)} sample questions (requested {num_questions}) for quiz type: {quiz_type}")
        
        # Store minimal quiz session data
        session['quiz_session_id'] = 1
        session['quiz_questions'] = questions
        session['quiz_question_ids'] = [q['id'] for q in questions]
        session['quiz_current'] = 0
        session['quiz_answers'] = {}
        session['quiz_start_time'] = datetime.now().isoformat()
        session['quiz_type'] = quiz_type
        session['quiz_total'] = len(questions)
        
        print(f"DEBUG: Quiz initialized successfully, redirecting to quiz_question")
        return redirect(url_for('quiz_question'))
    
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        # Get random questions based on quiz type
        query = ""
        if quiz_type == 'aws-cloud-practitioner':
            query = """
                SELECT id, question, option_a, option_b, option_c, option_d, option_e, correct_answer, explanation,
                       COALESCE(is_multiselect, CASE WHEN LENGTH(TRIM(correct_answer)) > 1 THEN true ELSE false END) as is_multiselect
                FROM aws_questions 
                WHERE category IS NULL OR category = '' OR category NOT ILIKE 'AWS Data Engineer'
                ORDER BY RANDOM() 
                LIMIT %s
            """
        elif quiz_type == 'aws-data-engineer':
            query = """
                SELECT id, question, option_a, option_b, option_c, option_d, option_e, correct_answer, explanation,
                       COALESCE(is_multiselect, CASE WHEN LENGTH(TRIM(correct_answer)) > 1 THEN true ELSE false END) as is_multiselect
                FROM aws_questions 
                WHERE category ILIKE 'AWS Data Engineer'
                ORDER BY RANDOM() 
                LIMIT %s
            """
        
        if not query:
             flash(f'Quiz type {quiz_type} is not implemented yet.', 'error')
             return redirect(url_for('quiz'))

        print(f"DEBUG: Executing query for {quiz_type}: {query}")
        cur.execute(query, (num_questions,))
        questions = cur.fetchall()
        
        print(f"DEBUG: Fetched {len(questions) if questions else 0} questions from database for {quiz_type}")
        
        if not questions:
            print(f"DEBUG: No questions found for quiz type: {quiz_type}")
            flash('No questions available for this quiz type.', 'error')
            return redirect(url_for('quiz'))
        
        # Create quiz session with quiz type information
        quiz_data = {
            'questions': [dict(q) for q in questions],
            'quiz_type': quiz_type,
            'quiz_type_display': 'AWS Cloud Practitioner' if quiz_type == 'aws-cloud-practitioner' else 'AWS Data Engineer'
        }
        
        cur.execute("""
            INSERT INTO quiz_sessions (user_id, total_questions, quiz_data)
            VALUES (%s, %s, %s)
            RETURNING id
        """, (session['user_id'], len(questions), json.dumps(quiz_data)))
        
        session_id = cur.fetchone()[0]
        conn.commit()
        
        print(f"DEBUG: Created quiz session {session_id} with {len(questions)} questions")
        
        # Convert questions to serializable format and detect multi-answer questions
        quiz_questions = []
        for i, q in enumerate(questions):
            try:
                # Clean the text content to remove PDF stamps
                # Handle both 'question' and 'question_text' column names
                question_text = clean_text(str(q.get('question') or q.get('question_text') or ''))
                option_a = clean_text(str(q['option_a'] or ''))
                option_b = clean_text(str(q['option_b'] or ''))
                option_c = clean_text(str(q['option_c'] or ''))
                option_d = clean_text(str(q['option_d'] or ''))
                option_e = clean_text(str(q['option_e'] or ''))
                
                # Store only essential data to reduce session size
                question_data = {
                    'id': int(q['id']),
                    'question': question_text,  # Use 'question' as the key
                    'option_a': option_a,
                    'option_b': option_b,
                    'option_c': option_c, 
                    'option_d': option_d,
                    'option_e': option_e,
                    'correct_answer': str(q['correct_answer'] or '').strip(),
                    'is_multi_select': bool(q.get('is_multiselect', len(str(q['correct_answer'] or '').strip()) > 1))
                }
                quiz_questions.append(question_data)
                print(f"DEBUG: Processed question {i+1}: {question_data['id']} - Multi: {question_data['is_multi_select']}")
            except Exception as e:
                print(f"DEBUG: Error processing question {i+1}: {e}")
                continue
        
        # Store quiz session data
        session['quiz_session_id'] = int(session_id)
        session['quiz_questions'] = quiz_questions  # Store the processed questions
        session['quiz_question_ids'] = [int(q['id']) for q in questions]
        session['quiz_total'] = len(quiz_questions) 
        session['quiz_current'] = 0
        session['quiz_answers'] = {}
        session['quiz_start_time'] = datetime.now().isoformat()
        session['quiz_type'] = quiz_type
        
        print(f"DEBUG: Stored {len(quiz_questions)} questions in session for quiz type: {quiz_type}")
        
        return redirect(url_for('quiz_question'))
        
    except Exception as e:
        print(f"Quiz creation error: {e}")
        flash('Error creating quiz.', 'error')
        return redirect(url_for('quiz'))
    finally:
        if conn:
            conn.close()

@app.route('/quiz/answer', methods=['POST'])
@limiter.limit("60 per minute")
def quiz_answer():
    """Handle quiz answer submission and redirect to next question"""
    if 'user_id' not in session or 'quiz_questions' not in session:
        return redirect(url_for('quiz'))
    
    # Get the answer from the form
    answers = session.get('quiz_answers', {})
    current_question_index = session.get('quiz_current', 0)
    questions = session['quiz_questions']
    
    if current_question_index < len(questions):
        question_data = questions[current_question_index]
        question_id = str(question_data['id'])
        
        # Handle both single and multiple answers
        user_answer = request.form.getlist('answer')
        if user_answer:
            answers[question_id] = ''.join(sorted(user_answer))
        
        session['quiz_answers'] = answers
        session['quiz_current'] = current_question_index + 1
    
    return redirect(url_for('quiz_question'))

@app.route('/quiz/question', methods=['GET', 'POST'])
@limiter.limit("60 per minute")  # Allow frequent answers
def quiz_question():
    """Display current quiz question"""
    if 'user_id' not in session:
        print("DEBUG: No user_id in session, redirecting to quiz")
        return redirect(url_for('quiz'))
        
    if 'quiz_questions' not in session:
        print("DEBUG: No quiz_questions in session, redirecting to quiz")
        print(f"DEBUG: Session keys: {list(session.keys())}")
        return redirect(url_for('quiz'))
    
    current = session.get('quiz_current', 0)
    questions = session.get('quiz_questions', [])
    total_questions = len(questions)
    
    print(f"DEBUG: Current question: {current}, Total questions: {total_questions}")
    print(f"DEBUG: Session quiz_current: {session.get('quiz_current')}")
    
    if current >= total_questions:
        print(f"DEBUG: Redirecting to results - current ({current}) >= total ({total_questions})")
        return redirect(url_for('quiz_results'))
    
    # Get the current question
    if current < len(questions):
        question = questions[current]
        print(f"DEBUG: Retrieved question {current + 1}: {question.get('question', 'No question text')[:50]}...")
        
        print(f"DEBUG: Displaying question {current + 1} of {total_questions}")
        
        return render_template('quiz/question.html', 
                             question=question, 
                             current=current + 1, 
                             total=total_questions)
    else:
        print("DEBUG: Current index out of range, redirecting to results")
        return redirect(url_for('quiz_results'))

@app.route('/quiz/results')
def quiz_results():
    """Show quiz results"""
    if 'user_id' not in session or 'quiz_session_id' not in session:
        return redirect(url_for('quiz'))
    
    question_ids = session.get('quiz_question_ids', [])
    questions = session.get('quiz_questions', [])  # Fallback for sample questions
    answers = session.get('quiz_answers', {})
    start_time = datetime.fromisoformat(session.get('quiz_start_time'))
    end_time = datetime.now()
    time_taken = int((end_time - start_time).total_seconds() / 60)
    
    # Calculate score
    correct_answers = 0
    results = []
    
    questions = session.get('quiz_questions', [])
    answers = session.get('quiz_answers', {})
    
    for i, q in enumerate(questions):
        question_id = str(q['id'])
        user_answer = answers.get(question_id)
        
        # Normalize correct answer by sorting characters
        correct_answer = "".join(sorted(q['correct_answer'].strip().upper()))
        
        is_correct = False
        if user_answer:
            # Also normalize user answer
            user_answer_sorted = "".join(sorted(user_answer.strip().upper()))
            if user_answer_sorted == correct_answer:
                is_correct = True
                correct_answers += 1
        
        results.append({
            'question_num': i + 1,
            'question': q,
            'user_answer': user_answer,
            'correct_answer': correct_answer,
            'is_correct': is_correct
        })
    
    total_questions = len(questions)
    score_percentage = (correct_answers / total_questions) * 100 if total_questions > 0 else 0
    
    # Save results to database
    conn = get_db_connection()
    if conn:
        try:
            cur = conn.cursor()
            
            # Update quiz session
            cur.execute("""
                UPDATE quiz_sessions 
                SET completed_at = %s, correct_answers = %s, score_percentage = %s, time_taken_minutes = %s
                WHERE id = %s
            """, (end_time, correct_answers, score_percentage, time_taken, session['quiz_session_id']))
            
            # Save detailed answers
            answer_records = []
            for res in results:
                answer_records.append((
                    session['quiz_session_id'],
                    res['question']['id'],
                    res['user_answer'],
                    res['correct_answer'],
                    res['is_correct']
                ))
            
            cur.executemany("""
                INSERT INTO quiz_answers (session_id, question_id, user_answer, correct_answer, is_correct)
                VALUES (%s, %s, %s, %s, %s)
            """, answer_records)
            
            conn.commit()
            
            # Update performance summary in the background (or could be a task queue)
            update_user_performance_summary(session['user_id'])
            
            # Check for new badges
            newly_awarded_badges = check_and_award_badges(session['user_id'])
            if newly_awarded_badges:
                flash(f"🎉 You've earned {len(newly_awarded_badges)} new badge(s)!", 'success')
                for badge in newly_awarded_badges:
                    flash(f"🏅 {badge['name']}: {badge['description']}", 'info')

        except Exception as e:
            print(f"Error saving quiz results: {e}")
            conn.rollback()
        finally:
            return_db_connection(conn)
    
    # Clear quiz session data
    session.pop('quiz_questions', None)
    session.pop('quiz_current', None)
    session.pop('quiz_answers', None)
    session.pop('quiz_start_time', None)
    session.pop('quiz_session_id', None)
    session.pop('current_quiz_type', None)
    
    return render_template('quiz/results.html', 
                         results=results, 
                         total_questions=total_questions,
                         correct_answers=correct_answers,
                         score_percentage=score_percentage,
                         time_taken=time_taken)

@app.route('/quiz/history')
def quiz_history():
    """Show quiz history"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    quiz_history = []
    
    if conn:
        try:
            cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            cur.execute("""
                SELECT id, started_at, completed_at, total_questions, correct_answers, 
                       score_percentage, time_taken_minutes
                FROM quiz_sessions 
                WHERE user_id = %s AND completed_at IS NOT NULL
                ORDER BY completed_at DESC
                LIMIT 50
            """, (session['user_id'],))
            
            quiz_history = cur.fetchall()
            
        except Exception as e:
            print(f"History error: {e}")
        finally:
            conn.close()
    
    return render_template('dashboard/history.html', quiz_history=quiz_history)

# Badge and Leaderboard Routes
@app.route('/badges')
def user_badges():
    """Display user's badges and achievements"""
    if 'user_id' not in session:
        flash('Please log in to view your badges.', 'error')
        return redirect(url_for('login'))
    
    # Get newly awarded badges from session
    newly_awarded = session.pop('newly_awarded_badges', [])
    
    user_badges = get_user_badges(session['user_id'])
    
    return render_template('badges.html', 
                         user_badges=user_badges, 
                         newly_awarded=newly_awarded)

@app.route('/leaderboard')
def leaderboard():
    """Display leaderboard with top performers"""
    leaderboard_data = get_leaderboard(20)
    
    # Get current user's position if logged in
    user_position = None
    if 'user_id' in session:
        for idx, user in enumerate(leaderboard_data):
            if user['id'] == session['user_id']:
                user_position = idx + 1
                break
    
    return render_template('leaderboard.html', 
                         leaderboard=leaderboard_data, 
                         user_position=user_position)

@app.route('/admin')
@admin_required
def admin_dashboard():
    """Admin dashboard with user statistics and analytics"""
    conn = get_db_connection()
    if not conn:
        flash('Database connection error.', 'error')
        return redirect(url_for('dashboard'))
    
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        # Get overall platform statistics
        cur.execute("""
            SELECT 
                COUNT(*) as total_users,
                COUNT(*) FILTER (WHERE is_active = TRUE) as active_users,
                COUNT(*) FILTER (WHERE last_login >= NOW() - INTERVAL '30 days') as active_last_30_days,
                COUNT(*) FILTER (WHERE created_at >= NOW() - INTERVAL '30 days') as new_users_30_days
            FROM users WHERE is_admin = FALSE
        """)
        user_stats = cur.fetchone()
        
        # Get quiz statistics
        cur.execute("""
            SELECT 
                COUNT(*) as total_quizzes,
                COUNT(DISTINCT user_id) as unique_users_took_quiz,
                ROUND(AVG(score_percentage), 1) as average_score,
                COUNT(*) FILTER (WHERE completed_at >= NOW() - INTERVAL '7 days') as quizzes_last_7_days
            FROM quiz_sessions WHERE completed_at IS NOT NULL
        """)
        quiz_stats = cur.fetchone()
        
        # Get top performers (last 30 days)
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
        
        # Get recent activities
        cur.execute("""
            SELECT ua.activity_type, ua.activity_description, ua.created_at,
                   u.first_name, u.last_name, u.email
            FROM user_activities ua
            JOIN users u ON ua.user_id = u.id
            WHERE u.is_admin = FALSE
            ORDER BY ua.created_at DESC
            LIMIT 20
        """)
        recent_activities = cur.fetchall()
        
        stats = {
            'user_stats': dict(user_stats) if user_stats else {},
            'quiz_stats': dict(quiz_stats) if quiz_stats else {},
            'top_performers': top_performers,
            'recent_activities': recent_activities
        }
        
        return render_template('admin/dashboard.html', stats=stats)
        
    except Exception as e:
        print(f"Admin dashboard error: {e}")
        flash('Error loading admin dashboard.', 'error')
        return redirect(url_for('dashboard'))
    finally:
        conn.close()

@app.route('/admin/users')
@admin_required
def admin_users():
    """Admin user management page"""
    conn = get_db_connection()
    if not conn:
        flash('Database connection error.', 'error')
        return redirect(url_for('admin_dashboard'))
    
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        # Get all users with their performance summary
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
        
        return render_template('admin/users.html', users=users)
        
    except Exception as e:
        print(f"Admin users error: {e}")
        flash('Error loading users page.', 'error')
        return redirect(url_for('admin_dashboard'))
    finally:
        conn.close()

@app.route('/admin/user/<int:user_id>')
@admin_required
def admin_user_detail(user_id):
    """Admin user detail page"""
    conn = get_db_connection()
    if not conn:
        flash('Database connection error.', 'error')
        return redirect(url_for('admin_users'))
    
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        # Get user details
        cur.execute("""
            SELECT u.*, ups.*
            FROM users u
            LEFT JOIN user_performance_summary ups ON u.id = ups.user_id
            WHERE u.id = %s AND u.is_admin = FALSE
        """, (user_id,))
        user = cur.fetchone()
        
        if not user:
            flash('User not found.', 'error')
            return redirect(url_for('admin_users'))
        
        # Get user's quiz history
        cur.execute("""
            SELECT id, started_at, completed_at, total_questions, correct_answers,
                   score_percentage, time_taken_minutes
            FROM quiz_sessions
            WHERE user_id = %s AND completed_at IS NOT NULL
            ORDER BY completed_at DESC
            LIMIT 50
        """, (user_id,))
        quiz_history = cur.fetchall()
        
        # Get user activities
        cur.execute("""
            SELECT activity_type, activity_description, created_at, ip_address
            FROM user_activities
            WHERE user_id = %s
            ORDER BY created_at DESC
            LIMIT 50
        """, (user_id,))
        activities = cur.fetchall()
        
        return render_template('admin/user_detail.html', 
                             user=dict(user), 
                             quiz_history=quiz_history,
                             activities=activities)
        
    except Exception as e:
        print(f"Admin user detail error: {e}")
        flash('Error loading user details.', 'error')
        return redirect(url_for('admin_users'))
    finally:
        conn.close()

@app.route('/admin/analytics')
@admin_required
def admin_analytics():
    """Admin analytics page with charts and detailed metrics"""
    conn = get_db_connection()
    if not conn:
        flash('Database connection error.', 'error')
        return redirect(url_for('admin_dashboard'))
    
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        # Score distribution
        cur.execute("""
            SELECT 
                CASE 
                    WHEN score_percentage >= 90 THEN '90-100%'
                    WHEN score_percentage >= 80 THEN '80-89%'
                    WHEN score_percentage >= 70 THEN '70-79%'
                    WHEN score_percentage >= 60 THEN '60-69%'
                    ELSE 'Below 60%'
                END as score_range,
                COUNT(*) as count
            FROM quiz_sessions 
            WHERE completed_at IS NOT NULL
            GROUP BY score_range
            ORDER BY MIN(score_percentage) DESC
        """)
        score_distribution = cur.fetchall()
        
        # Daily quiz activity (last 30 days)
        cur.execute("""
            SELECT DATE(completed_at) as quiz_date, COUNT(*) as quiz_count
            FROM quiz_sessions 
            WHERE completed_at >= NOW() - INTERVAL '30 days'
              AND completed_at IS NOT NULL
            GROUP BY DATE(completed_at)
            ORDER BY quiz_date
        """)
        daily_activity = cur.fetchall()
        
        # Question difficulty analysis (if question_id exists)
        cur.execute("""
            SELECT qa.correct_answer, 
                   COUNT(*) as total_attempts,
                   COUNT(*) FILTER (WHERE qa.is_correct = TRUE) as correct_attempts,
                   ROUND(COUNT(*) FILTER (WHERE qa.is_correct = TRUE) * 100.0 / COUNT(*), 1) as success_rate
            FROM quiz_answers qa
            GROUP BY qa.correct_answer
            HAVING COUNT(*) >= 10
            ORDER BY success_rate ASC
            LIMIT 10
        """)
        difficult_questions = cur.fetchall()
        
        analytics = {
            'score_distribution': score_distribution,
            'daily_activity': daily_activity,
            'difficult_questions': difficult_questions
        }
        
        return render_template('admin/analytics.html', analytics=analytics)
        
    except Exception as e:
        print(f"Admin analytics error: {e}")
        flash('Error loading analytics.', 'error')
        return redirect(url_for('admin_dashboard'))
    finally:
        conn.close()

@app.route('/admin/create-admin', methods=['GET', 'POST'])
@admin_required
def admin_create_admin():
    """Create new admin user (admin only)"""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        
        success, message = create_admin_user(username, email, password, first_name, last_name)
        
        if success:
            flash(message, 'success')
            return redirect(url_for('admin_users'))
        else:
            flash(message, 'error')
    
    return render_template('admin/create_admin.html')

# Route for initial admin creation (remove after first admin is created)
@app.route('/create-first-admin', methods=['GET', 'POST'])
def create_first_admin():
    """Create the first admin user - should be disabled after first admin exists"""
    conn = get_db_connection()
    if not conn:
        flash('Database connection error.', 'error')
        return "Database connection error"
    
    try:
        cur = conn.cursor()
        
        # First, ensure is_admin column exists
        cur.execute("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name = 'users' AND column_name = 'is_admin'
        """)
        admin_column_exists = cur.fetchone()
        
        if not admin_column_exists:
            cur.execute("ALTER TABLE users ADD COLUMN is_admin BOOLEAN DEFAULT FALSE")
            conn.commit()
            print("Added is_admin column to users table")
        
        # Check if any admin already exists
        cur.execute("SELECT COUNT(*) FROM users WHERE is_admin = TRUE")
        admin_count = cur.fetchone()[0]
        
        # If admin already exists, disable this route
        if admin_count > 0:
            flash('Admin user already exists. Please use the login page.', 'info')
            return redirect(url_for('login'))
        
    except Exception as e:
        print(f"Admin check error: {e}")
        # If there's any error, allow the route to continue
        pass
    finally:
        conn.close()
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        
        if not all([username, email, password, first_name, last_name]):
            flash('All fields are required.', 'error')
        elif len(password) < 6:
            flash('Password must be at least 6 characters long.', 'error')
        else:
            success, message = create_admin_user(username, email, password, first_name, last_name)
            
            if success:
                flash(message, 'success')
                flash('Admin user created! Please log in.', 'success')
                return redirect(url_for('login'))
            else:
                flash(message, 'error')
    
    return render_template('admin/create_first_admin.html')

# Migration route to add admin column safely
@app.route('/migrate-admin-column')
def migrate_admin_column():
    """Add is_admin column to existing users table"""
    conn = get_db_connection()
    if not conn:
        return "❌ Database connection error"
    
    try:
        cur = conn.cursor()
        
        # Check if is_admin column exists
        cur.execute("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name = 'users' AND column_name = 'is_admin'
        """)
        admin_column_exists = cur.fetchone()
        
        if not admin_column_exists:
            # Add the column
            cur.execute("ALTER TABLE users ADD COLUMN is_admin BOOLEAN DEFAULT FALSE")
            conn.commit()
            return "✅ Successfully added is_admin column to users table. You can now create admin users."
        else:
            return "✅ is_admin column already exists in users table. You can create admin users."
            
    except Exception as e:
        return f"❌ Error adding admin column: {e}"
    finally:
        conn.close()

# Test route to make a user admin (for development only)
@app.route('/make-admin/<username>')
def make_admin(username):
    """Make an existing user an admin (for development/testing only)"""
    conn = get_db_connection()
    if not conn:
        return "❌ Database connection error"
    
    try:
        cur = conn.cursor()
        
        # First ensure the admin column exists
        cur.execute("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name = 'users' AND column_name = 'is_admin'
        """)
        admin_column_exists = cur.fetchone()
        
        if not admin_column_exists:
            cur.execute("ALTER TABLE users ADD COLUMN is_admin BOOLEAN DEFAULT FALSE")
            conn.commit()
        
        # Check if user exists
        cur.execute("SELECT id, first_name, last_name FROM users WHERE username = %s", (username,))
        user = cur.fetchone()
        
        if not user:
            return f"❌ User '{username}' not found"
        
        # Make user admin
        cur.execute("UPDATE users SET is_admin = TRUE WHERE username = %s", (username,))
        conn.commit()
        
        return f"✅ User '{username}' ({user[1]} {user[2]}) has been made an admin! You can now login and access admin features."
        
    except Exception as e:
        return f"❌ Error making user admin: {e}"
    finally:
        conn.close()

# Route to show existing admin users (for development only)
@app.route('/show-admins')
def show_admins():
    """Show all admin users in the database"""
    conn = get_db_connection()
    if not conn:
        return "❌ Database connection error"
    
    try:
        cur = conn.cursor()
        
        # Check if is_admin column exists
        cur.execute("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name = 'users' AND column_name = 'is_admin'
        """)
        admin_column_exists = cur.fetchone()
        
        if not admin_column_exists:
            return "❌ Admin column doesn't exist. Please run /migrate-admin-column first."
        
        # Get all admin users
        cur.execute("""
            SELECT username, first_name, last_name, email, is_admin 
            FROM users 
            WHERE is_admin = TRUE 
            ORDER BY first_name, last_name
        """)
        admins = cur.fetchall()
        
        if not admins:
            return "❌ No admin users found in database."
        
        html = "<h2>🔑 Admin Users in Database</h2>"
        html += "<ul>"
        for admin in admins:
            username, first_name, last_name, email, is_admin = admin
            html += f"<li><strong>{username}</strong> - {first_name} {last_name} ({email})</li>"
        html += "</ul>"
        html += "<br><p>You can login with any of these admin usernames and their passwords.</p>"
        html += '<p><a href="/login">🔗 Go to Login Page</a></p>'
        
        return html
        
    except Exception as e:
        return f"❌ Error fetching admin users: {e}"
    finally:
        conn.close()

@app.route('/logout')
def logout():
    """Logout user"""
    session.clear()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('login'))

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('errors/500.html'), 500

@app.errorhandler(429)
def ratelimit_handler(e):
    """Handle rate limit exceeded errors"""
    return render_template('errors/429.html'), 429

# --- Health & Readiness Probes (for Load Balancers / Orchestrators) ---
@app.route('/healthz')
def healthz():
    """Liveness probe: returns 200 if process is up."""
    return jsonify(status="ok", service="quiz-app"), 200

def _db_ping():
    """Attempt a fast DB ping; return (ok: bool, message: str)."""
    conn = None
    try:
        conn = get_db_connection()
        if not conn:
            return False, "connection_failed"
        cur = conn.cursor()
        cur.execute("SELECT 1")
        cur.fetchone()
        return True, "ok"
    except Exception as e:
        return False, str(e)[:120]
    finally:
        if conn:
            return_db_connection(conn)

@app.route('/readyz')
def readyz():
    """Readiness probe: checks DB connectivity."""
    ok, msg = _db_ping()
    code = 200 if ok else 503
    return jsonify(status="ok" if ok else "degraded", db=msg), code

# Initialize application
def create_app(config_name='development'):
    """Application factory pattern"""
    from config import config
    app.config.from_object(config[config_name])
    
    return app

if __name__ == '__main__':
    print("🚀 Starting Quiz Application...")
    print("📋 Redis dependency removed - using in-memory storage")
    
    # Initialize database in background to avoid blocking startup
    import threading
    def initialize_db():
        try:
            print("🔄 Initializing database...")
            init_database()
            print("✅ Database initialized successfully")
        except Exception as e:
            print(f"⚠️ Database initialization warning: {e}")
            print("ℹ️ App will use fallback connections")
    
    # Start database initialization in background
    db_thread = threading.Thread(target=initialize_db)
    db_thread.daemon = True
    db_thread.start()
    
    print("🌐 Starting Flask server on http://localhost:5000")
    
    try:
        # Run the application
        app.run(debug=True, host='0.0.0.0', port=5000, threaded=True)
    finally:
        # Clean up on shutdown
        pass
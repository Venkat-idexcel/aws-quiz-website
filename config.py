
# Production Configuration for Quiz Website
import os
import tempfile
from datetime import timedelta

class Config:
    """Base configuration"""
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-production-secret-key-change-this')
    
    # Database Configuration - AWS RDS PostgreSQL (Custom port configuration)
    DB_HOST = os.getenv('DB_HOST', 'los-dev-psql-rdsclstr-new.cj6duvm27hk9.us-east-1.rds.amazonaws.com')
    DB_PORT = int(os.getenv('DB_PORT', 3306))  # Custom PostgreSQL port (not standard 5432)
    DB_NAME = os.getenv('DB_NAME', 'cretificate_quiz_db')  # Keep existing database name
    DB_USER = os.getenv('DB_USER', 'postgres')
    DB_PASSWORD = os.getenv('DB_PASSWORD', 'poc2*&(SRWSjnjkn@#@#')
    
    # Redis Configuration
    REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    
    # Session Configuration - Using filesystem for EC2 deployment
    SESSION_TYPE = 'filesystem'
    SESSION_PERMANENT = False
    SESSION_USE_SIGNER = True
    SESSION_KEY_PREFIX = 'quiz_session:'
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    # Cross-platform session file dir (defaults to system temp directory)
    SESSION_FILE_DIR = os.getenv('SESSION_FILE_DIR', os.path.join(tempfile.gettempdir(), 'flask_sessions'))
    
    # Security - Disabled SECURE for HTTP deployment
    SESSION_COOKIE_SECURE = False  # Set to True only with HTTPS
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Rate Limiting
    RATELIMIT_STORAGE_URL = os.getenv('RATELIMIT_STORAGE_URL', os.getenv('REDIS_URL', 'redis://localhost:6379/1'))
    RATELIMIT_DEFAULT = os.getenv('RATELIMIT_DEFAULT', '1000 per hour;100 per minute')
    
    # Email Configuration
    EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
    EMAIL_PORT = int(os.getenv('EMAIL_PORT', 587))
    EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', 'your-email@gmail.com')
    EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', 'your-app-password')
    EMAIL_USE_TLS = True
    
    # OAuth Configuration
    GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')
    GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET')
    GITHUB_CLIENT_ID = os.getenv('GITHUB_CLIENT_ID')
    GITHUB_CLIENT_SECRET = os.getenv('GITHUB_CLIENT_SECRET')
    MICROSOFT_CLIENT_ID = os.getenv('MICROSOFT_CLIENT_ID')
    MICROSOFT_CLIENT_SECRET = os.getenv('MICROSOFT_CLIENT_SECRET')

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    SESSION_COOKIE_SECURE = False
    
class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    SESSION_COOKIE_SECURE = False  # Set to True when using HTTPS
    
    # Database Connection Pool Settings
    DB_POOL_MIN = int(os.getenv('DB_POOL_MIN', 2))
    DB_POOL_MAX = int(os.getenv('DB_POOL_MAX', 15))
    
    # Performance Settings
    SEND_FILE_MAX_AGE_DEFAULT = timedelta(hours=1)

class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    WTF_CSRF_ENABLED = False

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
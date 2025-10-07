#!/usr/bin/env python3
"""
WSGI entry point for production deployment on EC2
Usage: gunicorn -c gunicorn_config.py wsgi:app
"""

import os
import sys
from pathlib import Path

# Add the application directory to Python path
app_dir = Path(__file__).parent.absolute()
sys.path.insert(0, str(app_dir))

# Set production environment
os.environ.setdefault('FLASK_ENV', 'production')

try:
    from app import app
    
    # Production configuration
    app.config.update(
        DEBUG=False,
        TESTING=False,
        SECRET_KEY=os.environ.get('SECRET_KEY', 'your-production-secret-key-change-this-immediately'),
    )
    
    # Ensure proper logging for production
    if not app.debug:
        import logging
        from logging.handlers import RotatingFileHandler
        
        # Setup file logging if log directory exists
        log_file = '/var/log/aws-quiz-website.log'
        if os.path.exists(os.path.dirname(log_file)):
            file_handler = RotatingFileHandler(log_file, maxBytes=10240000, backupCount=10)
            file_handler.setFormatter(logging.Formatter(
                '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
            ))
            file_handler.setLevel(logging.INFO)
            app.logger.addHandler(file_handler)
            app.logger.setLevel(logging.INFO)
            app.logger.info('AWS Quiz Website startup')

except Exception as e:
    print(f"Error importing application: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# This is what Gunicorn will use
application = app

if __name__ == "__main__":
    # For development/testing only
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port, debug=False)

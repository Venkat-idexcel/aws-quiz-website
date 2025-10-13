#!/bin/bash
# Quick deployment script
# Run this after uploading files to /var/www/aws-quiz-app

echo "Starting deployment..."

# Go to app directory
cd /var/www/aws-quiz-app

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3.11 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install/upgrade dependencies
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn

# Create wsgi.py if it doesn't exist
if [ ! -f "wsgi.py" ]; then
    echo "Creating wsgi.py..."
    cat > wsgi.py << 'WSGI_EOF'
from app import app

if __name__ == "__main__":
    app.run()
WSGI_EOF
fi

# Create gunicorn_config.py if it doesn't exist
if [ ! -f "gunicorn_config.py" ]; then
    echo "Creating gunicorn_config.py..."
    cat > gunicorn_config.py << 'GUNICORN_EOF'
import multiprocessing

# Server socket
bind = "127.0.0.1:5000"
backlog = 2048

# Worker processes
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = 'sync'
worker_connections = 1000
timeout = 120
keepalive = 2

# Logging
accesslog = '-'
errorlog = '-'
loglevel = 'info'
GUNICORN_EOF
fi

echo ""
echo "✅ Application setup complete!"
echo ""
echo "To start the application:"
echo "  sudo systemctl start aws-quiz-app"
echo ""
echo "To check status:"
echo "  sudo systemctl status aws-quiz-app"
echo ""
echo "To view logs:"
echo "  sudo journalctl -u aws-quiz-app -f"

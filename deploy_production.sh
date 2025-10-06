#!/bin/bash

# Production Deployment Script for Quiz Website
# This script sets up the production environment with load balancing capabilities

set -e  # Exit on any error

echo "🚀 Starting Quiz Website Production Deployment..."

# Check if running as root
if [ "$EUID" -eq 0 ]; then 
    echo "❌ Please don't run this script as root"
    exit 1
fi

# Environment setup
export FLASK_ENV=production
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Create logs directory
mkdir -p logs

# Install system dependencies (uncomment if needed)
# sudo apt-get update
# sudo apt-get install -y redis-server nginx

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

# Start Redis (if not already running)
echo "🔧 Starting Redis server..."
redis-server --daemonize yes --port 6379 || echo "Redis may already be running"

# Database initialization
echo "🗄️ Initializing database..."
python -c "from app import init_database; init_database()"

# Start Gunicorn with multiple workers
echo "🌐 Starting Gunicorn with load balancing..."
gunicorn \
    --config gunicorn_config.py \
    --bind 0.0.0.0:8000 \
    --workers 4 \
    --worker-class gevent \
    --worker-connections 1000 \
    --max-requests 1000 \
    --max-requests-jitter 50 \
    --timeout 30 \
    --keepalive 60 \
    --preload \
    --access-logfile logs/access.log \
    --error-logfile logs/error.log \
    --log-level info \
    --pid /tmp/gunicorn.pid \
    --daemon \
    app:app

echo "✅ Quiz Website deployed successfully!"
echo "📊 Server running on: http://localhost:8000"
echo "📝 Logs available in: logs/ directory"
echo "🔍 Monitor with: tail -f logs/error.log"
echo ""
echo "🛑 To stop the server: kill \$(cat /tmp/gunicorn.pid)"
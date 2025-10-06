@echo off
echo 🚀 Starting Quiz Website Production Deployment...

REM Environment setup
set FLASK_ENV=production
set PYTHONPATH=%PYTHONPATH%;%CD%

REM Create logs directory
if not exist "logs" mkdir logs

REM Install Python dependencies
echo 📦 Installing Python dependencies...
pip install -r requirements.txt

REM Database initialization
echo 🗄️ Initializing database...
python -c "from app import init_database; init_database()"

REM Start the application with Gunicorn
echo 🌐 Starting Gunicorn with load balancing...
gunicorn ^
    --config gunicorn_config.py ^
    --bind 0.0.0.0:8000 ^
    --workers 4 ^
    --worker-class gevent ^
    --worker-connections 1000 ^
    --max-requests 1000 ^
    --max-requests-jitter 50 ^
    --timeout 30 ^
    --keepalive 60 ^
    --preload ^
    --access-logfile logs/access.log ^
    --error-logfile logs/error.log ^
    --log-level info ^
    app:app

echo ✅ Quiz Website deployed successfully!
echo 📊 Server running on: http://localhost:8000
echo 📝 Logs available in: logs/ directory

pause
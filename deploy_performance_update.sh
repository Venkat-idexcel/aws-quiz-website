#!/bin/bash

# Performance Optimization Deployment Script
# Run this on your EC2 instance after updating the code

set -e  # Exit on any error

echo "🚀 Deploying Performance Optimizations..."
echo "=========================================="

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Navigate to app directory
APP_DIR="/home/ec2-user/aws-quiz-website"  # Change if using Ubuntu: /home/ubuntu/aws-quiz-website
cd $APP_DIR || { echo "Error: Cannot find app directory"; exit 1; }

# Pull latest changes from git
echo -e "${YELLOW}📥 Pulling latest code...${NC}"
git pull origin main || echo "Warning: Git pull failed or no changes"

# Activate virtual environment
echo -e "${YELLOW}🔧 Activating virtual environment...${NC}"
source venv/bin/activate

# Ensure dependencies are installed
echo -e "${YELLOW}📦 Checking dependencies...${NC}"
pip install -q psycopg2-binary gevent gunicorn

# Set environment variables for optimal performance
echo -e "${YELLOW}⚙️  Setting performance environment variables...${NC}"
export DB_POOL_MIN=5
export DB_POOL_MAX=50
export GUNICORN_WORKER_CONNECTIONS=1000
export GUNICORN_TIMEOUT=60
export GUNICORN_MAX_REQUESTS=10000
export LOG_LEVEL=INFO

# Check if using supervisor or systemd
if command -v supervisorctl &> /dev/null; then
    echo -e "${YELLOW}🔄 Restarting via Supervisor...${NC}"
    sudo supervisorctl restart quiz-app
    sleep 2
    sudo supervisorctl status quiz-app
elif systemctl is-active --quiet quiz-app; then
    echo -e "${YELLOW}🔄 Restarting via Systemd...${NC}"
    sudo systemctl restart quiz-app
    sleep 2
    sudo systemctl status quiz-app
else
    echo -e "${YELLOW}⚠️  No service manager found. Starting manually...${NC}"
    pkill gunicorn || true
    sleep 1
    gunicorn -c gunicorn_config.py app:app --daemon
fi

# Restart Nginx
echo -e "${YELLOW}🌐 Restarting Nginx...${NC}"
sudo systemctl restart nginx

# Check status
echo ""
echo -e "${GREEN}✅ Deployment Complete!${NC}"
echo "=========================================="

# Show worker count
WORKER_COUNT=$(ps aux | grep gunicorn | grep -v grep | wc -l)
echo -e "${GREEN}Active Gunicorn workers: $((WORKER_COUNT - 1))${NC}"

# Show database connections
echo ""
echo -e "${YELLOW}Checking database connections...${NC}"
python3 << EOF
import psycopg2
try:
    conn = psycopg2.connect(
        host='los-dev-psql-rdsclstr-new.cj6duvm27hk9.us-east-1.rds.amazonaws.com',
        port=3306,
        database='cretificate_quiz_db',
        user='postgres',
        password='poc2*&(SRWSjnjkn@#@#',
        connect_timeout=5
    )
    cur = conn.cursor()
    cur.execute("SELECT count(*) FROM pg_stat_activity WHERE datname='cretificate_quiz_db'")
    count = cur.fetchone()[0]
    print(f"✅ Database connected! Active connections: {count}")
    conn.close()
except Exception as e:
    print(f"❌ Database connection error: {e}")
EOF

echo ""
echo -e "${GREEN}🎉 Application is optimized and running!${NC}"
echo ""
echo "📊 Performance Monitoring:"
echo "  - Check logs: sudo tail -f /var/log/supervisor/quiz-app-stdout.log"
echo "  - Check errors: sudo tail -f /var/log/supervisor/quiz-app-stderr.log"
echo "  - Check nginx: sudo tail -f /var/log/nginx/access.log"
echo "  - Check workers: ps aux | grep gunicorn"
echo ""
echo "🔍 Performance Metrics:"
CPU_CORES=$(nproc)
echo "  - CPU Cores: $CPU_CORES"
echo "  - Recommended Workers: $((CPU_CORES * 2 + 1))"
echo "  - Max Concurrent Users: $((((CPU_CORES * 2 + 1) - 1) * 1000))"
echo ""

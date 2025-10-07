#!/bin/bash

# AWS Quiz Website EC2 Deployment Script
# This script automates the deployment process on EC2 instances

set -e  # Exit on any error

echo "🚀 Starting AWS Quiz Website EC2 Deployment..."

# Detect OS and set variables
if [ -f /etc/amazon-linux-release ] || [ -f /etc/system-release ]; then
    OS="amazon"
    PKG_MANAGER="yum"
    WEB_USER="ec2-user"
    HOME_DIR="/home/ec2-user"
    NGINX_CONF_DIR="/etc/nginx/conf.d"
elif [ -f /etc/lsb-release ] || [ -f /etc/debian_version ]; then
    OS="ubuntu"
    PKG_MANAGER="apt"
    WEB_USER="ubuntu" 
    HOME_DIR="/home/ubuntu"
    NGINX_CONF_DIR="/etc/nginx/sites-available"
else
    echo "❌ Unsupported OS. This script supports Amazon Linux and Ubuntu."
    exit 1
fi

echo "📋 Detected OS: $OS"
echo "👤 Web user: $WEB_USER"

# Check if running as correct user
if [ "$USER" != "$WEB_USER" ]; then
    echo "❌ Please run this script as $WEB_USER user"
    echo "   Example: sudo su - $WEB_USER"
    exit 1
fi

# Function to install packages
install_packages() {
    echo "📦 Installing required packages..."
    
    if [ "$OS" = "amazon" ]; then
        sudo yum update -y
        sudo yum groupinstall -y "Development Tools"
        sudo yum install -y python3 python3-pip python3-devel postgresql postgresql-server postgresql-devel nginx supervisor git
        
        # Initialize PostgreSQL for Amazon Linux
        if [ ! -f /var/lib/pgsql/data/postgresql.conf ]; then
            echo "🔧 Initializing PostgreSQL database..."
            sudo postgresql-setup initdb
            sudo systemctl start postgresql
            sudo systemctl enable postgresql
        fi
    else
        sudo apt update && sudo apt upgrade -y
        sudo apt install -y python3 python3-pip python3-dev python3-venv libpq-dev postgresql postgresql-contrib nginx supervisor git build-essential
        
        # Start PostgreSQL for Ubuntu
        sudo systemctl start postgresql
        sudo systemctl enable postgresql
    fi
}

# Function to setup application
setup_application() {
    echo "🏗️ Setting up application..."
    
    # Navigate to home directory
    cd $HOME_DIR
    
    # Create virtual environment
    if [ ! -d "aws-quiz-website/venv" ]; then
        cd aws-quiz-website
        python3 -m venv venv
        source venv/bin/activate
        
        # Upgrade pip
        pip install --upgrade pip
        
        # Install requirements
        pip install -r requirements.txt
        pip install gunicorn psycopg2-binary
        
        echo "✅ Virtual environment created and packages installed"
    else
        echo "✅ Virtual environment already exists"
        cd aws-quiz-website
        source venv/bin/activate
    fi
}

# Function to create production config
create_production_config() {
    echo "⚙️ Creating production configuration..."
    
    cat > config_production.py << 'EOF'
import os

class Config:
    # Database Configuration - Local PostgreSQL
    DB_HOST = 'localhost'
    DB_PORT = '5432'
    DB_USER = 'postgres'
    DB_PASSWORD = 'postgres'
    DB_NAME = 'aws_quiz_db'
    
    # Flask Configuration
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-super-secret-production-key-change-this-in-production'
    
    # Production settings
    DEBUG = False
    TESTING = False
    
    # Rate limiting (using memory storage for simplicity)
    RATELIMIT_STORAGE_URL = 'memory://'
    
    # Application settings
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 3600
    
    # Session settings
    PERMANENT_SESSION_LIFETIME = 7200  # 2 hours
    SESSION_COOKIE_SECURE = False  # Set to True when using HTTPS
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'

# Use this config for production
config = Config()
EOF

    echo "✅ Production configuration created"
}

# Function to setup local PostgreSQL database
setup_local_database() {
    echo "🗄️ Setting up local PostgreSQL database..."
    
    # Set password for postgres user
    sudo -u postgres psql -c "ALTER USER postgres PASSWORD 'postgres';"
    
    # Create database
    sudo -u postgres createdb aws_quiz_db 2>/dev/null || echo "Database aws_quiz_db already exists"
    
    # Configure PostgreSQL to accept local connections
    PG_VERSION=$(sudo -u postgres psql -t -c "SELECT version();" | grep -oP '\d+\.\d+' | head -1)
    
    if [ "$OS" = "amazon" ]; then
        PG_CONFIG_DIR="/var/lib/pgsql/data"
    else
        PG_CONFIG_DIR="/etc/postgresql/$PG_VERSION/main"
    fi
    
    # Update pg_hba.conf for local connections
    echo "🔧 Configuring PostgreSQL authentication..."
    sudo sed -i "s/#listen_addresses = 'localhost'/listen_addresses = 'localhost'/" $PG_CONFIG_DIR/postgresql.conf 2>/dev/null || true
    
    # Restart PostgreSQL
    sudo systemctl restart postgresql
    
    echo "✅ PostgreSQL setup complete"
}

# Function to test database connection
test_database_connection() {
    echo "🔍 Testing database connection..."
    
    python3 -c "
import psycopg2
try:
    conn = psycopg2.connect(
        host='localhost',
        port='5432',
        user='postgres',
        password='postgres',
        database='aws_quiz_db'
    )
    print('✅ Database connection successful!')
    
    # Test basic query
    cur = conn.cursor()
    cur.execute('SELECT version();')
    version = cur.fetchone()
    print(f'PostgreSQL version: {version[0][:50]}...')
    conn.close()
except Exception as e:
    print(f'❌ Database connection failed: {e}')
    print('❓ Make sure PostgreSQL is running and configured properly')
    exit(1)
"
}

# Function to setup gunicorn config
setup_gunicorn() {
    echo "🦄 Setting up Gunicorn configuration..."
    
    cat > gunicorn_config.py << 'EOF'
# Gunicorn configuration for AWS Quiz Website
import multiprocessing

# Bind to localhost on port 8000
bind = "127.0.0.1:8000"

# Number of worker processes (CPU cores * 2 + 1)
workers = multiprocessing.cpu_count() * 2 + 1

# Worker class
worker_class = "sync"

# Maximum number of simultaneous clients
worker_connections = 1000

# Restart workers after this many requests (prevents memory leaks)
max_requests = 1000
max_requests_jitter = 100

# Worker timeout
timeout = 30

# Keep-alive connections
keepalive = 2

# Preload the application
preload_app = True

# Logging
accesslog = '/var/log/gunicorn-access.log'
errorlog = '/var/log/gunicorn-error.log'
loglevel = 'info'

# Process naming
proc_name = 'aws-quiz-website'

# Daemon mode
daemon = False

# User and group
user = None
group = None
EOF

    echo "✅ Gunicorn configuration created"
}

# Function to setup nginx
setup_nginx() {
    echo "🌐 Setting up Nginx configuration..."
    
    # Get EC2 public IP
    PUBLIC_IP=$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4 2>/dev/null || echo "localhost")
    
    # Create nginx config
    sudo tee $NGINX_CONF_DIR/aws-quiz-website.conf > /dev/null << EOF
server {
    listen 80;
    server_name $PUBLIC_IP localhost;

    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";

    # Main application
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # Timeouts
        proxy_connect_timeout 30s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;
        
        # Buffer settings
        proxy_buffering on;
        proxy_buffer_size 128k;
        proxy_buffers 4 256k;
        proxy_busy_buffers_size 256k;
    }

    # Static files
    location /static/ {
        alias $HOME_DIR/aws-quiz-website/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
        
        # Security for static files
        location ~* \.(py|pyc|pyo|pyw|pyz)$ {
            deny all;
        }
    }

    # Favicon
    location /favicon.ico {
        alias $HOME_DIR/aws-quiz-website/static/img/favicon.ico;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Health check
    location /health {
        access_log off;
        return 200 "healthy\\n";
        add_header Content-Type text/plain;
    }

    # Deny access to sensitive files
    location ~ /\\. {
        deny all;
    }
    
    location ~ \\.(py|pyc|pyo|pyw|pyz|db|sqlite)$ {
        deny all;
    }

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types
        text/plain
        text/css
        text/xml
        text/javascript
        application/json
        application/javascript
        application/xml+rss
        application/atom+xml
        image/svg+xml;
}
EOF

    # Enable site for Ubuntu
    if [ "$OS" = "ubuntu" ]; then
        sudo ln -sf $NGINX_CONF_DIR/aws-quiz-website.conf /etc/nginx/sites-enabled/
        sudo rm -f /etc/nginx/sites-enabled/default
    fi

    # Test nginx configuration
    sudo nginx -t
    
    echo "✅ Nginx configuration created for IP: $PUBLIC_IP"
}

# Function to setup supervisor
setup_supervisor() {
    echo "👨‍💼 Setting up Supervisor configuration..."
    
    sudo tee /etc/supervisor/conf.d/aws-quiz-website.conf > /dev/null << EOF
[program:aws-quiz-website]
command=$HOME_DIR/aws-quiz-website/venv/bin/gunicorn -c gunicorn_config.py wsgi:app
directory=$HOME_DIR/aws-quiz-website
user=$WEB_USER
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/aws-quiz-website.log
stdout_logfile_maxbytes=50MB
stdout_logfile_backups=5
stderr_logfile=/var/log/aws-quiz-website-error.log
stderr_logfile_maxbytes=50MB
stderr_logfile_backups=5
environment=PATH="$HOME_DIR/aws-quiz-website/venv/bin"

[group:aws-quiz]
programs=aws-quiz-website
EOF

    echo "✅ Supervisor configuration created"
}

# Function to create log files
setup_logging() {
    echo "📝 Setting up logging..."
    
    # Create log files with proper permissions
    sudo touch /var/log/aws-quiz-website.log
    sudo touch /var/log/aws-quiz-website-error.log
    sudo touch /var/log/gunicorn-access.log
    sudo touch /var/log/gunicorn-error.log
    
    sudo chown $WEB_USER:$WEB_USER /var/log/aws-quiz-website*.log
    sudo chown $WEB_USER:$WEB_USER /var/log/gunicorn*.log
    
    echo "✅ Log files created"
}

# Function to start services
start_services() {
    echo "🚀 Starting services..."
    
    # Reload supervisor configuration
    sudo supervisorctl reread
    sudo supervisorctl update
    
    # Start the application
    sudo supervisorctl restart aws-quiz-website
    
    # Start nginx
    sudo systemctl restart nginx
    sudo systemctl enable nginx
    
    # Enable supervisor
    if [ "$OS" = "ubuntu" ]; then
        sudo systemctl enable supervisor
        sudo systemctl start supervisor
    else
        sudo chkconfig supervisord on
        sudo service supervisord start
    fi
    
    echo "✅ Services started"
}

# Function to show status
show_status() {
    echo "📊 Checking service status..."
    
    echo "=== Application Status ==="
    sudo supervisorctl status aws-quiz-website
    
    echo "=== Nginx Status ==="
    sudo systemctl status nginx --no-pager -l
    
    echo "=== Application Logs (last 10 lines) ==="
    sudo tail -n 10 /var/log/aws-quiz-website.log
    
    # Get public IP for access instructions
    PUBLIC_IP=$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4 2>/dev/null || echo "localhost")
    
    echo ""
    echo "🎉 Deployment Complete!"
    echo "========================================"
    echo "✅ Your AWS Quiz Website is now running!"
    echo "🌐 Access URL: http://$PUBLIC_IP"
    echo "📝 Application logs: /var/log/aws-quiz-website.log"
    echo "🔧 Manage app: sudo supervisorctl status aws-quiz-website"
    echo "🔄 Restart app: sudo supervisorctl restart aws-quiz-website"
    echo "🛑 Stop app: sudo supervisorctl stop aws-quiz-website"
    echo ""
    echo "📋 Useful commands:"
    echo "   - Check logs: sudo tail -f /var/log/aws-quiz-website.log"
    echo "   - Check nginx: sudo systemctl status nginx"
    echo "   - Restart nginx: sudo systemctl restart nginx"
    echo ""
}

# Main deployment function
main() {
    echo "Starting deployment process..."
    
    # Check if we're in the right directory
    if [ ! -f "app.py" ]; then
        echo "❌ app.py not found. Please run this script from the aws-quiz-website directory."
        exit 1
    fi
    
    # Install packages
    install_packages
    
    # Setup PostgreSQL database
    setup_local_database
    
    # Setup application
    setup_application
    
    # Create configurations
    create_production_config
    setup_gunicorn
    
    # Test database
    test_database_connection
    
    # Setup services
    setup_nginx
    setup_supervisor
    setup_logging
    
    # Start everything
    start_services
    
    # Show status
    show_status
}

# Run main function
main "$@"
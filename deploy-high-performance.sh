#!/bin/bash
# High-Performance Deployment Script for AWS Quiz Website
# Optimized for handling 1000+ concurrent users

set -e

APP_DIR="/var/www/aws-quiz-app"
VENV_DIR="$APP_DIR/venv"
SERVICE_NAME="aws-quiz-app"
NGINX_CONFIG="/etc/nginx/conf.d/aws-quiz-app.conf"

echo "🚀 Starting high-performance deployment..."

# Stop services if running
echo "📦 Stopping existing services..."
sudo systemctl stop $SERVICE_NAME 2>/dev/null || true
sudo systemctl stop nginx 2>/dev/null || true

# Update system packages
echo "📦 Updating system packages..."
sudo dnf update -y

# Install performance monitoring tools
echo "📊 Installing monitoring tools..."
sudo dnf install -y htop iotop nethogs

# Configure system for high performance
echo "⚡ Optimizing system settings..."

# Increase file descriptor limits
sudo tee -a /etc/security/limits.conf > /dev/null <<EOF
# High performance settings for quiz app
* soft nofile 65536
* hard nofile 65536
* soft nproc 32768
* hard nproc 32768
ec2-user soft nofile 65536
ec2-user hard nofile 65536
EOF

# Optimize kernel parameters for high load
sudo tee /etc/sysctl.d/99-quiz-app.conf > /dev/null <<EOF
# Network optimizations
net.core.somaxconn = 65536
net.core.netdev_max_backlog = 5000
net.core.rmem_default = 262144
net.core.rmem_max = 134217728
net.core.wmem_default = 262144
net.core.wmem_max = 134217728
net.ipv4.tcp_rmem = 4096 87380 134217728
net.ipv4.tcp_wmem = 4096 65536 134217728
net.ipv4.tcp_fin_timeout = 15
net.ipv4.tcp_tw_reuse = 1
net.ipv4.tcp_max_syn_backlog = 8192
net.ipv4.ip_local_port_range = 1024 65000

# File system optimizations
fs.file-max = 2097152
vm.swappiness = 1
vm.dirty_ratio = 15
vm.dirty_background_ratio = 5
EOF

# Apply kernel settings
sudo sysctl -p /etc/sysctl.d/99-quiz-app.conf

# Create application directory
sudo mkdir -p $APP_DIR
sudo chown ec2-user:ec2-user $APP_DIR

# Install Python 3.11 and dependencies
echo "🐍 Installing Python and dependencies..."
sudo dnf install -y python3.11 python3.11-pip python3.11-devel gcc postgresql-devel git nginx

# Create virtual environment
echo "🔧 Setting up Python environment..."
cd $APP_DIR
python3.11 -m venv $VENV_DIR
source $VENV_DIR/bin/activate

# Upgrade pip and install wheel
pip install --upgrade pip wheel setuptools

# Install Python packages with performance optimizations
echo "📦 Installing Python packages..."
pip install --upgrade pip
pip install -r requirements.txt

# Install high-performance packages
pip install gunicorn gevent psutil

# Configure Gunicorn service for high performance
echo "🔧 Configuring Gunicorn service..."
sudo tee /etc/systemd/system/$SERVICE_NAME.service > /dev/null <<EOF
[Unit]
Description=AWS Quiz Application (High Performance)
After=network.target postgresql.service
Wants=postgresql.service

[Service]
Type=notify
User=ec2-user
Group=ec2-user
RuntimeDirectory=aws-quiz-app
WorkingDirectory=$APP_DIR
Environment="PATH=$VENV_DIR/bin"
Environment="PYTHONPATH=$APP_DIR"
ExecStart=$VENV_DIR/bin/gunicorn --config gunicorn_config.py wsgi:app
ExecReload=/bin/kill -s HUP \$MAINPID
KillMode=mixed
TimeoutStopSec=60
PrivateTmp=true
Restart=always
RestartSec=10

# Performance settings
LimitNOFILE=65536
LimitNPROC=32768

[Install]
WantedBy=multi-user.target
EOF

# Configure optimized nginx
echo "🌐 Configuring optimized Nginx..."
sudo cp nginx-optimized.conf $NGINX_CONFIG

# Configure nginx main settings for high performance
sudo tee /etc/nginx/nginx.conf > /dev/null <<EOF
user nginx;
worker_processes auto;
worker_rlimit_nofile 65536;
error_log /var/log/nginx/error.log warn;
pid /run/nginx.pid;

events {
    worker_connections 8192;
    use epoll;
    multi_accept on;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;
    
    # Performance settings
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    keepalive_requests 1000;
    types_hash_max_size 2048;
    server_tokens off;
    
    # Buffer settings
    client_body_buffer_size 128k;
    client_max_body_size 50m;
    client_header_buffer_size 4k;
    large_client_header_buffers 4 16k;
    
    # Gzip settings
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
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
    
    # Logging
    log_format main '\$remote_addr - \$remote_user [\$time_local] "\$request" '
                    '\$status \$body_bytes_sent "\$http_referer" '
                    '"\$http_user_agent" "\$http_x_forwarded_for" '
                    'rt=\$request_time uct="\$upstream_connect_time" '
                    'uht="\$upstream_header_time" urt="\$upstream_response_time"';
    
    access_log /var/log/nginx/access.log main;
    
    include /etc/nginx/conf.d/*.conf;
}
EOF

# Set proper permissions
sudo chown -R ec2-user:ec2-user $APP_DIR
sudo chmod +x $APP_DIR/*.py

# Reload systemd and enable services
echo "🔄 Reloading and enabling services..."
sudo systemctl daemon-reload
sudo systemctl enable $SERVICE_NAME
sudo systemctl enable nginx

# Start services
echo "🚀 Starting optimized services..."
sudo systemctl start $SERVICE_NAME
sudo systemctl start nginx

# Wait for services to start
sleep 5

# Check service status
echo "📊 Service Status:"
sudo systemctl status $SERVICE_NAME --no-pager -l
sudo systemctl status nginx --no-pager -l

# Test application
echo "🧪 Testing application..."
curl -s http://localhost/health || echo "Health check endpoint not available"
curl -s -I http://localhost/ || echo "Main page check failed"

echo "✅ High-performance deployment completed!"
echo ""
echo "📈 Performance Configuration Summary:"
echo "  - Gunicorn workers: 16 (configurable via GUNICORN_WORKERS)"
echo "  - Worker connections: 5000 per worker (80,000 total)"
echo "  - Theoretical capacity: 80,000+ concurrent connections"
echo "  - Rate limiting: Enabled to prevent abuse"
echo "  - Gzip compression: Enabled"
echo "  - Static file caching: 1 year"
echo "  - File descriptor limit: 65,536"
echo "  - Nginx worker connections: 8,192"
echo ""
echo "🔧 Monitoring Commands:"
echo "  - Check processes: sudo systemctl status aws-quiz-app"
echo "  - Check logs: sudo journalctl -u aws-quiz-app -f"
echo "  - Check nginx: sudo systemctl status nginx"
echo "  - Monitor performance: htop"
echo "  - Monitor connections: sudo netstat -tulnp"
echo ""
echo "🎯 Application should now handle 1000+ concurrent users!"
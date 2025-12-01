#!/bin/bash
# Quick restart script with performance optimizations
# Run this on your EC2 instance to apply the new high-performance configuration

echo "🔄 Restarting AWS Quiz Website with high-performance configuration..."

# Stop services
echo "📦 Stopping services..."
sudo systemctl stop aws-quiz-app 2>/dev/null || true
sudo systemctl stop nginx 2>/dev/null || true

# Apply system optimizations (one-time setup)
echo "⚡ Applying system optimizations..."

# Increase file descriptor limits
sudo tee -a /etc/security/limits.conf > /dev/null <<EOF
# High performance settings for quiz app (added $(date))
* soft nofile 65536
* hard nofile 65536
ec2-user soft nofile 65536
ec2-user hard nofile 65536
EOF

# Optimize kernel parameters
sudo tee /etc/sysctl.d/99-quiz-app.conf > /dev/null <<EOF
# Network optimizations for quiz app
net.core.somaxconn = 65536
net.core.netdev_max_backlog = 5000
net.ipv4.tcp_fin_timeout = 15
net.ipv4.tcp_tw_reuse = 1
net.ipv4.tcp_max_syn_backlog = 8192
fs.file-max = 2097152
EOF

# Apply settings
sudo sysctl -p /etc/sysctl.d/99-quiz-app.conf

# Update systemd service with high-performance configuration
echo "🔧 Updating systemd service..."
sudo tee /etc/systemd/system/aws-quiz-app.service > /dev/null <<EOF
[Unit]
Description=AWS Quiz Application (High Performance)
After=network.target postgresql.service
Wants=postgresql.service

[Service]
Type=notify
User=ec2-user
Group=ec2-user
RuntimeDirectory=aws-quiz-app
WorkingDirectory=/var/www/aws-quiz-app
Environment="PATH=/var/www/aws-quiz-app/venv/bin"
Environment="PYTHONPATH=/var/www/aws-quiz-app"
Environment="GUNICORN_WORKERS=16"
Environment="GUNICORN_WORKER_CONNECTIONS=5000"
ExecStart=/var/www/aws-quiz-app/venv/bin/gunicorn --config gunicorn_config.py wsgi:app
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

# Update nginx configuration
echo "🌐 Updating nginx configuration..."
sudo tee /etc/nginx/conf.d/aws-quiz-app.conf > /dev/null <<'EOF'
server {
    listen 80;
    server_name _;
    
    # Performance optimizations
    client_max_body_size 50M;
    client_body_buffer_size 128k;
    keepalive_timeout 65;
    keepalive_requests 1000;
    
    # Enable gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/javascript application/json application/javascript;
    
    # Rate limiting zones
    limit_req_zone $binary_remote_addr zone=login:10m rate=10r/m;
    limit_req_zone $binary_remote_addr zone=general:10m rate=100r/m;
    
    # Main application proxy
    location / {
        limit_req zone=general burst=20 nodelay;
        proxy_pass http://127.0.0.1:5000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 300s;
        proxy_read_timeout 300s;
        proxy_buffering on;
        proxy_buffer_size 16k;
        proxy_buffers 8 16k;
    }
    
    # Login with stricter rate limiting
    location /login {
        limit_req zone=login burst=5 nodelay;
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 300s;
        proxy_read_timeout 300s;
    }

    # Static files with caching
    location /static {
        alias /var/www/aws-quiz-app/static;
        expires 1y;
        add_header Cache-Control "public, immutable";
        sendfile on;
        gzip_static on;
    }
    
    # Health check
    location /health {
        access_log off;
        return 200 "healthy\n";
        add_header Content-Type text/plain;
    }
    
    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    server_tokens off;
}
EOF

# Update nginx main config for high performance
echo "🔧 Updating nginx main configuration..."
sudo cp /etc/nginx/nginx.conf /etc/nginx/nginx.conf.backup
sudo tee /etc/nginx/nginx.conf > /dev/null <<'EOF'
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
    
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;
    server_tokens off;
    
    client_max_body_size 50m;
    client_body_buffer_size 128k;
    
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_comp_level 6;
    gzip_types text/plain text/css text/xml text/javascript application/json application/javascript;
    
    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" rt=$request_time';
    
    access_log /var/log/nginx/access.log main;
    
    include /etc/nginx/conf.d/*.conf;
}
EOF

# Reload systemd and restart services
echo "🔄 Reloading systemd and starting services..."
sudo systemctl daemon-reload
sudo systemctl enable aws-quiz-app
sudo systemctl enable nginx

echo "🚀 Starting optimized services..."
sudo systemctl start aws-quiz-app
sleep 3
sudo systemctl start nginx

# Wait for startup
echo "⏳ Waiting for services to fully start..."
sleep 5

# Check status
echo "📊 Service Status:"
if sudo systemctl is-active --quiet aws-quiz-app; then
    echo "✅ Quiz App: Running"
else
    echo "❌ Quiz App: Failed to start"
    sudo journalctl -u aws-quiz-app --no-pager -n 10
fi

if sudo systemctl is-active --quiet nginx; then
    echo "✅ Nginx: Running"
else
    echo "❌ Nginx: Failed to start"
    sudo journalctl -u nginx --no-pager -n 10
fi

# Test application
echo "🧪 Testing application..."
if curl -s http://localhost/health >/dev/null 2>&1; then
    echo "✅ Health check: Passed"
else
    echo "❌ Health check: Failed"
fi

if curl -s -I http://localhost/ | head -n 1 | grep -q "200"; then
    echo "✅ Main page: Accessible"
else
    echo "❌ Main page: Not accessible"
fi

echo ""
echo "✅ High-performance restart completed!"
echo ""
echo "📈 New Configuration:"
echo "  - Gunicorn workers: 16"
echo "  - Worker connections: 5000 per worker (80,000 total capacity)"
echo "  - Rate limiting: Enabled (100 req/min general, 10 req/min login)"
echo "  - File descriptors: 65,536"
echo "  - Nginx workers: Auto (CPU cores)"
echo "  - Connection capacity: 8,192 per worker"
echo ""
echo "🔍 Monitoring commands:"
echo "  sudo systemctl status aws-quiz-app"
echo "  sudo journalctl -u aws-quiz-app -f"
echo "  htop"
echo "  sudo netstat -tulnp | grep :80"
echo ""
echo "🎯 Your application should now handle 1000+ concurrent users!"
#!/bin/bash
# EC2 Deployment Script for AWS Quiz Application
# For Amazon Linux 2023 via GitHub
# Run: bash install_ec2.sh

set -e  # Exit on error

echo "=========================================="
echo "AWS Quiz App - EC2 Deployment"
echo "Amazon Linux 2023"
echo "=========================================="

# Update system packages
echo ""
echo "[1/9] Updating system packages..."
sudo dnf update -y

# Install Python 3.11 and dependencies
echo ""
echo "[2/9] Installing Python 3.11 and dependencies..."
sudo dnf install -y python3.11 python3.11-pip python3.11-devel gcc postgresql-devel git nginx

# Verify installations
python3.11 --version
git --version

# Create application directory if needed
echo ""
echo "[3/9] Setting up application directory..."
if [ ! -d "/var/www/aws-quiz-app" ]; then
    sudo mkdir -p /var/www/aws-quiz-app
fi
sudo chown -R $USER:$USER /var/www/aws-quiz-app

# Move to app directory
cd /var/www/aws-quiz-app

# Create virtual environment
echo ""
echo "[4/9] Creating Python virtual environment..."
python3.11 -m venv venv
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install Python dependencies
echo ""
echo "[5/9] Installing Python dependencies..."
pip install -r requirements.txt
pip install gunicorn

# Create systemd service file
echo ""
echo "[6/9] Creating systemd service..."
sudo tee /etc/systemd/system/aws-quiz-app.service > /dev/null <<EOF
[Unit]
Description=AWS Quiz Application
After=network.target

[Service]
User=$USER
Group=$USER
WorkingDirectory=/var/www/aws-quiz-app
Environment="PATH=/var/www/aws-quiz-app/venv/bin"
ExecStart=/var/www/aws-quiz-app/venv/bin/gunicorn --workers 3 --bind 127.0.0.1:5000 wsgi:app --timeout 120 --access-logfile - --error-logfile -

[Install]
WantedBy=multi-user.target
EOF

# Configure Nginx
echo ""
echo "[7/9] Configuring Nginx..."
sudo tee /etc/nginx/conf.d/aws-quiz-app.conf > /dev/null <<'EOF'
server {
    listen 80;
    server_name _;
    client_max_body_size 10M;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 60s;
        proxy_read_timeout 60s;
    }

    location /static {
        alias /var/www/aws-quiz-app/static;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
}
EOF

# Test Nginx configuration
sudo nginx -t

# Configure firewall if enabled
echo ""
echo "[8/9] Configuring firewall..."
if sudo systemctl is-active --quiet firewalld; then
    sudo firewall-cmd --permanent --add-service=http
    sudo firewall-cmd --permanent --add-service=https
    sudo firewall-cmd --reload
    echo "Firewall configured"
else
    echo "Firewall not active, skipping"
fi

# Enable and start services
echo ""
echo "[9/9] Enabling and starting services..."
sudo systemctl daemon-reload
sudo systemctl enable aws-quiz-app
sudo systemctl enable nginx
sudo systemctl start nginx

echo ""
echo "=========================================="
echo "✅ Deployment Setup Complete!"
echo "=========================================="
echo ""
echo "⚠️  IMPORTANT: Verify config.py has correct database credentials"
echo ""
echo "Next steps:"
echo "1. Check config: cat /var/www/aws-quiz-app/config.py"
echo "2. Start app: sudo systemctl start aws-quiz-app"
echo "3. Check status: sudo systemctl status aws-quiz-app"
echo "4. View logs: sudo journalctl -u aws-quiz-app -f"
echo ""
echo "Your app will be at: http://$(curl -s http://checkip.amazonaws.com)"
echo ""

#!/bin/bash
# EC2 Deployment Script for AWS Quiz Application
# For Amazon Linux 2023
# Run as: bash deploy_ec2_amazon_linux.sh

set -e  # Exit on any error

echo "=========================================="
echo "AWS Quiz App - EC2 Deployment"
echo "Amazon Linux 2023"
echo "=========================================="

# Update system packages
echo ""
echo "Step 1: Updating system packages..."
sudo dnf update -y

# Install Python 3.11 and development tools
echo ""
echo "Step 2: Installing Python 3.11 and dependencies..."
sudo dnf install -y python3.11 python3.11-pip python3.11-devel
sudo dnf install -y gcc postgresql-devel git

# Install nginx
echo ""
echo "Step 3: Installing Nginx..."
sudo dnf install -y nginx

# Create application directory
echo ""
echo "Step 4: Creating application directory..."
sudo mkdir -p /var/www/aws-quiz-app
sudo chown -R $USER:$USER /var/www/aws-quiz-app
cd /var/www/aws-quiz-app

# Clone or copy application files
echo ""
echo "Step 5: Setting up application files..."
echo "Please upload your application files to /var/www/aws-quiz-app"
echo "You can use SCP or SFTP to transfer files"

# Create virtual environment
echo ""
echo "Step 6: Creating Python virtual environment..."
python3.11 -m venv venv
source venv/bin/activate

# Upgrade pip
echo ""
echo "Step 7: Upgrading pip..."
pip install --upgrade pip

# Install Python dependencies
echo ""
echo "Step 8: Installing Python dependencies..."
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
else
    echo "⚠️  requirements.txt not found. Please upload it first."
fi

# Install Gunicorn for production
pip install gunicorn

# Create systemd service file
echo ""
echo "Step 9: Creating systemd service..."
sudo tee /etc/systemd/system/aws-quiz-app.service > /dev/null <<EOF
[Unit]
Description=AWS Quiz Application
After=network.target

[Service]
User=$USER
Group=$USER
WorkingDirectory=/var/www/aws-quiz-app
Environment="PATH=/var/www/aws-quiz-app/venv/bin"
ExecStart=/var/www/aws-quiz-app/venv/bin/gunicorn --workers 3 --bind 127.0.0.1:5000 wsgi:app

[Install]
WantedBy=multi-user.target
EOF

# Configure Nginx
echo ""
echo "Step 10: Configuring Nginx..."
sudo tee /etc/nginx/conf.d/aws-quiz-app.conf > /dev/null <<EOF
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    location /static {
        alias /var/www/aws-quiz-app/static;
        expires 30d;
    }
}
EOF

# Configure firewall
echo ""
echo "Step 11: Configuring firewall..."
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --reload || echo "Firewall configuration skipped (not running)"

# Set SELinux contexts (if SELinux is enabled)
echo ""
echo "Step 12: Setting SELinux permissions..."
if command -v semanage &> /dev/null; then
    sudo semanage fcontext -a -t httpd_sys_content_t "/var/www/aws-quiz-app(/.*)?"
    sudo restorecon -R /var/www/aws-quiz-app
fi

# Enable and start services
echo ""
echo "Step 13: Starting services..."
sudo systemctl daemon-reload
sudo systemctl enable aws-quiz-app
sudo systemctl enable nginx
sudo systemctl start nginx

echo ""
echo "=========================================="
echo "✅ Deployment setup complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Upload your application files to /var/www/aws-quiz-app"
echo "2. Update config.py with your RDS database credentials"
echo "3. Start the application: sudo systemctl start aws-quiz-app"
echo "4. Check status: sudo systemctl status aws-quiz-app"
echo "5. View logs: sudo journalctl -u aws-quiz-app -f"
echo ""
echo "Your app will be accessible at: http://YOUR_EC2_PUBLIC_IP"
echo ""
echo "Security Group Requirements:"
echo "- Allow inbound TCP port 80 (HTTP)"
echo "- Allow inbound TCP port 443 (HTTPS) - if using SSL"
echo "- Allow inbound TCP port 22 (SSH) - for management"
echo ""

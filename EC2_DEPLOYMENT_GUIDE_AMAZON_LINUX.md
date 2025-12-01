# EC2 Deployment Guide for AWS Quiz Application
# Amazon Linux 2023

## Prerequisites

1. **EC2 Instance Requirements:**
   - Instance Type: t2.micro or larger (t2.small recommended)
   - AMI: Amazon Linux 2023
   - Storage: At least 10 GB
   - Security Group: Allow ports 22 (SSH), 80 (HTTP), 443 (HTTPS)

2. **RDS PostgreSQL Database:**
   - Already configured and accessible
   - Security group allows connection from EC2

3. **PuTTY Setup:**
   - PuTTY installed on your Windows machine
   - Private key (.ppk format) for EC2 instance

## Step-by-Step Deployment

### Step 1: Connect to EC2 via PuTTY

1. Open PuTTY
2. Enter your EC2 public IP or DNS: `ec2-user@YOUR_EC2_IP`
3. Load your private key: Connection → SSH → Auth → Private key file
4. Click "Open"

### Step 2: Initial Server Setup

```bash
# Update system
sudo dnf update -y

# Install required packages
sudo dnf install -y python3.11 python3.11-pip python3.11-devel
sudo dnf install -y gcc postgresql-devel git nginx

# Verify Python version
python3.11 --version
```

### Step 3: Create Application Directory

```bash
# Create app directory
sudo mkdir -p /var/www/aws-quiz-app
sudo chown -R $USER:$USER /var/www/aws-quiz-app
cd /var/www/aws-quiz-app
```

### Step 4: Transfer Application Files

**Option A: Using WinSCP (Recommended for Windows)**
1. Download WinSCP: https://winscp.net/
2. Connect using same credentials as PuTTY
3. Navigate to `/var/www/aws-quiz-app`
4. Upload all files from `c:\Users\venkatasai.p\Documents\aws_quiz_website\`

**Option B: Using PSCP (PuTTY's SCP)**
```cmd
# On Windows Command Prompt
cd c:\Users\venkatasai.p\Documents\aws_quiz_website

# Upload files (run from Windows)
pscp -r -i YOUR_KEY.ppk * ec2-user@YOUR_EC2_IP:/var/www/aws-quiz-app/
```

**Option C: Using Git**
```bash
# On EC2 instance
cd /var/www/aws-quiz-app
git clone https://github.com/Venkat-idexcel/aws-quiz-website.git .
```

### Step 5: Set Up Python Environment

```bash
cd /var/www/aws-quiz-app

# Create virtual environment
python3.11 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt

# Install Gunicorn for production
pip install gunicorn
```

### Step 6: Configure Environment

```bash
# Edit config.py with your RDS credentials
nano config.py
```

Make sure these settings are correct:
```python
DB_HOST = 'los-dev-psql-rdsclstr-new.cj6duvm27hk9.us-east-1.rds.amazonaws.com'
DB_PORT = 3306
DB_NAME = 'cretificate_quiz_db'
DB_USER = 'postgres'
DB_PASSWORD = 'your_password_here'
```

Press `Ctrl+X`, then `Y`, then `Enter` to save.

### Step 7: Test Application

```bash
# Make sure you're in the venv
source /var/www/aws-quiz-app/venv/bin/activate

# Test run
python app.py
```

Press `Ctrl+C` to stop when you see it's working.

### Step 8: Create Systemd Service

```bash
# Create service file with high-performance settings
sudo nano /etc/systemd/system/aws-quiz-app.service
```

Paste this **optimized** content for handling 1000+ users:
```ini
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
ExecReload=/bin/kill -s HUP $MAINPID
KillMode=mixed
TimeoutStopSec=60
PrivateTmp=true
Restart=always
RestartSec=10

# Performance settings for high load
LimitNOFILE=65536
LimitNPROC=32768

[Install]
WantedBy=multi-user.target
```

Save and exit (`Ctrl+X`, `Y`, `Enter`).

### Step 9: Configure Nginx

```bash
# Create Nginx config
sudo nano /etc/nginx/conf.d/aws-quiz-app.conf
```

Paste this **high-performance** content optimized for 1000+ users:
```nginx
server {
    listen 80;
    server_name _;
    
    # Performance optimizations
    client_max_body_size 50M;
    client_body_buffer_size 128k;
    client_header_buffer_size 4k;
    large_client_header_buffers 4 16k;
    
    # Connection settings for high load
    keepalive_timeout 65;
    keepalive_requests 1000;
    
    # Enable gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
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
    
    # Rate limiting to prevent abuse
    limit_req_zone $binary_remote_addr zone=login:10m rate=10r/m;
    limit_req_zone $binary_remote_addr zone=quiz:10m rate=30r/m;
    limit_req_zone $binary_remote_addr zone=general:10m rate=100r/m;
    
    # Main application proxy with rate limiting
    location / {
        limit_req zone=general burst=20 nodelay;
        
        proxy_pass http://127.0.0.1:5000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        
        # Increased timeouts for high load
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
        
        # Buffer settings for better performance
        proxy_buffering on;
        proxy_buffer_size 16k;
        proxy_buffers 8 16k;
        proxy_busy_buffers_size 32k;
    }
    
    # Login rate limiting (stricter)
    location /login {
        limit_req zone=login burst=5 nodelay;
        proxy_pass http://127.0.0.1:5000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 300s;
        proxy_read_timeout 300s;
    }

    # Static files with aggressive caching
    location /static {
        alias /var/www/aws-quiz-app/static;
        expires 1y;
        add_header Cache-Control "public, immutable";
        add_header X-Cache-Status "STATIC";
        sendfile on;
        tcp_nopush on;
        tcp_nodelay on;
        gzip_static on;
        add_header X-Content-Type-Options nosniff;
    }
    
    # Health check endpoint
    location /health {
        access_log off;
        return 200 "healthy\n";
        add_header Content-Type text/plain;
    }
    
    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-XSS-Protection "1; mode=block";
    add_header X-Content-Type-Options nosniff;
    add_header Referrer-Policy strict-origin-when-cross-origin;
    server_tokens off;
}
```

Save and exit.

### Step 10: Start Services

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable services to start on boot
sudo systemctl enable aws-quiz-app
sudo systemctl enable nginx

# Start Nginx
sudo systemctl start nginx

# Start application
sudo systemctl start aws-quiz-app

# Check status
sudo systemctl status aws-quiz-app
sudo systemctl status nginx
```

### Step 11: Configure Firewall (if enabled)

```bash
# Check if firewall is running
sudo systemctl status firewalld

# If running, allow HTTP/HTTPS
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --reload
```

### Step 12: Verify Deployment

```bash
# Check application logs
sudo journalctl -u aws-quiz-app -f

# Test locally on EC2
curl http://localhost

# Get your EC2 public IP
curl http://checkip.amazonaws.com
```

Open browser and navigate to: `http://YOUR_EC2_PUBLIC_IP`

## Useful Commands

### Service Management
```bash
# Start application
sudo systemctl start aws-quiz-app

# Stop application
sudo systemctl stop aws-quiz-app

# Restart application
sudo systemctl restart aws-quiz-app

# View status
sudo systemctl status aws-quiz-app

# View logs (real-time)
sudo journalctl -u aws-quiz-app -f

# View last 100 lines of logs
sudo journalctl -u aws-quiz-app -n 100
```

### Nginx Commands
```bash
# Test Nginx configuration
sudo nginx -t

# Restart Nginx
sudo systemctl restart nginx

# View Nginx error log
sudo tail -f /var/log/nginx/error.log

# View Nginx access log
sudo tail -f /var/log/nginx/access.log
```

### Update Application
```bash
# Stop service
sudo systemctl stop aws-quiz-app

# Pull updates (if using git)
cd /var/www/aws-quiz-app
git pull

# Or upload new files via WinSCP

# Activate venv and install any new dependencies
source venv/bin/activate
pip install -r requirements.txt

# Restart service
sudo systemctl start aws-quiz-app
```

## Security Group Configuration

Make sure your EC2 Security Group has these inbound rules:

| Type  | Protocol | Port | Source    | Description          |
|-------|----------|------|-----------|----------------------|
| SSH   | TCP      | 22   | Your IP   | SSH access           |
| HTTP  | TCP      | 80   | 0.0.0.0/0 | Public web access    |
| HTTPS | TCP      | 443  | 0.0.0.0/0 | Secure web (future)  |

## RDS Security Group

Make sure RDS Security Group allows:

| Type       | Protocol | Port | Source           | Description      |
|------------|----------|------|------------------|------------------|
| PostgreSQL | TCP      | 3306 | EC2 Security Group | DB access from EC2 |

## Troubleshooting

### Application won't start
```bash
# Check logs for errors
sudo journalctl -u aws-quiz-app -n 50

# Check if port 5000 is in use
sudo netstat -tulpn | grep 5000

# Test database connection
cd /var/www/aws-quiz-app
source venv/bin/activate
python -c "from config import Config; import psycopg2; conn = psycopg2.connect(host=Config.DB_HOST, port=Config.DB_PORT, database=Config.DB_NAME, user=Config.DB_USER, password=Config.DB_PASSWORD); print('✅ Database connected!')"
```

### Nginx errors
```bash
# Check Nginx configuration
sudo nginx -t

# Check Nginx is running
sudo systemctl status nginx

# View error logs
sudo tail -f /var/log/nginx/error.log
```

### Cannot connect from browser
1. Check EC2 Security Group allows port 80
2. Check EC2 public IP: `curl http://checkip.amazonaws.com`
3. Check Nginx is running: `sudo systemctl status nginx`
4. Check app is running: `sudo systemctl status aws-quiz-app`
5. Test locally: `curl http://localhost` (from EC2)

### Database connection fails
1. Check RDS Security Group allows EC2 security group
2. Verify config.py has correct credentials
3. Test connection from EC2 to RDS
4. Check RDS is in available state

## Performance Optimization

### For Production Use:

1. **Use more Gunicorn workers:**
   ```bash
   sudo nano /etc/systemd/system/aws-quiz-app.service
   # Change: --workers 3 to --workers 4 (or 2 × CPU cores + 1)
   sudo systemctl daemon-reload
   sudo systemctl restart aws-quiz-app
   ```

2. **Enable Nginx caching:**
   Add to Nginx config in `/etc/nginx/conf.d/aws-quiz-app.conf`

3. **Set up SSL/HTTPS:**
   - Use AWS Certificate Manager + Application Load Balancer, OR
   - Use Let's Encrypt with certbot

4. **Monitor resources:**
   ```bash
   # Check memory usage
   free -h
   
   # Check disk usage
   df -h
   
   # Monitor processes
   htop
   ```

## Backup and Maintenance

### Daily Tasks
```bash
# Backup database (if using local backup)
# Your RDS should have automated backups enabled

# Check logs for errors
sudo journalctl -u aws-quiz-app --since today | grep -i error

# Monitor disk space
df -h
```

### Weekly Tasks
```bash
# Update system packages
sudo dnf update -y

# Restart services
sudo systemctl restart aws-quiz-app
sudo systemctl restart nginx
```

## Support

If you encounter issues:
1. Check application logs: `sudo journalctl -u aws-quiz-app -f`
2. Check Nginx logs: `sudo tail -f /var/log/nginx/error.log`
3. Verify database connectivity
4. Check security group settings

## Next Steps

After deployment:
1. ✅ Test login functionality
2. ✅ Take a test quiz
3. ✅ Verify results are saved
4. ✅ Check admin panel access
5. Set up SSL certificate (for HTTPS)
6. Configure domain name (optional)
7. Set up monitoring and alerts
8. Enable RDS backups and snapshots

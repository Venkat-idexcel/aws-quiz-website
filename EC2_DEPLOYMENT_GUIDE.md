# AWS Quiz Website - EC2 Deployment Guide

## 🚀 Complete Deployment Instructions for EC2 Instance

### Prerequisites
- EC2 instance with Ubuntu/Amazon Linux
- PuTTY access to EC2 instance
- Security group allowing HTTP (port 80) and HTTPS (port 443)
- Your EC2 instance should have internet access

---

## Step 1: Connect to EC2 Instance via PuTTY

1. **Open PuTTY**
2. **Enter Connection Details:**
   - Host Name: `your-ec2-public-ip` or `your-ec2-dns-name`
   - Port: `22`
   - Connection Type: `SSH`

3. **Load your private key (.ppk file):**
   - Go to: Connection → SSH → Auth → Credentials
   - Browse and select your `.ppk` private key file

4. **Connect and login as:**
   - Amazon Linux: `ec2-user`
   - Ubuntu: `ubuntu`

---

## Step 2: Install Required Software

```bash
# Update system
sudo yum update -y  # For Amazon Linux
# OR
sudo apt update && sudo apt upgrade -y  # For Ubuntu

# Install Git
sudo yum install -y git  # Amazon Linux
# OR
sudo apt install -y git  # Ubuntu

# Install Python 3 and pip
sudo yum install -y python3 python3-pip  # Amazon Linux
# OR
sudo apt install -y python3 python3-pip  # Ubuntu

# Install PostgreSQL client
sudo yum install -y postgresql  # Amazon Linux
# OR
sudo apt install -y postgresql-client  # Ubuntu

# Install Nginx
sudo yum install -y nginx  # Amazon Linux
# OR
sudo apt install -y nginx  # Ubuntu

# Install supervisor for process management
sudo yum install -y supervisor  # Amazon Linux
# OR
sudo apt install -y supervisor  # Ubuntu
```

---

## Step 3: Clone and Setup Application

```bash
# Navigate to web directory
cd /home/ec2-user  # Amazon Linux
# OR
cd /home/ubuntu    # Ubuntu

# Clone your repository
git clone https://github.com/Venkat-idexcel/aws-quiz-website.git
cd aws-quiz-website

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt

# Install Gunicorn for production
pip install gunicorn
```

---

## Step 4: Configure Database Connection

1. **Edit config.py for production:**

```bash
nano config.py
```

Update the database configuration:

```python
import os

class Config:
    # Database Configuration
    DB_HOST = 'los-dev-psql-rdsclstr-new.cj6duvm27hk9.us-east-1.rds.amazonaws.com'
    DB_PORT = '3306'
    DB_USER = 'postgres'
    DB_PASSWORD = 'poc2*&(SRWSjnjkn@#@#'
    DB_NAME = 'postgres'
    
    # Flask Configuration
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-super-secret-production-key-here'
    
    # Production settings
    DEBUG = False
    TESTING = False
```

2. **Test database connection:**

```bash
python3 -c "
import psycopg2
try:
    conn = psycopg2.connect(
        host='los-dev-psql-rdsclstr-new.cj6duvm27hk9.us-east-1.rds.amazonaws.com',
        port='3306',
        user='postgres',
        password='poc2*&(SRWSjnjkn@#@#',
        database='postgres'
    )
    print('✅ Database connection successful!')
    conn.close()
except Exception as e:
    print(f'❌ Database connection failed: {e}')
"
```

---

## Step 5: Setup Database (if needed)

```bash
# Activate virtual environment
source venv/bin/activate

# Run database migrations
python3 migrate_database.py

# Load AWS Data Engineer questions
python3 load_data_engineer_simple.py
```

---

## Step 6: Configure Gunicorn

Create Gunicorn configuration:

```bash
nano gunicorn.conf.py
```

Add this content:

```python
bind = "127.0.0.1:8000"
workers = 3
worker_class = "sync"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 100
timeout = 30
keepalive = 2
preload_app = True
```

---

## Step 7: Configure Nginx

```bash
# Create Nginx configuration
sudo nano /etc/nginx/sites-available/aws-quiz-website  # Ubuntu
# OR
sudo nano /etc/nginx/conf.d/aws-quiz-website.conf      # Amazon Linux
```

Add this configuration:

```nginx
server {
    listen 80;
    server_name your-ec2-public-ip your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 30s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;
    }

    location /static/ {
        alias /home/ec2-user/aws-quiz-website/static/;  # Amazon Linux
        # OR
        # alias /home/ubuntu/aws-quiz-website/static/;   # Ubuntu
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Gzip compression
    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;
}
```

**For Ubuntu, enable the site:**

```bash
sudo ln -s /etc/nginx/sites-available/aws-quiz-website /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default  # Remove default site
```

**Test Nginx configuration:**

```bash
sudo nginx -t
```

---

## Step 8: Configure Supervisor for Process Management

```bash
# Create supervisor configuration
sudo nano /etc/supervisor/conf.d/aws-quiz-website.conf
```

Add this content:

```ini
[program:aws-quiz-website]
command=/home/ec2-user/aws-quiz-website/venv/bin/gunicorn -c gunicorn.conf.py wsgi:app
directory=/home/ec2-user/aws-quiz-website
user=ec2-user
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/aws-quiz-website.log

# For Ubuntu, change paths:
# command=/home/ubuntu/aws-quiz-website/venv/bin/gunicorn -c gunicorn.conf.py wsgi:app
# directory=/home/ubuntu/aws-quiz-website
# user=ubuntu
```

---

## Step 9: Start Services

```bash
# Reload supervisor configuration
sudo supervisorctl reread
sudo supervisorctl update

# Start the application
sudo supervisorctl start aws-quiz-website

# Start and enable Nginx
sudo systemctl start nginx
sudo systemctl enable nginx

# Check status
sudo supervisorctl status aws-quiz-website
sudo systemctl status nginx
```

---

## Step 10: Configure Security Group

In your AWS Console:

1. **Go to EC2 → Security Groups**
2. **Select your instance's security group**
3. **Add Inbound Rules:**
   - Type: HTTP, Port: 80, Source: 0.0.0.0/0
   - Type: HTTPS, Port: 443, Source: 0.0.0.0/0 (for future SSL)
   - Type: SSH, Port: 22, Source: Your IP

---

## Step 11: Test Deployment

```bash
# Check if application is running
curl http://localhost:8000

# Check logs
sudo supervisorctl tail -f aws-quiz-website
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

**Access your website:**
- Open browser and go to: `http://your-ec2-public-ip`

---

## 🛠️ Troubleshooting

### Application won't start:
```bash
# Check supervisor logs
sudo supervisorctl tail aws-quiz-website

# Check if port is in use
sudo netstat -tlnp | grep :8000

# Restart services
sudo supervisorctl restart aws-quiz-website
sudo systemctl restart nginx
```

### Database connection issues:
```bash
# Check if EC2 can reach RDS
telnet los-dev-psql-rdsclstr-new.cj6duvm27hk9.us-east-1.rds.amazonaws.com 3306

# Check RDS security group allows EC2 access
# Make sure RDS security group allows inbound from EC2 security group on port 3306
```

### Permission issues:
```bash
# Fix file permissions
sudo chown -R ec2-user:ec2-user /home/ec2-user/aws-quiz-website
# OR for Ubuntu:
sudo chown -R ubuntu:ubuntu /home/ubuntu/aws-quiz-website

# Make scripts executable
chmod +x deploy.sh
```

---

## 🚀 Quick Deployment Script

For faster deployment, you can use the automated script:

```bash
# Make script executable
chmod +x deploy.sh

# Run deployment script
./deploy.sh
```

---

## 📝 Important Notes

1. **Replace placeholders:**
   - `your-ec2-public-ip` with your actual EC2 public IP
   - `your-domain.com` with your domain (if you have one)

2. **Security:**
   - Change the SECRET_KEY to a strong, unique value
   - Consider using environment variables for sensitive data

3. **SSL Certificate (Optional):**
   - Use Let's Encrypt with Certbot for free SSL certificates

4. **Monitoring:**
   - Check logs regularly: `/var/log/aws-quiz-website.log`
   - Monitor system resources: `htop`, `df -h`

---

## 🎉 Success!

If everything is working:
- Your website should be accessible at `http://your-ec2-public-ip`
- Both AWS Cloud Practitioner and AWS Data Engineer quizzes should work
- Database connections should be stable

**Your AWS Quiz Website is now live on EC2!** 🚀
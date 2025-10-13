# Step-by-Step Deployment Checklist
# AWS Quiz Application on Amazon Linux 2023

## Pre-Deployment Checklist

- [ ] EC2 instance created (Amazon Linux 2023)
- [ ] Security Group configured (ports 22, 80, 443)
- [ ] RDS PostgreSQL database accessible
- [ ] PuTTY installed with .ppk key file
- [ ] WinSCP or PSCP installed for file transfer

## Deployment Steps

### 1. Connect to EC2
```bash
# Using PuTTY
# Host: ec2-user@YOUR_EC2_IP
# Port: 22
# Auth: Load your .ppk file
```
- [ ] Successfully connected via PuTTY

### 2. Install System Dependencies
```bash
sudo dnf update -y
sudo dnf install -y python3.11 python3.11-pip python3.11-devel
sudo dnf install -y gcc postgresql-devel git nginx
```
- [ ] System packages updated
- [ ] Python 3.11 installed
- [ ] Nginx installed

### 3. Create Application Directory
```bash
sudo mkdir -p /var/www/aws-quiz-app
sudo chown -R $USER:$USER /var/www/aws-quiz-app
cd /var/www/aws-quiz-app
```
- [ ] Directory created
- [ ] Permissions set

### 4. Upload Application Files

**Option A: Using WinSCP (Recommended)**
- [ ] Downloaded WinSCP
- [ ] Connected to EC2
- [ ] Uploaded all files to /var/www/aws-quiz-app

**Option B: Using PSCP**
```cmd
pscp -r -i YOUR_KEY.ppk c:\Users\venkatasai.p\Documents\aws_quiz_website\* ec2-user@YOUR_EC2_IP:/var/www/aws-quiz-app/
```
- [ ] Files uploaded via PSCP

### 5. Set Up Python Environment
```bash
cd /var/www/aws-quiz-app
python3.11 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn
```
- [ ] Virtual environment created
- [ ] Dependencies installed
- [ ] Gunicorn installed

### 6. Configure Database Connection
```bash
nano config.py
```
Verify these settings:
```python
DB_HOST = 'los-dev-psql-rdsclstr-new.cj6duvm27hk9.us-east-1.rds.amazonaws.com'
DB_PORT = 3306
DB_NAME = 'cretificate_quiz_db'
DB_USER = 'postgres'
DB_PASSWORD = 'poc2*&(SRWSjnjkn@#@#'
```
- [ ] config.py updated with correct credentials

### 7. Test Database Connection
```bash
source venv/bin/activate
python -c "from config import Config; import psycopg2; conn = psycopg2.connect(host=Config.DB_HOST, port=Config.DB_PORT, database=Config.DB_NAME, user=Config.DB_USER, password=Config.DB_PASSWORD); print('✅ Database connected!')"
```
- [ ] Database connection successful

### 8. Test Application Locally
```bash
python app.py
# Press Ctrl+C to stop after verifying it starts
```
- [ ] Application starts without errors
- [ ] No Python errors in output

### 9. Create Systemd Service
```bash
sudo nano /etc/systemd/system/aws-quiz-app.service
```
Paste the service configuration and save.
- [ ] Service file created

### 10. Configure Nginx
```bash
sudo nano /etc/nginx/conf.d/aws-quiz-app.conf
```
Paste the nginx configuration and save.
- [ ] Nginx config created
- [ ] Configuration tested: `sudo nginx -t`

### 11. Start Services
```bash
sudo systemctl daemon-reload
sudo systemctl enable aws-quiz-app
sudo systemctl enable nginx
sudo systemctl start nginx
sudo systemctl start aws-quiz-app
```
- [ ] Services enabled for auto-start
- [ ] Nginx started
- [ ] Application started

### 12. Verify Deployment
```bash
# Check application status
sudo systemctl status aws-quiz-app

# Check Nginx status
sudo systemctl status nginx

# Get public IP
curl http://checkip.amazonaws.com

# Test locally
curl http://localhost
```
- [ ] Application service is active
- [ ] Nginx service is active
- [ ] Local test returns HTML
- [ ] Got EC2 public IP address

### 13. Browser Testing
Open browser and navigate to: `http://YOUR_EC2_PUBLIC_IP`
- [ ] Homepage loads
- [ ] Can login
- [ ] Can start quiz
- [ ] Can complete quiz
- [ ] Results display correctly
- [ ] Results saved to database

## Post-Deployment Tasks

### Verify Functionality
- [ ] Create test user account
- [ ] Take a complete quiz
- [ ] Check quiz history
- [ ] Verify admin panel (if applicable)
- [ ] Check leaderboard

### Monitor Logs
```bash
# Application logs
sudo journalctl -u aws-quiz-app -f

# Nginx access log
sudo tail -f /var/log/nginx/access.log

# Nginx error log
sudo tail -f /var/log/nginx/error.log
```
- [ ] Logs reviewed for errors

### Performance Check
```bash
# Check memory
free -h

# Check disk space
df -h

# Check processes
ps aux | grep gunicorn
```
- [ ] Memory usage acceptable
- [ ] Disk space sufficient
- [ ] Gunicorn workers running

## Troubleshooting Checklist

If application doesn't work:

- [ ] Check service status: `sudo systemctl status aws-quiz-app`
- [ ] Check logs: `sudo journalctl -u aws-quiz-app -n 50`
- [ ] Check Nginx: `sudo systemctl status nginx`
- [ ] Check security group allows port 80
- [ ] Check RDS security group allows EC2
- [ ] Verify database credentials in config.py
- [ ] Test database connection manually
- [ ] Check file permissions: `ls -la /var/www/aws-quiz-app`

## Maintenance Commands

### Restart Application
```bash
sudo systemctl restart aws-quiz-app
```

### Update Application
```bash
sudo systemctl stop aws-quiz-app
cd /var/www/aws-quiz-app
# Upload new files via WinSCP
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl start aws-quiz-app
```

### View Logs
```bash
# Real-time logs
sudo journalctl -u aws-quiz-app -f

# Last 100 lines
sudo journalctl -u aws-quiz-app -n 100

# Errors only
sudo journalctl -u aws-quiz-app -p err
```

## Security Checklist

- [ ] Changed default secret key in config.py
- [ ] RDS security group restricts access to EC2 only
- [ ] EC2 security group restricts SSH to your IP
- [ ] Regular system updates scheduled
- [ ] RDS automated backups enabled
- [ ] SSL certificate planned (for HTTPS)

## Deployment Status

- Date deployed: _______________
- EC2 Instance ID: _______________
- EC2 Public IP: _______________
- EC2 Private IP: _______________
- RDS Endpoint: los-dev-psql-rdsclstr-new.cj6duvm27hk9.us-east-1.rds.amazonaws.com
- Application URL: http://_______________

## Notes

Add any deployment-specific notes or issues here:

_______________________________________________
_______________________________________________
_______________________________________________

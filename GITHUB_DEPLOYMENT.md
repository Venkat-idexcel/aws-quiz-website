# GitHub Deployment Guide - AWS Quiz Application

## 📋 Overview

This guide walks you through deploying your AWS Quiz Application to EC2 using GitHub. This is the recommended approach for production deployments.

---

## Prerequisites

✅ EC2 instance running Amazon Linux 2023
✅ Security Group allows ports 22 (SSH) and 80 (HTTP)
✅ RDS PostgreSQL database accessible from EC2
✅ GitHub repository: https://github.com/Venkat-idexcel/aws-quiz-website
✅ PuTTY and .ppk key for SSH access

---

## Part 1: Push Code to GitHub (Windows)

### Step 1: Check Current Status

```powershell
cd c:\Users\venkatasai.p\Documents\aws_quiz_website
git status
```

### Step 2: Add All Changes

```powershell
git add .
```

### Step 3: Commit Changes

```powershell
git commit -m "Add EC2 deployment script and fix quiz results storage"
```

### Step 4: Push to GitHub

```powershell
git push origin main
```

**If you get authentication error:**
- GitHub no longer accepts passwords
- Use Personal Access Token (PAT)
- Generate at: GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic) → Generate new token
- Use the token as your password when prompted

### Step 5: Verify on GitHub

Open browser: https://github.com/Venkat-idexcel/aws-quiz-website

Verify these files are present:
- ✅ app.py (with latest fixes)
- ✅ config.py
- ✅ requirements.txt
- ✅ wsgi.py
- ✅ install_ec2.sh
- ✅ templates/ folder
- ✅ static/ folder

---

## Part 2: Deploy to EC2

### Step 1: Connect to EC2

Open PuTTY:
- Host: `ec2-user@YOUR_EC2_PUBLIC_IP`
- Port: 22
- Auth: Load your .ppk file
- Click "Open"

### Step 2: Update System

```bash
sudo dnf update -y
```

### Step 3: Install Required Packages

```bash
sudo dnf install -y python3.11 python3.11-pip python3.11-devel
sudo dnf install -y gcc postgresql-devel git nginx
```

Verify installations:
```bash
python3.11 --version
git --version
```

### Step 4: Clone Repository

```bash
# Create and set up directory
sudo mkdir -p /var/www/aws-quiz-app
sudo chown -R $USER:$USER /var/www/aws-quiz-app

# Clone from GitHub
cd /var/www/aws-quiz-app
git clone https://github.com/Venkat-idexcel/aws-quiz-website.git .
```

**Note:** The `.` at the end clones into current directory

### Step 5: Run Installation Script

```bash
cd /var/www/aws-quiz-app
chmod +x install_ec2.sh
bash install_ec2.sh
```

This script will:
- ✅ Set up Python virtual environment
- ✅ Install all dependencies
- ✅ Configure Nginx
- ✅ Create systemd service
- ✅ Enable services

### Step 6: Verify Configuration

Check that config.py has correct database credentials:

```bash
cat config.py | grep DB_
```

You should see:
```
DB_HOST = 'los-dev-psql-rdsclstr-new.cj6duvm27hk9.us-east-1.rds.amazonaws.com'
DB_PORT = 3306
DB_NAME = 'cretificate_quiz_db'
DB_USER = 'postgres'
```

**If credentials need updating:**
```bash
nano config.py
# Edit the values
# Save: Ctrl+X, Y, Enter
```

### Step 7: Start Application

```bash
sudo systemctl start aws-quiz-app
```

### Step 8: Check Status

```bash
sudo systemctl status aws-quiz-app
```

You should see:
```
● aws-quiz-app.service - AWS Quiz Application
   Loaded: loaded
   Active: active (running)
```

### Step 9: Test Application

Get your EC2 public IP:
```bash
curl http://checkip.amazonaws.com
```

Open browser and navigate to:
```
http://YOUR_EC2_PUBLIC_IP
```

You should see the AWS Quiz homepage!

---

## Verification Checklist

After deployment, test:

- [ ] Homepage loads (`http://YOUR_EC2_IP`)
- [ ] Can login with existing account
- [ ] Can register new account
- [ ] Can start a quiz
- [ ] Questions display correctly
- [ ] Can answer questions
- [ ] Can complete quiz
- [ ] Results page shows:
  - [ ] Correct answer count
  - [ ] Total questions
  - [ ] Score percentage
  - [ ] Time taken
- [ ] Results saved to database
- [ ] Quiz history shows completed quiz
- [ ] No errors in logs

---

## Useful Commands

### View Application Logs

```bash
# Real-time logs
sudo journalctl -u aws-quiz-app -f

# Last 100 lines
sudo journalctl -u aws-quiz-app -n 100

# Errors only
sudo journalctl -u aws-quiz-app -p err
```

### Service Management

```bash
# Start
sudo systemctl start aws-quiz-app

# Stop
sudo systemctl stop aws-quiz-app

# Restart
sudo systemctl restart aws-quiz-app

# Status
sudo systemctl status aws-quiz-app

# Enable on boot
sudo systemctl enable aws-quiz-app
```

### Nginx Commands

```bash
# Test configuration
sudo nginx -t

# Restart Nginx
sudo systemctl restart nginx

# View access log
sudo tail -f /var/log/nginx/access.log

# View error log
sudo tail -f /var/log/nginx/error.log
```

### Database Connection Test

```bash
cd /var/www/aws-quiz-app
source venv/bin/activate
python -c "from config import Config; import psycopg2; conn = psycopg2.connect(host=Config.DB_HOST, port=Config.DB_PORT, database=Config.DB_NAME, user=Config.DB_USER, password=Config.DB_PASSWORD); print('✅ Database connected!')"
```

---

## Updating Application

When you push changes to GitHub:

### On Windows:

```powershell
cd c:\Users\venkatasai.p\Documents\aws_quiz_website
git add .
git commit -m "Description of changes"
git push origin main
```

### On EC2:

```bash
cd /var/www/aws-quiz-app
git pull origin main
source venv/bin/activate
pip install -r requirements.txt  # Only if requirements changed
sudo systemctl restart aws-quiz-app
sudo systemctl status aws-quiz-app
```

---

## Troubleshooting

### Application Won't Start

```bash
# Check logs for error
sudo journalctl -u aws-quiz-app -n 50

# Check if port 5000 is in use
sudo netstat -tulpn | grep 5000

# Check Python errors
cd /var/www/aws-quiz-app
source venv/bin/activate
python app.py  # Run manually to see errors
```

### Cannot Connect from Browser

1. Check EC2 Security Group allows port 80
2. Check application is running: `sudo systemctl status aws-quiz-app`
3. Check Nginx is running: `sudo systemctl status nginx`
4. Test locally: `curl http://localhost` (from EC2)
5. Get public IP: `curl http://checkip.amazonaws.com`

### Database Connection Fails

1. Check RDS Security Group allows EC2
2. Verify config.py credentials
3. Test connection manually (see Database Connection Test above)
4. Check RDS endpoint is correct
5. Verify RDS is in "available" state

### Permission Errors

```bash
sudo chown -R ec2-user:ec2-user /var/www/aws-quiz-app
sudo chmod +x /var/www/aws-quiz-app/*.sh
```

### Git Pull Fails

```bash
# Discard local changes
cd /var/www/aws-quiz-app
git reset --hard origin/main
git pull origin main
```

---

## Security Best Practices

### 1. Update Secret Key

```bash
nano /var/www/aws-quiz-app/config.py
# Change SECRET_KEY to a random value
```

Generate random key:
```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

### 2. Restrict SSH Access

EC2 Security Group → Edit inbound rules → SSH (22) → Change source to "My IP"

### 3. Enable HTTPS (Optional but Recommended)

Install Let's Encrypt:
```bash
sudo dnf install -y certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com
```

### 4. Set Up Firewall

```bash
sudo systemctl enable firewalld
sudo systemctl start firewalld
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --reload
```

---

## Monitoring

### Check System Resources

```bash
# Memory usage
free -h

# Disk space
df -h

# CPU usage
top

# Running processes
ps aux | grep gunicorn
```

### Application Health

```bash
# Check if app responds
curl -I http://localhost

# Check database queries
sudo journalctl -u aws-quiz-app | grep -i "database\|error"
```

---

## Backup Strategy

### Database Backups

Your RDS should have automated backups enabled:
- AWS Console → RDS → Your Database → Maintenance & backups
- Enable automated backups
- Set retention period (7-30 days)

### Application Code

Your code is backed up on GitHub:
- Every commit is a backup
- You can rollback to any previous version
- Create tags for releases: `git tag v1.0`

### Static Files

Backup `/var/www/aws-quiz-app/static` if you add user-uploaded content:
```bash
tar -czf static-backup-$(date +%Y%m%d).tar.gz /var/www/aws-quiz-app/static
```

---

## Performance Optimization

### Increase Gunicorn Workers

```bash
sudo nano /etc/systemd/system/aws-quiz-app.service
```

Change `--workers 3` to `--workers 4` (or 2 × CPU cores + 1)

```bash
sudo systemctl daemon-reload
sudo systemctl restart aws-quiz-app
```

### Enable Nginx Caching

Add to `/etc/nginx/conf.d/aws-quiz-app.conf`:
```nginx
proxy_cache_path /var/cache/nginx levels=1:2 keys_zone=my_cache:10m max_size=1g;
```

### Database Connection Pooling

Already configured in your app.py with connection pooling

---

## Summary

You've successfully deployed using GitHub! 🎉

**Deployment workflow:**
1. Make changes locally
2. Test locally
3. Commit to GitHub
4. Pull on EC2
5. Restart service

**Your app is now running at:**
```
http://YOUR_EC2_PUBLIC_IP
```

**Need help?** Check logs first:
```bash
sudo journalctl -u aws-quiz-app -f
```

Happy deploying! 🚀

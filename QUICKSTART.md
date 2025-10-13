# Quick Start - GitHub Deployment

## On Windows (Do this first):

```powershell
# Navigate to project
cd c:\Users\venkatasai.p\Documents\aws_quiz_website

# Add all changes
git add .

# Commit
git commit -m "Deploy AWS Quiz App to EC2"

# Push to GitHub
git push origin main

# Verify at: https://github.com/Venkat-idexcel/aws-quiz-website
```

---

## On EC2 (via PuTTY):

```bash
# Install dependencies
sudo dnf update -y
sudo dnf install -y python3.11 python3.11-pip git nginx gcc postgresql-devel

# Clone repository
sudo mkdir -p /var/www/aws-quiz-app
sudo chown -R $USER:$USER /var/www/aws-quiz-app
cd /var/www/aws-quiz-app
git clone https://github.com/Venkat-idexcel/aws-quiz-website.git .

# Run installation script
chmod +x install_ec2.sh
bash install_ec2.sh

# Start application
sudo systemctl start aws-quiz-app

# Get your IP
curl http://checkip.amazonaws.com

# Access at: http://YOUR_EC2_IP
```

---

## Quick Commands:

```bash
# View logs
sudo journalctl -u aws-quiz-app -f

# Restart app
sudo systemctl restart aws-quiz-app

# Check status
sudo systemctl status aws-quiz-app

# Update from GitHub
cd /var/www/aws-quiz-app
git pull
sudo systemctl restart aws-quiz-app
```

---

## Troubleshooting:

```bash
# Test database connection
cd /var/www/aws-quiz-app
source venv/bin/activate
python -c "from config import Config; import psycopg2; conn = psycopg2.connect(host=Config.DB_HOST, port=Config.DB_PORT, database=Config.DB_NAME, user=Config.DB_USER, password=Config.DB_PASSWORD); print('✅ Connected!')"

# Check Nginx
sudo nginx -t
sudo systemctl status nginx

# View error logs
sudo tail -f /var/log/nginx/error.log
```

---

That's it! 🚀

# 🚀 GitHub Deployment - Step by Step

## ✅ STEP 1: Push to GitHub (Windows)

Open PowerShell:
```powershell
cd c:\Users\venkatasai.p\Documents\aws_quiz_website
git add .
git commit -m "Deploy AWS Quiz App to EC2"
git push origin main
```

Verify at: https://github.com/Venkat-idexcel/aws-quiz-website

---

## ✅ STEP 2: Connect to EC2 (PuTTY)

- Host: `ec2-user@YOUR_EC2_PUBLIC_IP`
- Port: 22
- Auth: Load your .ppk file
- Click "Open"

---

## ✅ STEP 3: Install Dependencies (EC2)

```bash
sudo dnf update -y
sudo dnf install -y python3.11 python3.11-pip python3.11-devel gcc postgresql-devel git nginx
```

---

## ✅ STEP 4: Clone Repository (EC2)

```bash
sudo mkdir -p /var/www/aws-quiz-app
sudo chown -R $USER:$USER /var/www/aws-quiz-app
cd /var/www/aws-quiz-app
git clone https://github.com/Venkat-idexcel/aws-quiz-website.git .
```

**Note:** Don't forget the `.` at the end!

---

## ✅ STEP 5: Run Installation (EC2)

```bash
chmod +x install_ec2.sh
bash install_ec2.sh
```

Wait 2-5 minutes for installation...

---

## ✅ STEP 6: Start Application (EC2)

```bash
sudo systemctl start aws-quiz-app
sudo systemctl status aws-quiz-app
```

Should show: **Active: active (running)** ✅

---

## ✅ STEP 7: Test (Browser)

```bash
# Get your IP
curl http://checkip.amazonaws.com
```

Open browser: `http://YOUR_EC2_PUBLIC_IP`

---

## 📋 Verify Everything Works:

- [ ] Homepage loads
- [ ] Can login
- [ ] Can start quiz  
- [ ] Questions display
- [ ] Can complete quiz
- [ ] Results show correctly
- [ ] Results saved to database

---

## 🔧 Useful Commands:

```bash
# View logs
sudo journalctl -u aws-quiz-app -f

# Restart app
sudo systemctl restart aws-quiz-app

# Update from GitHub
cd /var/www/aws-quiz-app && git pull && sudo systemctl restart aws-quiz-app
```

---

## 🆘 Troubleshooting:

**Can't access from browser?**
- Check Security Group allows port 80
- Check: `sudo systemctl status aws-quiz-app`
- Check: `sudo systemctl status nginx`

**Application errors?**
```bash
sudo journalctl -u aws-quiz-app -n 50
```

**Database connection issues?**
```bash
cd /var/www/aws-quiz-app
source venv/bin/activate
python -c "from config import Config; import psycopg2; conn = psycopg2.connect(host=Config.DB_HOST, port=Config.DB_PORT, database=Config.DB_NAME, user=Config.DB_USER, password=Config.DB_PASSWORD); print('✅ Connected!')"
```

---

## 🎉 Done!

Your app is live at: **http://YOUR_EC2_PUBLIC_IP**

For detailed guide, see: **GITHUB_DEPLOYMENT.md**

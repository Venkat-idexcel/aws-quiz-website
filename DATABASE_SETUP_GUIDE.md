# Local PostgreSQL Database Setup for EC2 Deployment

## 🎯 Database Connection Configuration

Your application will connect to a local PostgreSQL database on the same EC2 instance:

```
Host: localhost
Port: 5432 (standard PostgreSQL port)
User: postgres
Password: postgres (configurable)
Database: aws_quiz_db
```

## 🔧 Required Security Group Configuration

### EC2 Security Group Settings

Since PostgreSQL runs locally on the same EC2 instance, you only need these rules:

**Inbound Rules for EC2 Security Group:**
```
Type: HTTP
Port: 80
Source: 0.0.0.0/0
Description: Allow web traffic

Type: SSH
Port: 22
Source: Your IP address
Description: SSH access for administration
```

**Outbound Rules for EC2 Security Group:**
```
Type: All Traffic
Port: All
Destination: 0.0.0.0/0
Description: Allow outbound traffic (for package downloads, etc.)
```

**Note:** No external database connections needed since PostgreSQL runs locally!

## 🔍 Testing Local Database Connection

### Method 1: Using Python (Recommended)

```bash
# SSH into your EC2 instance first
python3 -c "
import psycopg2
try:
    conn = psycopg2.connect(
        host='localhost',
        port='5432',
        user='postgres',
        password='postgres',
        database='aws_quiz_db'
    )
    print('✅ Database connection successful!')
    
    # Test query
    cur = conn.cursor()
    cur.execute('SELECT version();')
    version = cur.fetchone()
    print(f'PostgreSQL version: {version[0]}')
    
    # Check if tables exist
    cur.execute(\"\"\"
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_name IN ('users', 'aws_questions', 'quiz_sessions')
    \"\"\")
    tables = cur.fetchall()
    print(f'Found tables: {[t[0] for t in tables]}')
    
    conn.close()
except Exception as e:
    print(f'❌ Database connection failed: {e}')
    import traceback
    traceback.print_exc()
"
```

### Method 2: Using psql client (Local)

```bash
# PostgreSQL is installed locally, so psql should be available
sudo -u postgres psql

# Or connect to specific database
sudo -u postgres psql -d aws_quiz_db

# If successful, you'll get a psql prompt:
# postgres=# 
```

### Method 3: Check PostgreSQL Service Status

```bash
# Check if PostgreSQL is running
sudo systemctl status postgresql

# Start PostgreSQL if not running
sudo systemctl start postgresql

# Enable PostgreSQL to start on boot
sudo systemctl enable postgresql

# View PostgreSQL logs
sudo journalctl -u postgresql -f
```

## 📋 Database Schema Verification

Once connected, verify your database has the required tables:

```sql
-- List all tables
\dt

-- Check users table structure
\d users

-- Check aws_questions table structure  
\d aws_questions

-- Check quiz_sessions table structure
\d quiz_sessions

-- Count questions by category
SELECT category, COUNT(*) FROM aws_questions GROUP BY category;

-- Sample a few questions
SELECT id, question, correct_answer FROM aws_questions LIMIT 5;
```

## 🔧 Database Migration/Setup Scripts

If you need to set up the database from scratch on EC2:

### 1. Run Database Migration

```bash
# Navigate to your application directory
cd /home/ec2-user/aws-quiz-website  # Amazon Linux
# OR
cd /home/ubuntu/aws-quiz-website     # Ubuntu

# Activate virtual environment
source venv/bin/activate

# Run migration script
python3 migrate_database.py
```

### 2. Load AWS Data Engineer Questions

```bash
# Load the new AWS Data Engineer questions
python3 load_data_engineer_simple.py

# Verify questions were loaded
python3 -c "
import psycopg2
from config import Config
conn = psycopg2.connect(
    host=Config.DB_HOST,
    port=Config.DB_PORT,
    user=Config.DB_USER,
    password=Config.DB_PASSWORD,
    database=Config.DB_NAME
)
cur = conn.cursor()
cur.execute(\"SELECT category, COUNT(*) FROM aws_questions GROUP BY category\")
for row in cur.fetchall():
    print(f'{row[0]}: {row[1]} questions')
conn.close()
"
```

### 3. Create Admin User (Optional)

```bash
# Create an admin user for testing
python3 create_admin.py
```

## 🚨 Troubleshooting Database Issues

### Connection Timeout Issues

```bash
# Check if EC2 can reach RDS
ping los-dev-psql-rdsclstr-new.cj6duvm27hk9.us-east-1.rds.amazonaws.com

# Check routing
traceroute los-dev-psql-rdsclstr-new.cj6duvm27hk9.us-east-1.rds.amazonaws.com

# Check DNS resolution
nslookup los-dev-psql-rdsclstr-new.cj6duvm27hk9.us-east-1.rds.amazonaws.com
```

### Security Group Issues

1. **Go to AWS Console → EC2 → Security Groups**
2. **Find your EC2 instance's security group**
3. **Check Outbound Rules** - Must allow port 3306 to RDS
4. **Go to RDS → Databases → Your DB → Security Groups**
5. **Check Inbound Rules** - Must allow port 3306 from EC2

### VPC/Subnet Issues

- Ensure both EC2 and RDS are in the same VPC or have proper VPC peering
- Check route tables allow communication between subnets
- Verify network ACLs don't block traffic

### Connection Pool Issues

If you get "too many connections" errors:

```python
# In your application, limit connection pool size
# Add to config.py:

class Config:
    # ... existing config ...
    
    # Database pool settings
    DB_POOL_SIZE = 5
    DB_POOL_OVERFLOW = 10
    DB_POOL_TIMEOUT = 30
    DB_POOL_RECYCLE = 3600
```

## 🔐 Security Best Practices

### 1. Environment Variables

Create a `.env` file for sensitive data:

```bash
# Create environment file
cat > .env << 'EOF'
SECRET_KEY=your-super-secret-production-key-here
DB_HOST=los-dev-psql-rdsclstr-new.cj6duvm27hk9.us-east-1.rds.amazonaws.com
DB_PORT=3306
DB_USER=postgres
DB_PASSWORD=poc2*&(SRWSjnjkn@#@#
DB_NAME=postgres
EOF

# Secure the file
chmod 600 .env
```

### 2. Database User Permissions

Consider creating a dedicated database user with limited permissions:

```sql
-- Connect as postgres user
CREATE USER quiz_app_user WITH PASSWORD 'strong_password_here';

-- Grant necessary permissions
GRANT CONNECT ON DATABASE postgres TO quiz_app_user;
GRANT USAGE ON SCHEMA public TO quiz_app_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO quiz_app_user;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO quiz_app_user;
```

### 3. SSL Connection (Recommended)

Enable SSL for database connections:

```python
# In your database connection code
conn = psycopg2.connect(
    host=Config.DB_HOST,
    port=Config.DB_PORT,
    user=Config.DB_USER,
    password=Config.DB_PASSWORD,
    database=Config.DB_NAME,
    sslmode='require'  # Require SSL connection
)
```

## ✅ Final Verification Checklist

- [ ] EC2 can ping RDS hostname
- [ ] Port 3306 is reachable from EC2 to RDS
- [ ] Python can connect to database successfully
- [ ] Required tables exist (users, aws_questions, quiz_sessions)
- [ ] Questions are loaded (both categories)
- [ ] Application starts without database errors
- [ ] Quiz functionality works end-to-end

## 📞 Need Help?

If you encounter issues:

1. **Check application logs:** `sudo tail -f /var/log/aws-quiz-website.log`
2. **Check supervisor status:** `sudo supervisorctl status aws-quiz-website`
3. **Test database connection** using the Python script above
4. **Verify security groups** in AWS console
5. **Check network connectivity** using ping/telnet

Remember: The most common issue is security group configuration. Make sure your EC2 security group allows outbound traffic on port 3306, and your RDS security group allows inbound traffic on port 3306 from your EC2 instance.
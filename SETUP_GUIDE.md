# AWS Quiz Website - Setup Guide

## QUICK START (3 Steps)

### Step 1: Setup Database
```bash
python setup_database.py
```

### Step 2: Import Questions
```bash
python import_csv_data.py
```

### Step 3: Run Application
```bash
python app.py
```

Visit: `http://localhost:5000`

---

## TROUBLESHOOTING

### Problem: Cannot Login

**Solution 1 - Run Diagnostic**
```bash
python diagnose_and_fix.py
```
This shows:
- Total users in database
- Total questions
- Table structure
- Missing columns

**Solution 2 - Check Your Credentials**
- Email must be lowercase
- Use the exact password you registered with

**Solution 3 - Verify Database**
Make sure `config.py` has correct settings:
- DB_HOST: `los-dev-psql-rdsclstr-new.cj6duvm27hk9.us-east-1.rds.amazonaws.com`
- DB_PORT: `3306`
- DB_NAME: `cretificate_quiz_db`

### Problem: No Questions Appearing

**Solution 1 - Check Questions**
```bash
python diagnose_and_fix.py
```
Look for "Total questions" - should be > 0

**Solution 2 - Re-import Questions**
```bash
python import_csv_data.py
```

**Solution 3 - Verify Categories**
Questions must have category:
- `AWS Cloud Practitioner`
- `AWS Data Engineer`

---

## ESSENTIAL FILES

### Keep These:
- ✅ `app.py` - Main application
- ✅ `config.py` - Configuration
- ✅ `wsgi.py` - Production server
- ✅ `requirements.txt` - Dependencies
- ✅ `setup_database.py` - Database setup
- ✅ `import_csv_data.py` - Question importer
- ✅ `diagnose_and_fix.py` - Diagnostic tool
- ✅ `database_schema.sql` - Schema reference
- ✅ `templates/` - All HTML pages
- ✅ `static/` - CSS, JS, images

### Removed (Cleanup Done):
- ❌ `deploy_ec2.sh` - EC2 deployment
- ❌ `EC2_DEPLOYMENT_GUIDE.md` - EC2 guide
- ❌ `deploy.sh` - Generic deployment
- ❌ `quick_setup.sh` - Old setup
- ❌ `simple_setup.sh` - Old setup
- ❌ `start.bat` - Old starter
- ❌ `migrate_*.py` - Old migrations
- ❌ `setup_local_database.py` - Duplicate
- ❌ `check_categories.py` - Old diagnostic
- ❌ `test_app.py` - Old tests

---

## DATABASE TABLES

The application uses these tables:

1. **users** - User accounts
   - id, username, email, password_hash
   - is_active, is_admin, created_at, last_login

2. **questions** - Quiz questions
   - id, question_id, question, options (a-e)
   - correct_answer, explanation, category

3. **quiz_sessions** - Quiz attempts
   - id, user_id, category, score_percentage
   - start_time, end_time, total_questions

4. **user_answers** - Individual answers
   - id, session_id, question_id
   - user_answer, is_correct

5. **badges** - Achievements
   - id, name, description, icon, criteria

6. **user_badges** - User achievements
   - user_id, badge_id, awarded_at

---

## FRESH START (If Needed)

If everything is broken, do this:

```bash
# 1. Setup database fresh
python setup_database.py

# 2. Import questions
python import_csv_data.py

# 3. Create your account
python app.py
# Then register at http://localhost:5000

# 4. (Optional) Create admin account
python create_admin.py
```

---

## SUPPORT

If you still have issues after trying the above:

1. Run diagnostic: `python diagnose_and_fix.py`
2. Check output for specific errors
3. Verify database credentials in `config.py`
4. Check that PostgreSQL is running
5. Ensure port 3306 is accessible

---

## DATABASE CONNECTION

The app connects to AWS RDS PostgreSQL on a custom port (3306).

Connection details in `config.py`:
```python
DB_HOST = 'los-dev-psql-rdsclstr-new.cj6duvm27hk9.us-east-1.rds.amazonaws.com'
DB_PORT = 3306  # Custom PostgreSQL port
DB_NAME = 'cretificate_quiz_db'
DB_USER = 'postgres'
DB_PASSWORD = 'poc2*&(SRWSjnjkn@#@#'
```

---

## NEXT STEPS AFTER SETUP

1. ✅ Register an account
2. ✅ Login
3. ✅ Take a quiz
4. ✅ View your results
5. ✅ Check leaderboard
6. ✅ Earn badges

For admin features:
```bash
python create_admin.py
```

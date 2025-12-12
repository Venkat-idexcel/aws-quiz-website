# User Password Reset Guide

## Quick Commands

### 1. List All Users
```bash
python manage_user_passwords.py --list
```
This shows all users with their ID, username, email, admin status, and creation date.

### 2. Search for a User
```bash
python manage_user_passwords.py --search "john"
```
Searches for users by username or email (partial match works).

### 3. Reset Password by Email (Interactive)
```bash
python manage_user_passwords.py --email user@example.com
```
Will prompt you to enter a new password or press Enter to generate a secure one.

### 4. Reset Password by Email (Direct)
```bash
python manage_user_passwords.py --email user@example.com --password "NewPass123!"
```
Directly sets the password to the specified value.

### 5. Reset with Auto-Generated Secure Password
```bash
python manage_user_passwords.py --email user@example.com --generate
```
Automatically generates a strong, random password.

### 6. Reset Password by Username
```bash
python manage_user_passwords.py --username johndoe --password "NewPass123!"
```
Same as email reset, but uses username instead.

### 7. Bulk Reset from CSV File
```bash
python manage_user_passwords.py --csv passwords.csv
```

CSV file format:
```csv
email,password
user1@example.com,NewPass123!
user2@example.com,AnotherPass456@
```

## Alternative: Using the Old Simple Script

If you prefer the simpler original script:
```bash
python reset_user_password.py --email user@example.com --password "NewPass123!"
```

## Web-Based Password Reset

Users can also reset their own passwords through the web interface:

1. Go to the login page
2. Click "Forgot Password?"
3. Enter their email address
4. They will receive a reset link via email (if email is configured)

## Admin Password Reset via Web

If you're an admin user:
1. Log in to the admin dashboard
2. Go to "User Management"
3. Find the user and click "Reset Password"
4. Enter the new password

## Security Tips

### Strong Password Requirements
A good password should have:
- At least 8 characters (12+ recommended)
- Uppercase letters (A-Z)
- Lowercase letters (a-z)
- Numbers (0-9)
- Special characters (!@#$%^&*)

### Example Strong Passwords
- `MyQuiz2024!Pass`
- `Secure@Quiz123`
- `Learning#2024$`

### Password Distribution
When resetting passwords for users:
1. ✅ Use the `--generate` flag for secure random passwords
2. ✅ Share passwords through secure channels (encrypted email, Slack DM)
3. ✅ Ask users to change password after first login
4. ❌ Don't share passwords in plain text files
5. ❌ Don't send passwords via regular email if possible

## Common Issues & Solutions

### Issue: "No user found with email"
**Solution:** Check if the email is correct and exists in the database:
```bash
python manage_user_passwords.py --search "user@example.com"
```

### Issue: "Database connection error"
**Solution:** Verify database credentials in `config.py` are correct.

### Issue: User still can't login after reset
**Solution:** 
1. Verify the password was set correctly
2. Check if the user account is active
3. Look at application logs for authentication errors

### Issue: Need to reset password on production server
**Solution:**
1. SSH into the EC2 instance
2. Navigate to the application directory:
   ```bash
   cd /var/www/aws-quiz-app
   source venv/bin/activate
   ```
3. Run the password reset script:
   ```bash
   python manage_user_passwords.py --email user@example.com --generate
   ```

## Examples for Common Scenarios

### Scenario 1: User forgot password
```bash
# Search for the user first
python manage_user_passwords.py --search "john"

# Reset with a generated password
python manage_user_passwords.py --email john.doe@example.com --generate

# Output will show the new password - share it with the user securely
```

### Scenario 2: New employee needs access
```bash
# Generate a secure temporary password
python manage_user_passwords.py --email newemployee@example.com --generate

# The user should change this on first login
```

### Scenario 3: Security incident - reset all admin passwords
Create a CSV file `admin_resets.csv`:
```csv
email,password
admin1@example.com,TempSecure1!Pass
admin2@example.com,TempSecure2@Pass
admin3@example.com,TempSecure3#Pass
```

Then run:
```bash
python manage_user_passwords.py --csv admin_resets.csv
```

### Scenario 4: Testing/Development
```bash
# Reset test user to a known password
python manage_user_passwords.py --email test@example.com --password "test123"
```

## Database Direct Access (Advanced)

If scripts don't work, you can reset passwords directly in PostgreSQL:

```sql
-- Connect to database
psql -h los-dev-psql-rdsclstr-new.cj6duvm27hk9.us-east-1.rds.amazonaws.com \
     -U postgres -d cretificate_quiz_db

-- Find user
SELECT id, username, email FROM users WHERE email = 'user@example.com';

-- Generate password hash (use Python):
python3 -c "from werkzeug.security import generate_password_hash; print(generate_password_hash('NewPassword123!'))"

-- Update password (replace USER_ID and HASH)
UPDATE users SET password_hash = 'scrypt:...' WHERE id = USER_ID;
```

## Troubleshooting

### Check if user exists
```bash
python manage_user_passwords.py --list | grep "user@example.com"
```

### View recent password reset activities
Check application logs:
```bash
# On EC2 instance
sudo journalctl -u aws-quiz-app | grep password
```

### Test new password immediately
After resetting, test the login through the web interface to ensure it works.

## Need Help?

If you encounter issues:
1. Check the application logs
2. Verify database connectivity
3. Ensure the user account exists
4. Check if the email/username is correct (case-sensitive for username)
5. Make sure the database credentials in `config.py` are up to date
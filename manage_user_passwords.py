#!/usr/bin/env python3
"""
Enhanced User Password Reset Tool for AWS Quiz Website
Supports multiple ways to reset user passwords with improved security and usability

Usage Examples:
  1. Reset by email (interactive):
     python manage_user_passwords.py --email user@example.com
  
  2. Reset by email with new password:
     python manage_user_passwords.py --email user@example.com --password NewPass123!
  
  3. Reset by username:
     python manage_user_passwords.py --username johndoe --password NewPass123!
  
  4. List all users:
     python manage_user_passwords.py --list
  
  5. Search for users:
     python manage_user_passwords.py --search john
  
  6. Reset multiple users from CSV:
     python manage_user_passwords.py --csv passwords.csv
     (CSV format: email,new_password)
  
  7. Generate random secure password:
     python manage_user_passwords.py --email user@example.com --generate
"""

import argparse
import psycopg2
import sys
import getpass
import secrets
import string
import csv
from werkzeug.security import generate_password_hash
from config import Config

def get_db_connection():
    """Get database connection using config"""
    try:
        config = Config()
        conn = psycopg2.connect(
            host=config.DB_HOST,
            port=config.DB_PORT,
            database=config.DB_NAME,
            user=config.DB_USER,
            password=config.DB_PASSWORD,
            connect_timeout=10
        )
        return conn
    except Exception as e:
        print(f"❌ Database connection error: {e}")
        return None

def generate_secure_password(length=12):
    """Generate a secure random password"""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    password = ''.join(secrets.choice(alphabet) for _ in range(length))
    # Ensure it has at least one of each type
    if not any(c.islower() for c in password):
        password = secrets.choice(string.ascii_lowercase) + password[1:]
    if not any(c.isupper() for c in password):
        password = secrets.choice(string.ascii_uppercase) + password[1:]
    if not any(c.isdigit() for c in password):
        password = secrets.choice(string.digits) + password[1:]
    if not any(c in "!@#$%^&*" for c in password):
        password = secrets.choice("!@#$%^&*") + password[1:]
    return password

def list_users():
    """List all users in the database"""
    conn = get_db_connection()
    if not conn:
        return
    
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT id, username, email, created_at, is_admin 
            FROM users 
            ORDER BY created_at DESC
        """)
        users = cur.fetchall()
        
        if not users:
            print("❌ No users found in database")
            return
        
        print(f"\n📋 Total Users: {len(users)}")
        print("-" * 100)
        print(f"{'ID':<6} {'Username':<20} {'Email':<35} {'Admin':<7} {'Created':<20}")
        print("-" * 100)
        
        for user in users:
            user_id, username, email, created_at, is_admin = user
            admin_status = "✅ Yes" if is_admin else "❌ No"
            created = str(created_at)[:19] if created_at else "N/A"
            print(f"{user_id:<6} {username[:19]:<20} {email[:34]:<35} {admin_status:<7} {created:<20}")
        
        print("-" * 100)
        
    except Exception as e:
        print(f"❌ Error listing users: {e}")
    finally:
        cur.close()
        conn.close()

def search_users(search_term):
    """Search for users by username or email"""
    conn = get_db_connection()
    if not conn:
        return []
    
    try:
        cur = conn.cursor()
        search_pattern = f"%{search_term}%"
        cur.execute("""
            SELECT id, username, email, is_admin 
            FROM users 
            WHERE username ILIKE %s OR email ILIKE %s
            ORDER BY username
        """, (search_pattern, search_pattern))
        users = cur.fetchall()
        
        if not users:
            print(f"❌ No users found matching '{search_term}'")
            return []
        
        print(f"\n🔍 Found {len(users)} user(s) matching '{search_term}':")
        print("-" * 80)
        print(f"{'ID':<6} {'Username':<20} {'Email':<35} {'Admin':<7}")
        print("-" * 80)
        
        for user in users:
            user_id, username, email, is_admin = user
            admin_status = "✅ Yes" if is_admin else "❌ No"
            print(f"{user_id:<6} {username[:19]:<20} {email[:34]:<35} {admin_status:<7}")
        
        print("-" * 80)
        return users
        
    except Exception as e:
        print(f"❌ Error searching users: {e}")
        return []
    finally:
        cur.close()
        conn.close()

def reset_password_by_email(email, new_password=None, generate_pass=False):
    """Reset password for a user by email"""
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        cur = conn.cursor()
        
        # Find user
        cur.execute('SELECT id, username, email FROM users WHERE email = %s', (email.lower(),))
        user = cur.fetchone()
        
        if not user:
            print(f"❌ No user found with email: {email}")
            return False
        
        user_id, username, user_email = user
        print(f"\n✅ Found user: {username} ({user_email})")
        
        # Get or generate password
        if generate_pass:
            new_password = generate_secure_password()
            print(f"🔑 Generated secure password: {new_password}")
        elif not new_password:
            print("\nEnter new password (or press Enter to generate a secure one):")
            new_password = getpass.getpass("New password: ")
            if not new_password:
                new_password = generate_secure_password()
                print(f"🔑 Generated secure password: {new_password}")
            else:
                confirm_password = getpass.getpass("Confirm password: ")
                if new_password != confirm_password:
                    print("❌ Passwords don't match!")
                    return False
        
        # Hash and update password
        password_hash = generate_password_hash(new_password)
        cur.execute('UPDATE users SET password_hash = %s WHERE id = %s', (password_hash, user_id))
        conn.commit()
        
        print(f"\n✅ Password successfully reset for {user_email}")
        print(f"   Username: {username}")
        print(f"   New Password: {new_password}")
        print(f"\n⚠️  Make sure to share this password securely with the user!")
        
        return True
        
    except Exception as e:
        print(f"❌ Error resetting password: {e}")
        return False
    finally:
        cur.close()
        conn.close()

def reset_password_by_username(username, new_password=None, generate_pass=False):
    """Reset password for a user by username"""
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        cur = conn.cursor()
        
        # Find user
        cur.execute('SELECT id, username, email FROM users WHERE username = %s', (username,))
        user = cur.fetchone()
        
        if not user:
            print(f"❌ No user found with username: {username}")
            return False
        
        user_id, username, user_email = user
        print(f"\n✅ Found user: {username} ({user_email})")
        
        # Get or generate password
        if generate_pass:
            new_password = generate_secure_password()
            print(f"🔑 Generated secure password: {new_password}")
        elif not new_password:
            print("\nEnter new password (or press Enter to generate a secure one):")
            new_password = getpass.getpass("New password: ")
            if not new_password:
                new_password = generate_secure_password()
                print(f"🔑 Generated secure password: {new_password}")
            else:
                confirm_password = getpass.getpass("Confirm password: ")
                if new_password != confirm_password:
                    print("❌ Passwords don't match!")
                    return False
        
        # Hash and update password
        password_hash = generate_password_hash(new_password)
        cur.execute('UPDATE users SET password_hash = %s WHERE id = %s', (password_hash, user_id))
        conn.commit()
        
        print(f"\n✅ Password successfully reset for {username}")
        print(f"   Email: {user_email}")
        print(f"   New Password: {new_password}")
        print(f"\n⚠️  Make sure to share this password securely with the user!")
        
        return True
        
    except Exception as e:
        print(f"❌ Error resetting password: {e}")
        return False
    finally:
        cur.close()
        conn.close()

def reset_passwords_from_csv(csv_file):
    """Reset passwords for multiple users from a CSV file"""
    try:
        with open(csv_file, 'r') as f:
            reader = csv.DictReader(f)
            
            if 'email' not in reader.fieldnames or 'password' not in reader.fieldnames:
                print("❌ CSV file must have 'email' and 'password' columns")
                return
            
            success_count = 0
            fail_count = 0
            
            print(f"\n📄 Processing CSV file: {csv_file}")
            print("-" * 80)
            
            for row in reader:
                email = row['email'].strip()
                password = row['password'].strip()
                
                if not email or not password:
                    print(f"⚠️  Skipping row with empty email or password")
                    fail_count += 1
                    continue
                
                print(f"\nProcessing: {email}")
                if reset_password_by_email(email, password):
                    success_count += 1
                else:
                    fail_count += 1
            
            print("\n" + "=" * 80)
            print(f"📊 Summary:")
            print(f"   ✅ Successful: {success_count}")
            print(f"   ❌ Failed: {fail_count}")
            print(f"   📋 Total: {success_count + fail_count}")
            
    except FileNotFoundError:
        print(f"❌ File not found: {csv_file}")
    except Exception as e:
        print(f"❌ Error processing CSV: {e}")

def main():
    parser = argparse.ArgumentParser(
        description='Enhanced User Password Reset Tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument('--email', help='User email address')
    parser.add_argument('--username', help='Username')
    parser.add_argument('--password', help='New password (leave empty for interactive prompt)')
    parser.add_argument('--generate', action='store_true', help='Generate a secure random password')
    parser.add_argument('--list', action='store_true', help='List all users')
    parser.add_argument('--search', help='Search for users by username or email')
    parser.add_argument('--csv', help='Reset passwords from CSV file (format: email,password)')
    
    args = parser.parse_args()
    
    print("=" * 80)
    print("🔐 AWS Quiz Website - Password Reset Tool")
    print("=" * 80)
    
    # List users
    if args.list:
        list_users()
        return
    
    # Search users
    if args.search:
        search_users(args.search)
        return
    
    # Reset from CSV
    if args.csv:
        reset_passwords_from_csv(args.csv)
        return
    
    # Reset by email
    if args.email:
        reset_password_by_email(args.email, args.password, args.generate)
        return
    
    # Reset by username
    if args.username:
        reset_password_by_username(args.username, args.password, args.generate)
        return
    
    # No valid arguments provided
    parser.print_help()
    print("\n💡 Examples:")
    print("  python manage_user_passwords.py --list")
    print("  python manage_user_passwords.py --email user@example.com --generate")
    print("  python manage_user_passwords.py --username johndoe --password NewPass123!")
    print("  python manage_user_passwords.py --search john")

if __name__ == '__main__':
    main()

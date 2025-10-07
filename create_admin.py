#!/usr/bin/env python3
"""
Admin User Creation Script
Creates a new admin user for the quiz application
"""

import psycopg2
import psycopg2.extras
from werkzeug.security import generate_password_hash
from datetime import datetime
import getpass
import re

# Database Configuration (AWS RDS)
DB_CONFIG = {
    'host': 'los-dev-psql-rdsclstr-new.cj6duvm27hk9.us-east-1.rds.amazonaws.com',
    'port': 3306,
    'database': 'cretificate_quiz_db',
    'user': 'postgres',
    'password': 'poc2*&(SRWSjnjkn@#@#'
}

def validate_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_username(username):
    """Validate username format"""
    # Username should be 3-50 characters, letters, numbers, and underscores only
    pattern = r'^[a-zA-Z0-9_]{3,50}$'
    return re.match(pattern, username) is not None

def check_existing_user(conn, username, email):
    """Check if user already exists"""
    try:
        cur = conn.cursor()
        cur.execute("SELECT id, username, email, is_admin FROM users WHERE username = %s OR email = %s", 
                   (username, email))
        return cur.fetchone()
    except Exception as e:
        print(f"Error checking existing user: {e}")
        return None

def create_admin_user():
    """Create a new admin user"""
    print("🔐 Admin User Creation Wizard")
    print("=" * 40)
    
    # Connect to database
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        print("✅ Connected to database")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False
    
    try:
        # Get user input
        print("\nPlease provide the following information:")
        
        # Username
        while True:
            username = input("Username (3-50 chars, letters/numbers/underscore): ").strip()
            if not username:
                print("❌ Username cannot be empty")
                continue
            if not validate_username(username):
                print("❌ Invalid username format")
                continue
            break
        
        # Email
        while True:
            email = input("Email address: ").strip().lower()
            if not email:
                print("❌ Email cannot be empty")
                continue
            if not validate_email(email):
                print("❌ Invalid email format")
                continue
            break
        
        # Check if user already exists
        existing = check_existing_user(conn, username, email)
        if existing:
            user_id, existing_username, existing_email, is_admin = existing
            print(f"\n⚠️ User already exists:")
            print(f"   ID: {user_id}")
            print(f"   Username: {existing_username}")
            print(f"   Email: {existing_email}")
            print(f"   Is Admin: {'Yes' if is_admin else 'No'}")
            
            if is_admin:
                print("✅ This user is already an admin!")
                return True
            else:
                response = input("Make this user an admin? (yes/no): ").lower()
                if response in ['yes', 'y']:
                    cur = conn.cursor()
                    cur.execute("UPDATE users SET is_admin = TRUE WHERE id = %s", (user_id,))
                    conn.commit()
                    print("✅ User promoted to admin successfully!")
                    return True
                else:
                    print("❌ Operation cancelled")
                    return False
        
        # First name
        while True:
            first_name = input("First name: ").strip()
            if not first_name:
                print("❌ First name cannot be empty")
                continue
            if len(first_name) > 50:
                print("❌ First name too long (max 50 characters)")
                continue
            break
        
        # Last name
        while True:
            last_name = input("Last name: ").strip()
            if not last_name:
                print("❌ Last name cannot be empty")
                continue
            if len(last_name) > 50:
                print("❌ Last name too long (max 50 characters)")
                continue
            break
        
        # Password
        while True:
            password = getpass.getpass("Password (min 8 characters): ")
            if not password:
                print("❌ Password cannot be empty")
                continue
            if len(password) < 8:
                print("❌ Password must be at least 8 characters")
                continue
            
            confirm_password = getpass.getpass("Confirm password: ")
            if password != confirm_password:
                print("❌ Passwords don't match")
                continue
            break
        
        # Show summary
        print(f"\n📋 Admin User Summary:")
        print(f"Username: {username}")
        print(f"Email: {email}")
        print(f"Name: {first_name} {last_name}")
        print(f"Role: Administrator")
        
        # Confirm creation
        confirm = input("\nCreate this admin user? (yes/no): ").lower()
        if confirm not in ['yes', 'y']:
            print("❌ Admin creation cancelled")
            return False
        
        # Create the admin user
        cur = conn.cursor()
        password_hash = generate_password_hash(password)
        
        cur.execute("""
            INSERT INTO users (username, email, password_hash, first_name, last_name, is_admin, created_at)
            VALUES (%s, %s, %s, %s, %s, TRUE, %s)
            RETURNING id
        """, (username, email, password_hash, first_name, last_name, datetime.now()))
        
        admin_id = cur.fetchone()[0]
        conn.commit()
        
        print(f"\n🎉 Admin user created successfully!")
        print(f"   Admin ID: {admin_id}")
        print(f"   Username: {username}")
        print(f"   Email: {email}")
        print(f"\n✅ You can now log in with these credentials and access the admin panel.")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating admin user: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def list_existing_admins():
    """List all existing admin users"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        cur.execute("""
            SELECT id, username, email, first_name, last_name, created_at, last_login, is_active
            FROM users 
            WHERE is_admin = TRUE 
            ORDER BY created_at DESC
        """)
        
        admins = cur.fetchall()
        conn.close()
        
        if admins:
            print(f"\n👥 Existing Admin Users ({len(admins)}):")
            print("-" * 80)
            for admin in admins:
                status = "🟢 Active" if admin['is_active'] else "🔴 Inactive"
                last_login = admin['last_login'].strftime('%Y-%m-%d %H:%M') if admin['last_login'] else "Never"
                created = admin['created_at'].strftime('%Y-%m-%d %H:%M') if admin['created_at'] else "Unknown"
                
                print(f"ID: {admin['id']} | {admin['username']} ({admin['first_name']} {admin['last_name']})")
                print(f"   Email: {admin['email']}")
                print(f"   Status: {status} | Created: {created} | Last Login: {last_login}")
                print()
        else:
            print("\n📭 No admin users found")
            
    except Exception as e:
        print(f"❌ Error listing admins: {e}")

def main():
    """Main function"""
    print("🚀 Quiz Application - Admin Management")
    print("=" * 50)
    
    while True:
        print("\nOptions:")
        print("1. Create new admin user")
        print("2. List existing admin users")
        print("3. Exit")
        
        choice = input("\nSelect an option (1-3): ").strip()
        
        if choice == '1':
            create_admin_user()
        elif choice == '2':
            list_existing_admins()
        elif choice == '3':
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice. Please select 1, 2, or 3.")

if __name__ == "__main__":
    main()
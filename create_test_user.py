#!/usr/bin/env python3
"""
Simple script to create a test user account
"""

import psycopg2
from werkzeug.security import generate_password_hash
from datetime import datetime

# Database Configuration
DB_CONFIG = {
    'host': 'los-dev-psql-rdsclstr-new.cj6duvm27hk9.us-east-1.rds.amazonaws.com',
    'port': 3306,
    'database': 'cretificate_quiz_db',
    'user': 'postgres',
    'password': 'poc2*&(SRWSjnjkn@#@#'
}

def create_test_user():
    """Create a simple test user for AWS Data Engineer quiz testing"""
    
    user_data = {
        'username': 'testuser',
        'email': 'test@example.com',
        'password': 'password123',
        'first_name': 'Test',
        'last_name': 'User'
    }
    
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        # Check if user already exists
        cur.execute("SELECT id FROM users WHERE username = %s OR email = %s", 
                   (user_data['username'], user_data['email']))
        existing_user = cur.fetchone()
        
        if existing_user:
            print(f"✅ Test user '{user_data['username']}' already exists")
            print(f"   Email: {user_data['email']}")
            print(f"   Password: {user_data['password']}")
            return
        
        # Hash the password
        password_hash = generate_password_hash(user_data['password'])
        
        # Insert new user
        cur.execute("""
            INSERT INTO users (username, email, password_hash, first_name, last_name, created_at, is_active, is_admin)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (
            user_data['username'],
            user_data['email'], 
            password_hash,
            user_data['first_name'],
            user_data['last_name'],
            datetime.now(),
            True,
            False
        ))
        
        user_id = cur.fetchone()[0]
        conn.commit()
        
        print(f"✅ Test user created successfully!")
        print(f"   User ID: {user_id}")
        print(f"   Username: {user_data['username']}")
        print(f"   Email: {user_data['email']}")
        print(f"   Password: {user_data['password']}")
        print("\n🎯 Now you can:")
        print("   1. Go to http://localhost:5000")
        print("   2. Login with the above credentials")
        print("   3. Click on 'AWS Data Engineer' quiz")
        print("   4. Configure and start the quiz")
        
    except Exception as e:
        print(f"❌ Error creating test user: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    create_test_user()
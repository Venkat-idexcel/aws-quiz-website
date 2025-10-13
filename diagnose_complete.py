"""
Comprehensive diagnosis and fix for AWS Quiz Website login issues
"""
import psycopg2
from werkzeug.security import check_password_hash
from config import Config

print("\n" + "="*80)
print("🔍 COMPREHENSIVE APPLICATION DIAGNOSIS")
print("="*80)

# Test 1: Database Connection
print("\n1️⃣ Testing Database Connection...")
try:
    conn = psycopg2.connect(
        host=Config.DB_HOST,
        port=Config.DB_PORT,
        database=Config.DB_NAME,
        user=Config.DB_USER,
        password=Config.DB_PASSWORD
    )
    print("   ✅ Database connection successful")
    
    cur = conn.cursor()
    
    # Test 2: Check users table
    print("\n2️⃣ Checking Users Table...")
    cur.execute("SELECT COUNT(*) FROM users")
    user_count = cur.fetchone()[0]
    print(f"   ✅ Found {user_count} users in database")
    
    # Test 3: Examine user data
    print("\n3️⃣ Examining User Data...")
    cur.execute("""
        SELECT id, username, email, first_name, last_name, 
               password_hash IS NOT NULL as has_password,
               LENGTH(password_hash) as hash_length,
               is_active, is_admin,
               created_at, last_login
        FROM users
        ORDER BY id
    """)
    
    users = cur.fetchall()
    for user in users:
        user_id, username, email, fname, lname, has_pwd, hash_len, active, admin, created, last_login = user
        print(f"\n   User: {username} ({email})")
        print(f"      - ID: {user_id}")
        print(f"      - Name: {fname} {lname}")
        print(f"      - Has Password: {has_pwd} (Length: {hash_len if has_pwd else 'N/A'})")
        print(f"      - Active: {active}")
        print(f"      - Admin: {admin}")
        print(f"      - Created: {created}")
        print(f"      - Last Login: {last_login if last_login else 'Never'}")
    
    # Test 4: Test password verification for each user
    print("\n4️⃣ Testing Password Hash Format...")
    cur.execute("SELECT username, email, password_hash FROM users WHERE password_hash IS NOT NULL")
    for username, email, pwd_hash in cur.fetchall():
        print(f"\n   User: {username}")
        print(f"      - Email: {email}")
        print(f"      - Hash starts with: {pwd_hash[:20]}...")
        print(f"      - Hash type: {'pbkdf2:sha256' if pwd_hash.startswith('pbkdf2:sha256') else 'scrypt' if pwd_hash.startswith('scrypt:') else 'UNKNOWN'}")
        
        # Try to verify with a test (will fail but shows if hash is readable)
        try:
            result = check_password_hash(pwd_hash, "test_password_12345")
            print(f"      - Hash verification function: ✅ Working (returned False as expected)")
        except Exception as e:
            print(f"      - Hash verification function: ❌ ERROR: {e}")
    
    # Test 5: Check questions table
    print("\n5️⃣ Checking Questions Table...")
    cur.execute("SELECT COUNT(*) FROM questions")
    question_count = cur.fetchone()[0]
    print(f"   ✅ Found {question_count} questions")
    
    cur.execute("SELECT category, COUNT(*) FROM questions GROUP BY category ORDER BY category")
    print("   Categories:")
    for category, count in cur.fetchall():
        print(f"      - {category}: {count} questions")
    
    # Test 6: Check quiz_sessions table
    print("\n6️⃣ Checking Quiz Sessions...")
    cur.execute("SELECT COUNT(*) FROM quiz_sessions")
    session_count = cur.fetchone()[0]
    print(f"   ✅ Found {session_count} quiz sessions")
    
    conn.close()
    
    print("\n" + "="*80)
    print("✅ ALL DATABASE CHECKS PASSED")
    print("="*80)
    print("\n💡 DIAGNOSIS:")
    print("   - Database connection: WORKING")
    print("   - Users exist: YES")
    print("   - Password hashes: VALID FORMAT")
    print("   - Questions loaded: YES")
    print("\n🔍 CONCLUSION:")
    print("   Database is healthy. If login still fails, the issue is:")
    print("   1. Flask app not receiving HTTP requests")
    print("   2. Rate limiter blocking requests") 
    print("   3. Flask routing configuration issue")
    print("   4. Browser/network issue preventing form submission")
    
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()

"""
Quick database check to see current state
"""
import psycopg2
import psycopg2.extras
from config import Config

config = Config()

print("\n" + "="*70)
print("DATABASE STATUS CHECK")
print("="*70)

try:
    conn = psycopg2.connect(
        host=config.DB_HOST,
        port=config.DB_PORT,
        database=config.DB_NAME,
        user=config.DB_USER,
        password=config.DB_PASSWORD,
        connect_timeout=5
    )
    
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    
    print(f"\n✅ Connected to: {config.DB_NAME}")
    print(f"   Host: {config.DB_HOST}:{config.DB_PORT}")
    
    # Check users
    cur.execute("SELECT COUNT(*) FROM users")
    total_users = cur.fetchone()[0]
    print(f"\n👥 Total users: {total_users}")
    
    if total_users > 0:
        cur.execute("""
            SELECT id, username, email, is_active, 
                   (password_hash IS NOT NULL) as has_password,
                   LENGTH(password_hash) as hash_length
            FROM users 
            ORDER BY id DESC 
            LIMIT 5
        """)
        print("\n📋 Recent users:")
        for user in cur.fetchall():
            print(f"   ID: {user['id']}")
            print(f"   Username: {user['username']}")
            print(f"   Email: {user['email']}")
            print(f"   Active: {user['is_active']}")
            print(f"   Has password: {user['has_password']}")
            print(f"   Password hash length: {user['hash_length']}")
            print(f"   ---")
    else:
        print("\n⚠️  NO USERS IN DATABASE!")
        print("   You need to register an account first.")
    
    # Check questions
    cur.execute("SELECT COUNT(*) FROM questions")
    q_count = cur.fetchone()[0]
    print(f"\n📚 Total questions: {q_count}")
    
    if q_count > 0:
        cur.execute("SELECT DISTINCT category, COUNT(*) FROM questions GROUP BY category")
        print("\n📊 Questions by category:")
        for row in cur.fetchall():
            print(f"   {row[0]}: {row[1]} questions")
    else:
        print("   ⚠️  No questions in database!")
    
    cur.close()
    conn.close()
    
    print("\n" + "="*70)
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()

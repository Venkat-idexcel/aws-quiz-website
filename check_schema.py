import psycopg2
from config import Config

conn = psycopg2.connect(
    host=Config.DB_HOST,
    port=Config.DB_PORT,
    database=Config.DB_NAME,
    user=Config.DB_USER,
    password=Config.DB_PASSWORD
)

cur = conn.cursor()

# Get users table schema
cur.execute("""
    SELECT column_name, data_type, is_nullable 
    FROM information_schema.columns 
    WHERE table_name='users' 
    ORDER BY ordinal_position
""")

print("\n📋 Users Table Schema:")
print("="*60)
for col_name, data_type, nullable in cur.fetchall():
    print(f"  {col_name:20} {data_type:15} {'NULL' if nullable == 'YES' else 'NOT NULL'}")

# Check if last_login exists
cur.execute("""
    SELECT COUNT(*) 
    FROM information_schema.columns 
    WHERE table_name='users' AND column_name='last_login'
""")
has_last_login = cur.fetchone()[0] > 0

print(f"\n✅ last_login column exists: {has_last_login}")

# Get sample user data
cur.execute("SELECT id, username, email, password_hash FROM users LIMIT 5")
print("\n👤 Sample Users:")
print("="*60)
for user_id, username, email, pwd_hash in cur.fetchall():
    print(f"\nID: {user_id}")
    print(f"  Username: {username}")
    print(f"  Email: {email}")
    print(f"  Password hash: {pwd_hash[:50] if pwd_hash else 'NULL'}...")

conn.close()

import psycopg2
import psycopg2.extras
from config import Config

def check_admin_users():
    """Check which users are marked as admin"""
    try:
        conn = psycopg2.connect(
            dbname=Config.DB_NAME,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            host=Config.DB_HOST,
            port=Config.DB_PORT
        )
        
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        # Get all users with is_admin status
        cur.execute("""
            SELECT id, username, email, first_name, last_name, is_admin, is_active 
            FROM users 
            ORDER BY id
        """)
        users = cur.fetchall()
        
        print("=== All Users and Admin Status ===")
        print(f"Total users: {len(users)}\n")
        
        admin_count = 0
        for user in users:
            is_admin = user['is_admin']
            if is_admin:
                admin_count += 1
                print(f"✓ ADMIN: {user['first_name']} {user['last_name']} ({user['email']})")
                print(f"  ID: {user['id']}, Username: {user['username']}, Active: {user['is_active']}")
            else:
                print(f"  User: {user['first_name']} {user['last_name']} ({user['email']})")
        
        print(f"\n=== Summary ===")
        print(f"Total users: {len(users)}")
        print(f"Admin users: {admin_count}")
        print(f"Regular users: {len(users) - admin_count}")
        
        conn.close()
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_admin_users()

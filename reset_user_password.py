#!/usr/bin/env python3
"""
Reset a user's password (CLI).
Usage:
  python reset_user_password.py --email user@example.com --password NewPass123!
"""
import argparse
import psycopg2
from werkzeug.security import generate_password_hash

DB = {
    'host': 'los-dev-psql-rdsclstr-new.cj6duvm27hk9.us-east-1.rds.amazonaws.com',
    'port': 3306,
    'dbname': 'cretificate_quiz_db',
    'user': 'postgres',
    'password': 'poc2*&(SRWSjnjkn@#@#'
}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--email', required=True, help='User email to reset')
    ap.add_argument('--password', required=True, help='New plaintext password')
    args = ap.parse_args()

    try:
        conn = psycopg2.connect(**DB, connect_timeout=5)
        cur = conn.cursor()
        cur.execute('SELECT id FROM users WHERE email=%s', (args.email.lower(),))
        row = cur.fetchone()
        if not row:
            print(f"❌ No user found with email {args.email}")
            return
        new_hash = generate_password_hash(args.password)
        cur.execute('UPDATE users SET password_hash=%s WHERE id=%s', (new_hash, row[0]))
        conn.commit()
        print(f"✅ Password reset for {args.email}")
    except Exception as e:
        print('❌ Error resetting password:', e)
    finally:
        try:
            cur.close(); conn.close()
        except Exception:
            pass

if __name__ == '__main__':
    main()

import psycopg2

print("🔥 Dropping all database tables...")

try:
    conn = psycopg2.connect(
        host='los-dev-psql-rdsclstr-new.cj6duvm27hk9.us-east-1.rds.amazonaws.com',
        port=3306, 
        database='cretificate_quiz_db',
        user='postgres',
        password='poc2*&(SRWSjnjkn@#@#'
    )
    
    cur = conn.cursor()
    
    # Get all tables in public schema
    cur.execute("""
        SELECT tablename FROM pg_tables 
        WHERE schemaname = 'public' AND tablename != 'pg_stat_statements'
    """)
    
    tables = cur.fetchall()
    
    if not tables:
        print("✅ No tables found to drop.")
    else:
        print(f"Found {len(tables)} tables to drop:")
        for table in tables:
            table_name = table[0]
            print(f"  - Dropping {table_name}...")
            cur.execute(f"DROP TABLE IF EXISTS {table_name} CASCADE")
        
        conn.commit()
        print("✅ All tables dropped successfully!")
        
except Exception as e:
    print(f"❌ Error: {e}")
finally:
    if 'conn' in locals():
        conn.close()
        print("✅ Connection closed.")
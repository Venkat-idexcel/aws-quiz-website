import psycopg2
import os

print("🚀 Creating new database tables...")

try:
    conn = psycopg2.connect(
        host='los-dev-psql-rdsclstr-new.cj6duvm27hk9.us-east-1.rds.amazonaws.com',
        port=3306, 
        database='cretificate_quiz_db',
        user='postgres',
        password='poc2*&(SRWSjnjkn@#@#'
    )
    
    cur = conn.cursor()
    
    # Read the SQL schema file
    schema_file = 'database_schema.sql'
    with open(schema_file, 'r') as f:
        sql_commands = f.read()
    
    # Execute the SQL commands
    cur.execute(sql_commands)
    conn.commit()
    
    print("✅ New database tables created successfully!")
    
    # Verify table creation
    cur.execute("""
        SELECT table_name FROM information_schema.tables 
        WHERE table_schema = 'public' 
        ORDER BY table_name
    """)
    
    tables = cur.fetchall()
    print(f"\n📊 Created {len(tables)} tables:")
    for table in tables:
        print(f"  ✓ {table[0]}")
        
except Exception as e:
    print(f"❌ Error creating tables: {e}")
finally:
    if 'conn' in locals():
        conn.close()
        print("\n✅ Connection closed.")
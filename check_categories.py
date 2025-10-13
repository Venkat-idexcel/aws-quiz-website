import psycopg2

# Database credentials
DB_HOST = 'los-dev-psql-rdsclstr-new.cj6duvm27hk9.us-east-1.rds.amazonaws.com'
DB_PORT = 3306  # Custom PostgreSQL port (AWS RDS configured on non-standard port)
DB_NAME = 'postgres'  # Use standard postgres database name
DB_USER = 'postgres'
DB_PASSWORD = 'poc2*&(SRWSjnjkn@#@#'

def check_categories():
    conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        connect_timeout=10
    )
    
    cur = conn.cursor()
    
    # Check what categories exist
    cur.execute("SELECT DISTINCT category, COUNT(*) FROM aws_questions GROUP BY category")
    results = cur.fetchall()
    
    print("Categories in database:")
    for category, count in results:
        print(f"  {category}: {count} questions")
    
    # Check if there are questions without category
    cur.execute("SELECT COUNT(*) FROM aws_questions WHERE category IS NULL OR category = ''")
    null_count = cur.fetchone()[0]
    print(f"Questions without category: {null_count}")
    
    cur.close()
    conn.close()

if __name__ == '__main__':
    check_categories()
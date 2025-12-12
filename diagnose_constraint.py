import psycopg2
import sys
from config import Config

# Simple script to diagnose the constraint issue
try:
    config = Config()
    conn = psycopg2.connect(
        host=config.DB_HOST,
        port=config.DB_PORT,
        database=config.DB_NAME,
        user=config.DB_USER,
        password=config.DB_PASSWORD
    )
    
    cur = conn.cursor()
    
    # Check the exact schema for question_id field
    cur.execute("""
        SELECT column_name, data_type, character_maximum_length 
        FROM information_schema.columns 
        WHERE table_name = 'questions' AND column_name = 'question_id'
    """)
    
    schema = cur.fetchone()
    print(f"question_id field: {schema[1]}({schema[2]})")
    
    # Check current count of Cloud Practitioner questions
    cur.execute("SELECT COUNT(*) FROM questions WHERE category = 'Cloud Practitioner Practice Test'")
    count = cur.fetchone()[0]
    print(f"Current question count: {count}")
    
    # Check what the longest question_id currently is
    cur.execute("SELECT question_id, LENGTH(question_id) FROM questions ORDER BY LENGTH(question_id) DESC, question_id DESC LIMIT 5")
    longest_ids = cur.fetchall()
    print("Longest question IDs:")
    for qid, length in longest_ids:
        print(f"  {qid} (length: {length})")
    
    # What would the next ID be?
    next_id = f"CP_{count + 1:04d}"
    print(f"Next ID would be: {next_id} (length: {len(next_id)})")
    
    if len(next_id) > schema[2]:
        print(f"PROBLEM: Next ID length ({len(next_id)}) exceeds field limit ({schema[2]})")
    
    cur.close()
    conn.close()
    
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)
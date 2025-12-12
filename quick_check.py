#!/usr/bin/env python3
from config import Config
import psycopg2

try:
    config = Config()
    conn = psycopg2.connect(
        host=config.DB_HOST, 
        port=config.DB_PORT, 
        database=config.DB_NAME, 
        user=config.DB_USER, 
        password=config.DB_PASSWORD, 
        connect_timeout=5
    )
    cur = conn.cursor()
    
    # Check total count
    cur.execute("SELECT COUNT(*) FROM questions WHERE category = 'Cloud Practitioner Practice Test'")
    count = cur.fetchone()[0]
    print(f'Total questions: {count}')
    
    # Check latest IDs
    cur.execute("SELECT question_id FROM questions WHERE category = 'Cloud Practitioner Practice Test' ORDER BY question_id DESC LIMIT 5")
    ids = cur.fetchall()
    print('Latest IDs:', [row[0] for row in ids])
    
    # Check schema
    cur.execute("SELECT column_name, data_type, character_maximum_length FROM information_schema.columns WHERE table_name='questions' AND column_name='question_id'")
    schema = cur.fetchone()
    if schema:
        print(f'question_id field: {schema[1]}({schema[2]})')
    
    conn.close()
except Exception as e:
    print(f'Error: {e}')
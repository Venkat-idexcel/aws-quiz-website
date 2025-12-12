import psycopg2
from config import Config

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
    
    # Count current questions
    cur.execute("SELECT COUNT(*) FROM questions")
    total_questions = cur.fetchone()[0]
    
    cur.execute("SELECT COUNT(*) FROM questions WHERE category = 'Cloud Practitioner Practice Test'")
    cp_questions = cur.fetchone()[0]
    
    print(f"Total questions in database: {total_questions}")
    print(f"Cloud Practitioner questions: {cp_questions}")
    
    # Get the latest question IDs
    cur.execute("""
        SELECT question_id 
        FROM questions 
        WHERE category = 'Cloud Practitioner Practice Test' 
        ORDER BY question_id DESC 
        LIMIT 10
    """)
    
    latest_questions = cur.fetchall()
    
    print("\nLatest Cloud Practitioner question IDs:")
    for row in latest_questions:
        question_id = row[0]
        print(f"  {question_id} (length: {len(question_id)})")
    
    # Check if we have any really long question IDs
    cur.execute("SELECT question_id FROM questions WHERE LENGTH(question_id) > 10 LIMIT 5")
    long_ids = cur.fetchall()
    
    if long_ids:
        print(f"\nFound questions with IDs longer than 10 characters:")
        for row in long_ids:
            question_id = row[0]
            print(f"  {question_id} (length: {len(question_id)})")
    else:
        print("\nNo questions found with IDs longer than 10 characters")
    
    # Check the schema for question_id
    cur.execute("""
        SELECT column_name, data_type, character_maximum_length 
        FROM information_schema.columns 
        WHERE table_name = 'questions' AND column_name = 'question_id'
    """)
    
    schema = cur.fetchone()
    print(f"\nSchema: question_id is {schema[1]}({schema[2]})")
    
    # What would be the next question ID?
    next_num = cp_questions + 1
    next_id = f"CP_{next_num:04d}"
    print(f"Next question ID would be: {next_id} (length: {len(next_id)})")
    
    if len(next_id) > schema[2]:
        print(f"❌ PROBLEM: Next ID '{next_id}' is {len(next_id)} chars, exceeds {schema[2]}-char limit")
    else:
        print(f"✅ Next ID '{next_id}' fits within {schema[2]}-char limit")
    
    cur.close()
    conn.close()
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
import psycopg2
from config import Config
import json

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
    
    # Get ALL fields schema
    cur.execute("""
        SELECT column_name, data_type, character_maximum_length, is_nullable
        FROM information_schema.columns 
        WHERE table_name = 'questions' 
        ORDER BY ordinal_position
    """)
    
    columns = cur.fetchall()
    print("Complete Questions table schema:")
    for col in columns:
        max_length = col[2] if col[2] else "unlimited"
        print(f"  • {col[0]}: {col[1]} ({max_length}) - nullable: {col[3]}")
    
    # Find any field with character limit of 10
    varchar_10_fields = [col for col in columns if col[2] == 10]
    if varchar_10_fields:
        print(f"\n⚠️ Fields with 10-character limit:")
        for col in varchar_10_fields:
            print(f"  • {col[0]}")
    
    # Let's also load a sample question from our JSON to see what might be too long
    with open("data/aws_practicetest_20_questions_improved.json", "r", encoding="utf-8") as f:
        questions = json.load(f)
    
    # Check the first few questions for field lengths
    print(f"\nSample question field lengths:")
    sample_q = questions[0]
    
    # Simulate what would be inserted
    question_id = "CP_0500"  # Next ID
    question_text = sample_q["question"]
    options = json.dumps(sample_q["options"])
    correct_answer = sample_q["answer"]
    explanation = ""  # Empty as per script
    category = "Cloud Practitioner Practice Test"
    
    print(f"  question_id: '{question_id}' (length: {len(question_id)})")
    print(f"  question: '{question_text[:50]}...' (length: {len(question_text)})")
    print(f"  correct_answer: '{correct_answer}' (length: {len(correct_answer)})")
    print(f"  explanation: '{explanation}' (length: {len(explanation)})")
    print(f"  category: '{category}' (length: {len(category)})")
    print(f"  options JSON: '{options[:50]}...' (length: {len(options)})")
    
    # Check if any of these exceed 10 characters
    field_checks = [
        ("question_id", question_id),
        ("correct_answer", correct_answer),
        ("explanation", explanation),
        ("category", category),
    ]
    
    print(f"\nField length analysis:")
    for field_name, value in field_checks:
        length = len(value)
        status = "❌" if length > 10 else "✅"
        print(f"  {status} {field_name}: {length} chars")
        if length > 10:
            print(f"      Value: '{value}'")
    
    cur.close()
    conn.close()
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
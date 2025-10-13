"""Check if questions have explanations in the database"""
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

# Check if explanation column exists
cur.execute("""
    SELECT column_name 
    FROM information_schema.columns 
    WHERE table_name='questions' AND column_name='explanation'
""")
has_explanation_column = cur.fetchone()

if has_explanation_column:
    print("✅ 'explanation' column exists in questions table")
    
    # Check how many questions have explanations
    cur.execute("SELECT COUNT(*) FROM questions WHERE explanation IS NOT NULL AND explanation != ''")
    with_explanation = cur.fetchone()[0]
    
    cur.execute("SELECT COUNT(*) FROM questions")
    total = cur.fetchone()[0]
    
    print(f"📊 {with_explanation} out of {total} questions have explanations ({(with_explanation/total*100):.1f}%)")
    
    # Show a sample question with explanation
    cur.execute("""
        SELECT id, question, explanation 
        FROM questions 
        WHERE explanation IS NOT NULL AND explanation != ''
        LIMIT 1
    """)
    sample = cur.fetchone()
    if sample:
        print(f"\n📝 Sample question with explanation:")
        print(f"ID: {sample[0]}")
        print(f"Question: {sample[1][:100]}...")
        print(f"Explanation: {sample[2][:200]}...")
else:
    print("❌ 'explanation' column does NOT exist in questions table")
    print("\n💡 You need to add the explanation column:")
    print("   ALTER TABLE questions ADD COLUMN explanation TEXT;")

conn.close()

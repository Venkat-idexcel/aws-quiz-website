"""
Quick check for remaining issues in Cloud Practitioner Practice Test questions
"""
import psycopg2
from config import Config

def quick_check():
    config = Config()
    conn = psycopg2.connect(
        host=config.DB_HOST,
        port=config.DB_PORT,
        database=config.DB_NAME,
        user=config.DB_USER,
        password=config.DB_PASSWORD
    )
    cur = conn.cursor()
    
    # Check for remaining option_e
    cur.execute("""
        SELECT COUNT(*) 
        FROM questions 
        WHERE category = 'Cloud Practitioner Practice Test' 
        AND option_e IS NOT NULL AND option_e != ''
    """)
    with_e = cur.fetchone()[0]
    
    # Check for long option_d (likely has explanation)
    cur.execute("""
        SELECT COUNT(*) 
        FROM questions 
        WHERE category = 'Cloud Practitioner Practice Test' 
        AND LENGTH(option_d) > 300
    """)
    long_d = cur.fetchone()[0]
    
    # Check for answers ending with ,E
    cur.execute("""
        SELECT COUNT(*) 
        FROM questions 
        WHERE category = 'Cloud Practitioner Practice Test' 
        AND correct_answer LIKE '%,E'
    """)
    bad_answers = cur.fetchone()[0]
    
    # Total questions
    cur.execute("""
        SELECT COUNT(*) 
        FROM questions 
        WHERE category = 'Cloud Practitioner Practice Test'
    """)
    total = cur.fetchone()[0]
    
    print(f"Total Cloud Practitioner questions: {total}")
    print(f"Questions with option_e: {with_e}")
    print(f"Questions with long option_d (>300 chars): {long_d}")
    print(f"Questions with bad correct_answer format: {bad_answers}")
    
    if with_e == 0 and long_d < 10 and bad_answers == 0:
        print("\nSTATUS: All major issues fixed!")
    else:
        print(f"\nSTATUS: {with_e + long_d + bad_answers} issues remaining")
    
    # Show examples of remaining long option_d
    if long_d > 0:
        print("\nExamples of remaining long option_d:")
        cur.execute("""
            SELECT question_id, LEFT(option_d, 100)
            FROM questions 
            WHERE category = 'Cloud Practitioner Practice Test' 
            AND LENGTH(option_d) > 300
            LIMIT 5
        """)
        for row in cur.fetchall():
            print(f"  {row[0]}: {row[1]}...")
    
    cur.close()
    conn.close()

if __name__ == '__main__':
    quick_check()

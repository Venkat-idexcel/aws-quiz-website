"""
Direct SQL-based fix for Cloud Practitioner questions
Uses PostgreSQL's string functions to fix in bulk
"""
import psycopg2
from config import Config

def fix_with_sql():
    config = Config()
    conn = psycopg2.connect(
        host=config.DB_HOST,
        port=config.DB_PORT,
        database=config.DB_NAME,
        user=config.DB_USER,
        password=config.DB_PASSWORD
    )
    cur = conn.cursor()
    
    print("Applying SQL fixes...")
    
    # Fix 1: Remove option_e for all Cloud Practitioner questions
    print("\n1. Clearing option_e...")
    cur.execute("""
        UPDATE questions 
        SET option_e = NULL
        WHERE category = 'Cloud Practitioner Practice Test'
        AND option_e IS NOT NULL
    """)
    print(f"   Cleared {cur.rowcount} option_e values")
    
    # Fix 2: Fix option_d that contains "Correct Answer:" text
    print("\n2. Fixing option_d with explanation text...")
    cur.execute("""
        UPDATE questions 
        SET option_d = SPLIT_PART(option_d, 'Correct Answer:', 1)
        WHERE category = 'Cloud Practitioner Practice Test'
        AND option_d LIKE '%Correct Answer:%'
    """)
    print(f"   Fixed {cur.rowcount} option_d values")
    
    # Fix 3: Remove trailing ,E from correct_answer
    print("\n3. Fixing correct_answer ending with ,E...")
    cur.execute("""
        UPDATE questions 
        SET correct_answer = REGEXP_REPLACE(correct_answer, ',\\s*E$', '', 'g')
        WHERE category = 'Cloud Practitioner Practice Test'
        AND correct_answer LIKE '%,E' OR correct_answer LIKE '%, E'
    """)
    print(f"   Fixed {cur.rowcount} correct_answer values")
    
    # Fix 4: For single-selection questions, keep only first answer
    print("\n4. Fixing single-selection questions with multiple answers...")
    cur.execute("""
        UPDATE questions 
        SET correct_answer = SPLIT_PART(correct_answer, ',', 1)
        WHERE category = 'Cloud Practitioner Practice Test'
        AND question NOT LIKE '%Choose%'
        AND question NOT LIKE '%Select%'
        AND question NOT LIKE '%select%'
        AND correct_answer LIKE '%,%'
    """)
    print(f"   Fixed {cur.rowcount} single-selection questions")
    
    # Commit all changes
    conn.commit()
    print("\nAll fixes committed!")
    
    cur.close()
    conn.close()

if __name__ == '__main__':
    fix_with_sql()

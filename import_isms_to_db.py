import psycopg2
import csv
import os

# Database connection settings (AWS RDS)
DB_HOST = os.getenv('DB_HOST', 'los-dev-psql-rdsclstr-new.cj6duvm27hk9.us-east-1.rds.amazonaws.com')
DB_PORT = int(os.getenv('DB_PORT', 3306))
DB_NAME = os.getenv('DB_NAME', 'cretificate_quiz_db')
DB_USER = os.getenv('DB_USER', 'postgres')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'poc2*&(SRWSjnjkn@#@#')

# CSV path - use relative path for portability
CSV_PATH = os.path.join(os.path.dirname(__file__), 'data', 'isms_questions.csv')

def import_isms_questions():
    """Import ISMS questions from CSV into database"""
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        cur = conn.cursor()
        
        # First, add the missing first question manually
        first_question = {
            'question': 'What is information security?',
            'option_a': 'Protection of business vision, mission and values',
            'option_b': 'Protection of policy and procedures',
            'option_c': 'Protection of confidentiality, integrity and availability',
            'option_d': 'Protection of intellectual property',
            'option_e': '',
            'correct_answer': 'C',
            'explanation': '',
            'category': 'ISMS Awareness'
        }
        
        print("Inserting first question...")
        cur.execute("""
            INSERT INTO questions (question, option_a, option_b, option_c, option_d, option_e, correct_answer, explanation, category)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            first_question['question'],
            first_question['option_a'],
            first_question['option_b'],
            first_question['option_c'],
            first_question['option_d'],
            first_question['option_e'],
            first_question['correct_answer'],
            first_question['explanation'],
            first_question['category']
        ))
        
        # Now import the rest from CSV
        print(f"Reading CSV: {CSV_PATH}")
        with open(CSV_PATH, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            count = 0
            for row in reader:
                cur.execute("""
                    INSERT INTO questions (question, option_a, option_b, option_c, option_d, option_e, correct_answer, explanation, category)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    row['question'].strip(),
                    row['option_a'].strip(),
                    row['option_b'].strip(),
                    row['option_c'].strip(),
                    row['option_d'].strip(),
                    row['option_e'].strip(),
                    row['correct_answer'].strip(),
                    row['explanation'].strip(),
                    row['category'].strip()
                ))
                count += 1
        
        conn.commit()
        print(f"\n✅ Successfully imported {count + 1} ISMS questions!")
        
        # Verify the import
        cur.execute("SELECT COUNT(*) FROM questions WHERE category = 'ISMS Awareness'")
        total = cur.fetchone()[0]
        print(f"✅ Total ISMS Awareness questions in database: {total}")
        
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    import_isms_questions()

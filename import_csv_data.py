import psycopg2
import csv

print("📥 Importing CSV data into the new database structure...")

try:
    conn = psycopg2.connect(
        host='los-dev-psql-rdsclstr-new.cj6duvm27hk9.us-east-1.rds.amazonaws.com',
        port=3306, 
        database='cretificate_quiz_db',
        user='postgres',
        password='poc2*&(SRWSjnjkn@#@#'
    )
    
    cur = conn.cursor()
    
    # Clear existing questions to avoid duplicates
    cur.execute('DELETE FROM questions')
    conn.commit()
    print("  Cleared existing questions")
    
    csv_file = r"c:\Users\venkatasai.p\Downloads\aws_questions_complete_20251008_132442.csv"
    
    with open(csv_file, 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        
        imported = 0
        for row in reader:
            try:
                cur.execute("""
                    INSERT INTO questions 
                    (question_id, question, option_a, option_b, option_c, option_d, option_e,
                     correct_answer, explanation, category, difficulty_level)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    row['question_id'],
                    row['question'],
                    row['option_a'],
                    row['option_b'], 
                    row['option_c'],
                    row['option_d'],
                    row['option_e'] if row['option_e'].strip() else None,
                    row['correct_answer'],
                    row['explanation'],
                    row['category'],
                    row['difficulty_level'] if row['difficulty_level'].strip() else 'Medium'
                ))
                imported += 1
                
                if imported % 100 == 0:
                    conn.commit()
                    print(f"  Imported {imported} questions...")
                    
            except Exception as e:
                print(f"  Error importing row {imported+1}: {str(e)[:100]}")
                continue
    
    conn.commit()
    print(f"✅ Import complete! {imported} questions imported.")
    
    # Verify import
    cur.execute('SELECT COUNT(*) FROM questions')
    total = cur.fetchone()[0]
    
    cur.execute('SELECT category, COUNT(*) FROM questions GROUP BY category')
    categories = cur.fetchall()
    
    print(f"\n📊 Verification:")
    print(f"  Total questions in database: {total}")
    for cat, count in categories:
        print(f"  {cat}: {count}")
        
except Exception as e:
    print(f"❌ Error: {e}")
finally:
    if 'conn' in locals():
        conn.close()
        print("\n✅ Connection closed.")
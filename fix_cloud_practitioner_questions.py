"""
Fix Cloud Practitioner Practice Test Questions
- Remove option_e data that leaked into option_d
- Fix correct_answer format (remove trailing E values)
- Clean up questions with explanation text in options
"""
import psycopg2
import json
import re
from config import Config

def fix_questions():
    config = Config()
    conn = psycopg2.connect(
        host=config.DB_HOST,
        port=config.DB_PORT,
        database=config.DB_NAME,
        user=config.DB_USER,
        password=config.DB_PASSWORD
    )
    cur = conn.cursor()
    
    # Get all Cloud Practitioner Practice Test questions
    cur.execute("""
        SELECT question_id, question, option_a, option_b, option_c, option_d, option_e, 
               correct_answer, explanation
        FROM questions 
        WHERE category = 'Cloud Practitioner Practice Test'
        ORDER BY question_id
    """)
    
    questions = cur.fetchall()
    print(f"Found {len(questions)} Cloud Practitioner Practice Test questions\n")
    
    fixed_count = 0
    
    for q in questions:
        q_id, question, opt_a, opt_b, opt_c, opt_d, opt_e, correct, explanation = q
        
        needs_fix = False
        new_option_d = opt_d
        new_option_e = None
        new_correct = correct
        
        # Fix 1: Check if option_d contains explanation text (starts with answer pattern)
        if opt_d and len(opt_d) > 200:
            # Look for "Correct Answer:" pattern in option_d
            if "Correct Answer:" in opt_d:
                # Extract only the option text before "Correct Answer:"
                parts = opt_d.split("Correct Answer:")
                new_option_d = parts[0].strip()
                needs_fix = True
                print(f"Fixed option_d for {q_id}")
        
        # Fix 2: Remove option_e if it exists
        if opt_e and opt_e.strip():
            new_option_e = None
            needs_fix = True
            print(f"Removed option_e for {q_id}")
        
        # Fix 3: Fix correct_answer - remove trailing ,E or E values that shouldn't be there
        if correct:
            # Clean up the correct answer
            corrected = correct.strip()
            
            # If it ends with ",E" or ", E", remove it
            if corrected.endswith(",E") or corrected.endswith(", E"):
                corrected = re.sub(r',\s*E$', '', corrected)
                needs_fix = True
                print(f"✓ Fixed correct_answer for {q_id}: '{correct}' -> '{corrected}'")
            # If it has multiple ,E at the end
            elif ",E" in corrected:
                # Remove all ,E occurrences at the end
                corrected = re.sub(r'(,E)+$', '', corrected)
                needs_fix = True
                print(f"✓ Fixed correct_answer for {q_id}: '{correct}' -> '{corrected}'")
            
            # Check if question asks for specific number of selections
            if "Choose TWO" in question or "Select 2" in question:
                # Should have exactly 2 answers
                answer_list = [a.strip() for a in corrected.split(',')]
                if len(answer_list) > 2:
                    # Keep only first 2
                    corrected = ','.join(answer_list[:2])
                    needs_fix = True
                    print(f"Limited to 2 answers for {q_id}: '{correct}' -> '{corrected}'")
            elif "Choose three" in question.lower() or "Select 3" in question:
                answer_list = [a.strip() for a in corrected.split(',')]
                if len(answer_list) > 3:
                    corrected = ','.join(answer_list[:3])
                    needs_fix = True
                    print(f"Limited to 3 answers for {q_id}: '{correct}' -> '{corrected}'")
            elif "Choose" not in question and "Select" not in question:
                # Single selection - should only have one answer
                if ',' in corrected:
                    corrected = corrected.split(',')[0].strip()
                    needs_fix = True
                    print(f"Fixed single selection for {q_id}: '{correct}' -> '{corrected}'")
            
            new_correct = corrected
        
        # Update the database if fixes are needed
        if needs_fix:
            try:
                cur.execute("""
                    UPDATE questions 
                    SET option_d = %s, option_e = %s, correct_answer = %s
                    WHERE question_id = %s
                """, (new_option_d, new_option_e, new_correct, q_id))
                fixed_count += 1
            except Exception as e:
                print(f"ERROR fixing {q_id}: {e}")
                conn.rollback()
                continue
    
    # Commit all changes
    conn.commit()
    print(f"\nSuccessfully fixed {fixed_count} questions!")
    
    # Verify fixes
    print("\nVerifying fixes...")
    cur.execute("""
        SELECT COUNT(*) 
        FROM questions 
        WHERE category = 'Cloud Practitioner Practice Test' 
        AND option_e IS NOT NULL AND option_e != ''
    """)
    remaining_e = cur.fetchone()[0]
    
    cur.execute("""
        SELECT COUNT(*) 
        FROM questions 
        WHERE category = 'Cloud Practitioner Practice Test' 
        AND LENGTH(option_d) > 300
    """)
    long_d = cur.fetchone()[0]
    
    print(f"  Remaining questions with option_e: {remaining_e}")
    print(f"  Remaining questions with long option_d: {long_d}")
    
    cur.close()
    conn.close()

if __name__ == '__main__':
    print("Starting Cloud Practitioner questions fix...\n")
    fix_questions()
    print("\nFix complete!")

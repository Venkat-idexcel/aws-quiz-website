"""
Fix Cloud Practitioner Practice Test Questions - Batch Processing
Processes questions in small batches to avoid timeouts
"""
import psycopg2
import re
from config import Config

BATCH_SIZE = 100

def fix_batch(conn, start_id):
    cur = conn.cursor()
    
    # Get next batch
    cur.execute("""
        SELECT question_id, question, option_a, option_b, option_c, option_d, option_e, 
               correct_answer, explanation
        FROM questions 
        WHERE category = 'Cloud Practitioner Practice Test'
        AND question_id >= %s
        ORDER BY question_id
        LIMIT %s
    """, (start_id, BATCH_SIZE))
    
    questions = cur.fetchall()
    if not questions:
        return 0, None
    
    fixed_count = 0
    
    for q in questions:
        q_id, question, opt_a, opt_b, opt_c, opt_d, opt_e, correct, explanation = q
        
        needs_fix = False
        new_option_d = opt_d
        new_option_e = None
        new_correct = correct
        
        # Fix option_d with explanation
        if opt_d and "Correct Answer:" in opt_d:
            parts = opt_d.split("Correct Answer:")
            new_option_d = parts[0].strip()
            needs_fix = True
        
        # Remove option_e
        if opt_e and opt_e.strip():
            new_option_e = None
            needs_fix = True
        
        # Fix correct_answer
        if correct:
            corrected = correct.strip()
            
            # Remove trailing ,E
            if ",E" in corrected:
                corrected = re.sub(r',\s*E$', '', corrected)
                corrected = re.sub(r'(,E)+$', '', corrected)
                needs_fix = True
            
            # Check selection count
            if any(x in question for x in ["Choose TWO", "Select 2", "(Choose two)", "choose two"]):
                answer_list = [a.strip() for a in corrected.split(',') if a.strip()]
                if len(answer_list) > 2:
                    corrected = ','.join(answer_list[:2])
                    needs_fix = True
            elif any(x in question for x in ["Choose three", "Select 3", "(Choose 3)"]):
                answer_list = [a.strip() for a in corrected.split(',') if a.strip()]
                if len(answer_list) > 3:
                    corrected = ','.join(answer_list[:3])
                    needs_fix = True
            elif not any(x in question for x in ["Choose", "Select", "select"]):
                # Single selection
                if ',' in corrected:
                    corrected = corrected.split(',')[0].strip()
                    needs_fix = True
            
            new_correct = corrected
        
        if needs_fix:
            try:
                cur.execute("""
                    UPDATE questions 
                    SET option_d = %s, option_e = %s, correct_answer = %s
                    WHERE question_id = %s
                """, (new_option_d, new_option_e, new_correct, q_id))
                fixed_count += 1
            except Exception as e:
                print(f"ERROR: {q_id}: {e}")
                conn.rollback()
                continue
    
    conn.commit()
    last_id = questions[-1][0]
    return fixed_count, last_id

def main():
    config = Config()
    conn = psycopg2.connect(
        host=config.DB_HOST,
        port=config.DB_PORT,
        database=config.DB_NAME,
        user=config.DB_USER,
        password=config.DB_PASSWORD
    )
    
    print("Fixing Cloud Practitioner questions in batches...")
    
    total_fixed = 0
    current_id = "CP_0001"
    batch_num = 0
    
    while True:
        batch_num += 1
        fixed, last_id = fix_batch(conn, current_id)
        total_fixed += fixed
        
        if last_id is None:
            break
        
        print(f"Batch {batch_num}: Fixed {fixed} questions (Total: {total_fixed})")
        current_id = last_id
        
        # Safety check
        if batch_num > 20:
            print("Processed 20 batches, checking if more remain...")
            break
    
    print(f"\nTotal fixed: {total_fixed}")
    conn.close()

if __name__ == '__main__':
    main()

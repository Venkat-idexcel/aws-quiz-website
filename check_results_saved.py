"""
Check if quiz results are being saved properly
"""
import psycopg2
from config import Config

def check_results():
    conn = psycopg2.connect(
        host=Config.DB_HOST,
        port=Config.DB_PORT,
        database=Config.DB_NAME,
        user=Config.DB_USER,
        password=Config.DB_PASSWORD
    )
    
    cur = conn.cursor()
    
    print("\n" + "="*80)
    print("QUIZ SESSIONS - LATEST RESULTS")
    print("="*80)
    
    # Get latest quiz sessions
    cur.execute("""
        SELECT id, user_id, category, start_time, end_time, 
               total_questions, correct_answers, score_percentage, is_completed
        FROM quiz_sessions
        ORDER BY id DESC
        LIMIT 5
    """)
    
    sessions = cur.fetchall()
    if sessions:
        print(f"\nLatest {len(sessions)} quiz sessions:")
        for s in sessions:
            status = "COMPLETED" if s[8] else "IN PROGRESS"
            print(f"\n  Session ID: {s[0]}")
            print(f"  User ID: {s[1]}")
            print(f"  Category: {s[2]}")
            print(f"  Started: {s[3]}")
            print(f"  Ended: {s[4]}")
            print(f"  Total Questions: {s[5]}")
            print(f"  Correct Answers: {s[6]}")
            print(f"  Score: {s[7]}%")
            print(f"  Status: {status}")
    else:
        print("\nNo quiz sessions found!")
    
    print("\n" + "="*80)
    print("USER ANSWERS - LATEST RECORDS")
    print("="*80)
    
    # Get latest user answers
    cur.execute("""
        SELECT ua.id, ua.session_id, ua.question_id, ua.user_answer, ua.is_correct,
               q.question
        FROM user_answers ua
        LEFT JOIN questions q ON ua.question_id = q.question_id
        ORDER BY ua.id DESC
        LIMIT 10
    """)
    
    answers = cur.fetchall()
    if answers:
        print(f"\nLatest {len(answers)} answers:")
        for a in answers:
            correct_mark = "CORRECT" if a[4] else "WRONG"
            print(f"\n  Answer ID: {a[0]}")
            print(f"  Session: {a[1]}")
            print(f"  Question ID: {a[2]}")
            print(f"  User Answer: {a[3]}")
            print(f"  Result: {correct_mark}")
            if a[5]:
                print(f"  Question: {a[5][:60]}...")
    else:
        print("\nNo user answers found!")
    
    # Summary statistics
    print("\n" + "="*80)
    print("SUMMARY STATISTICS")
    print("="*80)
    
    cur.execute("SELECT COUNT(*) FROM quiz_sessions WHERE is_completed = TRUE")
    completed = cur.fetchone()[0]
    
    cur.execute("SELECT COUNT(*) FROM quiz_sessions WHERE is_completed = FALSE")
    in_progress = cur.fetchone()[0]
    
    cur.execute("SELECT COUNT(*) FROM user_answers")
    total_answers = cur.fetchone()[0]
    
    print(f"\nCompleted quizzes: {completed}")
    print(f"In progress quizzes: {in_progress}")
    print(f"Total answers recorded: {total_answers}")
    
    if completed > 0:
        cur.execute("""
            SELECT AVG(score_percentage), MAX(score_percentage), MIN(score_percentage)
            FROM quiz_sessions
            WHERE is_completed = TRUE
        """)
        avg, max_s, min_s = cur.fetchone()
        print(f"\nScore Statistics (Completed Quizzes):")
        print(f"  Average: {avg:.2f}%" if avg else "  Average: N/A")
        print(f"  Highest: {max_s}%" if max_s else "  Highest: N/A")
        print(f"  Lowest: {min_s}%" if min_s else "  Lowest: N/A")
    
    conn.close()

if __name__ == "__main__":
    check_results()

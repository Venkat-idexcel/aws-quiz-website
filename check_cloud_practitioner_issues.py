"""
Check for issues in Cloud Practitioner Practice Test questions
"""
import psycopg2
import json
from config import Config

def check_questions():
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
    print(f"📊 Total Cloud Practitioner Practice Test questions: {len(questions)}\n")
    
    issues_found = []
    
    for q in questions:
        q_id, question, opt_a, opt_b, opt_c, opt_d, opt_e, correct, explanation = q
        
        issue = {
            'question_id': q_id,
            'question': question[:100] + "..." if len(question) > 100 else question,
            'problems': []
        }
        
        # Check if option_d is too long (contains explanation text)
        if opt_d and len(opt_d) > 200:
            issue['problems'].append(f"Option D is too long ({len(opt_d)} chars) - likely contains explanation")
            issue['option_d'] = opt_d[:200] + "..."
        
        # Check if option_e exists but shouldn't
        if opt_e and opt_e.strip():
            issue['problems'].append(f"Option E exists: {opt_e[:100]}")
        
        # Check correct_answer format
        if correct:
            # Count how many answers are expected
            answer_count = correct.count(',') + 1 if ',' in correct else 1
            
            # Check if it's asking for wrong number of selections
            if 'Select 2' in question and answer_count != 2:
                issue['problems'].append(f"Question asks for 2 answers but correct_answer has {answer_count}: {correct}")
            elif 'Select 4' in question and answer_count != 4:
                issue['problems'].append(f"Question asks for 4 answers but correct_answer has {answer_count}: {correct}")
            elif 'Select 2' not in question and 'Select 4' not in question and answer_count > 1:
                issue['problems'].append(f"Single selection question but correct_answer has multiple: {correct}")
        
        if issue['problems']:
            issues_found.append(issue)
    
    # Display issues
    if issues_found:
        print(f"🚨 Found {len(issues_found)} questions with issues:\n")
        for idx, issue in enumerate(issues_found, 1):
            print(f"\n{'='*80}")
            print(f"Issue #{idx} - Question ID: {issue['question_id']}")
            print(f"Question: {issue['question']}")
            for problem in issue['problems']:
                print(f"  ❌ {problem}")
            if 'option_d' in issue:
                print(f"  Option D preview: {issue['option_d']}")
    else:
        print("✅ No issues found!")
    
    # Save detailed report
    with open('cloud_practitioner_issues_report.json', 'w', encoding='utf-8') as f:
        json.dump(issues_found, f, indent=2, ensure_ascii=False)
    
    print(f"\n\n💾 Detailed report saved to: cloud_practitioner_issues_report.json")
    
    cur.close()
    conn.close()

if __name__ == '__main__':
    check_questions()

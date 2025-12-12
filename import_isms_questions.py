import psycopg2
import re

# Database credentials
DB_HOST = 'los-dev-psql-rdsclstr-new.cj6duvm27hk9.us-east-1.rds.amazonaws.com'
DB_PORT = 3306
DB_NAME = 'cretificate_quiz_db'
DB_USER = 'postgres'
DB_PASSWORD = 'poc2*&(SRWSjnjkn@#@#'

# ISMS questions data - properly formatted
isms_questions = [
    {
        'question': 'What is information security?',
        'option_a': 'Protection of business vision, mission and values',
        'option_b': 'Protection of policy and procedures',
        'option_c': 'Protection of confidentiality, integrity and availability',
        'option_d': 'Protection of intellectual property',
        'correct_answer': 'C'
    },
    {
        'question': 'Who is responsible for information security?',
        'option_a': 'Only the IT team',
        'option_b': 'Only management',
        'option_c': 'Every employee',
        'option_d': 'Only auditors',
        'correct_answer': 'C'
    },
    {
        'question': 'Information security focuses only on technology, not people or processes.',
        'option_a': 'True',
        'option_b': 'False',
        'option_c': '',
        'option_d': '',
        'correct_answer': 'B'
    },
    {
        'question': 'PCI-DSS stands for',
        'option_a': 'Payment Card Industry Data Security Standard',
        'option_b': 'Pay Card Industry Data Security Standard',
        'option_c': 'Payment Card Information Data Security Standard',
        'option_d': 'Pay Card Information Data Security Standard',
        'correct_answer': 'A'
    },
    {
        'question': 'Which of the following is not a Trust Services Criterion (TSC) in SOC 2?',
        'option_a': 'Security',
        'option_b': 'Availability',
        'option_c': 'Confidentiality',
        'option_d': 'Profitability',
        'correct_answer': 'D'
    },
    {
        'question': 'Which of the following is a direct effect of a security breach?',
        'option_a': 'Increased system performance',
        'option_b': 'Data loss or theft',
        'option_c': 'Reduced electricity consumption',
        'option_d': 'Improved employee morale',
        'correct_answer': 'B'
    },
    {
        'question': 'You receive an email from an unknown sender claiming to be from IT support, asking you to click a link to reset your password. What should you do?',
        'option_a': 'Click the link to check what it is',
        'option_b': 'Forward it to your colleagues for awareness',
        'option_c': 'Report it to the IT/security team and delete it',
        'option_d': 'Reply asking if it is genuine',
        'correct_answer': 'C'
    },
    {
        'question': 'You are working from a café using public Wi-Fi. What is the best way to protect organizational data?',
        'option_a': 'Connect directly to public Wi-Fi',
        'option_b': 'Use VPN and ensure no confidential data is visible',
        'option_c': 'Disable firewall for faster internet',
        'option_d': 'Share hotspot with others',
        'correct_answer': 'B'
    },
    {
        'question': 'A person without a badge enters your office area, claiming to be from maintenance. What should you do?',
        'option_a': 'Assume they are authorized and ignore',
        'option_b': 'Escort them to your manager\'s cabin',
        'option_c': 'Politely verify their identity or report to security',
        'option_d': 'Let them proceed since they seem harmless',
        'correct_answer': 'C'
    },
    {
        'question': 'You mistakenly send an internal confidential document to an external recipient. What should you do first?',
        'option_a': 'Ignore; they may not notice',
        'option_b': 'Inform the recipient to delete the email and notify ISMS immediately',
        'option_c': 'Delete it from Sent Items',
        'option_d': 'Wait until someone asks about it',
        'correct_answer': 'B'
    },
    {
        'question': 'You find a free tool online that would help in your work. Should you install it?',
        'option_a': 'Yes, if it helps productivity',
        'option_b': 'No, unless approved by IT/security',
        'option_c': 'Yes, if downloaded from a known website',
        'option_d': 'Yes, if others use it too',
        'correct_answer': 'B'
    },
    {
        'question': 'If an employee is caught doing an offense like abusing the internet, he/she will instantly receive an incident report instead of a mere warning.',
        'option_a': 'True',
        'option_b': 'False',
        'option_c': '',
        'option_d': '',
        'correct_answer': 'A'
    },
    {
        'question': 'What is social engineering?',
        'option_a': 'A group planning for social activity in the organization',
        'option_b': 'Creating a situation wherein a third party gains confidential information from you',
        'option_c': 'The organization is planning an activity for the welfare of the neighborhood',
        'option_d': 'None',
        'correct_answer': 'B'
    },
    {
        'question': 'Before leaving for the day, what should you ensure?',
        'option_a': 'Leave system unlocked for updates',
        'option_b': 'Clear desk of all confidential papers and lock system',
        'option_c': 'Keep printed data for tomorrow',
        'option_d': 'Keep system logged in for convenience',
        'correct_answer': 'B'
    },
    {
        'question': 'Your company laptop containing project data is stolen from your car. What should you do?',
        'option_a': 'Try to locate it yourself',
        'option_b': 'Inform the police only',
        'option_c': 'Immediately report to IT/security team and management',
        'option_d': 'Wait a day to see if it turns up',
        'correct_answer': 'C'
    },
    {
        'question': 'How often should you change your password as per ISMS best practices?',
        'option_a': 'Only when you forget it',
        'option_b': 'Every 45 days or as per organizational policy',
        'option_c': 'Once a year',
        'option_d': 'Never, if it is strong',
        'correct_answer': 'B'
    },
    {
        'question': 'A colleague says they have never read the ISMS policy. What should you do?',
        'option_a': 'Ignore - it is not your responsibility',
        'option_b': 'Remind them to review the ISMS awareness material or policy',
        'option_c': 'Report them to HR',
        'option_d': 'Share your copy with them',
        'correct_answer': 'B'
    },
    {
        'question': 'An employee leaves the company. What should be ensured as part of ISMS?',
        'option_a': 'Leave access active for handover',
        'option_b': 'Disable all system and physical access immediately',
        'option_c': 'Wait for IT\'s next monthly audit',
        'option_d': 'Do nothing if they were trustworthy',
        'correct_answer': 'B'
    },
    {
        'question': 'A friend visits your office and wants to see your workspace. What should you do?',
        'option_a': 'Allow them to enter freely',
        'option_b': 'Get visitor pass and escort them',
        'option_c': 'Let them wait in your cubicle',
        'option_d': 'Give your badge temporarily',
        'correct_answer': 'B'
    },
    {
        'question': 'While creating new documented information, what is essential?',
        'option_a': 'It is essential that the document carries company logo as the watermark',
        'option_b': 'A copy of the new information must be created so that in case the information is destroyed by mistake, the same can be recovered easily',
        'option_c': 'The document should be reviewed and approved before distribution',
        'option_d': 'None of the above',
        'correct_answer': 'C'
    }
]

def import_isms_questions():
    try:
        # Connect to database
        print(f"Connecting to database at {DB_HOST}:{DB_PORT}...")
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            connect_timeout=10
        )
        print("✅ Connected to database successfully!")
        
        cur = conn.cursor()
        
        # Check if ISMS questions already exist
        cur.execute("SELECT COUNT(*) FROM questions WHERE category = 'ISMS Awareness'")
        existing_count = cur.fetchone()[0]
        
        if existing_count > 0:
            print(f"⚠️  Found {existing_count} existing ISMS questions. Deleting them first...")
            cur.execute("DELETE FROM questions WHERE category = 'ISMS Awareness'")
            conn.commit()
        
        # Insert questions
        inserted = 0
        for i, q in enumerate(isms_questions, 1):
            cur.execute("""
                INSERT INTO questions (
                    question_id, question, option_a, option_b, option_c, option_d, option_e,
                    correct_answer, explanation, category, difficulty_level
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                f'ISMS-{i:03d}',
                q['question'],
                q['option_a'],
                q['option_b'],
                q.get('option_c', ''),
                q.get('option_d', ''),
                '',  # option_e
                q['correct_answer'],
                '',  # explanation
                'ISMS Awareness',
                'Medium'
            ))
            inserted += 1
            print(f"✅ Inserted question {i}: {q['question'][:60]}...")
        
        conn.commit()
        print(f"\n🎉 Successfully imported {inserted} ISMS questions!")
        
        # Verify
        cur.execute("SELECT COUNT(*) FROM questions WHERE category = 'ISMS Awareness'")
        final_count = cur.fetchone()[0]
        print(f"✅ Verification: {final_count} ISMS questions in database")
        
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    import_isms_questions()

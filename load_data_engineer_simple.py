import os
import re
import psycopg2
import hashlib

# Database credentials
DB_HOST = 'los-dev-psql-rdsclstr-new.cj6duvm27hk9.us-east-1.rds.amazonaws.com'
DB_PORT = 3306  # Custom PostgreSQL port (AWS RDS configured on non-standard port)
DB_NAME = 'postgres'  # Use standard postgres database name
DB_USER = 'postgres'
DB_PASSWORD = 'poc2*&(SRWSjnjkn@#@#'

def get_db_connection():
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        connect_timeout=10
    )

def parse_question_blocks(text):
    blocks = re.split(r'(?=### Question \d+:)', text)
    return [block.strip() for block in blocks if block.strip()]

def insert_questions(questions):
    conn = get_db_connection()
    cur = conn.cursor()

    # Add columns if they don't exist
    try:
        cur.execute("ALTER TABLE aws_questions ADD COLUMN IF NOT EXISTS explanation TEXT")
        cur.execute("ALTER TABLE aws_questions ADD COLUMN IF NOT EXISTS category VARCHAR(255)")
        cur.execute("ALTER TABLE aws_questions ADD COLUMN IF NOT EXISTS content_hash VARCHAR(64) UNIQUE")
        conn.commit()
    except Exception as e:
        print(f"Column add warning: {e}")

    inserted_count = 0
    for q in questions:
        content_to_hash = f"{q['question']}{q.get('option_a', '')}{q.get('option_b', '')}{q.get('option_c', '')}{q.get('option_d', '')}{q.get('option_e', '')}"
        content_hash = hashlib.sha256(content_to_hash.encode('utf-8')).hexdigest()

        cur.execute("SELECT 1 FROM aws_questions WHERE content_hash = %s", (content_hash,))
        if cur.fetchone():
            print(f"Skipping duplicate question: {q['question'][:30]}...")
            continue

        try:
            cur.execute("""
                INSERT INTO aws_questions (question, option_a, option_b, option_c, option_d, option_e, correct_answer, explanation, category, content_hash)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                q['question'],
                q.get('option_a'),
                q.get('option_b'),
                q.get('option_c'),
                q.get('option_d'),
                q.get('option_e'),
                q['correct_answer'],
                q.get('explanation'),
                'AWS Data Engineer',
                content_hash
            ))
            inserted_count += 1
        except Exception as e:
            print(f"Error inserting question: {e}")
            continue

    conn.commit()
    cur.close()
    conn.close()
    print(f"Successfully inserted {inserted_count} new questions.")

def main():
    file_path = r'C:\Users\venkatasai.p\Documents\Data eng.txt'
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    blocks = parse_question_blocks(content)
    questions = []

    for block in blocks:
        lines = [line.strip() for line in block.strip().split('\n') if line.strip()]
        if not lines:
            continue

        question_header = lines.pop(0)
        question_text = ""
        options = {}
        correct_answer = ''
        explanation = ''

        # Find where options start
        first_option_index = -1
        for i, line in enumerate(lines):
            if re.match(r'^[A-E]\.', line):
                first_option_index = i
                break
        
        if first_option_index == -1:
            continue

        # Question text is everything before first option
        question_text = " ".join(lines[:first_option_index])

        # Find correct answer line
        correct_answer_line_index = -1
        for i, line in enumerate(lines):
            if line.startswith('**Correct Answer:**'):
                correct_answer_line_index = i
                break
        
        if correct_answer_line_index == -1:
            continue

        # Extract options
        option_lines = lines[first_option_index:correct_answer_line_index]
        for i, line in enumerate(option_lines):
            option_key = f"option_{chr(97 + i)}"
            options[option_key] = re.sub(r'^[A-E]\.\s*', '', line).strip()

        # Extract correct answer
        correct_answer_line = lines[correct_answer_line_index]
        match = re.search(r'\*\*Correct Answer:\*\*\s*([A-E])', correct_answer_line)
        if match:
            correct_answer = match.group(1)

        # Extract explanation
        explanation_line_index = correct_answer_line_index + 1
        if explanation_line_index < len(lines) and lines[explanation_line_index].startswith('**Explanation:**'):
            explanation_text = lines[explanation_line_index]
            explanation = explanation_text.replace('**Explanation:**', '').strip()
            for i in range(explanation_line_index + 1, len(lines)):
                explanation += " " + lines[i]

        if question_text and len(options) > 0 and correct_answer:
            question_data = {
                'question': question_text,
                'correct_answer': correct_answer,
                'explanation': explanation,
                **options
            }
            questions.append(question_data)

    if questions:
        print(f"Successfully parsed {len(questions)} questions.")
        insert_questions(questions)
    else:
        print("No questions were parsed.")

if __name__ == '__main__':
    main()
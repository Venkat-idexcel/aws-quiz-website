import os
import re
import psycopg2
import hashlib

# Database Configuration (AWS RDS)
DB_CONFIG = {
    'host': 'los-dev-psql-rdsclstr-new.cj6duvm27hk9.us-east-1.rds.amazonaws.com',
    'port': 3306,
    'database': 'cretificate_quiz_db',
    'user': 'postgres',
    'password': 'poc2*&(SRWSjnjkn@#@#'
}

def get_db_connection():
    """Get database connection"""
    return psycopg2.connect(**DB_CONFIG)

def return_db_connection(conn):
    """Close database connection"""
    conn.close()

def parse_question_blocks(text):
    """Splits the text into blocks, each containing one question."""
    # Use a positive lookahead in the split pattern to keep the delimiter
    blocks = re.split(r'(?=### Question \d+:)', text)
    # Filter out any empty strings that may result from the split
    return [block.strip() for block in blocks if block.strip()]

def insert_questions(questions):
    conn = get_db_connection()
    if not conn:
        print("Failed to get a database connection.")
        return

    cur = conn.cursor()

    # Add explanation and category columns if they don't exist
    cur.execute("""
        ALTER TABLE aws_questions
        ADD COLUMN IF NOT EXISTS explanation TEXT,
        ADD COLUMN IF NOT EXISTS category VARCHAR(255),
        ADD COLUMN IF NOT EXISTS content_hash VARCHAR(64) UNIQUE;
    """)
    conn.commit()

    for q in questions:
        content_to_hash = f"{q['question']}{q.get('option_a', '')}{q.get('option_b', '')}{q.get('option_c', '')}{q.get('option_d', '')}{q.get('option_e', '')}"
        content_hash = hashlib.sha256(content_to_hash.encode('utf-8')).hexdigest()

        cur.execute(
            "SELECT 1 FROM aws_questions WHERE content_hash = %s", (content_hash,)
        )
        if cur.fetchone():
            print(f"Skipping duplicate question: {q['question'][:30]}...")
            continue

        cur.execute(
            """
            INSERT INTO aws_questions (question, option_a, option_b, option_c, option_d, option_e, correct_answer, explanation, category, content_hash)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
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
            )
        )
    conn.commit()
    cur.close()
    return_db_connection(conn)
    print(f"Successfully inserted {len(questions)} new questions.")

def main():
    file_path = r'C:\Users\venkatasai.p\Documents\Data eng.txt'
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        print(f"Error: The file '{file_path}' was not found.")
        return

    blocks = parse_question_blocks(content)
    questions = []

    for block in blocks:
        lines = [line.strip() for line in block.strip().split('\n') if line.strip()]
        if not lines:
            continue

        # The first line is the question header, e.g., '### Question 1:'
        question_header = lines.pop(0)
        
        question_text = ""
        options = {}
        correct_answer = ''
        explanation = ''

        # Find where the options start
        first_option_index = -1
        for i, line in enumerate(lines):
            if re.match(r'^[A-E]\.', line):
                first_option_index = i
                break
        
        if first_option_index == -1:
            print(f"Warning: Could not find options for block starting with: {question_header}")
            continue

        # Everything before the first option is part of the question
        question_text = " ".join(lines[:first_option_index])

        # Find where the correct answer is
        correct_answer_line_index = -1
        for i, line in enumerate(lines):
            if line.startswith('**Correct Answer:**'):
                correct_answer_line_index = i
                break
        
        if correct_answer_line_index == -1:
            print(f"Warning: Could not find correct answer for block: {question_header}")
            continue

        # Extract options (lines between question and correct answer)
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
            # Handle multi-line explanations
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
        print("No questions were parsed. Please check the file format.")

if __name__ == '__main__':
    main()

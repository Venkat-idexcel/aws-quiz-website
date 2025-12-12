#!/usr/bin/env python3
"""
Extract AWS Cloud Practitioner questions from PDF
Extracts 10 sets x 50 questions = 500 total questions
"""

import PyPDF2
import re
import json
import psycopg2
import psycopg2.extras
from config import Config

def extract_pdf_text(pdf_path):
    """Extract text from PDF file"""
    text = ""
    try:
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            print(f"PDF has {len(reader.pages)} pages")
            
            for page_num, page in enumerate(reader.pages):
                page_text = page.extract_text()
                text += page_text + "\n"
                if (page_num + 1) % 10 == 0:
                    print(f"Processed {page_num + 1} pages...")
                    
    except Exception as e:
        print(f"Error reading PDF: {e}")
        return ""
    
    return text

def parse_aws_questions(text):
    """Parse AWS questions from extracted text"""
    questions = []
    
    # Split text into potential question blocks
    lines = text.split('\n')
    current_question = {}
    question_text = ""
    options = []
    answer = ""
    explanation = ""
    
    collecting_question = False
    collecting_options = False
    collecting_answer = False
    collecting_explanation = False
    
    question_number_pattern = r'^(\d+)\.\s*(.+)'
    option_pattern = r'^([A-E])\.\s*(.+)'
    answer_pattern = r'(?:Answer|Correct Answer):\s*([A-E])'
    explanation_pattern = r'(?:Explanation|Rationale):\s*(.+)'
    
    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue
            
        # Check for question number
        question_match = re.match(question_number_pattern, line)
        if question_match:
            # Save previous question if exists
            if current_question and question_text and options and answer:
                current_question = {
                    'question': question_text.strip(),
                    'option_a': next((opt[1] for opt in options if opt[0] == 'A'), ''),
                    'option_b': next((opt[1] for opt in options if opt[0] == 'B'), ''),
                    'option_c': next((opt[1] for opt in options if opt[0] == 'C'), ''),
                    'option_d': next((opt[1] for opt in options if opt[0] == 'D'), ''),
                    'option_e': next((opt[1] for opt in options if opt[0] == 'E'), ''),
                    'correct_answer': answer.strip(),
                    'explanation': explanation.strip() if explanation else ''
                }
                questions.append(current_question)
                print(f"Extracted question {len(questions)}: {question_text[:50]}...")
            
            # Start new question
            question_text = question_match.group(2)
            options = []
            answer = ""
            explanation = ""
            collecting_question = True
            collecting_options = False
            collecting_answer = False
            collecting_explanation = False
            continue
        
        # Check for option
        option_match = re.match(option_pattern, line)
        if option_match:
            options.append((option_match.group(1), option_match.group(2)))
            collecting_question = False
            collecting_options = True
            collecting_answer = False
            collecting_explanation = False
            continue
        
        # Check for answer
        answer_match = re.search(answer_pattern, line)
        if answer_match:
            answer = answer_match.group(1)
            collecting_question = False
            collecting_options = False
            collecting_answer = True
            collecting_explanation = False
            continue
        
        # Check for explanation
        explanation_match = re.search(explanation_pattern, line)
        if explanation_match:
            explanation = explanation_match.group(1)
            collecting_question = False
            collecting_options = False
            collecting_answer = False
            collecting_explanation = True
            continue
        
        # Continue collecting based on current state
        if collecting_question:
            question_text += " " + line
        elif collecting_explanation:
            explanation += " " + line
        elif collecting_answer and not collecting_explanation:
            # Sometimes answer explanation continues on next line
            if not re.match(option_pattern, line) and not re.match(question_number_pattern, line):
                explanation += " " + line
    
    # Save the last question
    if current_question and question_text and options and answer:
        current_question = {
            'question': question_text.strip(),
            'option_a': next((opt[1] for opt in options if opt[0] == 'A'), ''),
            'option_b': next((opt[1] for opt in options if opt[0] == 'B'), ''),
            'option_c': next((opt[1] for opt in options if opt[0] == 'C'), ''),
            'option_d': next((opt[1] for opt in options if opt[0] == 'D'), ''),
            'option_e': next((opt[1] for opt in options if opt[0] == 'E'), ''),
            'correct_answer': answer.strip(),
            'explanation': explanation.strip() if explanation else ''
        }
        questions.append(current_question)
    
    return questions

def get_db_connection():
    """Get database connection"""
    try:
        conn = psycopg2.connect(
            host=Config.DB_HOST,
            port=Config.DB_PORT,
            database=Config.DB_NAME,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD
        )
        return conn
    except Exception as e:
        print(f"Database connection error: {e}")
        return None

def import_questions_to_db(questions):
    """Import questions to database"""
    conn = get_db_connection()
    if not conn:
        print("Failed to connect to database")
        return False
    
    try:
        cur = conn.cursor()
        
        # Check if category already exists
        cur.execute("SELECT COUNT(*) FROM questions WHERE category = %s", ('AWS Cloud Practitioner',))
        existing_count = cur.fetchone()[0]
        
        if existing_count > 0:
            print(f"Found {existing_count} existing AWS Cloud Practitioner questions")
            response = input("Do you want to replace them? (y/N): ")
            if response.lower() == 'y':
                cur.execute("DELETE FROM questions WHERE category = %s", ('AWS Cloud Practitioner',))
                print("Deleted existing questions")
            else:
                print("Keeping existing questions, adding new ones...")
        
        # Insert questions
        insert_query = """
        INSERT INTO questions (
            question, option_a, option_b, option_c, option_d, option_e,
            correct_answer, explanation, category, difficulty_level
        ) VALUES (
            %(question)s, %(option_a)s, %(option_b)s, %(option_c)s, %(option_d)s, %(option_e)s,
            %(correct_answer)s, %(explanation)s, 'AWS Cloud Practitioner', 'intermediate'
        )
        """
        
        successful_imports = 0
        for i, question in enumerate(questions):
            try:
                cur.execute(insert_query, question)
                successful_imports += 1
                if (i + 1) % 50 == 0:
                    print(f"Imported {i + 1} questions...")
            except Exception as e:
                print(f"Error importing question {i + 1}: {e}")
                continue
        
        conn.commit()
        print(f"Successfully imported {successful_imports} out of {len(questions)} questions")
        
        # Verify import
        cur.execute("SELECT COUNT(*) FROM questions WHERE category = 'AWS Cloud Practitioner'")
        total_count = cur.fetchone()[0]
        print(f"Total AWS Cloud Practitioner questions in database: {total_count}")
        
        return True
        
    except Exception as e:
        print(f"Database error: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def save_questions_to_json(questions, filename):
    """Save questions to JSON file for backup"""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(questions, f, indent=2, ensure_ascii=False)
        print(f"Questions saved to {filename}")
    except Exception as e:
        print(f"Error saving to JSON: {e}")

def main():
    print("🚀 Starting AWS Cloud Practitioner question extraction...")
    print("📄 Expected: 10 sets × 50 questions = 500 total questions")
    
    # Extract text from PDF
    pdf_path = "data/AWS_practioner_practicetest_10.pdf"
    print(f"📖 Reading PDF: {pdf_path}")
    
    text = extract_pdf_text(pdf_path)
    if not text:
        print("❌ Failed to extract text from PDF")
        return
    
    print(f"✅ Extracted {len(text)} characters from PDF")
    
    # Parse questions
    print("🔍 Parsing questions from text...")
    questions = parse_aws_questions(text)
    
    print(f"✅ Extracted {len(questions)} questions")
    
    if not questions:
        print("❌ No questions found. Please check the PDF format.")
        return
    
    # Save to JSON for backup
    json_filename = "data/aws_practitioner_questions.json"
    save_questions_to_json(questions, json_filename)
    
    # Display sample question
    if questions:
        print("\n📋 Sample question:")
        sample = questions[0]
        print(f"Q: {sample['question'][:100]}...")
        print(f"A: {sample['option_a'][:50]}...")
        print(f"B: {sample['option_b'][:50]}...")
        print(f"Correct: {sample['correct_answer']}")
    
    # Import to database
    print("\n💾 Importing questions to database...")
    if import_questions_to_db(questions):
        print("✅ Questions successfully imported to database!")
        print("🎯 New quiz category 'AWS Cloud Practitioner' is ready!")
    else:
        print("❌ Failed to import questions to database")

if __name__ == "__main__":
    main()
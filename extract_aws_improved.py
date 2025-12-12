#!/usr/bin/env python3
"""
Improved AWS Cloud Practitioner question extractor
Based on the analyzed PDF format
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
                if (page_num + 1) % 20 == 0:
                    print(f"Processed {page_num + 1} pages...")
                    
    except Exception as e:
        print(f"Error reading PDF: {e}")
        return ""
    
    return text

def parse_aws_questions(text):
    """Parse AWS questions from extracted text using improved logic"""
    questions = []
    lines = text.split('\n')
    
    i = 0
    question_count = 0
    
    while i < len(lines):
        line = lines[i].strip()
        
        # Look for question number pattern: "1. Question text..."
        question_match = re.match(r'^(\d+)\.\s+(.+)', line)
        
        if question_match:
            question_num = question_match.group(1)
            question_text = question_match.group(2)
            
            # Continue reading question text if it spans multiple lines
            i += 1
            while i < len(lines) and not re.match(r'^\s*-\s*[A-E]\.', lines[i]):
                if lines[i].strip() and not re.match(r'^(\d+)\.', lines[i]):
                    question_text += " " + lines[i].strip()
                i += 1
            
            # Now collect options A, B, C, D, E
            options = {}
            
            while i < len(lines):
                line = lines[i].strip()
                
                # Look for option pattern: "- A. Option text"
                option_match = re.match(r'^\s*-\s*([A-E])\.\s*(.+)', line)
                
                if option_match:
                    option_letter = option_match.group(1)
                    option_text = option_match.group(2)
                    
                    # Handle multi-line options
                    i += 1
                    while i < len(lines) and not re.match(r'^\s*-\s*[A-E]\.', lines[i]) and \
                          not re.match(r'^\s*Correct answer:', lines[i]) and \
                          not re.match(r'^(\d+)\.', lines[i]):
                        if lines[i].strip():
                            option_text += " " + lines[i].strip()
                        i += 1
                    
                    options[option_letter] = option_text
                    continue
                
                # Look for correct answer
                answer_match = re.match(r'^\s*Correct answer:\s*(.+)', line)
                if answer_match:
                    correct_answer = answer_match.group(1).strip()
                    
                    # Clean up answer (remove extra spaces, etc.)
                    correct_answer = re.sub(r'\s+', ' ', correct_answer)
                    
                    # Create question object
                    question_obj = {
                        'question_id': f'CP_{question_count + 1:04d}',  # Generate question_id like CP_0001
                        'question': question_text.strip(),
                        'option_a': options.get('A', ''),
                        'option_b': options.get('B', ''),
                        'option_c': options.get('C', ''),
                        'option_d': options.get('D', ''),
                        'option_e': options.get('E', ''),
                        'correct_answer': correct_answer,
                        'explanation': ''  # PDF doesn't seem to have explanations
                    }
                    
                    questions.append(question_obj)
                    question_count += 1
                    
                    if question_count % 50 == 0:
                        print(f"Extracted {question_count} questions...")
                    
                    # Move to next question
                    i += 1
                    break
                
                i += 1
                
                # If we've gone too far without finding an answer, break
                if i >= len(lines):
                    break
                    
        else:
            i += 1
    
    return questions

def validate_questions(questions):
    """Validate extracted questions"""
    valid_questions = []
    
    for i, q in enumerate(questions):
        issues = []
        
        # Check if question text exists
        if not q['question'].strip():
            issues.append("Empty question text")
        
        # Check if at least 2 options exist
        non_empty_options = sum(1 for opt in [q['option_a'], q['option_b'], q['option_c'], q['option_d']] if opt.strip())
        if non_empty_options < 2:
            issues.append("Less than 2 options")
        
        # Check if correct answer is specified
        if not q['correct_answer'].strip():
            issues.append("No correct answer")
        
        if issues:
            print(f"⚠️ Question {i+1} has issues: {', '.join(issues)}")
            print(f"   Question: {q['question'][:50]}...")
        else:
            valid_questions.append(q)
    
    print(f"✅ {len(valid_questions)} valid questions out of {len(questions)} extracted")
    return valid_questions

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
        cur.execute("SELECT COUNT(*) FROM questions WHERE category = %s", ('Cloud Practitioner Practice Test',))
        existing_count = cur.fetchone()[0]
        
        if existing_count > 0:
            print(f"Found {existing_count} existing Cloud Practitioner Practice Test questions")
            response = input("Do you want to replace them? (y/N): ")
            if response.lower() == 'y':
                cur.execute("DELETE FROM questions WHERE category = %s", ('Cloud Practitioner Practice Test',))
                print("Deleted existing questions")
            else:
                print("Keeping existing questions, adding new ones...")
        
        # Insert questions
        insert_query = """
        INSERT INTO questions (
            question_id, question, option_a, option_b, option_c, option_d, option_e,
            correct_answer, explanation, category, difficulty_level
        ) VALUES (
            %(question_id)s, %(question)s, %(option_a)s, %(option_b)s, %(option_c)s, %(option_d)s, %(option_e)s,
            %(correct_answer)s, %(explanation)s, 'Cloud Practitioner Practice Test', 'intermediate'
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
                print(f"Question: {question['question'][:50]}...")
                continue
        
        conn.commit()
        print(f"✅ Successfully imported {successful_imports} out of {len(questions)} questions")
        
        # Verify import
        cur.execute("SELECT COUNT(*) FROM questions WHERE category = 'Cloud Practitioner Practice Test'")
        total_count = cur.fetchone()[0]
        print(f"📊 Total Cloud Practitioner Practice Test questions in database: {total_count}")
        
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
        print(f"💾 Questions saved to {filename}")
    except Exception as e:
        print(f"Error saving to JSON: {e}")

def main():
    print("🚀 Starting AWS Cloud Practitioner question extraction...")
    print("📄 Expected: ~500 questions from practice tests")
    
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
    
    print(f"📋 Raw extraction: {len(questions)} questions")
    
    if not questions:
        print("❌ No questions found. Please check the PDF format.")
        return
    
    # Validate questions
    print("✅ Validating questions...")
    valid_questions = validate_questions(questions)
    
    if not valid_questions:
        print("❌ No valid questions found after validation.")
        return
    
    # Save to JSON for backup
    json_filename = "data/aws_practitioner_questions.json"
    save_questions_to_json(valid_questions, json_filename)
    
    # Display sample questions
    print("\n📋 Sample questions:")
    for i, sample in enumerate(valid_questions[:3]):
        print(f"\n{i+1}. {sample['question'][:100]}...")
        print(f"   A: {sample['option_a'][:60]}...")
        print(f"   B: {sample['option_b'][:60]}...")
        print(f"   C: {sample['option_c'][:60]}...")
        print(f"   D: {sample['option_d'][:60]}...")
        if sample['option_e']:
            print(f"   E: {sample['option_e'][:60]}...")
        print(f"   Correct: {sample['correct_answer']}")
    
    # Import to database
    print(f"\n💾 Importing {len(valid_questions)} questions to database...")
    if import_questions_to_db(valid_questions):
        print("✅ Questions successfully imported to database!")
        print("🎯 New quiz category 'Cloud Practitioner Practice Test' is ready!")
    else:
        print("❌ Failed to import questions to database")

if __name__ == "__main__":
    main()
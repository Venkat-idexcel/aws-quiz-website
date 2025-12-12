#!/usr/bin/env python3
"""
Import AWS Cloud Practitioner questions from PDF to database
Extracts questions, options, and correct answers from the parsed PDF text
"""

import os
import sys
import re
import PyPDF2
import psycopg2
from config import Config

def extract_text_from_pdf(pdf_path):
    """Extract text from PDF file"""
    print(f"📖 Extracting text from PDF: {pdf_path}")
    
    text = ""
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            print(f"📄 Found {len(pdf_reader.pages)} pages in PDF")
            
            for page_num, page in enumerate(pdf_reader.pages):
                try:
                    page_text = page.extract_text()
                    text += f"\n=== PAGE {page_num + 1} ===\n{page_text}\n"
                except Exception as e:
                    print(f"⚠️ Error reading page {page_num + 1}: {e}")
                    continue
                    
    except Exception as e:
        print(f"❌ Error reading PDF: {e}")
        return None
        
    print(f"✅ Successfully extracted {len(text)} characters from PDF")
    return text

def parse_questions_from_text(text):
    """Parse questions, options, and answers from extracted text"""
    questions = []
    
    # Split text into question blocks
    # Look for numbered questions (1., 2., etc.)
    question_pattern = r'(\d+)\.\s+(.+?)(?=\d+\.\s+|\Z)'
    question_blocks = re.findall(question_pattern, text, re.DOTALL)
    
    print(f"🔍 Found {len(question_blocks)} question blocks")
    
    for question_num, question_block in question_blocks:
        try:
            # Extract question text (everything before the first option)
            option_start = re.search(r'\s*-\s*[A-E]\.', question_block)
            if not option_start:
                print(f"⚠️ No options found for question {question_num}")
                continue
                
            question_text = question_block[:option_start.start()].strip()
            options_and_answer = question_block[option_start.start():].strip()
            
            # Extract options (A, B, C, D, E)
            option_pattern = r'-\s*([A-E])\.\s*(.+?)(?=-\s*[A-E]\.|Correct answer:|$)'
            option_matches = re.findall(option_pattern, options_and_answer, re.DOTALL)
            
            if len(option_matches) < 2:
                print(f"⚠️ Insufficient options for question {question_num}")
                continue
            
            # Clean up options
            options = {}
            for opt_letter, opt_text in option_matches:
                clean_text = re.sub(r'\s+', ' ', opt_text.strip())
                options[opt_letter] = clean_text
            
            # Extract correct answer
            answer_match = re.search(r'Correct answer:\s*([A-E,\s]+)', options_and_answer)
            if not answer_match:
                print(f"⚠️ No correct answer found for question {question_num}")
                continue
                
            correct_answer = answer_match.group(1).strip()
            
            # Handle multiple correct answers (e.g., "B, E")
            if ',' in correct_answer:
                # For multiple choice, take the first answer for now
                correct_answer = correct_answer.split(',')[0].strip()
            
            # Validate we have the correct answer option
            if correct_answer not in options:
                print(f"⚠️ Correct answer '{correct_answer}' not found in options for question {question_num}")
                continue
            
            # Create question dict
            question_data = {
                'question': question_text,
                'option_a': options.get('A', ''),
                'option_b': options.get('B', ''),
                'option_c': options.get('C', ''),
                'option_d': options.get('D', ''),
                'option_e': options.get('E', ''),
                'correct_answer': correct_answer,
                'category': 'AWS Cloud Practitioner'
            }
            
            questions.append(question_data)
            print(f"✅ Parsed question {question_num}: {question_text[:50]}...")
            
        except Exception as e:
            print(f"❌ Error parsing question {question_num}: {e}")
            continue
    
    return questions

def connect_to_database():
    """Connect to PostgreSQL database"""
    try:
        conn = psycopg2.connect(
            host=Config.DB_HOST,
            port=Config.DB_PORT,
            database=Config.DB_NAME,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD
        )
        print("✅ Connected to database successfully")
        return conn
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return None

def import_questions_to_db(questions):
    """Import questions to database"""
    if not questions:
        print("❌ No questions to import")
        return False
    
    conn = connect_to_database()
    if not conn:
        return False
    
    try:
        cur = conn.cursor()
        
        # Check if AWS Cloud Practitioner questions already exist
        cur.execute("SELECT COUNT(*) FROM questions WHERE category = %s", ('AWS Cloud Practitioner',))
        existing_count = cur.fetchone()[0]
        
        if existing_count > 0:
            response = input(f"⚠️ Found {existing_count} existing 'AWS Cloud Practitioner' questions. Replace them? (y/N): ")
            if response.lower() != 'y':
                print("❌ Import cancelled by user")
                return False
            
            # Delete existing questions
            cur.execute("DELETE FROM questions WHERE category = %s", ('AWS Cloud Practitioner',))
            print(f"🗑️ Deleted {existing_count} existing questions")
        
        # Insert new questions
        insert_query = """
            INSERT INTO questions (question, option_a, option_b, option_c, option_d, option_e, correct_answer, category)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        successful_imports = 0
        for i, q in enumerate(questions):
            try:
                cur.execute(insert_query, (
                    q['question'],
                    q['option_a'],
                    q['option_b'], 
                    q['option_c'],
                    q['option_d'],
                    q['option_e'] if q['option_e'] else None,  # Handle empty option E
                    q['correct_answer'],
                    q['category']
                ))
                successful_imports += 1
                if (i + 1) % 50 == 0:
                    print(f"📝 Imported {i + 1} questions...")
            except Exception as e:
                print(f"❌ Error importing question {i + 1}: {e}")
                continue
        
        conn.commit()
        print(f"✅ Successfully imported {successful_imports} out of {len(questions)} AWS Cloud Practitioner questions!")
        
        # Verify import
        cur.execute("SELECT COUNT(*) FROM questions WHERE category = %s", ('AWS Cloud Practitioner',))
        final_count = cur.fetchone()[0]
        print(f"📊 Total AWS Cloud Practitioner questions in database: {final_count}")
        
        return True
        
    except Exception as e:
        print(f"❌ Database import error: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def main():
    # First try PDF file, then fall back to sample text file
    pdf_path = r"c:\Users\venkatasai.p\Documents\aws_quiz_website\AWS_practitioner_practicetest_10.pdf"
    sample_text_path = r"c:\Users\venkatasai.p\Documents\aws_quiz_website\data\aws_pdf_sample.txt"
    
    text = None
    
    if os.path.exists(pdf_path):
        print("🚀 Starting AWS Cloud Practitioner question extraction from PDF...")
        text = extract_text_from_pdf(pdf_path)
    elif os.path.exists(sample_text_path):
        print("🚀 Using sample text file for AWS Cloud Practitioner questions...")
        with open(sample_text_path, 'r', encoding='utf-8') as f:
            text = f.read()
        print(f"✅ Successfully read {len(text)} characters from sample file")
    else:
        print(f"❌ Neither PDF nor sample text file found")
        print(f"Looked for: {pdf_path}")
        print(f"And: {sample_text_path}")
        return
    
    if not text:
        print("❌ Failed to extract text")
        return
    
    # Parse questions from text
    questions = parse_questions_from_text(text)
    
    if not questions:
        print("❌ No questions were parsed from the PDF")
        return
    
    print(f"📝 Successfully parsed {len(questions)} questions")
    
    # Show sample question
    if questions:
        sample = questions[0]
        print(f"\n📋 Sample question:")
        print(f"Q: {sample['question'][:100]}...")
        print(f"A: {sample['option_a'][:50]}...")
        print(f"Correct: {sample['correct_answer']}")
    
    # Import to database
    success = import_questions_to_db(questions)
    
    if success:
        print("🎉 AWS Cloud Practitioner quiz import completed successfully!")
    else:
        print("❌ Import failed")

if __name__ == "__main__":
    main()
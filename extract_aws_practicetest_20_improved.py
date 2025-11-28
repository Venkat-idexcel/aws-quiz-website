#!/usr/bin/env python3
"""
Improved AWS Practice Test 20 PDF Extractor
Handles the specific format of AWS_practioner_practicetest_20.pdf
"""

import re
import psycopg2
import json
from config import Config

def parse_questions_from_file():
    """Parse questions from the already extracted raw text file"""
    print("🔍 Parsing questions from extracted text...")
    
    with open("data/aws_practicetest_20_raw.txt", "r", encoding="utf-8") as f:
        text = f.read()
    
    # Split text into individual questions using the numbered pattern
    question_sections = re.split(r'\n\s*(\d+)\.\s+', text)[1:]  # Skip the first empty section
    
    questions = []
    
    # Process pairs: (number, content)
    for i in range(0, len(question_sections), 2):
        if i + 1 < len(question_sections):
            question_num = question_sections[i]
            question_content = question_sections[i + 1]
            
            # Parse this individual question
            parsed_question = parse_single_question(question_num, question_content)
            if parsed_question:
                questions.append(parsed_question)
            else:
                print(f"⚠️ Failed to parse question {question_num}")
    
    print(f"✅ Successfully parsed {len(questions)} questions")
    return questions

def parse_single_question(question_num, content):
    """Parse a single question from its content"""
    
    # Extract the question text (everything before the first option)
    question_match = re.match(r'^(.*?)(?=\s*-\s*[A-E]\.)', content.strip(), re.DOTALL)
    if not question_match:
        print(f"❌ Could not find question text for question {question_num}")
        return None
    
    question_text = question_match.group(1).strip()
    
    # Extract options using a more specific pattern for this format
    options = {}
    option_pattern = r'-\s*([A-E])\.\s+(.*?)(?=\s*-\s*[A-E]\.|(?:\s*Correct answer:)|\Z)'
    option_matches = re.findall(option_pattern, content, re.DOTALL)
    
    for letter, option_text in option_matches:
        # Clean up option text - remove extra whitespace and newlines
        clean_text = re.sub(r'\s+', ' ', option_text.strip())
        options[letter] = clean_text
    
    # Extract correct answer
    answer_match = re.search(r'Correct answer:\s*([A-E,\s]+)', content, re.IGNORECASE)
    if not answer_match:
        print(f"❌ Could not find answer for question {question_num}")
        return None
    
    correct_answer = answer_match.group(1).strip()
    # Clean up the answer format
    correct_answer = re.sub(r'\s*,\s*', ', ', correct_answer)
    correct_answer = correct_answer.upper()
    
    # Validate that we have minimum required components
    if not question_text or len(options) < 4 or not correct_answer:
        print(f"❌ Incomplete question {question_num}: Q={bool(question_text)}, Opts={len(options)}, Ans={bool(correct_answer)}")
        return None
    
    return {
        'number': question_num,
        'question': question_text,
        'options': options,
        'answer': correct_answer
    }

def get_next_question_id():
    """Get the next available question ID for Cloud Practitioner Practice Test"""
    config = Config()
    database_url = f'postgresql://{config.DB_USER}:{config.DB_PASSWORD}@{config.DB_HOST}:{config.DB_PORT}/{config.DB_NAME}'
    
    conn = psycopg2.connect(database_url)
    cursor = conn.cursor()
    
    # Find the highest existing CP_ question ID
    cursor.execute("""
        SELECT question_id FROM questions 
        WHERE category = 'Cloud Practitioner Practice Test' 
        AND question_id LIKE 'CP_%' 
        ORDER BY question_id DESC 
        LIMIT 1
    """)
    
    result = cursor.fetchone()
    if result:
        last_id = result[0]  # e.g., 'CP_0499'
        next_num = int(last_id.split('_')[1]) + 1
    else:
        next_num = 1
    
    cursor.close()
    conn.close()
    
    return next_num

def save_questions_to_database(questions):
    """Save extracted questions to the database"""
    config = Config()
    database_url = f'postgresql://{config.DB_USER}:{config.DB_PASSWORD}@{config.DB_HOST}:{config.DB_PORT}/{config.DB_NAME}'
    
    conn = psycopg2.connect(database_url)
    cursor = conn.cursor()
    
    # Get starting question ID number
    next_num = get_next_question_id()
    
    successful_imports = 0
    failed_imports = 0
    
    for q in questions:
        try:
            question_id = f"CP_{next_num:04d}"
            
            # Ensure all options are present (fill missing with empty string)
            option_a = q['options'].get('A', '')
            option_b = q['options'].get('B', '')
            option_c = q['options'].get('C', '')
            option_d = q['options'].get('D', '')
            option_e = q['options'].get('E', '')
            
            # Insert into database
            cursor.execute("""
                INSERT INTO questions (
                    question_id, question, option_a, option_b, option_c, option_d, option_e,
                    correct_answer, category, explanation
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                question_id,
                q['question'],
                option_a,
                option_b,
                option_c,
                option_d,
                option_e,
                q['answer'],
                'Cloud Practitioner Practice Test',
                ''  # No explanation provided in this format
            ))
            
            successful_imports += 1
            next_num += 1  # Increment for next question
            print(f"✅ Imported question {question_id}: {q['question'][:60]}...")
            
        except Exception as e:
            failed_imports += 1
            print(f"❌ Failed to import question {q['number']}: {e}")
            print(f"   Question: {q['question'][:100]}...")
            continue
    
    conn.commit()
    cursor.close()
    conn.close()
    
    print(f"\n📊 Import Summary:")
    print(f"✅ Successful imports: {successful_imports}")
    print(f"❌ Failed imports: {failed_imports}")
    print(f"📝 Total questions processed: {len(questions)}")
    
    return successful_imports

def main():
    """Main extraction and import process"""
    print("🚀 Starting improved AWS Practice Test 20 extraction...")
    
    # Parse questions from the existing raw text file
    questions = parse_questions_from_file()
    
    if not questions:
        print("❌ No questions parsed! Check the text file format.")
        return
    
    # Save processed questions as JSON for review
    with open("data/aws_practicetest_20_questions_improved.json", "w", encoding="utf-8") as f:
        json.dump(questions, f, indent=2, ensure_ascii=False)
    print("💾 Processed questions saved to data/aws_practicetest_20_questions_improved.json")
    
    # Show a sample question for verification
    if questions:
        print("\n📝 Sample question:")
        sample = questions[0]
        print(f"Question {sample['number']}: {sample['question'][:100]}...")
        for letter, option in sample['options'].items():
            print(f"  {letter}. {option[:80]}...")
        print(f"Answer: {sample['answer']}")
        
        # Ask for confirmation
        print(f"\n🤔 Found {len(questions)} questions. Import to database? (y/n): ", end="")
        response = input().lower().strip()
        
        if response in ['y', 'yes']:
            print("\n🗄️ Starting database import...")
            imported_count = save_questions_to_database(questions)
            
            if imported_count > 0:
                print(f"\n🎉 Successfully added {imported_count} new questions to Cloud Practitioner Practice Test!")
                print(f"📊 Total questions in database: {get_next_question_id() - 1}")
            else:
                print("\n❌ No questions were imported.")
        else:
            print("\n❌ Import cancelled by user.")
    else:
        print("\n❌ No valid questions to import.")

if __name__ == "__main__":
    main()
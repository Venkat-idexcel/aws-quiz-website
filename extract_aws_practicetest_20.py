#!/usr/bin/env python3
"""
AWS Practice Test 20 PDF Extractor
Extracts questions from AWS_practioner_practicetest_20.pdf and adds them to the existing 
Cloud Practitioner Practice Test category in the database.
"""

import PyPDF2
import re
import psycopg2
import json
from config import Config

def extract_pdf_text(pdf_path):
    """Extract text from PDF file"""
    print(f"📄 Opening PDF: {pdf_path}")
    
    with open(pdf_path, 'rb') as file:
        pdf_reader = PyPDF2.PdfReader(file)
        print(f"📊 Total pages: {len(pdf_reader.pages)}")
        
        # Extract text from all pages
        full_text = ""
        for page_num in range(len(pdf_reader.pages)):
            page = pdf_reader.pages[page_num]
            text = page.extract_text()
            full_text += text + "\n\n"
            print(f"📖 Processed page {page_num + 1}")
        
    return full_text

def parse_questions(text):
    """Parse questions from the extracted text"""
    print("🔍 Parsing questions from text...")
    
    # Split text into potential questions - look for numbered patterns
    question_patterns = [
        r'\n(\d+)\.\s+(.+?)(?=\n\d+\.\s+|\nAnswer[s]?[:\s]|\n[A-E]\.\s+|\Z)',
        r'\nQuestion\s+(\d+)[:\s]+(.+?)(?=\nQuestion\s+\d+|\nAnswer[s]?[:\s]|\n[A-E]\.\s+|\Z)',
        r'^(\d+)\.\s+(.+?)(?=^\d+\.\s+|\nAnswer[s]?[:\s]|\n[A-E]\.\s+|\Z)'
    ]
    
    questions = []
    
    # Try different question patterns
    for pattern in question_patterns:
        matches = re.findall(pattern, text, re.MULTILINE | re.DOTALL | re.IGNORECASE)
        if matches:
            print(f"✅ Found {len(matches)} questions using pattern")
            for match in matches:
                if len(match) == 2:
                    num, content = match
                    questions.append({
                        'number': num,
                        'content': content.strip()
                    })
            break
    
    if not questions:
        print("❌ No questions found with numbered patterns. Trying alternative approach...")
        # Split by likely question boundaries
        sections = re.split(r'\n(?=\d+\.\s+)', text)
        for i, section in enumerate(sections[1:], 1):  # Skip first empty section
            if len(section.strip()) > 50:  # Minimum question length
                questions.append({
                    'number': str(i),
                    'content': section.strip()
                })
    
    print(f"📝 Total questions extracted: {len(questions)}")
    return questions

def extract_question_components(question_text):
    """Extract question, options, and answer from question text"""
    
    # Clean up the text
    text = question_text.strip()
    
    # Try to find the main question (everything before options)
    question_match = re.search(r'^(.*?)(?=\n[A-E]\.\s+)', text, re.DOTALL)
    if question_match:
        question = question_match.group(1).strip()
    else:
        # If no clear options, take first substantial part
        lines = text.split('\n')
        question_lines = []
        for line in lines[:10]:  # Look at first 10 lines
            if re.match(r'^[A-E]\.\s+', line):
                break
            if len(line.strip()) > 10:
                question_lines.append(line.strip())
        question = ' '.join(question_lines)
    
    # Extract options A-E
    options = {}
    option_pattern = r'^([A-E])\.\s+(.+?)(?=\n[A-E]\.\s+|\nAnswer|\nCorrect|\n\n|\Z)'
    option_matches = re.findall(option_pattern, text, re.MULTILINE | re.DOTALL)
    
    for letter, content in option_matches:
        options[letter] = content.strip()
    
    # If no options found, try alternative pattern
    if not options:
        lines = text.split('\n')
        current_option = None
        for line in lines:
            option_start = re.match(r'^([A-E])\.\s+(.+)', line)
            if option_start:
                letter, content = option_start.groups()
                options[letter] = content.strip()
                current_option = letter
            elif current_option and line.strip() and not re.match(r'^[A-E]\.\s+', line):
                # Continue previous option
                if len(line.strip()) < 100:  # Avoid adding question text
                    options[current_option] += ' ' + line.strip()
    
    # Extract correct answer
    answer = None
    answer_patterns = [
        r'(?:Answer|Correct)[:\s]+([A-E,\s]+)',
        r'(?:Correct\s+Answer)[:\s]+([A-E,\s]+)',
        r'Answer:\s*([A-E,\s]+)',
        r'\nAnswer\s+([A-E,\s]+)',
    ]
    
    for pattern in answer_patterns:
        answer_match = re.search(pattern, text, re.IGNORECASE)
        if answer_match:
            answer = answer_match.group(1).strip().upper()
            break
    
    # Clean up answer - handle multiple answers
    if answer:
        # Remove extra spaces and clean up format
        answer = re.sub(r'\s+', ' ', answer)
        answer = re.sub(r'[,\s]+', ', ', answer)
        answer = answer.strip(', ')
    
    return {
        'question': question,
        'options': options,
        'answer': answer
    }

def save_questions_to_database(questions):
    """Save extracted questions to the database"""
    config = Config()
    database_url = f'postgresql://{config.DB_USER}:{config.DB_PASSWORD}@{config.DB_HOST}:{config.DB_PORT}/{config.DB_NAME}'
    
    conn = psycopg2.connect(database_url)
    cursor = conn.cursor()
    
    # Get starting question ID
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
    
    successful_imports = 0
    failed_imports = 0
    
    for i, q in enumerate(questions):
        try:
            question_id = f"CP_{next_num:04d}"
            
            # Ensure all options are present
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
            print(f"✅ Imported question {question_id}: {q['question'][:50]}...")
            
        except Exception as e:
            failed_imports += 1
            print(f"❌ Failed to import question {i+1}: {e}")
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
    print("🚀 Starting AWS Practice Test 20 extraction...")
    
    pdf_path = "data/AWS_practioner_practicetest_20.pdf"
    
    # Step 1: Extract text from PDF
    text = extract_pdf_text(pdf_path)
    
    # Save raw text for debugging
    with open("data/aws_practicetest_20_raw.txt", "w", encoding="utf-8") as f:
        f.write(text)
    print("💾 Raw text saved to data/aws_practicetest_20_raw.txt")
    
    # Step 2: Parse questions
    raw_questions = parse_questions(text)
    
    if not raw_questions:
        print("❌ No questions found! Check the PDF format.")
        return
    
    # Step 3: Extract question components
    print("🔧 Processing question components...")
    processed_questions = []
    
    for q in raw_questions:
        components = extract_question_components(q['content'])
        
        # Validate question has minimum required components
        if (components['question'] and 
            len(components['options']) >= 4 and 
            components['answer']):
            
            processed_questions.append(components)
        else:
            print(f"⚠️ Skipping incomplete question {q['number']}")
    
    print(f"✅ Processed {len(processed_questions)} valid questions")
    
    # Save processed questions as JSON for review
    with open("data/aws_practicetest_20_questions.json", "w", encoding="utf-8") as f:
        json.dump(processed_questions, f, indent=2, ensure_ascii=False)
    print("💾 Processed questions saved to data/aws_practicetest_20_questions.json")
    
    # Step 4: Import to database
    if processed_questions:
        print("\n🗄️ Starting database import...")
        imported_count = save_questions_to_database(processed_questions)
        
        if imported_count > 0:
            print(f"\n🎉 Successfully added {imported_count} new questions to Cloud Practitioner Practice Test!")
        else:
            print("\n❌ No questions were imported.")
    else:
        print("\n❌ No valid questions to import.")

if __name__ == "__main__":
    main()
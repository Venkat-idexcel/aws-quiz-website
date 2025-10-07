#!/usr/bin/env python3
"""
AWS Questions Loader Script
Parses the AWS questions text file and loads them into the database
Handles both single and multiple-choice questions properly
"""

import psycopg2
import psycopg2.extras
import re
from datetime import datetime

# Database Configuration (AWS RDS)
DB_CONFIG = {
    'host': 'los-dev-psql-rdsclstr-new.cj6duvm27hk9.us-east-1.rds.amazonaws.com',
    'port': 3306,
    'database': 'cretificate_quiz_db',
    'user': 'postgres',
    'password': 'poc2*&(SRWSjnjkn@#@#'
}

def clean_text(text):
    """Clean text by removing PDF stamps and unwanted content"""
    if not text:
        return text
    
    # Remove IT Exam Dumps stamp variations
    text = re.sub(r'IT Exam Dumps.*?VCEup\.com', '', text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r'IT Exam Dumps.*?Learn Anything.*?VCEup\.com', '', text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r'Learn Anything.*?VCEup\.com', '', text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r'VCEup\.com', '', text, flags=re.IGNORECASE)
    
    # Remove other common PDF stamps
    text = re.sub(r'www\..*?\.com', '', text, flags=re.IGNORECASE)
    text = re.sub(r'https?://[^\s]+', '', text, flags=re.IGNORECASE)
    
    # Clean up extra whitespace and newlines
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()
    
    return text

def parse_questions_file(file_path):
    """Parse the AWS questions text file and extract all questions"""
    questions = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        # Clean the entire content first
        content = clean_text(content)
        
        # Split content by question markers
        question_blocks = content.split('QUESTION ')
        
        for i, block in enumerate(question_blocks[1:], 1):  # Skip the header block
            try:
                # Extract question number
                question_match = re.search(r'^(\d+)', block)
                if not question_match:
                    continue
                
                question_num = int(question_match.group(1))
                
                # Find the question text (everything between dashes and first option A)
                question_pattern = r'-{2,}\s*(.*?)\s*A\.'
                question_match = re.search(question_pattern, block, re.DOTALL)
                
                if not question_match:
                    print(f"⚠️ Could not extract question text for question {question_num}")
                    continue
                
                question_text = clean_text(question_match.group(1).strip())
                
                # Extract options A, B, C, D, E
                options = {}
                option_pattern = r'([A-E])\.\s*(.*?)(?=\s*[A-E]\.|Correct Answer:|$)'
                
                option_matches = re.findall(option_pattern, block, re.DOTALL)
                
                for letter, text in option_matches:
                    # Clean up option text
                    option_text = clean_text(text.strip())
                    if option_text:  # Only add non-empty options
                        options[letter] = option_text
                
                # Extract correct answer
                answer_pattern = r'Correct Answer:\s*([A-E]+)'
                answer_match = re.search(answer_pattern, block)
                
                if not answer_match:
                    print(f"⚠️ Could not extract correct answer for question {question_num}")
                    continue
                
                correct_answer = answer_match.group(1).strip()
                
                # Validate correct answer contains only valid options
                if not all(c in 'ABCDE' for c in correct_answer):
                    print(f"⚠️ Invalid correct answer format for question {question_num}: {correct_answer}")
                    continue
                
                # Determine if it's multiple choice
                is_multiselect = len(correct_answer) > 1
                
                # Ensure we have at least options A and B
                if 'A' not in options or 'B' not in options:
                    print(f"⚠️ Missing required options A or B for question {question_num}")
                    print(f"   Available options: {list(options.keys())}")
                    continue
                
                # Validate that correct answer letters exist in options
                missing_options = [c for c in correct_answer if c not in options]
                if missing_options:
                    print(f"⚠️ Correct answer references missing options for question {question_num}: {missing_options}")
                    continue
                
                # Create question object
                question_obj = {
                    'question_num': question_num,
                    'question': question_text,
                    'option_a': options.get('A', ''),
                    'option_b': options.get('B', ''),
                    'option_c': options.get('C', ''),
                    'option_d': options.get('D', ''),
                    'option_e': options.get('E', ''),
                    'correct_answer': correct_answer,
                    'is_multiselect': is_multiselect,
                    'category': 'AWS Cloud Practitioner',
                    'difficulty_level': 'Intermediate'
                }
                
                questions.append(question_obj)
                
                if question_num % 50 == 0:
                    print(f"📝 Processed {question_num} questions...")
                
                # Debug output for first few questions
                if question_num <= 3:
                    print(f"   Q{question_num}: {question_text[:60]}...")
                    print(f"   Options: {list(options.keys())}")
                    print(f"   Answer: {correct_answer} ({'Multi' if is_multiselect else 'Single'})")
                    
            except Exception as e:
                print(f"❌ Error processing question {i}: {e}")
                continue
    
    except Exception as e:
        print(f"❌ Error reading file: {e}")
        return []
    
    print(f"✅ Successfully parsed {len(questions)} questions")
    return questions

def test_database_connection():
    """Test connection to the database"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        conn.close()
        print("✅ Database connection successful")
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def clear_existing_questions():
    """Clear existing questions from database"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        # Get count of existing questions
        cur.execute("SELECT COUNT(*) FROM aws_questions")
        existing_count = cur.fetchone()[0]
        
        if existing_count > 0:
            response = input(f"⚠️ Found {existing_count} existing questions. Delete them? (yes/no): ").lower()
            if response in ['yes', 'y']:
                cur.execute("DELETE FROM aws_questions")
                conn.commit()
                print(f"🗑️ Deleted {existing_count} existing questions")
            else:
                print("ℹ️ Keeping existing questions. New questions will be added.")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error clearing existing questions: {e}")
        return False

def load_questions_to_database(questions):
    """Load questions into the database"""
    if not questions:
        print("❌ No questions to load")
        return False
    
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        # Prepare insert statement
        insert_sql = """
            INSERT INTO aws_questions 
            (question, option_a, option_b, option_c, option_d, option_e, correct_answer, 
             is_multiselect, category, difficulty_level, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        successful_inserts = 0
        
        for i, q in enumerate(questions, 1):
            try:
                # Handle option_e if it exists - we'll put it in option_d if option_d is empty
                option_c = q['option_c'] or None
                option_d = q['option_d'] or None
                option_e = q['option_e'] or None

                cur.execute(insert_sql, (
                    q['question'],
                    q['option_a'],
                    q['option_b'], 
                    option_c,
                    option_d,
                    option_e,
                    q['correct_answer'],
                    q['is_multiselect'],
                    q['category'],
                    q['difficulty_level'],
                    datetime.now()
                ))
                
                successful_inserts += 1
                
                if i % 100 == 0:
                    conn.commit()
                    print(f"💾 Saved {i}/{len(questions)} questions...")
                    
            except Exception as e:
                print(f"❌ Error inserting question {q['question_num']}: {e}")
                continue
        
        # Final commit
        conn.commit()
        conn.close()
        
        print(f"✅ Successfully loaded {successful_inserts} questions into database")
        return True
        
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False

def validate_loaded_questions():
    """Validate that questions were loaded correctly"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        # Get total count
        cur.execute("SELECT COUNT(*) FROM aws_questions")
        total_count = cur.fetchone()[0]
        
        # Get multiselect count
        cur.execute("SELECT COUNT(*) FROM aws_questions WHERE is_multiselect = true")
        multiselect_count = cur.fetchone()[0]
        
        # Get single select count
        cur.execute("SELECT COUNT(*) FROM aws_questions WHERE is_multiselect = false")
        single_select_count = cur.fetchone()[0]
        
        # Sample some questions
        cur.execute("SELECT question, correct_answer, is_multiselect FROM aws_questions LIMIT 5")
        sample_questions = cur.fetchall()
        
        conn.close()
        
        print(f"\n📊 Database Validation Results:")
        print(f"Total Questions: {total_count}")
        print(f"Single Choice: {single_select_count}")
        print(f"Multiple Choice: {multiselect_count}")
        
        print(f"\n📋 Sample Questions:")
        for i, (question, answer, is_multi) in enumerate(sample_questions, 1):
            question_preview = question[:60] + "..." if len(question) > 60 else question
            choice_type = "Multiple" if is_multi else "Single"
            print(f"  {i}. [{choice_type}] {question_preview} → {answer}")
        
        return True
        
    except Exception as e:
        print(f"❌ Validation error: {e}")
        return False

def main():
    """Main function"""
    print("🚀 AWS Questions Database Loader")
    print("=" * 50)
    
    # File path to your questions
    questions_file = r"C:\Users\venkatasai.p\Documents\AWS_Questions_20250915_091740.txt"
    
    # Test database connection
    print("🔍 Testing database connection...")
    if not test_database_connection():
        return
    
    # Clear existing questions if user wants
    print("\n🗑️ Checking for existing questions...")
    if not clear_existing_questions():
        return
    
    # Parse questions file
    print(f"\n📖 Reading questions from: {questions_file}")
    questions = parse_questions_file(questions_file)
    
    if not questions:
        print("❌ No questions found or failed to parse file")
        return
    
    # Load questions to database
    print(f"\n💾 Loading {len(questions)} questions to database...")
    if not load_questions_to_database(questions):
        return
    
    # Validate results
    print("\n🔍 Validating loaded questions...")
    validate_loaded_questions()
    
    print(f"\n🎉 Question loading completed successfully!")
    print("You can now run your quiz application with all questions loaded.")

if __name__ == "__main__":
    main()
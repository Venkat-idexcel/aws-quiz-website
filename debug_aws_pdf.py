#!/usr/bin/env python3
"""
Debug and examine the AWS PDF structure
"""

import PyPDF2
import re

def extract_pdf_sample(pdf_path, max_pages=3):
    """Extract sample text from first few pages to understand structure"""
    try:
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            print(f"PDF has {len(reader.pages)} pages")
            
            sample_text = ""
            for i in range(min(max_pages, len(reader.pages))):
                page_text = reader.pages[i].extract_text()
                sample_text += f"\n=== PAGE {i+1} ===\n"
                sample_text += page_text + "\n"
                
            return sample_text
    except Exception as e:
        print(f"Error reading PDF: {e}")
        return ""

def analyze_structure(text):
    """Analyze text structure to identify question patterns"""
    lines = text.split('\n')
    patterns_found = {
        'question_numbers': [],
        'options': [],
        'answers': [],
        'set_headers': []
    }
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Look for question numbers (various formats)
        if re.match(r'^(\d+)[\.\)]\s', line):
            patterns_found['question_numbers'].append(line[:100])
        
        # Look for options (A, B, C, D, E)
        if re.match(r'^([A-E])[\.\)]\s', line):
            patterns_found['options'].append(line[:80])
        
        # Look for answers
        if re.search(r'(?:answer|correct|solution):\s*([A-E])', line, re.IGNORECASE):
            patterns_found['answers'].append(line[:100])
        
        # Look for set headers
        if re.search(r'(?:set|test|practice)\s*(\d+)', line, re.IGNORECASE):
            patterns_found['set_headers'].append(line[:100])
    
    return patterns_found

def main():
    pdf_path = "data/AWS_practioner_practicetest_10.pdf"
    print(f"📖 Analyzing PDF structure: {pdf_path}")
    
    # Extract sample text
    sample_text = extract_pdf_sample(pdf_path, 5)
    
    # Save sample to file for inspection
    with open('data/aws_pdf_sample.txt', 'w', encoding='utf-8') as f:
        f.write(sample_text)
    print("📝 Saved sample text to data/aws_pdf_sample.txt")
    
    # Analyze patterns
    patterns = analyze_structure(sample_text)
    
    print("\n🔍 Pattern Analysis:")
    print(f"Question numbers found: {len(patterns['question_numbers'])}")
    if patterns['question_numbers']:
        print("Sample question patterns:")
        for pattern in patterns['question_numbers'][:5]:
            print(f"  - {pattern}")
    
    print(f"\nOptions found: {len(patterns['options'])}")
    if patterns['options']:
        print("Sample option patterns:")
        for pattern in patterns['options'][:5]:
            print(f"  - {pattern}")
    
    print(f"\nAnswers found: {len(patterns['answers'])}")
    if patterns['answers']:
        print("Sample answer patterns:")
        for pattern in patterns['answers'][:5]:
            print(f"  - {pattern}")
    
    print(f"\nSet headers found: {len(patterns['set_headers'])}")
    if patterns['set_headers']:
        print("Sample set patterns:")
        for pattern in patterns['set_headers'][:5]:
            print(f"  - {pattern}")
    
    print("\n💡 Please check data/aws_pdf_sample.txt to see the actual text format")
    print("    Then we can adjust the parsing logic accordingly")

if __name__ == "__main__":
    main()
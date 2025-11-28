import json
import re

def clean_answer(answer):
    """Clean and standardize answer format"""
    if not answer:
        return answer
    
    # Remove all whitespace and newlines
    cleaned = re.sub(r'\s+', '', answer)
    
    # Handle multiple choice answers - convert to comma-separated format
    # E.g., "AB" -> "A,B", "ACD" -> "A,C,D"
    if len(cleaned) > 1 and all(c in 'ABCDE' for c in cleaned):
        cleaned = ','.join(sorted(cleaned))
    
    return cleaned

def fix_questions_file():
    """Fix the questions file by cleaning up answer formats"""
    try:
        # Load original questions
        with open("data/aws_practicetest_20_questions_improved.json", "r", encoding="utf-8") as f:
            questions = json.load(f)
        
        print(f"Loaded {len(questions)} questions to clean...")
        
        # Clean answers
        cleaned_count = 0
        answer_changes = {}
        
        for i, q in enumerate(questions):
            original_answer = q["answer"]
            cleaned_answer = clean_answer(original_answer)
            
            if original_answer != cleaned_answer:
                cleaned_count += 1
                answer_changes[i+1] = (original_answer, cleaned_answer)
                q["answer"] = cleaned_answer
        
        print(f"\nCleaned {cleaned_count} answers:")
        
        # Show sample changes
        for q_num, (original, cleaned) in list(answer_changes.items())[:10]:
            print(f"  Question {q_num}: '{original}' -> '{cleaned}'")
        
        if len(answer_changes) > 10:
            print(f"  ... and {len(answer_changes) - 10} more")
        
        # Check final answer lengths
        answer_lengths = {}
        long_answers = []
        
        for i, q in enumerate(questions):
            answer = q["answer"]
            length = len(answer)
            
            if length > 10:
                long_answers.append((i+1, answer, length))
            
            answer_lengths[length] = answer_lengths.get(length, 0) + 1
        
        print(f"\nFinal answer length distribution:")
        for length in sorted(answer_lengths.keys()):
            count = answer_lengths[length]
            status = "❌" if length > 10 else "✅"
            print(f"  {status} {length} chars: {count} questions")
        
        if long_answers:
            print(f"\n❌ Still have {len(long_answers)} questions with long answers:")
            for q_num, answer, length in long_answers:
                print(f"  Question {q_num}: '{answer}' (length: {length})")
        else:
            print(f"\n✅ All answers are now within 10-character limit!")
        
        # Save cleaned questions
        with open("data/aws_practicetest_20_questions_cleaned.json", "w", encoding="utf-8") as f:
            json.dump(questions, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Saved cleaned questions to: data/aws_practicetest_20_questions_cleaned.json")
        
        return questions
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    fix_questions_file()
import json

# Load and analyze the questions for any long correct_answer values
try:
    with open("data/aws_practicetest_20_questions_improved.json", "r", encoding="utf-8") as f:
        questions = json.load(f)
    
    print(f"Analyzing {len(questions)} questions for correct_answer lengths...")
    
    answer_lengths = {}
    long_answers = []
    
    for i, q in enumerate(questions):
        answer = q["answer"]
        length = len(answer)
        
        if length > 10:
            long_answers.append((i+1, answer, length))
        
        answer_lengths[length] = answer_lengths.get(length, 0) + 1
    
    print("\nCorrect answer length distribution:")
    for length in sorted(answer_lengths.keys()):
        count = answer_lengths[length]
        status = "❌" if length > 10 else "✅"
        print(f"  {status} {length} chars: {count} questions")
    
    if long_answers:
        print(f"\n❌ Found {len(long_answers)} questions with answers longer than 10 characters:")
        for q_num, answer, length in long_answers[:10]:  # Show first 10
            print(f"  Question {q_num}: '{answer}' (length: {length})")
        
        if len(long_answers) > 10:
            print(f"  ... and {len(long_answers) - 10} more")
    else:
        print("\n✅ All answers are within 10-character limit")
    
    # Let's also check for any unusual answer formats
    unique_answers = set(q["answer"] for q in questions)
    print(f"\nUnique answer values found: {sorted(unique_answers)}")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
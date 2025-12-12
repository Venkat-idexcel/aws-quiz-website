import json

# Check aws_practitioner_questions.json
with open('data/aws_practitioner_questions.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
    print(f'Total questions in aws_practitioner_questions.json: {len(data)}')
    print(f'Last ID: {data[-1]["question_id"]}')
    
    # Look for the load balancer question
    for q in data:
        if 'load balancer types are available' in q['question'].lower():
            print(f'\nFound: {q["question_id"]}')
            print(f'Answer: {q["correct_answer"]}')
            break

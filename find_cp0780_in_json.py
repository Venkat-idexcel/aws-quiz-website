import json

# Check if CP_0780 is in our JSON mapping
with open('data/aws_practicetest_20_questions_cleaned.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
    
# CP_0780 would be around index 280 (780 - 500)
index = 280
if index < len(data):
    q = data[index]
    print(f"Index {index}:")
    print(f"Question: {q['question'][:80]}")
    print(f"Options E: {q['options'].get('E', 'N/A')[:100]}")
    print(f"Answer: {q['answer']}")
    print()

# Also search for the load balancer question
for i, q in enumerate(data):
    if 'load balancer types are available' in q['question'].lower():
        print(f"Found at index {i} (would be CP_{500+i:04d}):")
        print(f"Question: {q['question'][:80]}")
        print(f"Option E: {q['options'].get('E', 'N/A')[:100]}")
        print(f"Answer: {q['answer']}")
        break

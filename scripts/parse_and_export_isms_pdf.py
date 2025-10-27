#!/usr/bin/env python3
"""
Parse the ISMS Awareness PDF into CSV and JSON sample.

Usage:
  python scripts/parse_and_export_isms_pdf.py "../ISMS Awareness question.pdf"

This script uses PyPDF2 to extract text and then heuristically parses questions and options.
It writes a CSV to data/isms_parsed.csv and a JSON sample to data/isms_sample.json.
"""
import sys
import re
import csv
import json
from pathlib import Path

try:
    from PyPDF2 import PdfReader
except Exception as e:
    print("PyPDF2 not installed. Run: pip install PyPDF2")
    raise


def extract_text_from_pdf(path):
    reader = PdfReader(path)
    texts = []
    for page in reader.pages:
        try:
            texts.append(page.extract_text() or '')
        except Exception:
            texts.append('')
    return '\n'.join(texts)


def split_into_questions(full_text):
    # Normalize newlines
    text = re.sub(r"\r\n|\r", "\n", full_text)

    # Remove repeated multiple newlines
    text = re.sub(r"\n{2,}", "\n\n", text)

    # Split at lines that start with a question number: e.g., '1.' or '12.' or '1)'
    parts = re.split(r"\n(?=\s*\d{1,3}\s*[\.)]\s+)", text)

    questions = []
    for part in parts:
        # Each part may contain multiple questions if PDF formatting joined them; attempt to find the first number
        m = re.match(r"\s*(\d{1,3})\s*[\.)]\s*(.*)$", part, flags=re.S)
        if m:
            # Remove the leading number
            qtext = re.sub(r"^\s*\d{1,3}\s*[\.)]\s*", "", part, count=1)
            questions.append(qtext.strip())
    return questions


def parse_question_block(block):
    # Try to extract options A-E
    # Options often start with 'A.' or 'A)'
    options = {'A': '', 'B': '', 'C': '', 'D': '', 'E': ''}

    # Attempt to find an 'Answer' or 'Key' inside block
    answer = None
    ans_match = re.search(r"\bAnswer[:\s]*([A-E]{1,5})\b", block, flags=re.IGNORECASE)
    if ans_match:
        answer = ans_match.group(1).upper()

    # Find option labels
    # Options pattern captures lines like '\nA. text' up to before next option
    opt_pattern = r"(^|\n)\s*([A-E])\s*[\.|\)]\s*(.*?)((?=\n\s*[A-E]\s*[\.|\)] )|\Z)"
    matches = re.findall(opt_pattern, block, flags=re.S | re.I)
    for m in matches:
        letter = m[1].upper()
        text = m[2].strip().replace('\n', ' ')
        options[letter] = text

    # If no explicit options found, try inline patterns like 'A. option B. option'
    if not any(options.values()):
        inline_matches = re.findall(r"([A-E])\s*[\.|\)]\s*([^A-E\n]{5,}?)\s*(?=[A-E]\s*[\.|\)]|$)", block)
        for letter, txt in inline_matches:
            options[letter.upper()] = txt.strip()

    # The question text is the block up to the first option
    split_at = None
    first_opt = re.search(r"\n\s*[A-E]\s*[\.|\)]\s", block)
    if first_opt:
        split_at = first_opt.start()
    if split_at:
        question_text = block[:split_at].strip().replace('\n', ' ')
    else:
        # Fallback: take first 200 chars as question
        question_text = block.strip().split('\n')[0][:800]

    # Clean question text
    question_text = re.sub(r"\s+", ' ', question_text).strip()

    return {
        'question': question_text,
        'option_a': options['A'],
        'option_b': options['B'],
        'option_c': options['C'],
        'option_d': options['D'],
        'option_e': options['E'],
        'correct_answer': answer or '',
        'explanation': ''
    }


def main(pdf_path):
    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        print(f"PDF not found: {pdf_path}")
        return 1

    print(f"Extracting text from {pdf_path}...")
    text = extract_text_from_pdf(str(pdf_path))
    print("Splitting into question blocks...")
    blocks = split_into_questions(text)
    print(f"Found {len(blocks)} question-like blocks")

    parsed = []
    for b in blocks:
        parsed.append(parse_question_block(b))

    out_dir = Path(pdf_path.parent) / 'data'
    out_dir.mkdir(exist_ok=True)
    csv_path = out_dir / 'isms_parsed.csv'
    json_path = out_dir / 'isms_sample.json'

    # Write CSV
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['question','option_a','option_b','option_c','option_d','option_e','correct_answer','explanation','category'])
        writer.writeheader()
        for p in parsed:
            row = p.copy()
            row['category'] = 'ISMS Awareness'
            writer.writerow(row)

    # Write JSON sample (first 20)
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(parsed[:20], f, ensure_ascii=False, indent=2)

    print(f"Wrote CSV: {csv_path}")
    print(f"Wrote JSON sample: {json_path}")
    print("Sample parsed questions:")
    for i, q in enumerate(parsed[:10], start=1):
        print(f"{i}. {q['question'][:120]}...")

    return 0


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python scripts/parse_and_export_isms_pdf.py <path-to-pdf>")
        sys.exit(1)
    sys.exit(main(sys.argv[1]))

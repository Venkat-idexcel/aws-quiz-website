#!/usr/bin/env python3
"""
Import parsed CSV into the questions table.

Usage:
  python scripts/import_csv_to_db.py data/isms_parsed.csv

This will read the CSV and insert rows into the `questions` table.
It will skip duplicates by question text or question_id.
"""
import sys
import csv
from pathlib import Path
import hashlib
import psycopg2
from psycopg2.extras import DictCursor
from config import Config


def generate_question_id(text):
    # deterministic id from hash of question text
    h = hashlib.sha1(text.encode('utf-8')).hexdigest()[:10]
    return f"ISMS-{h}"


def main(csv_path):
    csv_path = Path(csv_path)
    if not csv_path.exists():
        print(f"CSV file not found: {csv_path}")
        return 1

    conf = Config()

    conn = None
    try:
        conn = psycopg2.connect(
            host=conf.DB_HOST,
            port=conf.DB_PORT,
            database=conf.DB_NAME,
            user=conf.DB_USER,
            password=conf.DB_PASSWORD,
            connect_timeout=10
        )
        cur = conn.cursor(cursor_factory=DictCursor)

        inserted = 0
        skipped = 0

        with open(csv_path, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                question_text = (row.get('question') or '').strip()
                if not question_text:
                    skipped += 1
                    continue

                qid = (row.get('question_id') or '').strip()
                if not qid:
                    qid = generate_question_id(question_text)

                # Check for existing by question_id or exact question text
                cur.execute("SELECT id FROM questions WHERE question_id = %s OR question = %s", (qid, question_text))
                if cur.fetchone():
                    skipped += 1
                    continue

                cur.execute("""
                    INSERT INTO questions (question_id, question, option_a, option_b, option_c, option_d, option_e, correct_answer, explanation, category)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """, (
                    qid,
                    question_text,
                    row.get('option_a') or '',
                    row.get('option_b') or '',
                    row.get('option_c') or '',
                    row.get('option_d') or '',
                    row.get('option_e') or '',
                    (row.get('correct_answer') or '').strip(),
                    row.get('explanation') or '',
                    row.get('category') or 'ISMS Awareness'
                ))
                inserted += 1

        conn.commit()
        print(f"Inserted: {inserted}, Skipped: {skipped}")
        cur.close()
        return 0

    except Exception as e:
        print(f"Error: {e}")
        if conn:
            conn.rollback()
        return 2
    finally:
        if conn:
            conn.close()


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python scripts/import_csv_to_db.py <csv-path>")
        sys.exit(1)
    sys.exit(main(sys.argv[1]))

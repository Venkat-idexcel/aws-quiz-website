#!/usr/bin/env python3
"""Migration & Cleaning Script
1. Adds option_e column to aws_questions if missing.
2. Runs watermark & noise cleaning on question and option fields.
3. Attempts to recover E option if it was concatenated into option_d (best-effort pattern).

Safe & idempotent: running multiple times only re-cleans.
"""
import psycopg2, re, sys
from psycopg2 import sql

DB = dict(
    host='los-dev-psql-rdsclstr-new.cj6duvm27hk9.us-east-1.rds.amazonaws.com',
    port=3306,
    dbname='cretificate_quiz_db',
    user='postgres',
    password='poc2*&(SRWSjnjkn@#@#'
)

WATERMARK_PATTERNS = [
    r'it\s*exam\s*dumps',
    r'vce\s*up',
    r'vceup\.com',
    r'vce\.?up',
    r'examtopics',
    r'brain\s*dumps?',
    r'actual exam',
    r'real exam',
    r'learn anything',
    r'www\.[a-z0-9\-]+\.(com|net|org)',
    r'https?://\S+' ,
]

PAGE_NUMBER_PATTERN = re.compile(r'Page\s+\d+\s+of\s+\d+', re.IGNORECASE)
OPTION_E_EXTRACT_PATTERN = re.compile(r'(?:^|\s)(E)\.?\s+([^A-D]{3}.*)$', re.IGNORECASE)

MULTISPACE = re.compile(r'\s{2,}')


def clean_text(val: str) -> str:
    if not val:
        return val
    original = val
    text = val
    for pat in WATERMARK_PATTERNS:
        text = re.sub(pat, '', text, flags=re.IGNORECASE)
    text = PAGE_NUMBER_PATTERN.sub('', text)
    text = re.sub(r'\bQUESTION\s+\d+\b', '', text, flags=re.IGNORECASE)
    text = re.sub(r'Correct Answer:?\s*[A-E]+', '', text, flags=re.IGNORECASE)
    text = MULTISPACE.sub(' ', text)
    text = text.strip(' -\t\n')
    return text if text else original


def ensure_column(cur):
    cur.execute("""SELECT column_name FROM information_schema.columns
                   WHERE table_name='aws_questions' AND column_name='option_e'""")
    if not cur.fetchone():
        print("➡️ Adding column option_e ...")
        cur.execute("ALTER TABLE aws_questions ADD COLUMN option_e TEXT NULL")
    else:
        print("✅ option_e column already exists")


def recover_option_e(option_d: str):
    if not option_d:
        return option_d, None
    # Look for pattern where E might be appended after some separator like ' D. text  E. text'
    # We'll try a more explicit split on ' E.' if present.
    split_marker = re.split(r'\sE\.?\s', option_d, maxsplit=1)
    if len(split_marker) == 2:
        d_part, e_part = split_marker
        # Heuristic: ensure D still has meaningful content (length > 5) and E part > 3
        if len(e_part.strip()) > 3:
            return d_part.strip(), e_part.strip()
    return option_d, None


def main():
    print("🚀 Starting migration & cleaning...")
    conn = psycopg2.connect(**DB)
    cur = conn.cursor()

    ensure_column(cur)

    # Fetch rows
    cur.execute("SELECT id, question, option_a, option_b, option_c, option_d, option_e FROM aws_questions")
    rows = cur.fetchall()
    print(f"🔍 Found {len(rows)} rows to inspect")

    updated = 0
    for row in rows:
        _id, q, a, b, c, d, e = row
        changed = False

        cq = clean_text(q)
        if cq != q:
            q = cq; changed = True

        ca = clean_text(a)
        if ca != a:
            a = ca; changed = True

        cb = clean_text(b)
        if cb != b:
            b = cb; changed = True

        cc = clean_text(c) if c else c
        if c and cc != c:
            c = cc; changed = True

        cd = clean_text(d) if d else d
        if d and cd != d:
            d = cd; changed = True

        ce = clean_text(e) if e else e
        if e and ce != e:
            e = ce; changed = True

        # Attempt recovery of option_e if empty
        if not e and d:
            new_d, recovered_e = recover_option_e(d)
            if recovered_e:
                d = new_d
                e = clean_text(recovered_e)
                changed = True

        if changed:
            cur.execute(
                "UPDATE aws_questions SET question=%s, option_a=%s, option_b=%s, option_c=%s, option_d=%s, option_e=%s WHERE id=%s",
                (q, a, b, c, d, e, _id)
            )
            updated += 1
            if updated % 200 == 0:
                conn.commit(); print(f"💾 Committed {updated} updates so far...")

    conn.commit()
    print(f"✅ Cleaning complete. Updated {updated} rows.")

    # Basic stats after
    cur.execute("SELECT COUNT(*) FROM aws_questions WHERE option_e IS NOT NULL AND option_e <> ''")
    with_e = cur.fetchone()[0]
    print(f"📊 Questions now having option E: {with_e}")

    cur.close(); conn.close()
    print("🎉 Migration done.")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('\nInterrupted.')
        sys.exit(1)

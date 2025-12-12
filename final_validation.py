"""
Final comprehensive validation of Cloud Practitioner questions
"""
import psycopg2
from config import Config

config = Config()
conn = psycopg2.connect(
    host=config.DB_HOST,
    port=config.DB_PORT,
    database=config.DB_NAME,
    user=config.DB_USER,
    password=config.DB_PASSWORD
)
cur = conn.cursor()

print("=" * 80)
print("CLOUD PRACTITIONER PRACTICE TEST - FINAL VALIDATION")
print("=" * 80)

# Total questions
cur.execute("SELECT COUNT(*) FROM questions WHERE category = 'Cloud Practitioner Practice Test'")
total = cur.fetchone()[0]
print(f"\nTotal questions: {total}")

# Questions with option_e
cur.execute("SELECT COUNT(*) FROM questions WHERE category = 'Cloud Practitioner Practice Test' AND option_e IS NOT NULL AND option_e != ''")
with_e = cur.fetchone()[0]
print(f"Questions with option_e: {with_e} {'[OK]' if with_e == 0 else '[ISSUE]'}")

# Questions with long option_d
cur.execute("SELECT COUNT(*) FROM questions WHERE category = 'Cloud Practitioner Practice Test' AND LENGTH(option_d) > 300")
long_d = cur.fetchone()[0]
print(f"Questions with long option_d (>300 chars): {long_d} {'[OK]' if long_d == 0 else '[ISSUE]'}")

# Multi-select questions
cur.execute("""
    SELECT COUNT(*) 
    FROM questions 
    WHERE category = 'Cloud Practitioner Practice Test' 
    AND (question LIKE '%Choose two%' OR question LIKE '%Choose TWO%' OR question LIKE '%Select 2%' 
         OR question LIKE '%(Choose two)%' OR question LIKE '%choose two%')
""")
multi_select = cur.fetchone()[0]
print(f"\nMulti-select questions (Choose TWO/Select 2): {multi_select}")

# Single-select questions with multiple answers
cur.execute("""
    SELECT COUNT(*) 
    FROM questions 
    WHERE category = 'Cloud Practitioner Practice Test' 
    AND question NOT LIKE '%Choose%'
    AND question NOT LIKE '%Select%'
    AND correct_answer LIKE '%,%'
""")
bad_single = cur.fetchone()[0]
print(f"Single-select with multiple answers: {bad_single} {'[OK]' if bad_single == 0 else '[ISSUE]'}")

# Multi-select questions with only one answer
cur.execute("""
    SELECT COUNT(*) 
    FROM questions 
    WHERE category = 'Cloud Practitioner Practice Test' 
    AND (question LIKE '%Choose two%' OR question LIKE '%Choose TWO%' OR question LIKE '%Select 2%' 
         OR question LIKE '%(Choose two)%' OR question LIKE '%choose two%')
    AND correct_answer NOT LIKE '%,%'
""")
bad_multi = cur.fetchone()[0]
print(f"Multi-select with only one answer: {bad_multi} {'[OK]' if bad_multi == 0 else '[ISSUE]'}")

print("\n" + "=" * 80)
if with_e == 0 and long_d == 0 and bad_single == 0 and bad_multi == 0:
    print("STATUS: ALL CHECKS PASSED!")
    print("The Cloud Practitioner Practice Test questions are now properly formatted.")
else:
    print(f"STATUS: {with_e + long_d + bad_single + bad_multi} issues remaining")
print("=" * 80)

cur.close()
conn.close()

#!/usr/bin/env python3

import psycopg2
from config import Config

def main():
    try:
        # Load config
        config = Config()
        
        # Connect to database
        conn = psycopg2.connect(
            host=config.DB_HOST,
            port=config.DB_PORT,
            database=config.DB_NAME,
            user=config.DB_USER,
            password=config.DB_PASSWORD,
            connect_timeout=10
        )
        
        cursor = conn.cursor()
        
        print("🔍 Checking database schema...")
        
        # Get table schema
        cursor.execute("""
            SELECT column_name, data_type, character_maximum_length, is_nullable
            FROM information_schema.columns 
            WHERE table_name = 'questions' 
            ORDER BY ordinal_position
        """)
        
        columns = cursor.fetchall()
        print("\n📋 Questions table schema:")
        for col in columns:
            max_length = col[2] if col[2] else "unlimited"
            print(f"  • {col[0]}: {col[1]} ({max_length}) - nullable: {col[3]}")
        
        # Check current question count and latest IDs
        cursor.execute("""
            SELECT COUNT(*) FROM questions 
            WHERE category = 'Cloud Practitioner Practice Test'
        """)
        count = cursor.fetchone()[0]
        print(f"\n📊 Total Cloud Practitioner questions: {count}")
        
        # Get latest question IDs to see the pattern
        cursor.execute("""
            SELECT question_id, LENGTH(question_id) as id_length
            FROM questions 
            WHERE category = 'Cloud Practitioner Practice Test'
            ORDER BY question_id DESC 
            LIMIT 10
        """)
        
        latest_ids = cursor.fetchall()
        print("\n🔢 Latest question IDs and their lengths:")
        for row in latest_ids:
            print(f"  • {row[0]} (length: {row[1]})")
            
        # Check if we have any questions with IDs longer than 10 chars
        cursor.execute("""
            SELECT question_id, LENGTH(question_id) as id_length
            FROM questions 
            WHERE LENGTH(question_id) > 10
            LIMIT 5
        """)
        
        long_ids = cursor.fetchall()
        if long_ids:
            print("\n⚠️ Questions with IDs longer than 10 characters:")
            for row in long_ids:
                print(f"  • {row[0]} (length: {row[1]})")
        else:
            print("\n✅ No existing questions with IDs longer than 10 characters")
            
        # Test what the next ID would be
        next_num = count + 1
        next_id = f"CP_{next_num:04d}"
        print(f"\n🎯 Next question ID would be: {next_id} (length: {len(next_id)})")
        
        if len(next_id) > 10:
            print(f"❌ PROBLEM: Next ID '{next_id}' is {len(next_id)} characters, exceeds 10-char limit!")
            
            # Suggest solutions
            print("\n💡 Possible solutions:")
            print("1. Modify database schema to increase varchar limit")
            print("2. Change ID format (e.g., CP{number} instead of CP_{number:04d})")
            print("3. Use a shorter prefix")
            
            # Show what different formats would look like
            alt_formats = [
                f"CP{next_num}",
                f"C{next_num:04d}",
                f"P{next_num:04d}"
            ]
            
            print("\n🔄 Alternative ID formats:")
            for alt_id in alt_formats:
                status = "✅" if len(alt_id) <= 10 else "❌"
                print(f"  {status} {alt_id} (length: {len(alt_id)})")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Database Migration Script
Migrates data from old PostgreSQL database to new AWS RDS PostgreSQL database
"""

import psycopg2
import psycopg2.extras
from datetime import datetime
import sys
import os

# Old Database Configuration (current)
OLD_DB_CONFIG = {
    'host': 'localhost',
    'port': 5480,
    'database': 'cretificate_quiz_db',
    'user': 'psql_master',
    'password': 'LaS%J`ea&>7V2CR8C+P`'
}

# New Database Configuration (AWS RDS)
NEW_DB_CONFIG = {
    'host': 'los-dev-psql-rdsclstr-new.cj6duvm27hk9.us-east-1.rds.amazonaws.com',
    'port': 3306,
    'database': 'cretificate_quiz_db',  # You might need to create this database first
    'user': 'postgres',
    'password': 'poc2*&(SRWSjnjkn@#@#'
}

def test_connection(db_config, db_name="source"):
    """Test database connection"""
    try:
        conn = psycopg2.connect(**db_config)
        conn.close()
        print(f"✅ Successfully connected to {db_name} database")
        return True
    except Exception as e:
        print(f"❌ Failed to connect to {db_name} database: {e}")
        return False

def get_table_list(db_config):
    """Get list of all tables in the database"""
    try:
        conn = psycopg2.connect(**db_config)
        cur = conn.cursor()
        
        # Get all user tables (excluding system tables)
        cur.execute("""
            SELECT tablename 
            FROM pg_tables 
            WHERE schemaname = 'public'
            ORDER BY tablename;
        """)
        
        tables = [row[0] for row in cur.fetchall()]
        conn.close()
        return tables
    except Exception as e:
        print(f"❌ Error getting table list: {e}")
        return []

def export_table_data(old_conn, table_name):
    """Export data from a single table"""
    try:
        cur = old_conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        # Get all data from the table
        cur.execute(f"SELECT * FROM {table_name}")
        rows = cur.fetchall()
        
        if rows:
            # Get column names
            columns = [desc[0] for desc in cur.description]
            print(f"📤 Exported {len(rows)} rows from {table_name}")
            return columns, rows
        else:
            print(f"ℹ️ Table {table_name} is empty")
            return None, []
            
    except Exception as e:
        print(f"❌ Error exporting {table_name}: {e}")
        return None, []

def create_table_schema(new_conn, old_conn, table_name):
    """Create table schema in new database"""
    try:
        old_cur = old_conn.cursor()
        new_cur = new_conn.cursor()
        
        # Get table schema from old database
        old_cur.execute("""
            SELECT column_name, data_type, character_maximum_length, 
                   is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = %s AND table_schema = 'public'
            ORDER BY ordinal_position;
        """, (table_name,))
        
        schema_info = old_cur.fetchall()
        
        if not schema_info:
            print(f"⚠️ No schema found for table {table_name}")
            return False
        
        # Build CREATE TABLE statement
        create_sql = f"CREATE TABLE IF NOT EXISTS {table_name} (\n"
        columns = []
        
        for col in schema_info:
            col_name, data_type, max_length, nullable, default = col
            
            # Handle different data types
            if data_type == 'character varying':
                col_def = f"    {col_name} VARCHAR({max_length or 255})"
            elif data_type == 'integer':
                col_def = f"    {col_name} INTEGER"
            elif data_type == 'bigint':
                col_def = f"    {col_name} BIGINT"
            elif data_type == 'boolean':
                col_def = f"    {col_name} BOOLEAN"
            elif data_type == 'timestamp without time zone':
                col_def = f"    {col_name} TIMESTAMP"
            elif data_type == 'text':
                col_def = f"    {col_name} TEXT"
            elif data_type == 'numeric':
                col_def = f"    {col_name} DECIMAL"
            elif data_type == 'jsonb':
                col_def = f"    {col_name} JSONB"
            else:
                col_def = f"    {col_name} {data_type.upper()}"
            
            # Add NOT NULL constraint
            if nullable == 'NO':
                col_def += " NOT NULL"
            
            # Add DEFAULT value
            if default and not default.startswith('nextval('):
                col_def += f" DEFAULT {default}"
            
            columns.append(col_def)
        
        create_sql += ",\n".join(columns) + "\n);"
        
        # Execute CREATE TABLE
        new_cur.execute(create_sql)
        new_conn.commit()
        print(f"✅ Created table schema for {table_name}")
        return True
        
    except Exception as e:
        print(f"❌ Error creating schema for {table_name}: {e}")
        new_conn.rollback()
        return False

def import_table_data(new_conn, table_name, columns, rows):
    """Import data into new database table"""
    if not rows:
        return True
        
    try:
        cur = new_conn.cursor()
        
        # Prepare INSERT statement
        placeholders = ', '.join(['%s'] * len(columns))
        insert_sql = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})"
        
        # Insert data in batches
        batch_size = 1000
        total_rows = len(rows)
        
        for i in range(0, total_rows, batch_size):
            batch = rows[i:i + batch_size]
            batch_data = [tuple(row) for row in batch]
            
            cur.executemany(insert_sql, batch_data)
            new_conn.commit()
            
            print(f"📥 Imported {min(i + batch_size, total_rows)}/{total_rows} rows to {table_name}")
        
        print(f"✅ Successfully imported all data to {table_name}")
        return True
        
    except Exception as e:
        print(f"❌ Error importing data to {table_name}: {e}")
        new_conn.rollback()
        return False

def migrate_database():
    """Main migration function"""
    print("🚀 Starting database migration...")
    print("=" * 50)
    
    # Test connections
    print("🔍 Testing database connections...")
    if not test_connection(OLD_DB_CONFIG, "old"):
        print("❌ Cannot connect to old database. Migration aborted.")
        return False
        
    if not test_connection(NEW_DB_CONFIG, "new"):
        print("❌ Cannot connect to new database. Migration aborted.")
        return False
    
    print("\n📋 Getting list of tables to migrate...")
    tables = get_table_list(OLD_DB_CONFIG)
    
    if not tables:
        print("❌ No tables found in old database")
        return False
    
    print(f"📊 Found {len(tables)} tables: {', '.join(tables)}")
    
    # Connect to both databases
    old_conn = psycopg2.connect(**OLD_DB_CONFIG)
    new_conn = psycopg2.connect(**NEW_DB_CONFIG)
    
    try:
        # Migrate each table
        for table in tables:
            print(f"\n📦 Migrating table: {table}")
            print("-" * 30)
            
            # Create schema in new database
            if not create_table_schema(new_conn, old_conn, table):
                continue
            
            # Export data from old database
            columns, rows = export_table_data(old_conn, table)
            
            # Import data to new database
            if columns and rows:
                import_table_data(new_conn, table, columns, rows)
        
        print("\n🎉 Migration completed successfully!")
        print("=" * 50)
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False
    finally:
        old_conn.close()
        new_conn.close()

if __name__ == "__main__":
    print("Database Migration Tool")
    print("=" * 50)
    print("This will migrate data from your old database to the new AWS RDS database")
    print(f"Old DB: {OLD_DB_CONFIG['host']}:{OLD_DB_CONFIG['port']}")
    print(f"New DB: {NEW_DB_CONFIG['host']}:{NEW_DB_CONFIG['port']}")
    print()
    
    # Ask for confirmation
    response = input("Do you want to proceed with the migration? (yes/no): ").lower()
    
    if response in ['yes', 'y']:
        success = migrate_database()
        if success:
            print("\n✅ Migration completed! You can now update your app configuration.")
        else:
            print("\n❌ Migration failed. Please check the errors above.")
    else:
        print("Migration cancelled.")
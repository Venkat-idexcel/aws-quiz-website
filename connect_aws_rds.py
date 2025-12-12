"""
Script to connect to AWS RDS PostgreSQL Database
"""
import psycopg2
from psycopg2 import OperationalError
import sys

# AWS RDS PostgreSQL Configuration
DB_CONFIG = {
    'host': 'los-dev-psql-rdsclstr-new.cj6duvm27hk9.us-east-1.rds.amazonaws.com',
    'port': 5432,
    'database': 'postgres',
    'user': 'postgres',
    'password': 'poc2*&(SRWSjnjkn@#@#'
}

def connect_to_rds():
    """Connect to AWS RDS PostgreSQL database"""
    try:
        print("Attempting to connect to AWS RDS PostgreSQL...")
        print(f"Host: {DB_CONFIG['host']}")
        print(f"Port: {DB_CONFIG['port']}")
        print(f"Database: {DB_CONFIG['database']}")
        print(f"User: {DB_CONFIG['user']}")
        print("-" * 60)
        
        # Establish connection
        connection = psycopg2.connect(
            host=DB_CONFIG['host'],
            port=DB_CONFIG['port'],
            database=DB_CONFIG['database'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            connect_timeout=10
        )
        
        print("✓ Successfully connected to AWS RDS PostgreSQL!")
        print("-" * 60)
        
        # Get database version
        cursor = connection.cursor()
        cursor.execute("SELECT version();")
        db_version = cursor.fetchone()[0]
        print(f"\nPostgreSQL Version:\n{db_version}")
        print("-" * 60)
        
        # List all databases
        cursor.execute("""
            SELECT datname, pg_size_pretty(pg_database_size(datname)) as size
            FROM pg_database
            WHERE datistemplate = false
            ORDER BY datname;
        """)
        databases = cursor.fetchall()
        
        print("\nAvailable Databases:")
        for db_name, size in databases:
            print(f"  • {db_name} ({size})")
        print("-" * 60)
        
        # List all schemas in current database
        cursor.execute("""
            SELECT schema_name 
            FROM information_schema.schemata
            WHERE schema_name NOT IN ('pg_catalog', 'information_schema')
            ORDER BY schema_name;
        """)
        schemas = cursor.fetchall()
        
        print(f"\nSchemas in '{DB_CONFIG['database']}' database:")
        for schema in schemas:
            print(f"  • {schema[0]}")
        print("-" * 60)
        
        # List all tables in public schema
        cursor.execute("""
            SELECT table_name, pg_size_pretty(pg_total_relation_size(quote_ident(table_name)::regclass)) as size
            FROM information_schema.tables
            WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
            ORDER BY table_name;
        """)
        tables = cursor.fetchall()
        
        print(f"\nTables in 'public' schema:")
        if tables:
            for table_name, size in tables:
                print(f"  • {table_name} ({size})")
        else:
            print("  (No tables found)")
        print("-" * 60)
        
        # Get connection info
        cursor.execute("""
            SELECT 
                current_database() as database,
                current_user as user,
                inet_server_addr() as server_ip,
                inet_server_port() as server_port;
        """)
        conn_info = cursor.fetchone()
        
        print("\nConnection Information:")
        print(f"  • Current Database: {conn_info[0]}")
        print(f"  • Current User: {conn_info[1]}")
        print(f"  • Server IP: {conn_info[2]}")
        print(f"  • Server Port: {conn_info[3]}")
        print("-" * 60)
        
        cursor.close()
        return connection
        
    except OperationalError as e:
        print(f"✗ Connection failed!")
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"✗ An error occurred: {e}")
        sys.exit(1)

def main():
    """Main function"""
    connection = connect_to_rds()
    
    print("\n✓ Connection is active and ready for queries.")
    print("\nTo keep the connection open, the script will wait.")
    print("Press Ctrl+C to close the connection and exit.\n")
    
    try:
        # Keep connection alive
        input("Press Enter to close connection...")
    except KeyboardInterrupt:
        print("\n\nClosing connection...")
    finally:
        if connection:
            connection.close()
            print("✓ Connection closed successfully.")

if __name__ == "__main__":
    main()

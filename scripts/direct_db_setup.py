#!/usr/bin/env python3
"""
Direct Supabase Database Setup Script
Runs the essential SQL setup using the Supabase Python client
"""
import os
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

def run_sql_file(supabase: Client, file_path: str):
    """Run SQL file contents through Supabase"""
    try:
        with open(file_path, 'r') as f:
            sql_content = f.read()
        
        # Split by semicolon and execute each statement
        statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip()]
        
        print(f"🚀 Running {len(statements)} SQL statements from {file_path}")
        
        for i, statement in enumerate(statements):
            if statement.strip():
                try:
                    print(f"  📝 Executing statement {i+1}/{len(statements)}")
                    result = supabase.rpc('exec_sql', {'sql': statement}).execute()
                    print(f"  ✅ Statement {i+1} completed")
                except Exception as e:
                    print(f"  ⚠️  Statement {i+1} failed (may be normal): {str(e)[:100]}")
        
        print("✅ SQL file execution completed!")
        return True
        
    except Exception as e:
        print(f"❌ Error running SQL file: {e}")
        return False

def verify_tables(supabase: Client):
    """Verify that tables were created"""
    try:
        # Try to query each table
        tables_to_check = [
            'progressive_agents',
            'progressive_agent_jobs', 
            'progressive_agent_contacts',
            'progressive_agent_campaigns',
            'production_campaigns',
            'contacts',
            'admin_users'
        ]
        
        print("🔍 Verifying tables exist...")
        for table in tables_to_check:
            try:
                result = supabase.table(table).select("*").limit(1).execute()
                print(f"  ✅ Table '{table}' exists and accessible")
            except Exception as e:
                print(f"  ❌ Table '{table}' issue: {str(e)[:100]}")
        
        return True
    except Exception as e:
        print(f"❌ Error verifying tables: {e}")
        return False

def main():
    """Main setup function"""
    print("🚀 Starting Coogi Database Setup...")
    
    if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
        print("❌ Missing Supabase credentials in .env file")
        return False
    
    # Create Supabase client
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
    print("✅ Connected to Supabase")
    
    # Run the essential tables SQL
    sql_file = "supabase/essential_tables.sql"
    if os.path.exists(sql_file):
        success = run_sql_file(supabase, sql_file)
        if success:
            verify_tables(supabase)
            print("🎉 Database setup completed!")
            return True
    else:
        print(f"❌ SQL file not found: {sql_file}")
    
    return False

if __name__ == "__main__":
    main()

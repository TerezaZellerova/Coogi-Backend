#!/usr/bin/env python3
"""
Supabase Table Creation Script
Executes SQL scripts to create all required database tables
"""

import os
import sys
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_supabase_client() -> Client:
    """Initialize Supabase client with admin permissions"""
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    
    if not url or not key:
        print("❌ Error: Missing Supabase credentials")
        sys.exit(1)
    
    return create_client(url, key)

def create_tables_via_sql():
    """Create tables by executing SQL files directly"""
    print("🗄️ Creating Supabase Tables via Terminal...")
    print("=" * 60)
    
    supabase = get_supabase_client()
    
    # Test basic connection first
    try:
        print("📡 Testing Supabase connection...")
        # Try a simple query to test connection
        result = supabase.table('information_schema.tables').select('table_name').limit(1).execute()
        print("✅ Supabase connection successful")
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False
    
    # SQL for creating essential tables
    table_sqls = {
        "search_logs": """
        CREATE TABLE IF NOT EXISTS search_logs (
            id SERIAL PRIMARY KEY,
            batch_id TEXT NOT NULL,
            message TEXT NOT NULL,
            level TEXT DEFAULT 'info',
            company TEXT,
            job_title TEXT,
            job_url TEXT,
            event_type TEXT,
            timestamp TIMESTAMPTZ DEFAULT NOW()
        );
        """,
        
        "hunter_emails": """
        CREATE TABLE IF NOT EXISTS hunter_emails (
            id SERIAL PRIMARY KEY,
            batch_id TEXT NOT NULL,
            company TEXT NOT NULL,
            job_title TEXT,
            job_url TEXT,
            emails_found INTEGER DEFAULT 0,
            email_list JSONB,
            search_success BOOLEAN DEFAULT FALSE,
            search_error TEXT,
            timestamp TIMESTAMPTZ DEFAULT NOW()
        );
        """,
        
        "instantly_campaigns": """
        CREATE TABLE IF NOT EXISTS instantly_campaigns (
            id SERIAL PRIMARY KEY,
            batch_id TEXT NOT NULL,
            company TEXT NOT NULL,
            campaign_id TEXT,
            campaign_name TEXT,
            leads_added INTEGER DEFAULT 0,
            campaign_success BOOLEAN DEFAULT FALSE,
            campaign_error TEXT,
            timestamp TIMESTAMPTZ DEFAULT NOW()
        );
        """,
        
        "company_processing_summary": """
        CREATE TABLE IF NOT EXISTS company_processing_summary (
            id SERIAL PRIMARY KEY,
            batch_id TEXT NOT NULL,
            company TEXT NOT NULL,
            job_title TEXT,
            job_url TEXT,
            domain_found BOOLEAN DEFAULT FALSE,
            linkedin_resolved BOOLEAN DEFAULT FALSE,
            rapidapi_analyzed BOOLEAN DEFAULT FALSE,
            hunter_emails_found BOOLEAN DEFAULT FALSE,
            instantly_campaign_created BOOLEAN DEFAULT FALSE,
            final_recommendation TEXT,
            processing_success BOOLEAN DEFAULT FALSE,
            processing_error TEXT,
            timestamp TIMESTAMPTZ DEFAULT NOW()
        );
        """
    }
    
    # Create each table
    created_tables = []
    failed_tables = []
    
    for table_name, sql in table_sqls.items():
        try:
            print(f"📋 Creating table: {table_name}")
            
            # Execute SQL using RPC call
            result = supabase.rpc('exec_sql', {'sql': sql}).execute()
            
            if result.data:
                print(f"✅ Created table: {table_name}")
                created_tables.append(table_name)
            else:
                print(f"⚠️  Table creation result unclear for: {table_name}")
                created_tables.append(table_name)  # Assume success if no error
                
        except Exception as e:
            print(f"❌ Failed to create table {table_name}: {e}")
            failed_tables.append(table_name)
    
    # Summary
    print("\n📊 Table Creation Summary:")
    print("=" * 60)
    print(f"✅ Successfully created: {len(created_tables)} tables")
    for table in created_tables:
        print(f"   - {table}")
    
    if failed_tables:
        print(f"❌ Failed to create: {len(failed_tables)} tables")
        for table in failed_tables:
            print(f"   - {table}")
    
    return len(failed_tables) == 0

def verify_tables():
    """Verify that tables were created successfully"""
    print("\n🔍 Verifying table creation...")
    
    supabase = get_supabase_client()
    
    tables_to_check = [
        "search_logs",
        "hunter_emails", 
        "instantly_campaigns",
        "company_processing_summary"
    ]
    
    verified_tables = []
    
    for table in tables_to_check:
        try:
            # Try to query the table
            result = supabase.table(table).select("*").limit(1).execute()
            print(f"✅ Table verified: {table}")
            verified_tables.append(table)
        except Exception as e:
            print(f"❌ Table verification failed: {table} - {e}")
    
    print(f"\n📊 Verification Result: {len(verified_tables)}/{len(tables_to_check)} tables working")
    return len(verified_tables) == len(tables_to_check)

def main():
    """Main execution function"""
    print("🚀 Supabase Database Setup")
    print("=" * 60)
    
    # Create tables
    tables_created = create_tables_via_sql()
    
    if tables_created:
        # Verify tables
        tables_verified = verify_tables()
        
        if tables_verified:
            print("\n🎉 SUCCESS: Database setup complete!")
            print("   All required tables created and verified")
            print("   Ready for lead generation workflow")
        else:
            print("\n⚠️  PARTIAL SUCCESS: Tables created but verification failed")
            print("   Manual verification may be needed")
    else:
        print("\n❌ FAILED: Could not create all tables")
        print("   May need to use Supabase dashboard method")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Supabase Authentication Debug Script
Tests different authentication methods and RLS policies
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_service_role_vs_anon():
    """Test both service role key and anon key"""
    print("🔑 TESTING DIFFERENT API KEYS")
    print("=" * 50)
    
    try:
        from supabase import create_client, Client
        
        url = os.getenv("SUPABASE_URL")
        anon_key = os.getenv("SUPABASE_ANON_KEY")
        service_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        
        # Test 1: Anon Key
        print("Testing Anon Key...")
        try:
            supabase_anon = create_client(url, anon_key)
            result = supabase_anon.table("agent_logs").select("*").limit(1).execute()
            print(f"✅ Anon Key: Success - {len(result.data)} rows")
        except Exception as e:
            print(f"❌ Anon Key: {e}")
        
        # Test 2: Service Role Key
        print("\nTesting Service Role Key...")
        try:
            supabase_service = create_client(url, service_key)
            result = supabase_service.table("agent_logs").select("*").limit(1).execute()
            print(f"✅ Service Role Key: Success - {len(result.data)} rows")
            return supabase_service
        except Exception as e:
            print(f"❌ Service Role Key: {e}")
        
        # Test 3: Raw HTTP Request
        print("\nTesting Raw HTTP Request...")
        import requests
        headers = {
            "apikey": service_key,
            "Authorization": f"Bearer {service_key}",
            "Content-Type": "application/json"
        }
        
        response = requests.get(
            f"{url}/rest/v1/agent_logs?select=*&limit=1",
            headers=headers
        )
        
        print(f"HTTP Status: {response.status_code}")
        print(f"Response: {response.text}")
        
    except ImportError:
        print("❌ Supabase library not installed")
        return None
    except Exception as e:
        print(f"❌ General error: {e}")
        return None

def test_table_creation(supabase):
    """Test if we need to create tables"""
    print("\n🏗️  TESTING TABLE CREATION")
    print("=" * 50)
    
    # SQL to create agent_logs table if it doesn't exist
    create_agent_logs_sql = """
    CREATE TABLE IF NOT EXISTS agent_logs (
        id SERIAL PRIMARY KEY,
        batch_id TEXT NOT NULL,
        message TEXT NOT NULL,
        level TEXT DEFAULT 'info',
        company TEXT,
        job_title TEXT,
        job_url TEXT,
        processing_stage TEXT,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
    );
    
    -- Enable RLS
    ALTER TABLE agent_logs ENABLE ROW LEVEL SECURITY;
    
    -- Create policy to allow all operations for service role
    CREATE POLICY IF NOT EXISTS "Allow all for service role" 
    ON agent_logs FOR ALL 
    TO service_role 
    USING (true) 
    WITH CHECK (true);
    
    -- Create policy to allow read for anon users
    CREATE POLICY IF NOT EXISTS "Allow read for anon" 
    ON agent_logs FOR SELECT 
    TO anon 
    USING (true);
    """
    
    # SQL to create agents table if it doesn't exist
    create_agents_sql = """
    CREATE TABLE IF NOT EXISTS agents (
        id TEXT PRIMARY KEY,
        query TEXT NOT NULL,
        status TEXT DEFAULT 'pending',
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        total_jobs_found INTEGER DEFAULT 0,
        total_emails_found INTEGER DEFAULT 0,
        hours_old INTEGER DEFAULT 24,
        custom_tags TEXT,
        batch_id TEXT,
        processed_cities INTEGER DEFAULT 0,
        processed_companies INTEGER DEFAULT 0,
        start_time TIMESTAMP WITH TIME ZONE,
        end_time TIMESTAMP WITH TIME ZONE
    );
    
    -- Enable RLS
    ALTER TABLE agents ENABLE ROW LEVEL SECURITY;
    
    -- Create policies
    CREATE POLICY IF NOT EXISTS "Allow all for service role" 
    ON agents FOR ALL 
    TO service_role 
    USING (true) 
    WITH CHECK (true);
    
    CREATE POLICY IF NOT EXISTS "Allow read for anon" 
    ON agents FOR SELECT 
    TO anon 
    USING (true);
    """
    
    try:
        print("Creating agent_logs table...")
        supabase.rpc('exec_sql', {'sql': create_agent_logs_sql}).execute()
        print("✅ agent_logs table created/verified")
        
        print("Creating agents table...")  
        supabase.rpc('exec_sql', {'sql': create_agents_sql}).execute()
        print("✅ agents table created/verified")
        
        return True
    except Exception as e:
        print(f"❌ Table creation failed: {e}")
        # Try alternative method - direct table operations
        try:
            print("Trying direct table access...")
            result = supabase.table("agent_logs").select("*").limit(1).execute()
            print(f"✅ agent_logs table exists - {len(result.data)} rows")
            return True
        except Exception as e2:
            print(f"❌ Direct access also failed: {e2}")
            return False

def main():
    """Main test function"""
    print("🔧 SUPABASE AUTHENTICATION DEBUG")
    print("=" * 50)
    
    # Test different authentication methods
    supabase = test_service_role_vs_anon()
    
    if supabase:
        # Test table creation
        test_table_creation(supabase)
    
    print("\n💡 RECOMMENDATIONS:")
    print("=" * 50)
    print("1. Check if your Supabase project is active")
    print("2. Verify API keys in Supabase dashboard")
    print("3. Ensure Row Level Security policies allow access")
    print("4. Consider creating tables manually if needed")

if __name__ == "__main__":
    main()

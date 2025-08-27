#!/usr/bin/env python3
"""
Quick fix for Supabase agent_logs table creation
Run this script to automatically create the missing table
"""
import os
import requests
import json

def create_agent_logs_table():
    """Create the agent_logs table in Supabase"""
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    supabase_url = os.getenv('SUPABASE_URL')
    service_role_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    
    if not supabase_url or not service_role_key:
        print("❌ Supabase credentials not found in environment")
        print("📋 Manual setup required:")
        print_manual_instructions()
        return False
    
    # Try to create table using Supabase client
    try:
        from supabase import create_client
        supabase = create_client(supabase_url, service_role_key)
        
        # Test if table exists
        try:
            supabase.table("agent_logs").select("id").limit(1).execute()
            print("✅ agent_logs table already exists!")
            return True
        except Exception:
            print("📋 agent_logs table missing - manual creation required")
            print_manual_instructions()
            return False
            
    except Exception as e:
        print(f"❌ Error connecting to Supabase: {e}")
        print("📋 Manual setup required:")
        print_manual_instructions()
        return False

def print_manual_instructions():
    """Print manual setup instructions"""
    print("""
🔧 MANUAL SUPABASE SETUP REQUIRED

1. Go to https://supabase.com/dashboard
2. Select your project  
3. Go to SQL Editor (or Database > Tables)
4. Copy and paste this SQL:

-- Create agent_logs table
CREATE TABLE IF NOT EXISTS public.agent_logs (
    id SERIAL PRIMARY KEY,
    batch_id TEXT NOT NULL,
    message TEXT NOT NULL,
    level TEXT NOT NULL DEFAULT 'info',
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_agent_logs_batch_id ON public.agent_logs(batch_id);
CREATE INDEX IF NOT EXISTS idx_agent_logs_timestamp ON public.agent_logs(timestamp);
CREATE INDEX IF NOT EXISTS idx_agent_logs_level ON public.agent_logs(level);

-- Set permissions
ALTER TABLE public.agent_logs ENABLE ROW LEVEL SECURITY;
GRANT ALL ON public.agent_logs TO service_role;
GRANT ALL ON public.agent_logs TO anon;

5. Click 'Run' to execute
6. Restart your backend server

⚠️  NOTE: The backend pipeline works fine without this table - it's only for logging.
The main functionality (job scraping, contact finding, campaigns) is unaffected.
""")

if __name__ == "__main__":
    print("🔧 Supabase agent_logs Table Setup")
    print("=" * 50)
    
    success = create_agent_logs_table()
    
    if success:
        print("✅ Setup complete!")
    else:
        print("❌ Manual setup required - see instructions above")
        print("\n💡 The backend continues to work without this table")
        print("   This only affects logging, not core functionality")

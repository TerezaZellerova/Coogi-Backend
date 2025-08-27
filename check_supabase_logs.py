#!/usr/bin/env python3
"""
Check Supabase Logs Script
Verifies that logs are being written to Supabase correctly
"""

import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

def check_recent_logs():
    """Check recent logs in Supabase"""
    print("📊 CHECKING RECENT SUPABASE LOGS")
    print("=" * 50)
    
    try:
        from supabase import create_client
        
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        
        supabase = create_client(url, key)
        
        # Get logs from the last hour (use timestamp column that exists)
        one_hour_ago = (datetime.now() - timedelta(hours=1)).isoformat()
        
        result = supabase.table("agent_logs").select("*").gte("timestamp", one_hour_ago).order("timestamp", desc=True).limit(10).execute()
        
        print(f"Found {len(result.data)} recent logs:")
        print("-" * 50)
        
        for log in result.data:
            timestamp = log.get('timestamp', 'Unknown')
            batch_id = log.get('batch_id', 'Unknown')
            level = log.get('level', 'info').upper()
            message = log.get('message', 'No message')
            company = log.get('company', '')
            
            print(f"🕐 {timestamp}")
            print(f"🆔 Batch: {batch_id}")
            print(f"📝 [{level}] {message}")
            if company:
                print(f"🏢 Company: {company}")
            print("-" * 30)
        
        return len(result.data) > 0
        
    except Exception as e:
        print(f"❌ Error checking logs: {e}")
        return False

def check_agents_table():
    """Check agents table content"""
    print("\n🤖 CHECKING AGENTS TABLE")
    print("=" * 50)
    
    try:
        from supabase import create_client
        
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        
        supabase = create_client(url, key)
        
        result = supabase.table("agents").select("*").order("created_at", desc=True).limit(5).execute()
        
        print(f"Found {len(result.data)} agents:")
        print("-" * 30)
        
        for agent in result.data:
            agent_id = agent.get('id', 'Unknown')
            query = agent.get('query', 'Unknown')
            status = agent.get('status', 'unknown')
            jobs_found = agent.get('total_jobs_found', 0)
            created_at = agent.get('created_at', 'Unknown')
            
            print(f"🆔 ID: {agent_id}")
            print(f"🔍 Query: {query}")
            print(f"📊 Status: {status}")
            print(f"💼 Jobs Found: {jobs_found}")
            print(f"🕐 Created: {created_at}")
            print("-" * 30)
        
        return True
        
    except Exception as e:
        print(f"❌ Error checking agents: {e}")
        return False

def main():
    """Main function"""
    print("🔍 SUPABASE INTEGRATION VERIFICATION")
    print("=" * 50)
    print(f"Timestamp: {datetime.now()}")
    print()
    
    # Check logs
    logs_working = check_recent_logs()
    
    # Check agents
    agents_working = check_agents_table()
    
    print("\n📋 SUMMARY")
    print("=" * 50)
    print(f"Logs Working: {'✅ YES' if logs_working else '❌ NO'}")
    print(f"Agents Table: {'✅ YES' if agents_working else '❌ NO'}")
    
    if logs_working and agents_working:
        print("\n🎉 SUPABASE INTEGRATION IS WORKING!")
        print("✅ Ready for production deployment")
    else:
        print("\n⚠️  Some issues detected - check above for details")

if __name__ == "__main__":
    main()

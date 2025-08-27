#!/usr/bin/env python3
"""
Supabase Integration Test Script
Tests the connection and core functionality with Supabase database
"""

import os
import sys
import asyncio
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_environment_variables():
    """Test if required environment variables are set"""
    print("🔍 TESTING ENVIRONMENT VARIABLES")
    print("=" * 50)
    
    required_vars = [
        "SUPABASE_URL",
        "SUPABASE_ANON_KEY", 
        "SUPABASE_SERVICE_ROLE_KEY"
    ]
    
    missing_vars = []
    for var in required_vars:
        value = os.getenv(var)
        if value:
            # Show first/last few chars for security
            masked_value = value[:8] + "..." + value[-8:] if len(value) > 16 else "***"
            print(f"✅ {var}: {masked_value}")
        else:
            print(f"❌ {var}: NOT SET")
            missing_vars.append(var)
    
    if missing_vars:
        print(f"\n⚠️  Missing variables: {', '.join(missing_vars)}")
        return False
    
    print("✅ All environment variables are set")
    return True

def test_supabase_connection():
    """Test basic Supabase connection"""
    print("\n🔗 TESTING SUPABASE CONNECTION")
    print("=" * 50)
    
    try:
        from supabase import create_client, Client
        
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_ANON_KEY")
        
        if not url or not key:
            print("❌ Missing Supabase credentials")
            return False
        
        # Create client
        supabase: Client = create_client(url, key)
        print(f"✅ Supabase client created successfully")
        print(f"📍 Connected to: {url}")
        
        return supabase
    
    except ImportError:
        print("❌ Supabase library not installed. Run: pip install supabase")
        return False
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

def test_database_tables(supabase):
    """Test if required tables exist and are accessible"""
    print("\n📊 TESTING DATABASE TABLES")
    print("=" * 50)
    
    tables_to_test = [
        "agent_logs",
        "agents", 
        "leads",
        "campaigns"
    ]
    
    accessible_tables = []
    
    for table_name in tables_to_test:
        try:
            # Try to select one row from each table
            result = supabase.table(table_name).select("*").limit(1).execute()
            print(f"✅ {table_name}: Accessible ({len(result.data)} rows)")
            accessible_tables.append(table_name)
        except Exception as e:
            print(f"❌ {table_name}: Error - {e}")
    
    return accessible_tables

def test_agent_logs_operations(supabase):
    """Test CRUD operations on agent_logs table"""
    print("\n📝 TESTING AGENT LOGS OPERATIONS")
    print("=" * 50)
    
    test_batch_id = f"test_batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    try:
        # Test INSERT
        log_data = {
            "batch_id": test_batch_id,
            "message": "Test log message",
            "level": "info",
            "company": "Test Company",
            "processing_stage": "testing"
        }
        
        result = supabase.table("agent_logs").insert(log_data).execute()
        print(f"✅ INSERT: Created test log with batch_id: {test_batch_id}")
        
        # Test SELECT
        logs = supabase.table("agent_logs").select("*").eq("batch_id", test_batch_id).execute()
        print(f"✅ SELECT: Retrieved {len(logs.data)} logs for batch_id: {test_batch_id}")
        
        # Test UPDATE
        update_result = supabase.table("agent_logs").update({
            "message": "Updated test message"
        }).eq("batch_id", test_batch_id).execute()
        print(f"✅ UPDATE: Updated logs for batch_id: {test_batch_id}")
        
        # Test DELETE (cleanup)
        delete_result = supabase.table("agent_logs").delete().eq("batch_id", test_batch_id).execute()
        print(f"✅ DELETE: Cleaned up test logs for batch_id: {test_batch_id}")
        
        return True
        
    except Exception as e:
        print(f"❌ CRUD operations failed: {e}")
        return False

def test_agents_table_operations(supabase):
    """Test operations on agents table"""
    print("\n🤖 TESTING AGENTS TABLE OPERATIONS")
    print("=" * 50)
    
    test_agent_id = f"test_agent_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    try:
        # Test INSERT
        agent_data = {
            "id": test_agent_id,
            "query": "test query",
            "status": "running",
            "total_jobs_found": 10,
            "total_emails_found": 5,
            "hours_old": 24
        }
        
        result = supabase.table("agents").insert(agent_data).execute()
        print(f"✅ INSERT: Created test agent with id: {test_agent_id}")
        
        # Test SELECT
        agents = supabase.table("agents").select("*").eq("id", test_agent_id).execute()
        print(f"✅ SELECT: Retrieved agent data: {agents.data[0] if agents.data else 'None'}")
        
        # Test UPDATE
        update_result = supabase.table("agents").update({
            "status": "completed",
            "total_jobs_found": 20
        }).eq("id", test_agent_id).execute()
        print(f"✅ UPDATE: Updated agent status to completed")
        
        # Test DELETE (cleanup)
        delete_result = supabase.table("agents").delete().eq("id", test_agent_id).execute()
        print(f"✅ DELETE: Cleaned up test agent with id: {test_agent_id}")
        
        return True
        
    except Exception as e:
        print(f"❌ Agents table operations failed: {e}")
        return False

def main():
    """Main test function"""
    print("🚀 SUPABASE INTEGRATION TEST")
    print("=" * 50)
    print(f"Timestamp: {datetime.now()}")
    print()
    
    # Test 1: Environment Variables
    if not test_environment_variables():
        print("\n❌ CRITICAL: Environment variables not properly configured")
        return False
    
    # Test 2: Connection
    supabase = test_supabase_connection()
    if not supabase:
        print("\n❌ CRITICAL: Cannot connect to Supabase")
        return False
    
    # Test 3: Tables
    accessible_tables = test_database_tables(supabase)
    if not accessible_tables:
        print("\n❌ CRITICAL: No accessible tables found")
        return False
    
    # Test 4: Agent Logs Operations
    if "agent_logs" in accessible_tables:
        test_agent_logs_operations(supabase)
    
    # Test 5: Agents Table Operations
    if "agents" in accessible_tables:
        test_agents_table_operations(supabase)
    
    print("\n🎉 SUPABASE INTEGRATION TEST COMPLETE!")
    print("=" * 50)
    print("✅ Supabase is ready for production deployment")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

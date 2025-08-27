#!/usr/bin/env python3
"""
Test Supabase Logging Directly
"""

import os
import asyncio
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

async def test_direct_logging():
    """Test logging directly to Supabase"""
    print("🧪 TESTING DIRECT SUPABASE LOGGING")
    print("=" * 50)
    
    try:
        from supabase import create_client
        
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        
        supabase = create_client(url, key)
        
        # Test log data
        test_batch_id = f"direct_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        log_data = {
            "batch_id": test_batch_id,
            "message": "Direct Supabase logging test",
            "level": "info",
            "company": "Test Company Direct",
            "job_title": "Test Job",
            "processing_stage": "direct_testing"
        }
        
        print(f"Inserting log with batch_id: {test_batch_id}")
        result = supabase.table("agent_logs").insert(log_data).execute()
        print(f"✅ Insert successful: {result.data}")
        
        # Verify the log was inserted
        print("\nVerifying log was inserted...")
        logs = supabase.table("agent_logs").select("*").eq("batch_id", test_batch_id).execute()
        print(f"✅ Found {len(logs.data)} logs with our batch_id")
        
        if logs.data:
            log = logs.data[0]
            print("Retrieved log:")
            for key, value in log.items():
                print(f"  {key}: {value}")
        
        # Clean up
        print("\nCleaning up test data...")
        supabase.table("agent_logs").delete().eq("batch_id", test_batch_id).execute()
        print("✅ Cleanup complete")
        
        return True
        
    except Exception as e:
        print(f"❌ Direct logging failed: {e}")
        return False

async def test_backend_logging():
    """Test the backend logging function"""
    print("\n🔧 TESTING BACKEND LOGGING FUNCTION")
    print("=" * 50)
    
    try:
        # Import the logging function from dependencies
        import sys
        sys.path.append('/Users/waqaskhan/Documents/Coogi New Project/coogi-backend')
        
        from api.dependencies import log_to_supabase
        
        test_batch_id = f"backend_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        print(f"Testing backend log function with batch_id: {test_batch_id}")
        await log_to_supabase(
            batch_id=test_batch_id,
            message="Backend logging function test",
            level="info",
            company="Backend Test Co",
            job_title="Backend Test Job",
            processing_stage="backend_testing"
        )
        
        print("✅ Backend logging function executed without errors")
        
        # Verify the log was created
        from supabase import create_client
        
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        
        supabase = create_client(url, key)
        logs = supabase.table("agent_logs").select("*").eq("batch_id", test_batch_id).execute()
        
        if logs.data:
            print(f"✅ Backend log found in database: {len(logs.data)} entries")
            # Clean up
            supabase.table("agent_logs").delete().eq("batch_id", test_batch_id).execute()
        else:
            print("❌ Backend log not found in database")
        
        return len(logs.data) > 0
        
    except Exception as e:
        print(f"❌ Backend logging test failed: {e}")
        return False

async def main():
    """Main test function"""
    print("🔬 COMPREHENSIVE SUPABASE LOGGING TEST")
    print("=" * 50)
    print(f"Timestamp: {datetime.now()}")
    print()
    
    # Test 1: Direct logging
    direct_success = await test_direct_logging()
    
    # Test 2: Backend function
    backend_success = await test_backend_logging()
    
    print("\n📋 FINAL RESULTS")
    print("=" * 50)
    print(f"Direct Supabase Logging: {'✅ WORKING' if direct_success else '❌ FAILED'}")
    print(f"Backend Logging Function: {'✅ WORKING' if backend_success else '❌ FAILED'}")
    
    if direct_success and backend_success:
        print("\n🎉 SUPABASE LOGGING IS FULLY FUNCTIONAL!")
        print("✅ Ready for production deployment")
    else:
        print("\n⚠️  Some logging issues detected")

if __name__ == "__main__":
    asyncio.run(main())

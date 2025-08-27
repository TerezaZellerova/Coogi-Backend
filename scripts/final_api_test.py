#!/usr/bin/env python3
"""
FINAL COMPREHENSIVE API TEST
Testing all available APIs and services before Milestone 1 development
"""

import os
import requests
import json
import openai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_openai():
    """Test OpenAI API"""
    try:
        openai.api_key = os.getenv('OPENAI_API_KEY')
        client = openai.OpenAI(api_key=openai.api_key)
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Say 'OpenAI API working' in exactly 3 words"}],
            max_tokens=10
        )
        
        result = response.choices[0].message.content.strip()
        print("✅ OpenAI API: WORKING")
        print(f"   Response: {result}")
        return True
    except Exception as e:
        print(f"❌ OpenAI API: FAILED - {e}")
        return False

def test_hunter():
    """Test Hunter.io API"""
    try:
        api_key = os.getenv('HUNTER_API_KEY')
        url = f"https://api.hunter.io/v2/domain-search"
        params = {
            'domain': 'stripe.com',
            'api_key': api_key,
            'limit': 1
        }
        
        response = requests.get(url, params=params)
        if response.status_code == 200:
            data = response.json()
            email_count = data['data']['emails']
            print("✅ Hunter.io API: WORKING")
            print(f"   Found {len(email_count)} emails for stripe.com")
            return True
        else:
            print(f"❌ Hunter.io API: FAILED - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Hunter.io API: FAILED - {e}")
        return False

def test_instantly():
    """Test Instantly.ai API"""
    try:
        api_key = os.getenv('INSTANTLY_API_KEY')
        url = "https://api.instantly.ai/api/v2/campaigns"
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            campaigns = data['items']
            print("✅ Instantly.ai API: WORKING")
            print(f"   Found {len(campaigns)} campaigns configured")
            return True
        else:
            print(f"❌ Instantly.ai API: FAILED - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Instantly.ai API: FAILED - {e}")
        return False

def test_apify():
    """Test Apify API"""
    try:
        api_key = os.getenv('APIFY_API_KEY')
        url = f"https://api.apify.com/v2/acts"
        params = {'token': api_key}
        
        response = requests.get(url, params=params)
        if response.status_code == 200:
            data = response.json()
            total_count = data.get('total', 0)
            print("✅ Apify API: WORKING")
            print(f"   Account has {total_count} actors available")
            return True
        else:
            print(f"❌ Apify API: FAILED - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Apify API: FAILED - {e}")
        return False

def test_supabase():
    """Test Supabase connection"""
    try:
        from supabase import create_client, Client
        url = os.getenv('SUPABASE_URL')
        key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
        
        supabase: Client = create_client(url, key)
        
        # Try to query a table that should exist
        response = supabase.table('agents').select("*").limit(1).execute()
        print("✅ Supabase: WORKING")
        print(f"   Connected to database successfully")
        return True
    except Exception as e:
        print(f"❌ Supabase: FAILED - {e}")
        return False

def test_jobspy():
    """Test JobSpy API"""
    try:
        # Use JobSpy library directly instead of Railway endpoint
        try:
            from python_jobspy import scrape_jobs
            logger.info("✅ Using JobSpy library directly")
            job_df = scrape_jobs(
                search_term="software engineer",
                location="California", 
                results_wanted=5,
                hours_old=720
            )
            if job_df is not None and not job_df.empty:
                logger.info(f"✅ JobSpy returned {len(job_df)} jobs")
                return job_df.to_dict('records')
            else:
                logger.warning("⚠️ JobSpy returned no jobs")
                return []
        except ImportError:
            logger.error("❌ JobSpy library not installed. Please run: pip install python-jobspy")
            return []
        except Exception as e:
            logger.error(f"❌ JobSpy error: {e}")
            return []
        
        response = requests.get(f"{url}/health")
        if response.status_code == 200:
            print("✅ JobSpy API: WORKING")
            print(f"   Health check passed")
            return True
        else:
            print(f"❌ JobSpy API: FAILED - Status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ JobSpy API: FAILED - {e}")
        return False

def main():
    print("🚀 FINAL COMPREHENSIVE API TEST")
    print("=" * 60)
    print("Testing all APIs before Milestone 1 development...\n")
    
    tests = [
        ("OpenAI", test_openai),
        ("Hunter.io", test_hunter),
        ("Instantly.ai", test_instantly),
        ("Apify", test_apify),
        ("Supabase", test_supabase),
        ("JobSpy", test_jobspy)
    ]
    
    results = {}
    for name, test_func in tests:
        print(f"🔍 Testing {name}...")
        results[name] = test_func()
        print()
    
    print("=" * 60)
    print("📊 FINAL RESULTS:")
    print("=" * 60)
    
    working = []
    broken = []
    
    for name, status in results.items():
        if status:
            working.append(name)
            print(f"✅ {name}: WORKING")
        else:
            broken.append(name)
            print(f"❌ {name}: BROKEN")
    
    print(f"\n🎯 SUMMARY:")
    print(f"   ✅ Working APIs: {len(working)}/6 ({', '.join(working)})")
    print(f"   ❌ Broken APIs: {len(broken)}/6 ({', '.join(broken) if broken else 'None!'})")
    
    if len(working) >= 4:
        print(f"\n🚀 READY FOR MILESTONE 1 DEVELOPMENT!")
        print(f"   We have enough working APIs to proceed with core functionality.")
    else:
        print(f"\n⚠️  Need to fix more APIs before proceeding.")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    main()

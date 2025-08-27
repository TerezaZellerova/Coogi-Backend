#!/usr/bin/env python3
"""
Pre-deployment validation script
Checks that all required components are ready for Render deployment
"""

import os
import sys
import subprocess
from dotenv import load_dotenv

def check_requirements():
    """Check if requirements.txt is properly configured"""
    print("📋 CHECKING REQUIREMENTS.TXT")
    print("=" * 50)
    
    required_packages = [
        "fastapi",
        "uvicorn",
        "requests",
        "httpx", 
        "openai",
        "pydantic",
        "supabase",
        "python-dotenv",
        "python-multipart",
        "python-jobspy"
    ]
    
    try:
        with open("requirements.txt", "r") as f:
            content = f.read().lower()
        
        missing = []
        for package in required_packages:
            if package not in content:
                missing.append(package)
        
        if missing:
            print(f"❌ Missing packages: {', '.join(missing)}")
            return False
        else:
            print("✅ All required packages present")
            return True
            
    except FileNotFoundError:
        print("❌ requirements.txt not found")
        return False

def check_main_app():
    """Check if main application is properly configured"""
    print("\n🚀 CHECKING MAIN APPLICATION")
    print("=" * 50)
    
    # Check if main.py exists and has proper structure
    if not os.path.exists("main.py"):
        print("❌ main.py not found")
        return False
    
    with open("main.py", "r") as f:
        content = f.read()
    
    required_patterns = [
        "from fastapi import FastAPI",
        "app = FastAPI",
        "if __name__ == \"__main__\":",
        "uvicorn.run"
    ]
    
    missing = []
    for pattern in required_patterns:
        if pattern not in content:
            missing.append(pattern)
    
    if missing:
        print(f"❌ Missing patterns in main.py: {missing}")
        return False
    else:
        print("✅ main.py properly configured")
        return True

def check_environment_variables():
    """Check environment variables configuration"""
    print("\n🔧 CHECKING ENVIRONMENT VARIABLES")
    print("=" * 50)
    
    load_dotenv()
    
    critical_vars = [
        "OPENAI_API_KEY",
        "SUPABASE_URL", 
        "SUPABASE_SERVICE_ROLE_KEY",
        "HUNTER_API_KEY",
        "RAPIDAPI_KEY"
    ]
    
    missing = []
    for var in critical_vars:
        if not os.getenv(var):
            missing.append(var)
        else:
            print(f"✅ {var}: Set")
    
    if missing:
        print(f"❌ Missing environment variables: {missing}")
        return False
    else:
        print("✅ All critical environment variables set")
        return True

def check_supabase_connection():
    """Check Supabase connection"""
    print("\n🗄️  CHECKING SUPABASE CONNECTION")
    print("=" * 50)
    
    try:
        from supabase import create_client
        
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        
        if not url or not key:
            print("❌ Supabase credentials not configured")
            return False
        
        supabase = create_client(url, key)
        
        # Test connection by selecting from agent_logs
        result = supabase.table("agent_logs").select("*").limit(1).execute()
        print("✅ Supabase connection successful")
        print(f"✅ agent_logs table accessible")
        
        # Test agents table
        agents = supabase.table("agents").select("*").limit(1).execute()
        print(f"✅ agents table accessible")
        
        return True
        
    except Exception as e:
        print(f"❌ Supabase connection failed: {e}")
        return False

def check_api_endpoints():
    """Check that critical API endpoints are defined"""
    print("\n🌐 CHECKING API ENDPOINTS")
    print("=" * 50)
    
    # Check if router files exist
    router_files = [
        "api/routers/agents.py",
        "api/routers/leads.py",
        "api/routers/campaigns.py"
    ]
    
    for router_file in router_files:
        if os.path.exists(router_file):
            print(f"✅ {router_file}: Found")
        else:
            print(f"❌ {router_file}: Missing")
            return False
    
    # Check if main.py includes routers
    with open("main.py", "r") as f:
        content = f.read()
    
    if "include_router" in content and "agents" in content:
        print("✅ Routers properly included in main.py")
        return True
    else:
        print("❌ Routers not properly included in main.py")
        return False

def create_render_config():
    """Create render.yaml configuration file"""
    print("\n📝 CREATING RENDER CONFIGURATION")
    print("=" * 50)
    
    render_config = """services:
  - type: web
    name: coogi-backend
    env: python
    buildCommand: "./render-build.sh"
    startCommand: "uvicorn main:app --host 0.0.0.0 --port $PORT"
    envVars:
      - key: PYTHON_VERSION
        value: 3.11.0
      - key: PORT
        value: 10000
      - key: DEMO_MODE
        value: false
      - key: ENVIRONMENT
        value: production
"""
    
    with open("render.yaml", "w") as f:
        f.write(render_config)
    
    print("✅ render.yaml created")
    return True

def check_port_configuration():
    """Check if PORT is properly configured for Render"""
    print("\n🔌 CHECKING PORT CONFIGURATION")
    print("=" * 50)
    
    with open("main.py", "r") as f:
        content = f.read()
    
    # Check if PORT environment variable is used
    if "os.getenv(\"PORT\"" in content or "os.environ.get(\"PORT\"" in content:
        print("✅ PORT environment variable properly configured")
        return True
    else:
        print("⚠️  PORT environment variable not found - will add it")
        
        # Add PORT configuration to main.py
        port_code = '''
import os
# ... existing code ...

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8001))
    uvicorn.run(app, host="0.0.0.0", port=port)
'''
        print("💡 Add this to your main.py for Render compatibility:")
        print(port_code)
        return False

def main():
    """Main validation function"""
    print("🚀 RENDER DEPLOYMENT VALIDATION")
    print("=" * 60)
    print("Checking if backend is ready for Render deployment...")
    print()
    
    checks = [
        check_requirements,
        check_main_app,
        check_environment_variables,
        check_supabase_connection,
        check_api_endpoints,
        check_port_configuration
    ]
    
    results = []
    for check in checks:
        try:
            result = check()
            results.append(result)
        except Exception as e:
            print(f"❌ Check failed with error: {e}")
            results.append(False)
    
    # Create render config regardless
    create_render_config()
    
    print("\n📋 VALIDATION SUMMARY")
    print("=" * 60)
    passed = sum(results)
    total = len(results)
    
    print(f"Checks passed: {passed}/{total}")
    
    if passed == total:
        print("\n🎉 READY FOR RENDER DEPLOYMENT!")
        print("✅ All validation checks passed")
        print("\nNext steps:")
        print("1. Push code to GitHub repository")
        print("2. Connect repository to Render")
        print("3. Add environment variables from render-env-vars.txt")
        print("4. Deploy!")
    else:
        print(f"\n⚠️  {total - passed} issues need to be resolved before deployment")
        print("Please fix the issues above and run this script again")

if __name__ == "__main__":
    main()

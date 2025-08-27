#!/usr/bin/env python3
"""
Frontend Deployment Preparation Script Template
Replace placeholder values with your actual API keys before using
"""

import os
import shutil
from pathlib import Path

def prepare_frontend_env():
    """Create production environment file for frontend deployment"""
    
    # Production environment variables template
    env_content = """
# ✅ BACKEND API URL
NEXT_PUBLIC_API_URL=https://your-backend-url.render.com

# ✅ SUPABASE (if using client-side)
NEXT_PUBLIC_SUPABASE_URL=your_supabase_url_here
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key_here

# ✅ CLIENT-SIDE API KEYS (only if needed for client-side calls)
NEXT_PUBLIC_OPENAI_API_KEY=your_openai_api_key_here
NEXT_PUBLIC_HUNTER_API_KEY=your_hunter_api_key_here
NEXT_PUBLIC_INSTANTLY_API_KEY=your_instantly_api_key_here
NEXT_PUBLIC_RAPIDAPI_KEY=your_rapidapi_key_here
NEXT_PUBLIC_APIFY_API_KEY=your_apify_api_key_here

# ✅ PRODUCTION MODE
NODE_ENV=production
"""
    
    # Write to frontend directory
    frontend_path = Path(__file__).parent.parent / "frontend"
    env_file = frontend_path / ".env.production"
    
    if frontend_path.exists():
        with open(env_file, "w") as f:
            f.write(env_content.strip())
        print(f"✅ Created production environment file: {env_file}")
    else:
        print("❌ Frontend directory not found")

if __name__ == "__main__":
    prepare_frontend_env()

#!/usr/bin/env python3
"""
Coogi Backend Server Startup Script
Run this from the coogi-backend directory
"""

import os
import sys
import subprocess

def main():
    print("🚀 Starting Coogi Backend Server")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not os.path.exists("main.py"):
        print("❌ Error: main.py not found")
        print("Make sure you're running this from the coogi-backend directory")
        sys.exit(1)
    
    # Check if .env exists
    if not os.path.exists(".env"):
        print("⚠️  Warning: .env file not found")
        print("Copy env_template.txt to .env and configure your API keys")
        
        # Check if env_template exists
        if os.path.exists("env_template.txt"):
            response = input("Would you like me to copy env_template.txt to .env? (y/n): ")
            if response.lower() == 'y':
                subprocess.run(["cp", "env_template.txt", ".env"])
                print("✅ Created .env file from template")
                print("📝 Please edit .env and add your API keys")
                return
    
    # Check if requirements are installed
    print("📦 Checking dependencies...")
    try:
        import fastapi
        import uvicorn
        print("✅ FastAPI and Uvicorn found")
    except ImportError:
        print("❌ Missing dependencies. Installing...")
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
    
    # Start the server
    print("\n🌟 Starting server on http://localhost:8001")
    print("📋 API docs: http://localhost:8001/docs")
    print("❤️  Health check: http://localhost:8001/health")
    print("\nPress Ctrl+C to stop the server")
    print("=" * 50)
    
    try:
        subprocess.run([
            sys.executable, "-m", "uvicorn", 
            "main:app", 
            "--host", "0.0.0.0", 
            "--port", "8001", 
            "--reload"
        ])
    except KeyboardInterrupt:
        print("\n\n👋 Server stopped")

if __name__ == "__main__":
    main()

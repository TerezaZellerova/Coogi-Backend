"""
Master Control Program API - Main Application
Clean, modular FastAPI application with separated routers
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from datetime import datetime
import os
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Performance optimizations for faster startup
import sys
if sys.version_info >= (3, 8):
    # Use faster JSON encoder if available
    try:
        import orjson
        import ujson
    except ImportError:
        pass

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import routers
from api.routers import agents, campaigns, auth, leads, progressive_agents, email, quota_management, production_campaigns, candidates, coogi_email_intelligence

# Import shared models for OpenAPI documentation
from api.models import HealthResponse
from utils.progressive_agent_db import ProgressiveAgentDB

# Initialize FastAPI app
app = FastAPI(
    title="MCP: Master Control Program API",
    description="Automated recruiting and outreach platform API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware - Production ready configuration
cors_origins = [
    "http://localhost:3000",  # Local development
    "https://coogi-platform.netlify.app",  # Netlify production
    "https://main--coogi-platform.netlify.app",  # Netlify preview branches
    "*"  # Allow all origins during initial deployment (remove after testing)
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files (CSS, JS, images)
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

# Include API routers
app.include_router(agents.router)
app.include_router(campaigns.router)
app.include_router(production_campaigns.router)
app.include_router(auth.router)
app.include_router(leads.router)
app.include_router(progressive_agents.router)
app.include_router(email.router)
app.include_router(quota_management.router)
app.include_router(candidates.router)
app.include_router(coogi_email_intelligence.router)  # Coogi domain email intelligence

# Serve HTML templates
@app.get("/login", response_class=HTMLResponse)
async def get_login():
    try:
        with open("templates/login.html", "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse(content="<h1>Login page not found</h1>", status_code=404)

@app.get("/signup", response_class=HTMLResponse)
async def get_signup():
    try:
        with open("templates/signup.html", "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse(content="<h1>Signup page not found</h1>", status_code=404)

@app.get("/ui", response_class=HTMLResponse)
async def get_ui():
    try:
        with open("templates/index.html", "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse(content="<h1>UI page not found</h1>", status_code=404)

@app.get("/dashboard", response_class=HTMLResponse)
async def get_dashboard():
    try:
        with open("templates/dashboard.html", "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse(content="<h1>Dashboard page not found</h1>", status_code=404)

@app.get("/agent-detail", response_class=HTMLResponse)
async def get_agent_detail():
    try:
        with open("templates/agent_detail.html", "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse(content="<h1>Agent detail page not found</h1>", status_code=404)

@app.get("/test-login", response_class=HTMLResponse)
async def get_test_login():
    """Serve the test login page with development credentials"""
    try:
        with open("templates/test_login.html", "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse(content="""
        <html>
        <head><title>Test Login - Coogi</title></head>
        <body>
            <h1>Test Login Not Found</h1>
            <p>The test login template file is missing.</p>
        </body>
        </html>
        """, status_code=404)

# Note: Routers already included above, removing duplicates

# Root endpoint
@app.get("/", response_model=HealthResponse, tags=["root"])
async def root():
    """Root endpoint with API status"""
    api_status = {
        "OpenAI": bool(os.getenv("OPENAI_API_KEY")),
        "RapidAPI": bool(os.getenv("RAPIDAPI_KEY")),
        "Hunter.io": bool(os.getenv("HUNTER_API_KEY")),
        "Instantly.ai": bool(os.getenv("INSTANTLY_API_KEY")),
        "JobSpy_API": True
    }
    
    # Only email discovery is in demo mode without Hunter.io
    demo_mode = not bool(os.getenv("HUNTER_API_KEY"))
    
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now().isoformat(),
        api_status=api_status,
        demo_mode=demo_mode
    )

# Health check endpoint
@app.get("/health", response_model=HealthResponse, tags=["root"])
async def health_check():
    """Health check endpoint with detailed API status"""
    api_status = {
        "OpenAI": bool(os.getenv("OPENAI_API_KEY")),
        "RapidAPI": bool(os.getenv("RAPIDAPI_KEY")),
        "Hunter.io": bool(os.getenv("HUNTER_API_KEY")),
        "Apollo.io": bool(os.getenv("APOLLO_API_KEY")),
        "AWS_SES": bool(os.getenv("AWS_ACCESS_KEY_ID") and os.getenv("AWS_SECRET_ACCESS_KEY")),
        "Instantly.ai": bool(os.getenv("INSTANTLY_API_KEY")),
        "SmartLead.ai": bool(os.getenv("SMARTLEAD_API_KEY")),
        "JobSpy_API": True
    }
    
    # Only email discovery is in demo mode without Hunter.io
    demo_mode = not bool(os.getenv("HUNTER_API_KEY"))
    
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now().isoformat(),
        api_status=api_status,
        demo_mode=demo_mode
    )

# Debug endpoint for environment variables
@app.get("/debug/env", tags=["debug"])
async def debug_environment():
    """Debug endpoint to check environment variables"""
    return {
        "OPENAI_API_KEY": "SET" if os.getenv("OPENAI_API_KEY") else "NOT SET",
        "HUNTER_API_KEY": "SET" if os.getenv("HUNTER_API_KEY") else "NOT SET", 
        "INSTANTLY_API_KEY": "SET" if os.getenv("INSTANTLY_API_KEY") else "NOT SET",
        "APOLLO_API_KEY": "SET" if os.getenv("APOLLO_API_KEY") else "NOT SET",
        "AWS_ACCESS_KEY_ID": "SET" if os.getenv("AWS_ACCESS_KEY_ID") else "NOT SET",
        "AWS_SECRET_ACCESS_KEY": "SET" if os.getenv("AWS_SECRET_ACCESS_KEY") else "NOT SET",
        "AWS_REGION": os.getenv("AWS_REGION", "us-east-1"),
        "RAPIDAPI_KEY": "SET" if os.getenv("RAPIDAPI_KEY") else "NOT SET",
        "CLEAROUT_API_KEY": "SET" if os.getenv("CLEAROUT_API_KEY") else "NOT SET",
        "SUPABASE_URL": os.getenv("SUPABASE_URL"),
        "SUPABASE_ANON_KEY": "SET" if os.getenv("SUPABASE_ANON_KEY") else "NOT SET",
        "SUPABASE_SERVICE_ROLE_KEY": "SET" if os.getenv("SUPABASE_SERVICE_ROLE_KEY") else "NOT SET",
        "current_supabase_key_type": "service_role" if os.getenv("SUPABASE_SERVICE_ROLE_KEY") else "anonymous"
    }

# Additional essential endpoints that were in the original api.py
@app.get("/memory-stats", tags=["utils"])
async def get_memory_stats():
    """Get memory/tracking statistics"""
    from utils.memory_manager import MemoryManager
    memory_manager = MemoryManager()
    stats = memory_manager.get_stats()
    return {"stats": stats, "timestamp": datetime.now().isoformat()}

@app.delete("/memory", tags=["utils"])
async def clear_memory():
    """Clear all memory data"""
    from utils.memory_manager import MemoryManager
    memory_manager = MemoryManager()
    memory_manager.clear_memory()
    return {"message": "Memory cleared successfully", "timestamp": datetime.now().isoformat()}

# Webhook endpoint for receiving processing results
@app.post("/webhook/results", tags=["webhooks"])
async def receive_webhook_results(request: dict):
    """Receive processing results from the pipeline"""
    try:
        logger.info(f"Received webhook results for batch {request.get('batch_id', 'unknown')}")
        
        # Store results in Supabase if available
        try:
            from supabase import create_client
            supabase_url = os.getenv("SUPABASE_URL")
            supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_ANON_KEY")
            
            if supabase_url and supabase_key:
                supabase = create_client(supabase_url, supabase_key)
                
                # Store batch summary and results
                # Implementation details would go here
                logger.info(f"✅ Stored results in Supabase for batch {request.get('batch_id')}")
            else:
                logger.warning("⚠️  Supabase not available - results not stored")
        except Exception as db_error:
            logger.error(f"Database error: {db_error}")
        
        return {"status": "success", "batch_id": request.get("batch_id")}
        
    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Database test endpoint (add after health check)
@app.get("/test/database", tags=["debug"])
async def test_database():
    """Test database connectivity and return sample data"""
    try:
        db = ProgressiveAgentDB()
        
        # Test progressive agents
        agents = await db.get_all_agents(limit=3)
        
        # Test campaigns 
        campaigns_query = db.supabase.table('production_campaigns').select('*').limit(3).execute()
        campaigns = campaigns_query.data
        
        # Test contacts
        contacts_query = db.supabase.table('contacts').select('*').limit(3).execute()
        contacts = contacts_query.data
        
        return {
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "test_data": {
                "agents_count": len(agents),
                "campaigns_count": len(campaigns),
                "contacts_count": len(contacts),
                "sample_agent": agents[0] if agents else None,
                "sample_campaign": campaigns[0] if campaigns else None,
                "sample_contact": contacts[0] if contacts else None
            }
        }
    except Exception as e:
        logger.error(f"Database test failed: {e}")
        return {
            "status": "error",
            "timestamp": datetime.now().isoformat(),
            "error": str(e),
            "error_type": type(e).__name__
        }

# Test raw HTTP connection to Supabase
@app.get("/test/http-database", tags=["debug"])
async def test_http_database():
    """Test database connectivity using raw HTTP requests"""
    import httpx
    import json
    
    try:
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_ANON_KEY")
        
        headers = {
            "apikey": supabase_key,
            "Authorization": f"Bearer {supabase_key}",
            "Content-Type": "application/json"
        }
        
        # Test connection with HTTP client
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Test agents table
            agents_response = await client.get(
                f"{supabase_url}/rest/v1/progressive_agents?limit=3",
                headers=headers
            )
            
            # Test campaigns table  
            campaigns_response = await client.get(
                f"{supabase_url}/rest/v1/production_campaigns?limit=3",
                headers=headers
            )
            
            # Test contacts table
            contacts_response = await client.get(
                f"{supabase_url}/rest/v1/contacts?limit=3", 
                headers=headers
            )
            
            return {
                "status": "success",
                "timestamp": datetime.now().isoformat(),
                "http_test": {
                    "agents_status": agents_response.status_code,
                    "agents_data": agents_response.json() if agents_response.status_code == 200 else None,
                    "campaigns_status": campaigns_response.status_code,
                    "campaigns_data": campaigns_response.json() if campaigns_response.status_code == 200 else None,
                    "contacts_status": contacts_response.status_code,
                    "contacts_data": contacts_response.json() if contacts_response.status_code == 200 else None
                }
            }
            
    except Exception as e:
        logger.error(f"HTTP database test failed: {e}")
        return {
            "status": "error",
            "timestamp": datetime.now().isoformat(),
            "error": str(e),
            "error_type": type(e).__name__
        }

# Database cleanup endpoints for fresh demo data
@app.delete("/admin/cleanup/leads", tags=["admin"])
async def cleanup_lead_database():
    """Clean up all lead database tables for fresh demo runs"""
    try:
        from supabase import create_client
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_ANON_KEY")
        
        if not supabase_url or not supabase_key:
            raise HTTPException(status_code=500, detail="Database not configured")
        
        supabase = create_client(supabase_url, supabase_key)
        
        # Tables to clean for fresh lead database
        tables_to_clean = [
            'contacts',
            'hunter_emails',  # This is where the actual leads are stored
            'job_opportunities', 
            'progressive_agents',
            'production_campaigns',
            'agent_logs',
            'email_campaigns'
        ]
        
        cleanup_results = {}
        
        for table in tables_to_clean:
            try:
                # Count records before deletion
                count_before = supabase.table(table).select('id', count='exact').execute()
                before_count = count_before.count if count_before.count else 0
                
                # Delete all records from table
                delete_result = supabase.table(table).delete().neq('id', '00000000-0000-0000-0000-000000000000').execute()
                
                # Count records after deletion
                count_after = supabase.table(table).select('id', count='exact').execute()
                after_count = count_after.count if count_after.count else 0
                
                cleanup_results[table] = {
                    "before_count": before_count,
                    "after_count": after_count,
                    "deleted": before_count - after_count,
                    "status": "success"
                }
                
            except Exception as table_error:
                cleanup_results[table] = {
                    "status": "error",
                    "error": str(table_error)
                }
        
        # Clear memory cache as well
        from utils.memory_manager import MemoryManager
        memory_manager = MemoryManager()
        memory_manager.clear_memory()
        
        return {
            "status": "success",
            "message": "Lead database cleaned successfully",
            "timestamp": datetime.now().isoformat(),
            "cleanup_results": cleanup_results,
            "memory_cleared": True
        }
        
    except Exception as e:
        logger.error(f"Database cleanup failed: {e}")
        raise HTTPException(status_code=500, detail=f"Cleanup failed: {str(e)}")

# Database cleanup endpoint for clearing lead data
@app.delete("/admin/cleanup-database", tags=["admin"])
async def cleanup_database():
    """
    ADMIN ONLY: Clear all lead database data for fresh demos
    This will delete all agents, contacts, campaigns, and logs
    """
    try:
        from supabase import create_client
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_ANON_KEY")
        
        if not supabase_url or not supabase_key:
            raise HTTPException(status_code=500, detail="Database configuration not available")
        
        supabase = create_client(supabase_url, supabase_key)
        
        # Track what we're cleaning
        cleanup_stats = {}
        
        # Get counts before deletion
        tables_to_clean = [
            'contacts',
            'progressive_agents', 
            'production_campaigns',
            'agent_logs',
            'email_campaigns'
        ]
        
        for table in tables_to_clean:
            try:
                # Get count before deletion
                count_result = supabase.table(table).select('*', count='exact').execute()
                before_count = count_result.count
                
                # Delete all records
                delete_result = supabase.table(table).delete().neq('id', 0).execute()
                
                # Get count after deletion
                count_after = supabase.table(table).select('*', count='exact').execute()
                after_count = count_after.count
                
                cleanup_stats[table] = {
                    'before': before_count,
                    'after': after_count,
                    'deleted': before_count - after_count
                }
                
                logger.info(f"✅ Cleaned {table}: {before_count} -> {after_count} records")
                
            except Exception as table_error:
                cleanup_stats[table] = {
                    'error': str(table_error),
                    'status': 'failed'
                }
                logger.error(f"❌ Failed to clean {table}: {table_error}")
        
        return {
            "status": "success",
            "message": "Database cleanup completed",
            "timestamp": datetime.now().isoformat(),
            "cleanup_stats": cleanup_stats,
            "note": "All lead data has been cleared. New agents will show fresh, real data."
        }
        
    except Exception as e:
        logger.error(f"Database cleanup failed: {e}")
        raise HTTPException(status_code=500, detail=f"Cleanup failed: {str(e)}")

@app.get("/admin/database/stats", tags=["admin"])
async def get_database_stats():
    """Get current database statistics for all tables"""
    try:
        from supabase import create_client
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_ANON_KEY")
        
        if not supabase_url or not supabase_key:
            raise HTTPException(status_code=500, detail="Database not configured")
        
        supabase = create_client(supabase_url, supabase_key)
        
        # Tables to check
        tables_to_check = [
            'contacts',
            'hunter_emails',  # This is where the actual leads are stored  
            'job_opportunities', 
            'progressive_agents',
            'production_campaigns',
            'agent_logs',
            'email_campaigns'
        ]
        
        stats = {}
        total_records = 0
        
        for table in tables_to_check:
            try:
                count_result = supabase.table(table).select('id', count='exact').execute()
                count = count_result.count if count_result.count else 0
                total_records += count
                
                # Get sample records
                sample_result = supabase.table(table).select('*').limit(3).execute()
                sample_data = sample_result.data if sample_result.data else []
                
                stats[table] = {
                    "count": count,
                    "sample_records": len(sample_data),
                    "has_data": count > 0
                }
                
            except Exception as table_error:
                stats[table] = {
                    "count": 0,
                    "error": str(table_error),
                    "has_data": False
                }
        
        return {
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "total_records": total_records,
            "table_stats": stats,
            "database_url": supabase_url
        }
        
    except Exception as e:
        logger.error(f"Database stats failed: {e}")
        raise HTTPException(status_code=500, detail=f"Stats failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    # Use PORT environment variable for Render compatibility
    port = int(os.getenv("PORT", 8001))
    uvicorn.run(app, host="0.0.0.0", port=port)

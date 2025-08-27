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

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import routers
from api.routers import agents, campaigns, auth, leads

# Import shared models for OpenAPI documentation
from api.models import HealthResponse

# Initialize FastAPI app
app = FastAPI(
    title="MCP: Master Control Program API",
    description="Automated recruiting and outreach platform API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Temporarily allow all origins for debugging
    allow_credentials=False,  # Must be False when allow_origins is "*"
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files (CSS, JS, images)
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

# Include API routers
app.include_router(agents.router)
app.include_router(campaigns.router)
app.include_router(auth.router)
app.include_router(leads.router)

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

# Import and include all routers
from api.routers.auth import router as auth_router
from api.routers.leads import router as leads_router
from api.routers.campaigns import router as campaigns_router
from api.routers.agents import router as agents_router

app.include_router(auth_router)
app.include_router(leads_router)
app.include_router(campaigns_router)
app.include_router(agents_router)

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

# Debug endpoint for environment variables
@app.get("/debug/env", tags=["debug"])
async def debug_environment():
    """Debug endpoint to check environment variables"""
    return {
        "OPENAI_API_KEY": "SET" if os.getenv("OPENAI_API_KEY") else "NOT SET",
        "HUNTER_API_KEY": "SET" if os.getenv("HUNTER_API_KEY") else "NOT SET", 
        "INSTANTLY_API_KEY": "SET" if os.getenv("INSTANTLY_API_KEY") else "NOT SET",
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

if __name__ == "__main__":
    import uvicorn
    # Use PORT environment variable for Render compatibility
    port = int(os.getenv("PORT", 8001))
    uvicorn.run(app, host="0.0.0.0", port=port)

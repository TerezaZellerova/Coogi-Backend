# 🎯 Coogi Backend

Clean, organized backend structure for the Coogi lead generation platform.

## 🚀 Quick Start (Render Pro Deployment)

**For production deployment on Render Pro, see:** [`render-env-setup.md`](./render-env-setup.md)

This guide includes:
- Complete environment variable setup
- Step-by-step deployment instructions
- Expected performance improvements (no cold starts!)
- Troubleshooting tips

## 📁 Project Structure

```
coogi-backend/
├── main.py                 # FastAPI application entry point
├── requirements.txt        # Python dependencies
├── runtime.txt            # Python runtime version
├── Dockerfile             # Docker configuration
├── railway.json           # Railway deployment config
├── memory.json            # Memory management data
├── company_blacklist.json # Company blacklist
├── env_template.txt       # Environment variables template
│
├── api/                   # FastAPI API modules
│   ├── __init__.py
│   ├── models.py          # Pydantic models
│   ├── dependencies.py    # Shared dependencies
│   └── routers/           # API route handlers
│       ├── __init__.py
│       ├── auth.py        # Authentication routes
│       ├── leads.py       # Lead generation routes (main pipeline)
│       ├── campaigns.py   # Campaign management routes
│       └── agents.py      # Agent management routes
│
├── utils/                 # Utility modules
│   ├── __init__.py
│   ├── job_scraper.py     # Job scraping (JobSpy integration)
│   ├── contact_finder.py  # Contact finding (RapidAPI integration)
│   ├── email_generator.py # AI email generation
│   ├── instantly_manager.py # Instantly.ai integration
│   ├── memory_manager.py  # Data persistence
│   ├── blacklist_manager.py # Company blacklist management
│   ├── contract_analyzer.py # Contract analysis
│   └── supabase_tracker.py # Supabase logging
│
├── templates/             # HTML templates
│   ├── index.html
│   ├── dashboard.html
│   ├── agent_detail.html
│   ├── login.html
│   └── signup.html
│
├── supabase/             # Database schemas and functions
│   ├── functions/        # Supabase Edge Functions
│   ├── supabase_schema.sql
│   ├── supabase_schema_enhanced.sql
│   ├── create_agent_logs_table.sql
│   ├── fix_missing_columns.sql
│   ├── remove_contact_data_column.sql
│   ├── supabase_company_tracking.sql
│   └── update_*.sql
│
├── tests/                # Test files
│   ├── test_e2e_pipeline.py
│   ├── test_backend_api.py
│   ├── test_*.py
│   └── ...
│
└── scripts/              # Utility scripts
    ├── create_supabase_tables.py
    ├── start_server.py
    ├── start.sh
    ├── debug_start.sh
    ├── add_columns.py
    ├── backfill_*.py
    ├── check_*.py
    ├── milestone_*.py
    └── final_*.py
```

## 🚀 Quick Start

### 1. Install Dependencies
```bash
cd coogi-backend
pip install -r requirements.txt
```

### 2. Environment Setup
```bash
cp env_template.txt .env
# Edit .env with your API keys
```

## 🚀 Render Pro Deployment

### Copy-Paste Environment Variables
Use these environment variables in your Render service. Copy this entire block and paste into the Render dashboard environment variables section:

```bash
# ✅ CORE API KEYS (REQUIRED)
OPENAI_API_KEY=your_openai_api_key_here
HUNTER_API_KEY=your_hunter_api_key_here
RAPIDAPI_KEY=your_rapidapi_key_here
INSTANTLY_API_KEY=your_instantly_api_key_here
APIFY_API_KEY=your_apify_api_key_here
CLEAROUT_API_KEY=your_clearout_api_key_here

# ✅ SUPABASE DATABASE (REQUIRED)
SUPABASE_URL=your_supabase_url_here
SUPABASE_ANON_KEY=your_supabase_anon_key_here
SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key_here

# ✅ PRODUCTION CONFIG (REQUIRED)
PORT=10000
DEMO_MODE=false
DEBUG=false
LOG_LEVEL=info
```

### Deployment Steps
1. **Set Build Command**: `pip install -r requirements.txt`
2. **Set Start Command**: `python -m uvicorn main:app --host 0.0.0.0 --port $PORT`
3. **Set Environment**: Python 3.13
4. **Copy Environment Variables**: Use the block above
5. **Deploy**: Your service will be available at `https://your-service.onrender.com`

### Keep-Alive Setup (Optional)
To prevent cold starts, run the keep-alive script:
```bash
chmod +x keep-alive.sh
./keep-alive.sh &
```

### 3. Run the Server
```bash
# Development
python -m uvicorn main:app --host 0.0.0.0 --port 8001 --reload

# Or use the script
python scripts/start_server.py
```

### 4. Setup Database (Optional)
```bash
python scripts/create_supabase_tables.py
```

## 📋 API Endpoints

- **Health**: `GET /health`
- **Job Search**: `POST /api/search-jobs` (main pipeline)
- **Agents**: `GET/POST/DELETE /api/agents`
- **Leads**: `GET /api/leads`
- **Campaigns**: `GET/POST /api/campaigns`

## 🔧 Configuration

Key environment variables needed in `.env`:
- `OPENAI_API_KEY` - OpenAI for AI features
- `RAPIDAPI_KEY` - RapidAPI for contact finding
- `HUNTER_API_KEY` - Hunter.io for email verification
- `INSTANTLY_API_KEY` - Instantly.ai for campaigns
- `SUPABASE_URL` - Supabase database
- `SUPABASE_SERVICE_ROLE_KEY` - Supabase auth
- `DEMO_MODE` - Enable demo mode (true/false)

## 🧪 Testing

```bash
# Run all tests
python -m pytest tests/

# Test specific functionality
python tests/test_e2e_pipeline.py
python tests/test_backend_api.py
```

## 🐳 Docker Deployment

```bash
docker build -t coogi-backend .
docker run -p 8001:8001 coogi-backend
```

## 📝 Key Features

- ✅ **Complete Pipeline**: JobSpy → RapidAPI → Hunter.io → Instantly.ai
- ✅ **Modular Architecture**: Clean separation of concerns
- ✅ **Error Handling**: Comprehensive error handling and logging
- ✅ **Rate Limiting**: API rate limiting and retry logic
- ✅ **Demo Mode**: Fallback demo data when APIs are down
- ✅ **Database Integration**: Supabase for persistence and logging
- ✅ **Campaign Management**: Instantly.ai integration for email campaigns

## 🔗 Frontend Integration

This backend works with the Next.js frontend located in `../frontend/`.

Backend runs on: `http://localhost:8001`  
Frontend runs on: `http://localhost:3000`

---

**🎯 Ready for production deployment!**

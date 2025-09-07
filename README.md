# 🎯 Coogi Backend

Production-ready backend for the Coogi lead generation platform.

## 🚀 Quick Start

Deploy on Render or any cloud platform supporting Python applications.

### Environment Variables Required:
See `render-env-vars.template` for complete list of required environment variables including:
- Database credentials (Supabase)
- API keys (RapidAPI, OpenAI, etc.)
- Email service configurations (SES, Instantly, Smartlead)
- Authentication settings

## 📁 Project Structure

```
coogi-backend/
├── main.py                 # FastAPI application entry point
├── requirements.txt        # Python dependencies
├── runtime.txt            # Python runtime version
├── Dockerfile             # Docker configuration
├── render.yaml            # Render deployment config
├── company_blacklist.json # Company blacklist
├── render-env-vars.template # Environment variables template
│
├── api/                   # FastAPI API modules
│   ├── __init__.py
│   ├── models.py          # Pydantic models
│   ├── dependencies.py    # Shared dependencies
│   └── routers/           # API route handlers
│       ├── __init__.py
│       ├── auth.py        # Authentication routes
│       ├── leads.py       # Lead generation routes
│       ├── campaigns.py   # Campaign management routes
│       ├── agents.py      # Agent management routes
│       ├── email.py       # Email service routes
│       └── progressive_agents.py # Progressive agent routes
│
├── utils/                 # Utility modules
│   ├── __init__.py
│   ├── job_scraper.py     # Job scraping (JobSpy integration)
│   ├── contact_finder.py  # Contact finding (RapidAPI integration)
│   ├── email_generator.py # AI email generation
│   ├── instantly_manager.py # Instantly.ai integration
│   ├── smartlead_manager.py # Smartlead.ai integration
│   ├── ses_manager.py     # Amazon SES integration
│   ├── memory_manager.py  # Data persistence
│   ├── blacklist_manager.py # Company blacklist management
│   ├── contract_analyzer.py # Contract analysis
│   └── supabase_tracker.py # Supabase logging
│
└── scripts/               # Database and setup scripts
    ├── setup_supabase.py  # Supabase table creation
    └── start.sh           # Server startup script
## 🚀 Quick Start

### 1. Install Dependencies
```bash
cd coogi-backend
pip install -r requirements.txt
```

### 2. Environment Setup
```bash
cp render-env-vars.template .env
# Edit .env with your API keys
```

### 3. Run the Server
```bash
python -m uvicorn main:app --host 0.0.0.0 --port 8001 --reload
```

### 4. Setup Database (Optional)
```bash
python scripts/setup_supabase.py
```

## 📋 API Endpoints

### Core Endpoints
- **Health**: `GET /health`
- **Authentication**: `POST /api/auth/login`, `POST /api/auth/register`
- **Job Search**: `POST /api/search-jobs` (main pipeline)
- **Agents**: `GET/POST/DELETE /api/agents`
- **Leads**: `GET /api/leads`
- **Campaigns**: `GET/POST /api/campaigns`

### Email Services
- **SES**: `POST /api/ses/send-email`, `POST /api/ses/send-bulk-email`
- **Instantly**: Campaign management via Instantly.ai
- **Smartlead**: AI-powered email campaigns

## 🔧 Configuration

Key environment variables needed (see `render-env-vars.template`):
- `OPENAI_API_KEY` - OpenAI for AI features
- `RAPIDAPI_KEY` - RapidAPI for contact finding
- `HUNTER_API_KEY` - Hunter.io for email verification
- `INSTANTLY_API_KEY` - Instantly.ai for campaigns
- `SMARTLEAD_API_KEY` - Smartlead.ai integration
- `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` - Amazon SES
- `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY` - Database

## 🐳 Docker Deployment

```bash
docker build -t coogi-backend .
docker run -p 8001:8001 coogi-backend
```

## 📝 Key Features

- ✅ **Complete Pipeline**: JobSpy → RapidAPI → Hunter.io → Email Services
- ✅ **Multiple Email Providers**: SES, Instantly.ai, Smartlead.ai
- ✅ **Modular Architecture**: Clean separation of concerns
- ✅ **Error Handling**: Comprehensive error handling and logging
- ✅ **Rate Limiting**: API rate limiting and retry logic
- ✅ **Database Integration**: Supabase for persistence and logging
- ✅ **Progressive Agents**: Advanced lead qualification system

## 🔗 Frontend Integration

This backend works with the Next.js frontend located in `../frontend/`.

Backend runs on: `http://localhost:8001`  
Frontend runs on: `http://localhost:3000`

---

**🎯 Ready for production deployment!**

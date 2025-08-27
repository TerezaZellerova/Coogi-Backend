# Render Pro Deployment Setup Guide

## 🚀 Environment Variables for Render

When deploying to your Render Pro account, you'll need to set these environment variables in the Render dashboard:

### Required Environment Variables

```bash
# OpenAI API
OPENAI_API_KEY=your_openai_api_key_here

# Hunter.io API
HUNTER_API_KEY=your_hunter_api_key_here

# Supabase Database
SUPABASE_URL=your_supabase_url_here
SUPABASE_ANON_KEY=your_supabase_anon_key_here
SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key_here

# RapidAPI
RAPIDAPI_KEY=your_rapidapi_key_here

# Instantly.AI
INSTANTLY_API_KEY=your_instantly_api_key_here

# Apify
APIFY_API_KEY=your_apify_api_key_here

# ClearOut (Email Verification)
CLEAROUT_API_KEY=MDY2MzE5NmYtZjU5ZS00NDdlLWFlYzQtNDg1NmUwZjA2MjhhOkhTTEhFWUxDU3ZRVQ==

# Application Settings
PORT=10000
DEMO_MODE=false
ENVIRONMENT=production
PYTHON_VERSION=3.11.0
```

## 📋 Deployment Steps

1. **Connect GitHub Repository**
   - Go to Render Dashboard → New → Web Service
   - Connect your GitHub repository: `your-github-username/coogi-backend`
   - Select the `main` branch

2. **Service Configuration**
   - **Name**: `coogi-backend-pro`
   - **Environment**: `Python`
   - **Build Command**: `./render-build.sh`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`

3. **Add Environment Variables**
   - Copy all variables from the list above
   - Add them one by one in Render's Environment tab

4. **Deploy**
   - Click "Create Web Service"
   - Wait for deployment (should be much faster on Pro)

## ✅ Expected Benefits on Render Pro

- **No Cold Starts**: Service stays warm 24/7
- **Faster Response Times**: < 1 second instead of 30+ seconds
- **Better Performance**: More CPU and memory
- **Reliable Agent Creation**: No more timeouts

## 🔗 Post-Deployment

After deployment completes:
1. Update frontend `.env.production` with new backend URL
2. Test agent creation flow
3. Verify job scraping functionality
4. Monitor performance in Render dashboard

## 🆘 Troubleshooting

If you encounter issues:
- Check Render logs in the dashboard
- Verify all environment variables are set correctly
- Ensure the GitHub repository is up to date
- Contact support if needed - you now have Pro support access!

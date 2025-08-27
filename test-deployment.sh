#!/bin/bash
# Quick Backend Test Script
# Run this after deployment to verify everything works

echo "🧪 Testing Coogi Backend Deployment"
echo "=================================="

# Get backend URL from user
read -p "Enter your backend URL (e.g., https://coogi-backend-pro.onrender.com): " BACKEND_URL

if [ -z "$BACKEND_URL" ]; then
    echo "❌ Backend URL is required"
    exit 1
fi

echo "Testing backend: $BACKEND_URL"
echo ""

# Test 1: Health Check
echo "1️⃣ Testing health endpoint..."
response_time=$(curl -s -w "%{time_total}" -o /dev/null "$BACKEND_URL/health")
http_code=$(curl -s -w "%{http_code}" -o /dev/null "$BACKEND_URL/health")

if [ "$http_code" = "200" ]; then
    echo "✅ Health check passed (HTTP $http_code)"
    echo "⏱️  Response time: ${response_time}s"
else
    echo "❌ Health check failed (HTTP $http_code)"
fi

echo ""

# Test 2: Root Endpoint
echo "2️⃣ Testing root endpoint..."
response_time=$(curl -s -w "%{time_total}" -o /dev/null "$BACKEND_URL/")
http_code=$(curl -s -w "%{http_code}" -o /dev/null "$BACKEND_URL/")

if [ "$http_code" = "200" ]; then
    echo "✅ Root endpoint passed (HTTP $http_code)"
    echo "⏱️  Response time: ${response_time}s"
else
    echo "❌ Root endpoint failed (HTTP $http_code)"
fi

echo ""

# Test 3: API Documentation
echo "3️⃣ Testing API docs..."
response_time=$(curl -s -w "%{time_total}" -o /dev/null "$BACKEND_URL/docs")
http_code=$(curl -s -w "%{http_code}" -o /dev/null "$BACKEND_URL/docs")

if [ "$http_code" = "200" ]; then
    echo "✅ API docs available (HTTP $http_code)"
    echo "⏱️  Response time: ${response_time}s"
    echo "🔗 View docs at: $BACKEND_URL/docs"
else
    echo "❌ API docs failed (HTTP $http_code)"
fi

echo ""

# Test 4: Cold Start Test
echo "4️⃣ Testing for cold starts..."
echo "Making 3 consecutive requests to check consistency..."

for i in {1..3}; do
    start_time=$(date +%s.%N)
    http_code=$(curl -s -w "%{http_code}" -o /dev/null "$BACKEND_URL/health")
    end_time=$(date +%s.%N)
    response_time=$(echo "$end_time - $start_time" | bc)
    
    echo "Request $i: HTTP $http_code, ${response_time}s"
    
    if [ "$http_code" != "200" ]; then
        echo "❌ Request $i failed"
    fi
    
    sleep 1
done

echo ""
echo "🎯 Test Summary"
echo "==============="
echo "All requests should be:"
echo "- HTTP 200 status"
echo "- Response time < 2 seconds (ideally < 1s)"
echo "- Consistent performance (no cold starts)"
echo ""
echo "If you see slow first request (>10s), you might still be on free tier."
echo "Render Pro should eliminate cold starts completely!"
echo ""
echo "Next steps:"
echo "1. Test agent creation in your frontend"
echo "2. Verify job scraping works"
echo "3. Check Supabase data flow"
echo "4. Monitor performance over 24 hours"

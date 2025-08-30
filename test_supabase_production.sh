#!/bin/bash

# TEST SUPABASE PRODUCTION CONNECTION
echo "🧪 TESTING SUPABASE PRODUCTION CONNECTION"
echo "========================================="
echo ""

echo "🔍 Testing API Health Check..."
HEALTH_RESPONSE=$(curl -s "https://coogi-backend-7yca.onrender.com")
echo "Response: $HEALTH_RESPONSE"
echo ""

echo "🔍 Testing Progressive Agent Creation (requires Supabase)..."
AGENT_RESPONSE=$(curl -s -X POST "https://coogi-backend-7yca.onrender.com/api/agents/create-progressive" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Test Job",
    "target_type": "hiring_managers",
    "company_size": "medium",
    "hours_old": 168
  }')

echo "Response: $AGENT_RESPONSE"
echo ""

# Check for 401 errors
if echo "$AGENT_RESPONSE" | grep -q "401\|Unauthorized\|authentication"; then
    echo "❌ SUPABASE AUTH ERROR DETECTED"
    echo "   Still getting 401 errors - keys need to be updated on Render"
    echo ""
    echo "🔧 NEXT STEPS:"
    echo "   1. Go to https://render.com/dashboard"
    echo "   2. Find coogi-backend service"
    echo "   3. Update Environment variables"
    echo "   4. Wait for redeploy"
    echo "   5. Run this test again"
elif echo "$AGENT_RESPONSE" | grep -q "agent.*id"; then
    echo "✅ SUPABASE CONNECTION WORKING!"
    echo "   Agent creation successful - database connected"
else
    echo "⚠️  UNEXPECTED RESPONSE - check manually"
fi

echo ""
echo "🔗 Manual check URL: https://coogi-backend-7yca.onrender.com"

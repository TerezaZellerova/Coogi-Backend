#!/bin/bash
# Backend Keep-Alive Script
# Pings the backend every 10 minutes to prevent cold starts

BACKEND_URL="https://coogi-backend.onrender.com"

echo "🏃 Starting backend keep-alive service..."
echo "Backend URL: $BACKEND_URL"

while true; do
    echo "📡 Pinging backend at $(date)"
    
    # Simple health check
    response=$(curl -s -w "%{http_code}" -o /dev/null "$BACKEND_URL/")
    
    if [ "$response" = "200" ]; then
        echo "✅ Backend is alive (HTTP $response)"
    else
        echo "⚠️  Backend response: HTTP $response"
    fi
    
    # Wait 10 minutes (600 seconds)
    echo "💤 Sleeping for 10 minutes..."
    sleep 600
done

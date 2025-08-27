#!/bin/bash

# Coogi Backend Server Startup Script
# This script starts the FastAPI backend server cleanly

echo "🚀 Starting Coogi Backend Server..."

# Navigate to the backend directory
cd "$(dirname "$0")"

# Kill any existing processes on port 8080
echo "🧹 Cleaning up any existing processes..."
lsof -ti:8080 | xargs kill -9 2>/dev/null || echo "No existing processes on port 8080"

# Start the server
echo "🔥 Starting FastAPI server on port 8080..."
python3 -m uvicorn main:app --host 0.0.0.0 --port 8080 --reload

echo "✅ Server started successfully!"
echo "📖 API docs available at: http://localhost:8080/docs"
echo "🏥 Health check: http://localhost:8080/health"

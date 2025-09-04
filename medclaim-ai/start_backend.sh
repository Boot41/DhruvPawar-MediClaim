#!/bin/bash

# Start Backend Server
echo "🚀 Starting MediClaim AI Backend Server..."

cd backend

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt

# Set environment variables
export GOOGLE_API_KEY="AIzaSyC6ZNdpGyKQLPcUFCa76qLOufLEKcz7oFs"
export SECRET_KEY="your_secret_key_here"
export DATABASE_URL="sqlite:///./medclaim.db"

# Start server
echo "🌟 Starting FastAPI server on http://localhost:8000"
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

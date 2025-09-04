#!/bin/bash

# Start Frontend Server
echo "🚀 Starting MediClaim AI Frontend Server..."

cd frontend

# Install dependencies
echo "📥 Installing dependencies..."
npm install

# Set environment variables
export REACT_APP_API_URL="http://localhost:8000"

# Start development server
echo "🌟 Starting React development server on http://localhost:3000"
npm start

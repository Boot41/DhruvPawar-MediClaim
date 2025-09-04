#!/usr/bin/env python3
"""
MediClaim AI Backend Startup Script
Production-ready FastAPI server with all dependencies
"""

import os
import sys
import subprocess
from pathlib import Path

def check_dependencies():
    """Check if all required dependencies are installed."""
    try:
        import fastapi
        import uvicorn
        import sqlalchemy
        import jose
        import passlib
        import aiofiles
        import magic
        print("✓ All Python dependencies are installed")
        return True
    except ImportError as e:
        print(f"✗ Missing dependency: {e}")
        return False

def setup_environment():
    """Setup environment variables and configuration."""
    env_file = Path(".env")
    if not env_file.exists():
        print("Creating .env file from template...")
        subprocess.run(["cp", ".env.example", ".env"])
        print("✓ Environment file created. Please update .env with your settings.")
    else:
        print("✓ Environment file exists")

def create_directories():
    """Create necessary directories."""
    directories = [
        "uploads/documents",
        "uploads/forms", 
        "uploads/temp",
        "claim_forms"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"✓ Created directory: {directory}")

def initialize_database():
    """Initialize the database."""
    try:
        from database import create_tables
        create_tables()
        print("✓ Database tables created successfully")
        return True
    except Exception as e:
        print(f"✗ Database initialization failed: {e}")
        return False

def start_server():
    """Start the FastAPI server."""
    print("\n🚀 Starting MediClaim AI Backend Server...")
    print("Server will be available at: http://localhost:8080")
    print("API Documentation: http://localhost:8080/docs")
    print("Press Ctrl+C to stop the server\n")
    
    try:
        import uvicorn
        uvicorn.run(
            "main:app",
            host="0.0.0.0",
            port=8080,
            reload=True,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n👋 Server stopped")
    except Exception as e:
        print(f"✗ Server failed to start: {e}")

def main():
    """Main startup function."""
    print("🏥 MediClaim AI Backend - Production Setup")
    print("=" * 50)
    
    # Check dependencies
    if not check_dependencies():
        print("\n📦 Installing dependencies...")
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        
        if not check_dependencies():
            print("✗ Failed to install dependencies. Please install manually.")
            return
    
    # Setup environment
    setup_environment()
    
    # Create directories
    create_directories()
    
    # Initialize database
    if not initialize_database():
        print("✗ Database setup failed. Please check your configuration.")
        return
    
    # Start server
    start_server()

if __name__ == "__main__":
    main()

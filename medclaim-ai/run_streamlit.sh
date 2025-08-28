#!/bin/bash
# Script to run the MedClaim AI Streamlit application

echo "Starting MedClaim AI Validator..."
echo "Make sure Ollama is running with: ollama serve"
echo "And Gemma 7B is installed with: ollama pull gemma:7b"
echo ""

cd "$(dirname "$0")"
streamlit run src/ui/streamlit_app.py --server.port 8501 --server.address 0.0.0.0

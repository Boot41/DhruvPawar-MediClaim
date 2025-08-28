#!/usr/bin/env python3
"""Quick test script to verify MedClaim AI setup."""

import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

def test_imports():
    """Test if all required modules can be imported."""
    try:
        from config.settings import get_settings
        from utils.document_processor import DocumentProcessor
        from utils.vector_store import VectorStoreManager
        from services.rag_service import MedClaimRAGService
        print("✅ All imports successful")
        return True
    except Exception as e:
        print(f"❌ Import error: {e}")
        return False

def test_settings():
    """Test settings configuration."""
    try:
        from config.settings import get_settings
        settings = get_settings()
        print(f"✅ Settings loaded:")
        print(f"   - Ollama model: {settings.ollama_model}")
        print(f"   - Embedding model: {settings.embedding_model}")
        print(f"   - Chroma dir: {settings.chroma_persist_dir}")
        return True
    except Exception as e:
        print(f"❌ Settings error: {e}")
        return False

def test_ollama():
    """Test Ollama connection."""
    try:
        import requests
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            print("✅ Ollama service is running")
            return True
        else:
            print(f"❌ Ollama returned status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Ollama connection error: {e}")
        return False

def test_rag_service():
    """Test RAG service initialization."""
    try:
        from services.rag_service import MedClaimRAGService
        service = MedClaimRAGService()
        print("✅ RAG service initialized successfully")
        return True
    except Exception as e:
        print(f"❌ RAG service error: {e}")
        return False

if __name__ == "__main__":
    print("🏥 Testing MedClaim AI Setup...")
    print("=" * 40)
    
    tests = [
        ("Imports", test_imports),
        ("Settings", test_settings),
        ("Ollama", test_ollama),
        ("RAG Service", test_rag_service),
    ]
    
    passed = 0
    for name, test_func in tests:
        print(f"\n🔍 Testing {name}...")
        if test_func():
            passed += 1
    
    print("\n" + "=" * 40)
    print(f"📊 Results: {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("🎉 Setup is ready! You can now run the Streamlit app.")
    else:
        print("⚠️  Some issues found. Check the errors above.")

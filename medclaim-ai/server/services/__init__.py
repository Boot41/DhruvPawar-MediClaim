# Import real services
from typing import Any, Dict, Optional
from .auth_service import auth_service

class GeminiService:
    """Stub Gemini AI service"""
    
    async def test_connection(self) -> bool:
        return False
    
    async def process_document(self, file_path: str) -> Dict[str, Any]:
        return {"extracted_data": {}, "confidence": 0.0}
    
    async def generate_response(self, prompt: str) -> str:
        return "AI service not available - using stub response"

# Create singleton instances
# auth_service is imported from auth_service module
gemini_service = GeminiService()

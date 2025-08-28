from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import sys
from pathlib import Path

# Add src to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from services.rag_service import MedClaimRAGService
from config.settings import get_settings

# Initialize FastAPI app
app = FastAPI(
    title="MedClaim AI Validator API",
    description="API for medical claim document processing and validation",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global service instance
rag_service = None
settings = get_settings()

@app.on_event("startup")
async def startup_event():
    """Initialize the RAG service on startup."""
    global rag_service
    rag_service = MedClaimRAGService()

# Request/Response models
class QueryRequest(BaseModel):
    question: str
    filter_filenames: Optional[List[str]] = None

class QueryResponse(BaseModel):
    answer: str
    sources: List[dict]
    status: str

class UploadResponse(BaseModel):
    filename: str
    status: str
    chunks_added: int
    message: str

# API endpoints
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "MedClaim AI Validator"}

@app.post("/upload", response_model=UploadResponse)
async def upload_document(file: UploadFile = File(...)):
    """Upload and process a PDF document."""
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    
    try:
        file_bytes = await file.read()
        result = rag_service.ingest_pdf(file_bytes, file.filename)
        return UploadResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")

@app.post("/query", response_model=QueryResponse)
async def query_documents(request: QueryRequest):
    """Query the processed documents."""
    try:
        result = rag_service.query(request.question, request.filter_filenames)
        return QueryResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")

@app.get("/stats")
async def get_stats():
    """Get system statistics."""
    try:
        stats = rag_service.get_document_stats()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting stats: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

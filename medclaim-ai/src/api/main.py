from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import sys
from pathlib import Path
import asyncio
from concurrent.futures import ThreadPoolExecutor
import logging
import time

# Add src to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from services.rag_service import MedClaimRAGService
from config.settings import get_settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('medclaim_api.log')
    ]
)
logger = logging.getLogger(__name__)

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

# Global service instance and thread pool
rag_service = None
settings = get_settings()
executor = ThreadPoolExecutor(max_workers=4)

@app.on_event("startup")
async def startup_event():
    """Initialize the RAG service on startup."""
    global rag_service
    logger.info("Starting MedClaim AI API...")
    start_time = time.time()
    rag_service = MedClaimRAGService()
    init_time = time.time() - start_time
    logger.info(f"RAG service initialized in {init_time:.2f} seconds")

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
    """Upload and process a PDF document asynchronously."""
    logger.info(f"Received upload request for file: {file.filename}")
    
    if not file.filename.lower().endswith('.pdf'):
        logger.warning(f"Invalid file type for {file.filename}")
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    
    try:
        start_time = time.time()
        logger.info(f"Reading file bytes for {file.filename}")
        file_bytes = await file.read()
        logger.info(f"File read completed, size: {len(file_bytes)} bytes")
        
        # Run PDF processing in thread pool to avoid blocking
        logger.info(f"Starting PDF processing for {file.filename}")
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            executor,
            rag_service.ingest_pdf,
            file_bytes,
            file.filename
        )
        
        processing_time = time.time() - start_time
        logger.info(f"Upload processing completed for {file.filename} in {processing_time:.2f} seconds")
        return UploadResponse(**result)
    except Exception as e:
        logger.error(f"Error processing file {file.filename}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")

@app.post("/query", response_model=QueryResponse)
async def query_documents(request: QueryRequest):
    """Query the processed documents asynchronously."""
    logger.info(f"Received query: {request.question[:100]}...")
    if request.filter_filenames:
        logger.info(f"Query filters: {request.filter_filenames}")
    
    try:
        start_time = time.time()
        logger.info("Starting query processing")
        
        # Run query in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            executor, 
            rag_service.query, 
            request.question, 
            request.filter_filenames
        )
        
        query_time = time.time() - start_time
        logger.info(f"Query processing completed in {query_time:.2f} seconds")
        logger.info(f"Answer length: {len(result.get('answer', ''))} chars, Sources: {len(result.get('sources', []))}")
        
        return QueryResponse(**result)
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")

@app.get("/stats")
async def get_stats():
    """Get system statistics asynchronously."""
    try:
        loop = asyncio.get_event_loop()
        stats = await loop.run_in_executor(executor, rag_service.get_document_stats)
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting stats: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting uvicorn server...")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")

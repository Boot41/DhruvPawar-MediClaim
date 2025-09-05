"""
Main FastAPI application for Insurance Claim Processing System
"""
from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Form, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from typing import List, Optional
import json
import os
from datetime import datetime, timedelta
import uuid

# Local imports
from database_connection import get_db, init_database
from database import User, UserSession, Document, DocumentChunk, Claim, Vendor, WorkflowState, ChatMessage as DBChatMessage
from schemas import *
from auth import (
    authenticate_user, create_access_token, get_current_user, require_active_user,
    get_password_hash, create_user, create_user_session
)
from file_handler import file_handler
from agent_service import agent_service

# Initialize FastAPI app
app = FastAPI(
    title="MediClaim AI API",
    description="AI-powered insurance claim processing system with document chunking and chatbot",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize database and seed data."""
    init_database()
    print("🔗 Health Check: http://localhost:8000/health")
    print("📚 API Documentation: http://localhost:8000/docs")

# =============== HEALTH CHECK ===============

@app.get("/health", response_model=HealthCheck)
async def health_check():
    """Health check endpoint."""
    return HealthCheck(
        status="healthy",
        timestamp=datetime.utcnow(),
        version="1.0.0",
        database="connected",
        agents="ready"
    )

# =============== AUTHENTICATION ===============

@app.post("/auth/register", response_model=UserResponse)
async def register(user: UserCreate, db: Session = Depends(get_db)):
    """Register a new user."""
    try:
        db_user = create_user(db, user)
        return UserResponse(
            id=db_user.id,
            email=db_user.email,
            full_name=db_user.full_name,
            is_active=db_user.is_active,
            created_at=db_user.created_at
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/auth/login", response_model=Token)
async def login(user: UserLogin, db: Session = Depends(get_db)):
    """Login user and return access token."""
    db_user = authenticate_user(db, user.email, user.password)
    if not db_user:
        raise HTTPException(
            status_code=401,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(data={"sub": db_user.id})
    return Token(access_token=access_token, token_type="bearer")

@app.post("/auth/session", response_model=dict)
async def create_session(
    current_user: User = Depends(require_active_user),
    db: Session = Depends(get_db)
):
    """Create a new user session."""
    session = create_user_session(db, current_user.id)
    return {
        "session_id": session.id,
        "session_token": session.session_token,
        "expires_at": session.expires_at.isoformat()
    }

# =============== DOCUMENT UPLOAD ===============

@app.post("/api/documents/upload", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    file_type: str = Form(...),
    session_id: str = Form(...),
    current_user: User = Depends(require_active_user),
    db: Session = Depends(get_db)
):
    """Upload and process a document."""
    try:
        # Validate file type
        if file_type not in ["policy", "invoice", "medical_record"]:
            raise HTTPException(status_code=400, detail="Invalid file type")
        
        # Save file
        file_result = await file_handler.save_file(file, current_user.id, file_type)
        if not file_result.get("success"):
            raise HTTPException(status_code=500, detail=file_result.get("error"))
        
        # Create document record
        document = Document(
            user_id=current_user.id,
            session_id=session_id,
            filename=file_result["filename"],
            original_filename=file_result["original_filename"],
            file_path=file_result["file_path"],
            file_type=file_type,
            file_size=file_result["file_size"],
            upload_status="uploaded"
        )
        db.add(document)
        db.commit()
        db.refresh(document)
        
        # Process document with agent service
        processing_result = await agent_service.process_document(
            file_result["file_path"], file_type, current_user.id, db, document.id
        )
        
        if processing_result.get("success"):
            # Update document with extracted data
            document.extracted_data = processing_result.get("extracted_data")
            document.upload_status = "processed"
            document.processed_at = datetime.utcnow()
            db.commit()
        
        return DocumentResponse(
            id=document.id,
            filename=document.filename,
            original_filename=document.original_filename,
            file_type=document.file_type,
            upload_status=document.upload_status,
            extracted_data=document.extracted_data,
            total_chunks=processing_result.get("total_chunks", 0),
            created_at=document.created_at
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/documents", response_model=List[DocumentResponse])
async def get_documents(
    current_user: User = Depends(require_active_user),
    db: Session = Depends(get_db)
):
    """Get user's uploaded documents."""
    documents = db.query(Document).filter(
        Document.user_id == current_user.id
    ).order_by(Document.created_at.desc()).all()
    
    return [
        DocumentResponse(
            id=doc.id,
            filename=doc.filename,
            original_filename=doc.original_filename,
            file_type=doc.file_type,
            upload_status=doc.upload_status,
            extracted_data=doc.extracted_data,
            total_chunks=len(doc.chunk_data) if doc.chunk_data else 0,
            created_at=doc.created_at
        )
        for doc in documents
    ]

@app.get("/api/documents/summary")
async def get_documents_summary(
    current_user: User = Depends(require_active_user),
    db: Session = Depends(get_db)
):
    """Get a summary of user's documents for display on upload page."""
    documents = db.query(Document).filter(
        Document.user_id == current_user.id,
        Document.upload_status == "processed"
    ).order_by(Document.created_at.desc()).all()
    
    if not documents:
        return {"has_documents": False, "documents": []}
    
    # Group documents by type
    documents_by_type = {}
    for doc in documents:
        doc_type = doc.file_type
        if doc_type not in documents_by_type:
            documents_by_type[doc_type] = []
        
        # Extract key info for display
        display_info = {
            "id": str(doc.id),
            "filename": doc.original_filename,  # Use human-readable filename
            "file_type": doc.file_type,
            "created_at": doc.created_at.isoformat(),
            "extracted_data": doc.extracted_data
        }
        documents_by_type[doc_type].append(display_info)
    
    return {
        "has_documents": True,
        "total_documents": len(documents),
        "documents_by_type": documents_by_type,
        "recent_documents": [
            {
                "id": str(doc.id),
                "filename": doc.original_filename,  # Use human-readable filename
                "file_type": doc.file_type,
                "created_at": doc.created_at.isoformat(),
                "extracted_data": doc.extracted_data
            }
            for doc in documents[:5]  # Show last 5 documents
        ]
    }

# =============== CHAT SYSTEM ===============

@app.post("/api/chat", response_model=ChatResponse)
async def chat(
    message: ChatMessage,
    current_user: User = Depends(require_active_user),
    db: Session = Depends(get_db)
):
    """Chat with the AI assistant."""
    try:
        # Debug: Log the session ID being used
        print(f"DEBUG: Chat request for user {current_user.email}")
        print(f"DEBUG: Session ID from frontend: {message.session_id}")
        
        # Check if session exists
        session = db.query(UserSession).filter(UserSession.id == message.session_id).first()
        if not session:
            print(f"DEBUG: Session {message.session_id} not found in database")
            # Get user's most recent session as fallback
            recent_session = db.query(UserSession).filter(
                UserSession.user_id == current_user.id,
                UserSession.is_active == True
            ).order_by(UserSession.created_at.desc()).first()
            
            if recent_session:
                print(f"DEBUG: Using fallback session: {recent_session.id}")
                message.session_id = recent_session.id
            else:
                print(f"DEBUG: No active sessions found for user")
                raise HTTPException(status_code=400, detail="No active session found")
        
        result = await agent_service.chat_with_agent(
            message.message, message.session_id, db
        )
        
        if result.get("success"):
            return ChatResponse(
                response=result["response"],
                agent_name=result["agent_name"],
                metadata=result.get("metadata", {}),
                timestamp=datetime.utcnow()
            )
        else:
            raise HTTPException(status_code=500, detail=result.get("error"))
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/chat/history/{session_id}", response_model=List[dict])
async def get_chat_history(
    session_id: str,
    current_user: User = Depends(require_active_user),
    db: Session = Depends(get_db)
):
    """Get chat history for a session."""
    messages = db.query(DBChatMessage).filter(
        DBChatMessage.session_id == session_id
    ).order_by(DBChatMessage.created_at.asc()).all()
    
    return [
        {
            "id": msg.id,
            "message_type": msg.message_type,
            "content": msg.content,
            "agent_name": msg.agent_name,
            "created_at": msg.created_at.isoformat()
        }
        for msg in messages
    ]


# =============== CLAIM FORM GENERATION ===============

@app.post("/api/claims/generate-form", response_model=ClaimFormPreview)
async def generate_claim_form(
    request: ClaimInitiate,
    current_user: User = Depends(require_active_user),
    db: Session = Depends(get_db)
):
    """Generate claim form based on uploaded documents."""
    try:
        result = await agent_service.generate_claim_form(request.session_id, db)
        
        if result.get("success"):
            return ClaimFormPreview(
                form_data=result["form_data"],
                preview_html=result["preview_html"],
                missing_fields=result["missing_fields"],
                pdf_path=result.get("pdf_path"),
                pdf_filename=result.get("pdf_filename")
            )
        else:
            raise HTTPException(status_code=500, detail=result.get("error"))
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/claims/file-claim", response_model=ClaimFormPreview)
async def file_claim(
    request: ClaimFilingRequest,
    current_user: User = Depends(require_active_user),
    db: Session = Depends(get_db)
):
    """File a claim - either with a vendor form or synthetic form."""
    try:
        if request.form_type == "vendor" and request.vendor_id:
            # Generate form using vendor template
            result = await agent_service.generate_vendor_claim_form(
                request.session_id, request.vendor_id, db
            )
        else:
            # Generate synthetic form
            result = await agent_service.generate_synthetic_claim_form(
                request.session_id, db
            )
        
        if result.get("success"):
            return ClaimFormPreview(
                form_data=result["form_data"],
                preview_html=result["preview_html"],
                missing_fields=result["missing_fields"],
                pdf_path=result.get("pdf_path"),
                pdf_filename=result.get("pdf_filename")
            )
        else:
            raise HTTPException(status_code=500, detail=result.get("error"))
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/claims/generate-synthetic", response_model=ClaimFormPreview)
async def generate_synthetic_claim_form(
    request: SyntheticFormRequest,
    current_user: User = Depends(require_active_user),
    db: Session = Depends(get_db)
):
    """Generate a synthetic claim form similar to popular vendor forms."""
    try:
        result = await agent_service.generate_synthetic_claim_form(
            request.session_id, db, request.template_url
        )
        
        if result.get("success"):
            return ClaimFormPreview(
                form_data=result["form_data"],
                preview_html=result["preview_html"],
                missing_fields=result["missing_fields"],
                pdf_path=result.get("pdf_path"),
                pdf_filename=result.get("pdf_filename")
            )
        else:
            raise HTTPException(status_code=500, detail=result.get("error"))
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/claims/generate-vendor", response_model=ClaimFormPreview)
async def generate_vendor_claim_form(
    request: VendorFormRequest,
    current_user: User = Depends(require_active_user),
    db: Session = Depends(get_db)
):
    """Generate claim form using a specific vendor template."""
    try:
        result = await agent_service.generate_vendor_claim_form(
            request.session_id, request.vendor_id, db
        )
        
        if result.get("success"):
            return ClaimFormPreview(
                form_data=result["form_data"],
                preview_html=result["preview_html"],
                missing_fields=result["missing_fields"],
                pdf_path=result.get("pdf_path"),
                pdf_filename=result.get("pdf_filename")
            )
        else:
            raise HTTPException(status_code=500, detail=result.get("error"))
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/claims/submit", response_model=SuccessResponse)
async def submit_claim(
    claim_data: ClaimSubmission,
    current_user: User = Depends(require_active_user),
    db: Session = Depends(get_db)
):
    """Submit approved claim form."""
    try:
        claim = db.query(Claim).filter(
            Claim.id == claim_data.claim_id,
            Claim.user_id == current_user.id
        ).first()
        
        if not claim:
            raise HTTPException(status_code=404, detail="Claim not found")
        
        # Update claim with approved data
        claim.form_data = claim_data.approved_data
        claim.status = "submitted"
        claim.submitted_at = datetime.utcnow()
        db.commit()
        
        return SuccessResponse(
            success=True,
            message="Claim submitted successfully",
            data={"claim_id": str(claim.id)}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# =============== VENDORS ===============

@app.get("/api/vendors", response_model=List[VendorResponse])
async def get_vendors(db: Session = Depends(get_db)):
    """Get list of available insurance vendors."""
    vendors = db.query(Vendor).filter(Vendor.is_active == True).all()
    
    return [
        VendorResponse(
            id=vendor.id,
            name=vendor.name,
            display_name=vendor.display_name,
            form_template_url=vendor.form_template_url,
            is_active=vendor.is_active
        )
        for vendor in vendors
    ]

# =============== WORKFLOW STATE ===============

@app.get("/api/workflow/{session_id}", response_model=WorkflowState)
async def get_workflow_state(
    session_id: str,
    current_user: User = Depends(require_active_user),
    db: Session = Depends(get_db)
):
    """Get current workflow state for a session."""
    workflow = db.query(WorkflowState).filter(
        WorkflowState.session_id == session_id
    ).order_by(WorkflowState.updated_at.desc()).first()
    
    if not workflow:
        # Create default workflow state
        workflow = WorkflowState(
            session_id=session_id,
            current_step="document_upload",
            step_data={},
            conversation_history=[],
            agent_context={}
        )
        db.add(workflow)
        db.commit()
    
    return WorkflowState(
        current_step=workflow.current_step,
        step_data=workflow.step_data,
        conversation_history=workflow.conversation_history
    )

@app.post("/api/workflow/{session_id}/update", response_model=SuccessResponse)
async def update_workflow_state(
    session_id: str,
    workflow_data: WorkflowState,
    current_user: User = Depends(require_active_user),
    db: Session = Depends(get_db)
):
    """Update workflow state for a session."""
    try:
        workflow = db.query(WorkflowState).filter(
            WorkflowState.session_id == session_id
        ).first()
        
        if workflow:
            workflow.current_step = workflow_data.current_step
            workflow.step_data = workflow_data.step_data
            workflow.conversation_history = workflow_data.conversation_history
            workflow.updated_at = datetime.utcnow()
        else:
            workflow = WorkflowState(
                session_id=session_id,
                current_step=workflow_data.current_step,
                step_data=workflow_data.step_data,
                conversation_history=workflow_data.conversation_history,
                agent_context={}
            )
            db.add(workflow)
        
        db.commit()
        
        return SuccessResponse(
            success=True,
            message="Workflow state updated successfully"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# =============== PDF DOWNLOAD ===============

@app.get("/api/claims/download-pdf/{pdf_filename}")
async def download_claim_pdf(
    pdf_filename: str,
    current_user: User = Depends(require_active_user)
):
    """Download generated claim form PDF."""
    try:
        pdf_path = os.path.join("uploads", "generated_forms", pdf_filename)
        
        if not os.path.exists(pdf_path):
            raise HTTPException(status_code=404, detail="PDF file not found")
        
        return FileResponse(
            path=pdf_path,
            filename=pdf_filename,
            media_type="application/pdf"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

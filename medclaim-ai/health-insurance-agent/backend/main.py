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
import asyncio

# Local imports
from backend.database import get_db, create_tables, User, UserSession, Document, Vendor, Claim, WorkflowState, ChatMessage
from backend.schemas import *
from backend.auth import (
    authenticate_user, create_access_token, get_current_user, require_active_user,
    get_password_hash, create_user_session, get_current_session, get_session_by_id
)
from backend.file_handler import file_handler
from backend.agent_service import agent_service

# Initialize FastAPI app
app = FastAPI(
    title="MediClaim AI API",
    description="Production-ready API for AI-powered insurance claim processing",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Agent service is imported as singleton from backend.agent_service

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
    create_tables()
    await seed_vendors()
    print("✅ MediClaim AI Backend started successfully!")
    print("📊 API Documentation: http://localhost:8080/docs")
    print("🔗 Health Check: http://localhost:8080/health")

async def seed_vendors():
    """Seed initial vendor data."""
    db = next(get_db())
    try:
        # Check if vendors already exist
        existing_vendors = db.query(Vendor).count()
        if existing_vendors > 0:
            return
        
        # Seed popular vendors
        vendors_data = [
            {"name": "HDFC ERGO", "display_name": "HDFC ERGO General Insurance", "form_template_path": "./claim_forms/hdfc_ergo.pdf"},
            {"name": "Star Health Insurance", "display_name": "Star Health & Allied Insurance", "form_template_path": "./claim_forms/star_health.pdf"},
            {"name": "ICICI Lombard", "display_name": "ICICI Lombard General Insurance", "form_template_path": "./claim_forms/icici_lombard.pdf"},
            {"name": "New India Assurance", "display_name": "The New India Assurance Company", "form_template_path": "./claim_forms/new_india_assurance.pdf"},
            {"name": "Max Bupa (Niva Bupa)", "display_name": "Niva Bupa Health Insurance", "form_template_path": "./claim_forms/max_bupa.pdf"}
        ]
        
        for vendor_data in vendors_data:
            vendor = Vendor(**vendor_data)
            db.add(vendor)
        
        db.commit()
    except Exception as e:
        print(f"Error seeding vendors: {e}")
    finally:
        db.close()

# Health check endpoint
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

# Authentication endpoints
@app.options("/auth/register")
async def options_register():
    """Handle CORS preflight for register endpoint."""
    return {"message": "OK"}

@app.options("/auth/login")
async def options_login():
    """Handle CORS preflight for login endpoint."""
    return {"message": "OK"}

@app.post("/auth/register", response_model=APIResponse)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """Register a new user."""
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create new user
    hashed_password = get_password_hash(user_data.password)
    user = User(
        email=user_data.email,
        hashed_password=hashed_password,
        full_name=user_data.full_name,
        phone=user_data.phone
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return APIResponse(
        success=True,
        message="User registered successfully",
        data={"user_id": user.id}
    )

@app.post("/auth/login", response_model=APIResponse)
async def login(user_credentials: UserLogin, db: Session = Depends(get_db)):
    """Authenticate user and return access token."""
    user = authenticate_user(db, user_credentials.email, user_credentials.password)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Incorrect email or password"
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": user.id}, expires_delta=access_token_expires
    )
    
    # Create user session
    session = create_user_session(db, user.id)
    
    return APIResponse(
        success=True,
        message="Login successful",
        data={
            "access_token": access_token,
            "token_type": "bearer",
            "session_id": session.id,
            "user": {
                "id": user.id,
                "email": user.email,
                "full_name": user.full_name
            }
        }
    )

# Document upload endpoints
@app.options("/upload-document")
async def options_upload():
    """Handle CORS preflight for upload endpoint."""
    return {"message": "OK"}

@app.post("/upload-document", response_model=FileUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    file_type: str = Form(...),
    session_id: str = Form(...),
    current_user: User = Depends(require_active_user),
    db: Session = Depends(get_db)
):
    """Upload and process document."""
    try:
        print(f"Upload request - File: {file.filename}, Type: {file_type}, Session: {session_id}, User: {current_user.id}")
        
        # Validate session
        session = get_session_by_id(session_id, db)
        
        # Save file
        file_info = await file_handler.save_file(file, file_type, current_user.id)
        
        # Create document record
        document = Document(
            user_id=current_user.id,
            filename=file_info["filename"],
            file_path=file_info["file_path"],
            file_type=file_type,
            mime_type=file_info["mime_type"],
            file_size=file_info["file_size"],
            upload_status="processing"
        )
        
        db.add(document)
        db.commit()
        db.refresh(document)
        
        # Process document with agent
        processing_result = await agent_service.process_document(
            file_info["file_path"], file_type, current_user.id, db
        )
        
        if processing_result["success"]:
            # Update document with extracted data
            document.extracted_data = json.dumps(processing_result["extracted_data"])
            document.upload_status = "processed"
        else:
            document.upload_status = "failed"
        
        db.commit()
        
        # Generate agent response about the processed document
        agent_response = None
        if processing_result["success"]:
            # Create a conversational response about what was extracted
            extracted_data = processing_result.get("extracted_data", {})
            
            if file_type == "policy":
                agent_response = await agent_service.generate_document_response(
                    "policy", extracted_data, session_id, db
                )
            elif file_type == "invoice":
                agent_response = await agent_service.generate_document_response(
                    "invoice", extracted_data, session_id, db
                )
        
        # Update workflow state
        await agent_service.update_workflow_state(
            session_id, 
            f"{file_type}_uploaded", 
            {
                "document_id": document.id, 
                "extracted_data": processing_result.get("extracted_data"),
                "agent_response": agent_response.get("response") if agent_response and agent_response.get("success") else None
            },
            db
        )
        
        return FileUploadResponse(
            success=processing_result["success"],
            document_id=document.id,
            message="Document uploaded and processed successfully" if processing_result["success"] else "Document uploaded but processing failed",
            extracted_data=processing_result.get("extracted_data"),
            agent_response=agent_response.get("response") if agent_response and agent_response.get("success") else None
        )
        
    except HTTPException as he:
        # Re-raise HTTP exceptions (like auth failures, validation errors)
        print(f"HTTP Exception during upload: {he.status_code} - {he.detail}")
        raise he
    except Exception as e:
        print(f"Unexpected error during upload: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

# Vendor endpoints
@app.get("/vendors", response_model=List[VendorResponse])
async def get_vendors(current_user: User = Depends(require_active_user), db: Session = Depends(get_db)):
    """Get list of available insurance vendors."""
    vendors = db.query(Vendor).filter(Vendor.is_active == True).all()
    return vendors

# Claim endpoints
@app.post("/claims", response_model=APIResponse)
async def create_claim(
    claim_data: ClaimCreate,
    current_user: User = Depends(require_active_user),
    db: Session = Depends(get_db)
):
    """Create a new insurance claim."""
    claim = Claim(
        user_id=current_user.id,
        vendor_id=claim_data.vendor_id,
        policy_document_id=claim_data.policy_document_id,
        claim_number=f"CLM-{str(uuid.uuid4())[:8].upper()}"
    )
    
    db.add(claim)
    db.commit()
    db.refresh(claim)
    
    return APIResponse(
        success=True,
        message="Claim created successfully",
        data={"claim_id": claim.id}
    )

@app.get("/claims/{claim_id}", response_model=ClaimResponse)
async def get_claim(
    claim_id: str,
    current_user: User = Depends(require_active_user),
    db: Session = Depends(get_db)
):
    """Get claim details."""
    claim = db.query(Claim).filter(
        Claim.id == claim_id,
        Claim.user_id == current_user.id
    ).first()
    
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")
    
    return claim

@app.put("/claims/{claim_id}", response_model=APIResponse)
async def update_claim(
    claim_id: str,
    claim_update: ClaimUpdate,
    current_user: User = Depends(require_active_user),
    db: Session = Depends(get_db)
):
    """Update claim details."""
    claim = db.query(Claim).filter(
        Claim.id == claim_id,
        Claim.user_id == current_user.id
    ).first()
    
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")
    
    # Update fields
    for field, value in claim_update.dict(exclude_unset=True).items():
        if hasattr(claim, field):
            if field in ["policy_data", "invoice_data", "coverage_analysis"] and value:
                setattr(claim, field, json.dumps(value))
            else:
                setattr(claim, field, value)
    
    db.commit()
    
    return APIResponse(
        success=True,
        message="Claim updated successfully"
    )

# Coverage analysis endpoint
@app.post("/calculate-coverage", response_model=CoverageAnalysisResponse)
async def calculate_coverage(
    policy_document_id: str = Form(...),
    invoice_document_id: str = Form(...),
    current_user: User = Depends(require_active_user),
    db: Session = Depends(get_db)
):
    """Calculate coverage based on policy and invoice documents."""
    # Get documents
    policy_doc = db.query(Document).filter(
        Document.id == policy_document_id,
        Document.user_id == current_user.id,
        Document.file_type == "policy"
    ).first()
    
    invoice_doc = db.query(Document).filter(
        Document.id == invoice_document_id,
        Document.user_id == current_user.id,
        Document.file_type == "invoice"
    ).first()
    
    if not policy_doc or not invoice_doc:
        raise HTTPException(status_code=404, detail="Required documents not found")
    
    # Get extracted data
    policy_data = json.loads(policy_doc.extracted_data) if policy_doc.extracted_data else {}
    invoice_data = json.loads(invoice_doc.extracted_data) if invoice_doc.extracted_data else {}
    
    # Calculate coverage
    coverage_result = await agent_service.calculate_coverage(policy_data, invoice_data)
    
    if not coverage_result["success"]:
        raise HTTPException(status_code=500, detail=coverage_result["error"])
    
    return coverage_result["coverage_analysis"]

# Form generation endpoint
@app.post("/file-claim", response_model=FormGenerationResponse)
async def file_claim(
    form_request: FormGenerationRequest,
    current_user: User = Depends(require_active_user),
    db: Session = Depends(get_db)
):
    """Generate and file insurance claim form."""
    # Get claim
    claim = db.query(Claim).filter(
        Claim.id == form_request.claim_id,
        Claim.user_id == current_user.id
    ).first()
    
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")
    
    # Get vendor
    vendor = db.query(Vendor).filter(Vendor.id == form_request.vendor_id).first()
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")
    
    # Prepare claim data
    claim_data = {
        "policy_data": json.loads(claim.policy_data) if claim.policy_data else {},
        "invoice_data": json.loads(claim.invoice_data) if claim.invoice_data else {},
        "coverage_analysis": json.loads(claim.coverage_analysis) if claim.coverage_analysis else {}
    }
    
    # Generate form
    form_result = await agent_service.generate_claim_form(
        claim.id, vendor.name, claim_data, db
    )
    
    if form_result["success"]:
        # Update claim
        claim.vendor_id = vendor.id
        claim.filled_form_path = form_result["form_path"]
        claim.form_status = "generated"
        claim.status = "submitted"
        db.commit()
        
        return FormGenerationResponse(
            success=True,
            form_id=claim.id,
            download_url=form_result["download_url"],
            message="Claim form generated successfully"
        )
    else:
        raise HTTPException(status_code=500, detail=form_result["error"])

# Form download endpoint
@app.get("/forms/{claim_id}/download")
async def download_form(
    claim_id: str,
    current_user: User = Depends(require_active_user),
    db: Session = Depends(get_db)
):
    """Download generated claim form."""
    claim = db.query(Claim).filter(
        Claim.id == claim_id,
        Claim.user_id == current_user.id
    ).first()
    
    if not claim or not claim.filled_form_path:
        raise HTTPException(status_code=404, detail="Form not found")
    
    if not os.path.exists(claim.filled_form_path):
        raise HTTPException(status_code=404, detail="Form file not found")
    
    return FileResponse(
        claim.filled_form_path,
        media_type="application/pdf",
        filename=f"claim_{claim.claim_number}.pdf"
    )

# Chat endpoint
@app.options("/chat")
async def options_chat():
    """Handle CORS preflight for chat endpoint."""
    return {"message": "OK"}

@app.post("/chat", response_model=APIResponse)
async def chat(
    message: ChatMessage,
    current_user: User = Depends(require_active_user),
    db: Session = Depends(get_db)
):
    """Process chat message with AI agent."""
    # Session validation is handled by require_active_user dependency
    
    # Process message with agent
    response = await agent_service.process_chat_message(
        message.message, message.session_id, db
    )
    
    return APIResponse(
        success=response["success"],
        message="Message processed",
        data={
            "response": response.get("response"),
            "metadata": response.get("metadata", {}),
            "next_step": response.get("next_step")
        }
    )

# Session management
@app.post("/sessions", response_model=APIResponse)
async def create_session(
    current_user: User = Depends(require_active_user),
    db: Session = Depends(get_db)
):
    """Create a new user session."""
    session = create_user_session(db, current_user.id)
    
    return APIResponse(
        success=True,
        message="Session created successfully",
        data={"session_id": session.id}
    )

@app.get("/sessions/{session_id}/state", response_model=WorkflowStateResponse)
async def get_session_state(
    session_id: str,
    current_user: User = Depends(require_active_user),
    db: Session = Depends(get_db)
):
    """Get current workflow state for session."""
    # Validate session belongs to user
    session = db.query(UserSession).filter(
        UserSession.id == session_id,
        UserSession.user_id == current_user.id
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Get workflow state
    workflow_state = db.query(WorkflowState).filter(
        WorkflowState.session_id == session_id
    ).order_by(WorkflowState.updated_at.desc()).first()
    
    if not workflow_state:
        # Create initial state
        workflow_state = WorkflowState(
            session_id=session_id,
            current_step="initial",
            step_data=json.dumps({}),
            conversation_history=json.dumps([]),
            agent_context=json.dumps({})
        )
        db.add(workflow_state)
        db.commit()
        db.refresh(workflow_state)
    
    # Parse JSON strings to proper objects for response validation
    try:
        step_data = json.loads(workflow_state.step_data) if workflow_state.step_data else {}
    except (json.JSONDecodeError, TypeError):
        step_data = {}
    
    try:
        conversation_history = json.loads(workflow_state.conversation_history) if workflow_state.conversation_history else []
    except (json.JSONDecodeError, TypeError):
        conversation_history = []
    
    try:
        agent_context = json.loads(workflow_state.agent_context) if workflow_state.agent_context else {}
    except (json.JSONDecodeError, TypeError):
        agent_context = {}
    
    # Return properly formatted response
    return WorkflowStateResponse(
        id=workflow_state.id,
        current_step=workflow_state.current_step,
        step_data=step_data,
        conversation_history=conversation_history,
        agent_context=agent_context,
        updated_at=workflow_state.updated_at
    )

# Background task for cleanup
@app.on_event("startup")
async def startup_cleanup():
    """Start background cleanup tasks."""
    import asyncio
    asyncio.create_task(periodic_cleanup())

async def periodic_cleanup():
    """Periodic cleanup of temporary files and expired sessions."""
    while True:
        try:
            # Cleanup temp files
            file_handler.cleanup_temp_files(24)
            
            # Cleanup expired sessions
            db = next(get_db())
            expired_sessions = db.query(UserSession).filter(
                UserSession.expires_at < datetime.utcnow()
            ).all()
            
            for session in expired_sessions:
                session.is_active = False
            
            db.commit()
            db.close()
            
        except Exception as e:
            print(f"Cleanup error: {e}")
        
        # Wait 1 hour before next cleanup
        await asyncio.sleep(3600)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080, reload=True)

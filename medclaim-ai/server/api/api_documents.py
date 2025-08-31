from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Form, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from database import get_db
from services import auth_service
from business_logic import document_service
from schemas import (
    DocumentResponse, DocumentUpdate, DocumentUploadResponse,
    ApiResponse, PaginatedResponse, DocumentType
)
import uuid

router = APIRouter(prefix="/documents", tags=["Documents"])

# ============================================================================
# DOCUMENT UPLOAD ENDPOINTS
# ============================================================================

@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    document_type: DocumentType = Form(...),
    claim_id: Optional[uuid.UUID] = Form(None),
    current_user = Depends(auth_service.get_current_user),
    db: Session = Depends(get_db)
):
    """Upload and process a medical document"""
    try:
        # Validate file
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file provided")
            
        # Process document upload
        document_data = await document_service.upload_and_process_document(
            db=db,
            file=file,
            user_id=current_user.id,
            claim_id=claim_id,
            document_type=document_type
        )
        
        return DocumentUploadResponse(**document_data)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@router.post("/upload/bulk", response_model=List[DocumentUploadResponse])
async def upload_multiple_documents(
    files: List[UploadFile] = File(...),
    document_types: List[DocumentType] = Form(...),
    claim_id: Optional[uuid.UUID] = Form(None),
    current_user = Depends(auth_service.get_current_user),
    db: Session = Depends(get_db)
):
    """Upload multiple documents at once"""
    try:
        if len(files) != len(document_types):
            raise HTTPException(
                status_code=400, 
                detail="Number of files must match number of document types"
            )
            
        if len(files) > 10:  # Limit bulk uploads
            raise HTTPException(status_code=400, detail="Maximum 10 files per upload")
            
        results = []
        for file, doc_type in zip(files, document_types):
            try:
                document_data = await document_service.upload_and_process_document(
                    db=db,
                    file=file,
                    user_id=current_user.id,
                    claim_id=claim_id,
                    document_type=doc_type
                )
                results.append(DocumentUploadResponse(**document_data))
            except Exception as e:
                # Continue with other files if one fails
                results.append({
                    "document_id": None,
                    "filename": file.filename,
                    "extracted_data": {},
                    "message": f"Upload failed: {str(e)}"
                })
                
        return results
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# DOCUMENT MANAGEMENT ENDPOINTS
# ============================================================================

@router.get("/", response_model=PaginatedResponse)
async def get_documents(
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100),
    document_type: Optional[DocumentType] = None,
    claim_id: Optional[uuid.UUID] = None,
    is_processed: Optional[bool] = None,
    is_verified: Optional[bool] = None,
    current_user = Depends(auth_service.get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's documents with filtering"""
    try:
        user_id = current_user.id if current_user.role != "admin" else None
        
        documents, total = await document_service.get_documents(
            db=db,
            user_id=user_id,
            page=page,
            size=size,
            document_type=document_type,
            claim_id=claim_id,
            is_processed=is_processed,
            is_verified=is_verified
        )
        
        return PaginatedResponse(
            items=[DocumentResponse.from_orm(doc) for doc in documents],
            total=total,
            page=page,
            size=size,
            pages=(total + size - 1) // size
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document_by_id(
    document_id: uuid.UUID,
    current_user = Depends(auth_service.get_current_user),
    db: Session = Depends(get_db)
):
    """Get document by ID"""
    try:
        document = await document_service.get_document_by_id(db, document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
            
        # Check permissions
        if current_user.role != "admin" and document.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")
            
        return DocumentResponse.from_orm(document)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/{document_id}", response_model=ApiResponse)
async def update_document(
    document_id: uuid.UUID,
    document_update: DocumentUpdate,
    current_user = Depends(auth_service.get_current_user),
    db: Session = Depends(get_db)
):
    """Update document metadata"""
    try:
        document = await document_service.get_document_by_id(db, document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
            
        # Check permissions
        if current_user.role != "admin" and document.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")
            
        updated_document = await document_service.update_document(db, document_id, document_update)
        return ApiResponse(
            success=True,
            message="Document updated successfully",
            data=DocumentResponse.from_orm(updated_document)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{document_id}", response_model=ApiResponse)
async def delete_document(
    document_id: uuid.UUID,
    current_user = Depends(auth_service.get_current_user),
    db: Session = Depends(get_db)
):
    """Delete document"""
    try:
        document = await document_service.get_document_by_id(db, document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
            
        # Check permissions
        if current_user.role != "admin" and document.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")
            
        success = await document_service.delete_document(db, document_id)
        if success:
            return ApiResponse(
                success=True,
                message="Document deleted successfully"
            )
        else:
            raise HTTPException(status_code=500, detail="Failed to delete document")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# ============================================================================
# DOCUMENT PROCESSING ENDPOINTS
# ============================================================================

@router.post("/{document_id}/reprocess", response_model=ApiResponse)
async def reprocess_document(
    document_id: uuid.UUID,
    current_user = Depends(auth_service.get_current_user),
    db: Session = Depends(get_db)
):
    """Reprocess document with AI extraction"""
    try:
        document = await document_service.get_document_by_id(db, document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
            
        # Check permissions
        if current_user.role != "admin" and document.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")
            
        reprocessed_document = await document_service.reprocess_document(db, document_id)
        return ApiResponse(
            success=True,
            message="Document reprocessed successfully",
            data=DocumentResponse.from_orm(reprocessed_document)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{document_id}/verify", response_model=ApiResponse)
async def verify_document(
    document_id: uuid.UUID,
    current_user = Depends(auth_service.require_agent_or_admin),
    db: Session = Depends(get_db)
):
    """Verify document extraction (agent/admin only)"""
    try:
        verified_document = await document_service.verify_document(db, document_id, current_user.id)
        if not verified_document:
            raise HTTPException(status_code=404, detail="Document not found")
            
        return ApiResponse(
            success=True,
            message="Document verified successfully",
            data=DocumentResponse.from_orm(verified_document)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{document_id}/download")
async def download_document(
    document_id: uuid.UUID,
    current_user = Depends(auth_service.get_current_user),
    db: Session = Depends(get_db)
):
    """Download original document file"""
    try:
        document = await document_service.get_document_by_id(db, document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
            
        # Check permissions
        if current_user.role != "admin" and document.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")
            
        file_response = await document_service.get_document_file(document)
        return file_response
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# ============================================================================
# DOCUMENT ANALYSIS ENDPOINTS
# ============================================================================

@router.get("/{document_id}/analysis", response_model=dict)
async def get_document_analysis(
    document_id: uuid.UUID,
    current_user = Depends(auth_service.get_current_user),
    db: Session = Depends(get_db)
):
    """Get detailed document analysis and extracted data"""
    try:
        document = await document_service.get_document_by_id(db, document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
            
        # Check permissions
        if current_user.role != "admin" and document.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")
            
        analysis = await document_service.get_document_analysis(db, document_id)
        return analysis
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
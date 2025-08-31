from pydantic import Field
from typing import Optional, Dict, Any
from datetime import datetime
import uuid
from server.schemas.base_schema import BaseSchema, DocumentType

# ============================================================================
# DOCUMENT SCHEMAS
# ============================================================================

class DocumentBase(BaseSchema):
    filename: str = Field(..., min_length=1, max_length=255)
    original_filename: str = Field(..., min_length=1, max_length=255)
    file_size: Optional[int] = Field(None, ge=0)
    mime_type: Optional[str] = Field(None, max_length=100)
    document_type: DocumentType
    upload_source: str = Field(default="web", max_length=50)

class DocumentCreate(DocumentBase):
    user_id: uuid.UUID
    claim_id: Optional[uuid.UUID] = None
    file_path: str = Field(..., max_length=500)
    extracted_data: Optional[Dict[str, Any]] = {}
    extraction_confidence: float = Field(default=0.0, ge=0, le=1.0)

class DocumentUpdate(BaseSchema):
    filename: Optional[str] = Field(None, min_length=1, max_length=255)
    document_type: Optional[DocumentType] = None
    extracted_data: Optional[Dict[str, Any]] = None
    extraction_confidence: Optional[float] = Field(None, ge=0, le=1.0)
    is_processed: Optional[bool] = None
    is_verified: Optional[bool] = None

class DocumentResponse(DocumentBase):
    id: uuid.UUID
    user_id: uuid.UUID
    claim_id: Optional[uuid.UUID] = None
    file_path: str
    extracted_data: Optional[Dict[str, Any]] = {}
    extraction_confidence: float
    is_processed: bool
    is_verified: bool
    created_at: datetime

class DocumentUploadResponse(BaseSchema):
    document_id: uuid.UUID
    filename: str
    extracted_data: Dict[str, Any]
    message: str

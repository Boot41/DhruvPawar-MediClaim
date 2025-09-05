"""
Pydantic schemas for API request/response validation
"""
from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime

# =============== AUTH SCHEMAS ===============

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: str
    email: str
    full_name: Optional[str]
    is_active: bool
    created_at: datetime

class Token(BaseModel):
    access_token: str
    token_type: str

# =============== DOCUMENT SCHEMAS ===============

class DocumentUpload(BaseModel):
    file_type: str  # 'policy', 'invoice', 'medical_record'
    session_id: str

class DocumentChunk(BaseModel):
    chunk_id: str
    document_id: str
    chunk_index: int
    content: str
    metadata: Dict[str, Any]
    chunk_type: Optional[str] = None

class DocumentResponse(BaseModel):
    id: str
    filename: str
    file_type: str
    upload_status: str
    extracted_data: Optional[Dict[str, Any]]
    total_chunks: Optional[int]
    created_at: datetime

class DocumentChunkResponse(BaseModel):
    chunks: List[DocumentChunk]
    total_chunks: int
    chunk_summary: Dict[str, Any]

# =============== CHAT SCHEMAS ===============

class ChatMessage(BaseModel):
    message: str
    session_id: str

class ChatResponse(BaseModel):
    response: str
    agent_name: str
    metadata: Optional[Dict[str, Any]]
    timestamp: datetime

# =============== CLAIM SCHEMAS ===============

class ClaimInitiate(BaseModel):
    session_id: str

class ClaimStatus(BaseModel):
    claim_id: str
    status: str
    created_at: datetime
    claim_data: Optional[Dict[str, Any]]

class ClaimFormPreview(BaseModel):
    form_data: Dict[str, Any]
    preview_html: str
    missing_fields: List[str]
    pdf_path: Optional[str] = None
    pdf_filename: Optional[str] = None

class ClaimSubmission(BaseModel):
    claim_id: str
    approved_data: Dict[str, Any]

class ClaimFilingRequest(BaseModel):
    session_id: str
    vendor_id: Optional[str] = None  # If None, generate synthetic form
    form_type: str = "synthetic"  # "vendor" or "synthetic"

class SyntheticFormRequest(BaseModel):
    session_id: str
    template_url: Optional[str] = None  # Reference URL for form structure

class VendorFormRequest(BaseModel):
    session_id: str
    vendor_id: str

# =============== VENDOR SCHEMAS ===============

class VendorResponse(BaseModel):
    id: str
    name: str
    display_name: str
    form_template_url: Optional[str]
    is_active: bool

# =============== WORKFLOW SCHEMAS ===============

class WorkflowState(BaseModel):
    current_step: str
    step_data: Optional[Dict[str, Any]]
    conversation_history: Optional[List[Dict[str, Any]]]

# =============== COVERAGE SCHEMAS ===============

class CoverageAnalysis(BaseModel):
    total_cost: float
    deductible_applied: float
    insurance_covers: float
    out_of_pocket: float
    coverage_percentage: float

class CoverageRequest(BaseModel):
    session_id: str
    policy_data: Optional[Dict[str, Any]]
    invoice_data: Optional[Dict[str, Any]]

# =============== RESPONSE SCHEMAS ===============

class SuccessResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None

class ErrorResponse(BaseModel):
    success: bool
    error: str
    details: Optional[Dict[str, Any]] = None

# =============== HEALTH CHECK ===============

class HealthCheck(BaseModel):
    status: str
    timestamp: datetime
    version: str
    database: str
    agents: str

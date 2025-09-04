from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional, List, Dict, Any, Generic, TypeVar
from datetime import datetime
from enum import Enum

# ----------------------
# Enums
# ----------------------
class DocumentType(str, Enum):
    POLICY = "policy"
    INVOICE = "invoice"
    CLAIM_FORM = "claim_form"
    PRESCRIPTION = "prescription"
    DISCHARGE_SUMMARY = "discharge_summary"


class ClaimStatus(str, Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    PROCESSING = "processing"
    APPROVED = "approved"
    REJECTED = "rejected"


class WorkflowStep(str, Enum):
    POLICY_UPLOAD = "policy_upload"
    DOCUMENT_ANALYSIS = "document_analysis"
    INVOICE_UPLOAD = "invoice_upload"
    COVERAGE_ANALYSIS = "coverage_analysis"
    VENDOR_SELECTION = "vendor_selection"
    FORM_GENERATION = "form_generation"
    FORM_DOWNLOAD = "form_download"
    COMPLETED = "completed"


# ----------------------
# User Schemas
# ----------------------
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    phone: Optional[str] = None

    @field_validator("password")
    def validate_password_length(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        return v


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    phone: Optional[str]
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# ----------------------
# Session Schemas
# ----------------------
class SessionCreate(BaseModel):
    user_id: str


class SessionResponse(BaseModel):
    id: str
    user_id: str
    session_token: str
    expires_at: datetime
    is_active: bool

    model_config = {"from_attributes": True}


# ----------------------
# Document Schemas
# ----------------------
class DocumentUpload(BaseModel):
    file_type: DocumentType
    filename: str


class DocumentResponse(BaseModel):
    id: str
    filename: str
    file_type: str
    mime_type: str
    file_size: int
    upload_status: str
    extracted_data: Optional[Dict[str, Any]] = None
    created_at: datetime

    model_config = {"from_attributes": True}


# ----------------------
# Vendor Schemas
# ----------------------
class VendorResponse(BaseModel):
    id: str
    name: str
    display_name: str
    logo_url: Optional[str]
    is_active: bool

    model_config = {"from_attributes": True}


# ----------------------
# Claim Schemas
# ----------------------
class ClaimCreate(BaseModel):
    vendor_id: Optional[str] = None
    policy_document_id: Optional[str] = None


class ClaimUpdate(BaseModel):
    vendor_id: Optional[str] = None
    total_amount: Optional[float] = None
    covered_amount: Optional[float] = None
    out_of_pocket_amount: Optional[float] = None
    policy_data: Optional[Dict[str, Any]] = None
    invoice_data: Optional[Dict[str, Any]] = None
    coverage_analysis: Optional[Dict[str, Any]] = None


class ClaimResponse(BaseModel):
    id: str
    claim_number: Optional[str]
    status: str
    total_amount: Optional[float]
    covered_amount: Optional[float]
    out_of_pocket_amount: Optional[float]
    deductible_applied: Optional[float]
    policy_data: Optional[Dict[str, Any]] = None
    invoice_data: Optional[Dict[str, Any]] = None
    coverage_analysis: Optional[Dict[str, Any]] = None
    form_status: str
    created_at: datetime
    vendor: Optional[VendorResponse] = None

    model_config = {"from_attributes": True}


# ----------------------
# Chat Schemas
# ----------------------
class ChatMessage(BaseModel):
    message: str
    session_id: str


class ChatResponse(BaseModel):
    id: str
    message_type: str
    content: str
    metadata: Optional[Dict[str, Any]] = None
    created_at: datetime

    model_config = {"from_attributes": True}


# ----------------------
# Workflow Schemas
# ----------------------
class WorkflowStateUpdate(BaseModel):
    current_step: WorkflowStep
    step_data: Optional[Dict[str, Any]] = None
    agent_context: Optional[Dict[str, Any]] = None


class WorkflowStateResponse(BaseModel):
    id: str
    current_step: str
    step_data: Optional[Dict[str, Any]] = None
    conversation_history: Optional[List[Dict[str, Any]]] = None
    agent_context: Optional[Dict[str, Any]] = None
    updated_at: datetime

    model_config = {"from_attributes": True}


# ----------------------
# File Upload Schemas
# ----------------------
class FileUploadResponse(BaseModel):
    success: bool
    document_id: Optional[str] = None
    message: str
    extracted_data: Optional[Dict[str, Any]] = None
    agent_response: Optional[str] = None


# ----------------------
# Coverage Analysis Schemas
# ----------------------
class CoverageAnalysisResponse(BaseModel):
    total_cost: float
    insurance_covers: float
    out_of_pocket: float
    deductible_applied: float
    eligible_services: List[str]
    coverage_percentage: float
    policy_details: Dict[str, Any]
    invoice_details: Dict[str, Any]


# ----------------------
# Form Generation Schemas
# ----------------------
class FormGenerationRequest(BaseModel):
    claim_id: str
    vendor_id: str


class FormGenerationResponse(BaseModel):
    success: bool
    form_id: Optional[str] = None
    download_url: Optional[str] = None
    message: str


# ----------------------
# API Response Schemas
# ----------------------
class APIResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Any] = None
    error: Optional[str] = None


T = TypeVar("T")

class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    size: int
    pages: int


# ----------------------
# Health Check Schema
# ----------------------
class HealthCheck(BaseModel):
    status: str
    timestamp: datetime
    version: str
    database: str
    agents: str

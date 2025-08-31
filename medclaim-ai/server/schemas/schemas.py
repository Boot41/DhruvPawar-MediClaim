from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from enum import Enum
import uuid

# ============================================================================
# ENUMS
# ============================================================================

class UserRole(str, Enum):
    ADMIN = "admin"
    AGENT = "agent"
    CUSTOMER = "customer"

class DocumentType(str, Enum):
    MEDICAL_BILL = "medical_bill"
    PRESCRIPTION = "prescription"
    LAB_REPORT = "lab_report"
    DISCHARGE_SUMMARY = "discharge_summary"
    INSURANCE_CARD = "insurance_card"
    ID_DOCUMENT = "id_document"
    OTHER = "other"

class ClaimStatus(str, Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    DENIED = "denied"
    PAID = "paid"
    APPEALED = "appealed"
    CLOSED = "closed"

class PaymentStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"

# ============================================================================
# BASE SCHEMAS
# ============================================================================

class BaseSchema(BaseModel):
    class Config:
        from_attributes = True
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            date: lambda v: v.isoformat(),
        }

# ============================================================================
# USER SCHEMAS
# ============================================================================

class UserBase(BaseSchema):
    email: EmailStr
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    phone: Optional[str] = Field(None, regex=r'^\+?[1-9]\d{1,14}$')
    date_of_birth: Optional[date] = None
    address: Optional[str] = None
    role: UserRole = UserRole.CUSTOMER

class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=128)

class UserUpdate(BaseSchema):
    email: Optional[EmailStr] = None
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    phone: Optional[str] = Field(None, regex=r'^\+?[1-9]\d{1,14}$')
    date_of_birth: Optional[date] = None
    address: Optional[str] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None

class UserResponse(UserBase):
    id: uuid.UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime

class UserLogin(BaseSchema):
    email: EmailStr
    password: str

class UserProfile(UserResponse):
    pass

# ============================================================================
# INSURANCE PROVIDER SCHEMAS
# ============================================================================

class InsuranceProviderBase(BaseSchema):
    name: str = Field(..., min_length=1, max_length=200)
    code: str = Field(..., min_length=1, max_length=50)
    contact_email: Optional[EmailStr] = None
    contact_phone: Optional[str] = None
    address: Optional[str] = None
    api_endpoint: Optional[str] = None

class InsuranceProviderCreate(InsuranceProviderBase):
    pass

class InsuranceProviderUpdate(BaseSchema):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    code: Optional[str] = Field(None, min_length=1, max_length=50)
    contact_email: Optional[EmailStr] = None
    contact_phone: Optional[str] = None
    address: Optional[str] = None
    api_endpoint: Optional[str] = None
    is_active: Optional[bool] = None

class InsuranceProviderResponse(InsuranceProviderBase):
    id: uuid.UUID
    is_active: bool
    created_at: datetime

# ============================================================================
# INSURANCE POLICY SCHEMAS
# ============================================================================

class InsurancePolicyBase(BaseSchema):
    policy_number: str = Field(..., min_length=1, max_length=100)
    group_number: Optional[str] = Field(None, max_length=100)
    policy_type: Optional[str] = Field(None, max_length=100)
    coverage_start_date: date
    coverage_end_date: Optional[date] = None
    annual_deductible: float = Field(default=0.0, ge=0)
    annual_out_of_pocket_max: Optional[float] = Field(None, ge=0)
    copay_amount: float = Field(default=0.0, ge=0)
    coverage_percentage: float = Field(default=0.8, ge=0, le=1.0)
    policy_details: Optional[Dict[str, Any]] = {}

class InsurancePolicyCreate(InsurancePolicyBase):
    user_id: uuid.UUID
    provider_id: uuid.UUID

class InsurancePolicyUpdate(BaseSchema):
    policy_number: Optional[str] = Field(None, min_length=1, max_length=100)
    group_number: Optional[str] = Field(None, max_length=100)
    policy_type: Optional[str] = Field(None, max_length=100)
    coverage_start_date: Optional[date] = None
    coverage_end_date: Optional[date] = None
    annual_deductible: Optional[float] = Field(None, ge=0)
    annual_out_of_pocket_max: Optional[float] = Field(None, ge=0)
    copay_amount: Optional[float] = Field(None, ge=0)
    coverage_percentage: Optional[float] = Field(None, ge=0, le=1.0)
    policy_details: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None

class InsurancePolicyResponse(InsurancePolicyBase):
    id: uuid.UUID
    user_id: uuid.UUID
    provider_id: uuid.UUID
    is_active: bool
    created_at: datetime
    
    # Related data
    user: Optional[UserResponse] = None
    provider: Optional[InsuranceProviderResponse] = None

# ============================================================================
# HEALTHCARE PROVIDER SCHEMAS
# ============================================================================

class HealthcareProviderBase(BaseSchema):
    name: str = Field(..., min_length=1, max_length=200)
    npi_number: Optional[str] = Field(None, max_length=10)
    specialty: Optional[str] = Field(None, max_length=100)
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    tax_id: Optional[str] = Field(None, max_length=20)

class HealthcareProviderCreate(HealthcareProviderBase):
    pass

class HealthcareProviderUpdate(BaseSchema):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    npi_number: Optional[str] = Field(None, max_length=10)
    specialty: Optional[str] = Field(None, max_length=100)
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    tax_id: Optional[str] = Field(None, max_length=20)
    is_active: Optional[bool] = None

class HealthcareProviderResponse(HealthcareProviderBase):
    id: uuid.UUID
    is_active: bool
    created_at: datetime

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

# ============================================================================
# MEDICAL SERVICE SCHEMAS
# ============================================================================

class MedicalServiceBase(BaseSchema):
    service_code: str = Field(..., min_length=1, max_length=20)
    service_description: Optional[str] = None
    service_date: date
    quantity: int = Field(default=1, ge=1)
    unit_price: float = Field(..., ge=0)
    total_charge: float = Field(..., ge=0)

class MedicalServiceCreate(MedicalServiceBase):
    claim_id: uuid.UUID
    provider_id: Optional[uuid.UUID] = None

class MedicalServiceUpdate(BaseSchema):
    service_code: Optional[str] = Field(None, min_length=1, max_length=20)
    service_description: Optional[str] = None
    service_date: Optional[date] = None
    quantity: Optional[int] = Field(None, ge=1)
    unit_price: Optional[float] = Field(None, ge=0)
    total_charge: Optional[float] = Field(None, ge=0)
    allowed_amount: Optional[float] = Field(None, ge=0)
    paid_amount: Optional[float] = Field(None, ge=0)
    denial_reason: Optional[str] = None

class MedicalServiceResponse(MedicalServiceBase):
    id: uuid.UUID
    claim_id: uuid.UUID
    provider_id: Optional[uuid.UUID] = None
    allowed_amount: Optional[float] = None
    paid_amount: Optional[float] = None
    denial_reason: Optional[str] = None
    created_at: datetime
    
    # Related data
    provider: Optional[HealthcareProviderResponse] = None

# ============================================================================
# CLAIM SCHEMAS
# ============================================================================

class ClaimBase(BaseSchema):
    claim_type: Optional[str] = Field(None, max_length=50)
    diagnosis_code: Optional[str] = Field(None, max_length=20)
    diagnosis_description: Optional[str] = None
    date_of_service_start: Optional[date] = None
    date_of_service_end: Optional[date] = None

class ClaimCreate(ClaimBase):
    user_id: uuid.UUID
    policy_id: uuid.UUID
    healthcare_provider_id: Optional[uuid.UUID] = None

class ClaimUpdate(BaseSchema):
    status: Optional[ClaimStatus] = None
    claim_type: Optional[str] = Field(None, max_length=50)
    diagnosis_code: Optional[str] = Field(None, max_length=20)
    diagnosis_description: Optional[str] = None
    date_of_service_start: Optional[date] = None
    date_of_service_end: Optional[date] = None
    total_billed_amount: Optional[float] = Field(None, ge=0)
    total_allowed_amount: Optional[float] = Field(None, ge=0)
    insurance_paid_amount: Optional[float] = Field(None, ge=0)
    patient_responsibility: Optional[float] = Field(None, ge=0)
    deductible_applied: Optional[float] = Field(None, ge=0)
    copay_applied: Optional[float] = Field(None, ge=0)
    coinsurance_applied: Optional[float] = Field(None, ge=0)
    denial_reason: Optional[str] = None
    notes: Optional[str] = None

class ClaimResponse(ClaimBase):
    id: uuid.UUID
    claim_number: str
    user_id: uuid.UUID
    policy_id: uuid.UUID
    healthcare_provider_id: Optional[uuid.UUID] = None
    status: ClaimStatus
    submission_date: Optional[datetime] = None
    decision_date: Optional[datetime] = None
    total_billed_amount: float
    total_allowed_amount: float
    insurance_paid_amount: float
    patient_responsibility: float
    deductible_applied: float
    copay_applied: float
    coinsurance_applied: float
    processed_by: Optional[str] = None
    denial_reason: Optional[str] = None
    notes: Optional[str] = None
    external_claim_id: Optional[str] = None
    ai_estimated_coverage: Optional[float] = None
    ai_estimated_patient_cost: Optional[float] = None
    ai_confidence_score: Optional[float] = None
    created_at: datetime
    updated_at: datetime
    
    # Related data
    user: Optional[UserResponse] = None
    policy: Optional[InsurancePolicyResponse] = None
    healthcare_provider: Optional[HealthcareProviderResponse] = None
    documents: Optional[List[DocumentResponse]] = []
    services: Optional[List[MedicalServiceResponse]] = []

# ============================================================================
# PAYMENT SCHEMAS
# ============================================================================

class PaymentBase(BaseSchema):
    payment_type: str = Field(..., max_length=50)
    amount: float = Field(..., ge=0)
    payment_date: Optional[date] = None
    payment_method: Optional[str] = Field(None, max_length=50)
    reference_number: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = None

class PaymentCreate(PaymentBase):
    claim_id: uuid.UUID

class PaymentUpdate(BaseSchema):
    payment_type: Optional[str] = Field(None, max_length=50)
    amount: Optional[float] = Field(None, ge=0)
    payment_date: Optional[date] = None
    payment_method: Optional[str] = Field(None, max_length=50)
    reference_number: Optional[str] = Field(None, max_length=100)
    status: Optional[PaymentStatus] = None
    notes: Optional[str] = None

class PaymentResponse(PaymentBase):
    id: uuid.UUID
    claim_id: uuid.UUID
    status: PaymentStatus
    created_at: datetime

# ============================================================================
# CONVERSATION SCHEMAS
# ============================================================================

class ConversationMessageBase(BaseSchema):
    session_id: Optional[str] = Field(None, max_length=100)
    role: str = Field(..., max_length=20)
    message_type: str = Field(default="text", max_length=50)
    content: str = Field(..., min_length=1)
    metadata: Optional[Dict[str, Any]] = {}

class ConversationMessageCreate(ConversationMessageBase):
    user_id: uuid.UUID
    claim_id: Optional[uuid.UUID] = None
    parent_message_id: Optional[uuid.UUID] = None

class ConversationMessageResponse(ConversationMessageBase):
    id: uuid.UUID
    user_id: uuid.UUID
    claim_id: Optional[uuid.UUID] = None
    parent_message_id: Optional[uuid.UUID] = None
    is_flagged: bool
    created_at: datetime

class ChatMessage(BaseSchema):
    message: str = Field(..., min_length=1)
    user_id: Optional[str] = "default"
    claim_id: Optional[uuid.UUID] = None
    context: Optional[Dict[str, Any]] = {}

class ChatResponse(BaseSchema):
    response: str
    extracted_data: Optional[Dict[str, Any]] = {}
    claim_estimation: Optional[Dict[str, Any]] = {}
    conversation_id: Optional[uuid.UUID] = None

# ============================================================================
# CLAIM ESTIMATION SCHEMAS
# ============================================================================

class ClaimEstimateRequest(BaseSchema):
    user_id: Optional[str] = "default"
    claim_id: Optional[uuid.UUID] = None
    policy_id: Optional[uuid.UUID] = None

class ClaimEstimateResponse(BaseSchema):
    total_amount: float = 0.0
    covered_amount: float = 0.0
    deductible: float = 0.0
    copay: float = 0.0
    patient_responsibility: float = 0.0
    coverage_percentage: float = 0.0
    services_count: int = 0
    confidence_score: Optional[float] = None
    breakdown: Optional[Dict[str, Any]] = {}

# ============================================================================
# PROCESSING JOB SCHEMAS
# ============================================================================

class ProcessingJobBase(BaseSchema):
    job_type: str = Field(..., max_length=50)
    entity_id: Optional[uuid.UUID] = None
    entity_type: Optional[str] = Field(None, max_length=50)
    input_data: Optional[Dict[str, Any]] = {}

class ProcessingJobCreate(ProcessingJobBase):
    pass

class ProcessingJobUpdate(BaseSchema):
    status: Optional[str] = Field(None, max_length=20)
    output_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

class ProcessingJobResponse(ProcessingJobBase):
    id: uuid.UUID
    status: str
    output_data: Optional[Dict[str, Any]] = {}
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime

# ============================================================================
# RESPONSE WRAPPERS
# ============================================================================

class PaginatedResponse(BaseSchema):
    items: List[Any]
    total: int
    page: int = 1
    size: int = 50
    pages: int

class ApiResponse(BaseSchema):
    success: bool
    message: str
    data: Optional[Any] = None
    errors: Optional[List[str]] = None

class HealthCheckResponse(BaseSchema):
    status: str = "healthy"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    version: str = "1.0.0"
    database: bool = True
    gemini_api: bool = True
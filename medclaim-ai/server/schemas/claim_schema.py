from pydantic import Field
from typing import Optional, List
from datetime import datetime, date
import uuid
from server.schemas.base_schema import BaseSchema, ClaimStatus
from server.schemas.user_schema import UserResponse
from server.schemas.insurance_schema import InsurancePolicyResponse
from server.schemas.healthcare_schema import HealthcareProviderResponse
from server.schemas.document_schema import DocumentResponse

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
    breakdown: Optional[dict] = {}

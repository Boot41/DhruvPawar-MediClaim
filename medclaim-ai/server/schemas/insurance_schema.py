from pydantic import EmailStr, Field
from typing import Optional, Dict, Any
from datetime import datetime, date
import uuid
from server.schemas.base_schema import BaseSchema
from server.schemas.user_schema import UserResponse

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

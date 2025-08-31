from pydantic import EmailStr, Field
from typing import Optional
from datetime import datetime
import uuid
from server.schemas.base_schema import BaseSchema

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

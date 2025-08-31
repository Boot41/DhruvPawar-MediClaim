from pydantic import Field
from typing import Optional
from datetime import datetime, date
import uuid
from server.schemas.base_schema import BaseSchema, PaymentStatus

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

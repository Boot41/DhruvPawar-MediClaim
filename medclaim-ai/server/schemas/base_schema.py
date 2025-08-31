from pydantic import BaseModel, Field
from typing import Optional, List, Any
from datetime import datetime, date
from enum import Enum
import uuid

# ============================================================================
# ENUMS
# ============================================================================

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
# BASE SCHEMA
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

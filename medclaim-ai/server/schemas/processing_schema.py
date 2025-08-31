from pydantic import Field
from typing import Optional, Dict, Any
from datetime import datetime
import uuid
from server.schemas.base_schema import BaseSchema

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

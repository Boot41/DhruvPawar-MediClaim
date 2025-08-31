from pydantic import Field
from typing import Optional, Dict, Any
from datetime import datetime
import uuid
from server.schemas.base_schema import BaseSchema

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

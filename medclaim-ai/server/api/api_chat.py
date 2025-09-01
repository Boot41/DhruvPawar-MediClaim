from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import Field
from sqlalchemy.orm import Session
from typing import List, Optional
from server.config.database import get_db
from server.services import auth_service
from server.business_logic import chat_service
from server.schemas.conversation_schema import (
    ChatMessage, ChatResponse, ConversationMessageResponse
)
from server.schemas.base_schema import ApiResponse, PaginatedResponse
import uuid

router = APIRouter(prefix="", tags=["AI Chat Assistant"])

# ============================================================================
# CHAT ENDPOINTS
# ============================================================================

@router.post("/", response_model=ChatResponse)
async def chat_with_assistant(
    message: ChatMessage,
    current_user = Depends(auth_service.get_current_user),
    db: Session = Depends(get_db)
):
    """Chat with AI assistant about insurance claims"""
    try:
        # Set user ID from authenticated user
        message.user_id = str(current_user.id)
        
        response = await chat_service.process_chat_message(db, message, current_user)
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat processing failed: {str(e)}")

@router.post("/session", response_model=ApiResponse)
async def start_chat_session(
    claim_id: Optional[uuid.UUID] = None,
    current_user = Depends(auth_service.get_current_user),
    db: Session = Depends(get_db)
):
    """Start a new chat session"""
    try:
        session_data = await chat_service.start_chat_session(
            db, current_user.id, claim_id
        )
        
        return ApiResponse(
            success=True,
            message="Chat session started",
            data=session_data
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/sessions", response_model=List[dict])
async def get_chat_sessions(
    current_user = Depends(auth_service.get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's chat sessions"""
    try:
        sessions = await chat_service.get_user_chat_sessions(db, current_user.id)
        return sessions
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/sessions/{session_id}/messages", response_model=PaginatedResponse)
async def get_session_messages(
    session_id: str,
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100),
    current_user = Depends(auth_service.get_current_user),
    db: Session = Depends(get_db)
):
    """Get messages from a chat session"""
    try:
        messages, total = await chat_service.get_session_messages(
            db, session_id, current_user.id, page, size
        )
        
        return PaginatedResponse(
            items=[ConversationMessageResponse.from_orm(msg) for msg in messages],
            total=total,
            page=page,
            size=size,
            pages=(total + size - 1) // size
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/sessions/{session_id}", response_model=ApiResponse)
async def delete_chat_session(
    session_id: str,
    current_user = Depends(auth_service.get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a chat session"""
    try:
        success = await chat_service.delete_chat_session(db, session_id, current_user.id)
        
        if success:
            return ApiResponse(
                success=True,
                message="Chat session deleted successfully"
            )
        else:
            raise HTTPException(status_code=404, detail="Session not found")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# ============================================================================
# CHAT CONTEXT ENDPOINTS
# ============================================================================

@router.get("/context/claims", response_model=List[dict])
async def get_user_claims_context(
    current_user = Depends(auth_service.get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's claims for chat context"""
    try:
        claims_context = await chat_service.get_user_claims_context(db, current_user.id)
        return claims_context
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/context/documents", response_model=List[dict])
async def get_user_documents_context(
    current_user = Depends(auth_service.get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's documents for chat context"""
    try:
        documents_context = await chat_service.get_user_documents_context(db, current_user.id)
        return documents_context
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/context/policies", response_model=List[dict])
async def get_user_policies_context(
    current_user = Depends(auth_service.get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's insurance policies for chat context"""
    try:
        policies_context = await chat_service.get_user_policies_context(db, current_user.id)
        return policies_context
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# ============================================================================
# CHAT SUGGESTIONS ENDPOINTS
# ============================================================================

@router.get("/suggestions", response_model=List[str])
async def get_chat_suggestions(
    context: Optional[str] = None,
    current_user = Depends(auth_service.get_current_user),
    db: Session = Depends(get_db)
):
    """Get contextual chat suggestions"""
    try:
        suggestions = await chat_service.get_chat_suggestions(db, current_user.id, context)
        return suggestions
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# ============================================================================
# CHAT FEEDBACK ENDPOINTS
# ============================================================================

@router.post("/feedback", response_model=ApiResponse)
async def submit_chat_feedback(
    message_id: uuid.UUID = Query(...),
    rating: int = Query(..., ge=1, le=5),
    feedback: Optional[str] = Query(None),
    current_user = Depends(auth_service.get_current_user),
    db: Session = Depends(get_db)
):
    """Submit feedback for chat response"""
    try:
        success = await chat_service.submit_chat_feedback(
            db, message_id, current_user.id, rating, feedback
        )
        
        if success:
            return ApiResponse(
                success=True,
                message="Feedback submitted successfully"
            )
        else:
            raise HTTPException(status_code=404, detail="Message not found")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/messages/{message_id}/flag", response_model=ApiResponse)
async def flag_message(
    message_id: uuid.UUID,
    reason: str,
    current_user = Depends(auth_service.get_current_user),
    db: Session = Depends(get_db)
):
    """Flag inappropriate chat message"""
    try:
        success = await chat_service.flag_message(db, message_id, current_user.id, reason)
        
        if success:
            return ApiResponse(
                success=True,
                message="Message flagged successfully"
            )
        else:
            raise HTTPException(status_code=404, detail="Message not found")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
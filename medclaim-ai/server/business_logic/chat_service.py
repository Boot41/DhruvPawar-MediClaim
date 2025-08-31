"""
Chat Business Logic Service
Handles AI chat functionality, conversation management, and context processing.
"""

from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import uuid
from server.schemas.conversation_schema import ChatMessage, ChatResponse, ConversationMessageResponse


class ChatService:
    """Service class for chat and conversation operations"""
    
    async def process_chat_message(self, db: Session, message: ChatMessage, current_user) -> ChatResponse:
        """Process incoming chat message and generate AI response"""
        try:
            from server.models.models import ConversationMessage
            from server.services import gemini_service
            
            # Get or create conversation session
            conversation = await self._get_or_create_conversation(db, current_user.id, message.session_id)
            
            # Get user context (claims, documents, policies)
            user_context = await self._build_user_context(db, current_user.id)
            
            # Get conversation history
            history = await self._get_conversation_history(db, conversation.id, limit=10)
            
            # Build AI prompt with context
            ai_prompt = await self._build_ai_prompt(message.message, user_context, history)
            
            # Generate AI response
            ai_response = await gemini_service.generate_response(ai_prompt)
            
            # Save user message
            user_msg = ConversationMessage(
                id=uuid.uuid4(),
                conversation_id=conversation.id,
                role="user",
                content=message.message,
                created_at=datetime.utcnow()
            )
            db.add(user_msg)
            
            # Save AI response
            ai_msg = ConversationMessage(
                id=uuid.uuid4(),
                conversation_id=conversation.id,
                role="assistant",
                content=ai_response,
                created_at=datetime.utcnow()
            )
            db.add(ai_msg)
            
            # Update conversation timestamp
            conversation.updated_at = datetime.utcnow()
            
            db.commit()
            
            # Generate claim estimation if relevant
            claim_estimation = None
            if self._should_estimate_claim(message.message):
                claim_estimation = await self._generate_claim_estimation(db, current_user.id)
            
            return ChatResponse(
                response=ai_response,
                session_id=str(conversation.id),
                message_id=str(ai_msg.id),
                extracted_data=user_context.get("documents", {}),
                claim_estimation=claim_estimation
            )
            
        except Exception as e:
            db.rollback()
            raise Exception(f"Failed to process chat message: {str(e)}")
    
    async def start_chat_session(self, db: Session, user_id: uuid.UUID, claim_id: Optional[uuid.UUID] = None) -> Dict[str, Any]:
        """Start a new chat session"""
        try:
            # Note: Conversation model not found, using ConversationMessage only
            
            conversation = Conversation(
                id=uuid.uuid4(),
                user_id=user_id,
                claim_id=claim_id,
                title="New Chat Session",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            db.add(conversation)
            db.commit()
            
            return {
                "session_id": str(conversation.id),
                "created_at": conversation.created_at.isoformat(),
                "claim_id": str(claim_id) if claim_id else None
            }
            
        except Exception as e:
            db.rollback()
            raise Exception(f"Failed to start chat session: {str(e)}")
    
    async def get_user_chat_sessions(self, db: Session, user_id: uuid.UUID) -> List[Dict[str, Any]]:
        """Get all chat sessions for a user"""
        try:
            # Note: Conversation model not found, using ConversationMessage only
            
            conversations = db.query(Conversation).filter(
                Conversation.user_id == user_id
            ).order_by(Conversation.updated_at.desc()).all()
            
            sessions = []
            for conv in conversations:
                # Get last message for preview
                last_message = db.query(ConversationMessage).filter(
                    ConversationMessage.conversation_id == conv.id
                ).order_by(ConversationMessage.created_at.desc()).first()
                
                sessions.append({
                    "session_id": str(conv.id),
                    "title": conv.title,
                    "created_at": conv.created_at.isoformat(),
                    "updated_at": conv.updated_at.isoformat(),
                    "claim_id": str(conv.claim_id) if conv.claim_id else None,
                    "last_message": last_message.content[:100] + "..." if last_message and len(last_message.content) > 100 else last_message.content if last_message else None,
                    "message_count": db.query(ConversationMessage).filter(ConversationMessage.conversation_id == conv.id).count()
                })
            
            return sessions
            
        except Exception as e:
            raise Exception(f"Failed to get chat sessions: {str(e)}")
    
    async def get_session_messages(self, db: Session, session_id: str, user_id: uuid.UUID, page: int, size: int) -> Tuple[List, int]:
        """Get messages from a chat session with pagination"""
        try:
            # Note: Conversation model not found, using ConversationMessage only, ConversationMessage
            
            # Verify user owns the conversation
            conversation = db.query(Conversation).filter(
                Conversation.id == session_id,
                Conversation.user_id == user_id
            ).first()
            
            if not conversation:
                raise Exception("Conversation not found or access denied")
            
            # Get total count
            total = db.query(ConversationMessage).filter(
                ConversationMessage.conversation_id == session_id
            ).count()
            
            # Get messages with pagination
            messages = db.query(ConversationMessage).filter(
                ConversationMessage.conversation_id == session_id
            ).order_by(ConversationMessage.created_at.asc()).offset(
                (page - 1) * size
            ).limit(size).all()
            
            return messages, total
            
        except Exception as e:
            raise Exception(f"Failed to get session messages: {str(e)}")
    
    async def delete_chat_session(self, db: Session, session_id: str, user_id: uuid.UUID) -> bool:
        """Delete a chat session and all its messages"""
        try:
            # Note: Conversation model not found, using ConversationMessage only, ConversationMessage
            
            # Verify user owns the conversation
            conversation = db.query(Conversation).filter(
                Conversation.id == session_id,
                Conversation.user_id == user_id
            ).first()
            
            if not conversation:
                return False
            
            # Delete all messages first
            db.query(ConversationMessage).filter(
                ConversationMessage.conversation_id == session_id
            ).delete()
            
            # Delete conversation
            db.delete(conversation)
            db.commit()
            
            return True
            
        except Exception as e:
            db.rollback()
            raise Exception(f"Failed to delete chat session: {str(e)}")
    
    async def get_user_claims_context(self, db: Session, user_id: uuid.UUID) -> List[Dict[str, Any]]:
        """Get user's claims for chat context"""
        try:
            from server.models.models import Claim
            
            claims = db.query(Claim).filter(Claim.user_id == user_id).all()
            
            claims_context = []
            for claim in claims:
                claims_context.append({
                    "claim_id": str(claim.id),
                    "claim_type": claim.claim_type,
                    "status": claim.status,
                    "amount": float(claim.amount) if claim.amount else 0,
                    "date_of_service": claim.date_of_service.isoformat() if claim.date_of_service else None,
                    "description": claim.description
                })
            
            return claims_context
            
        except Exception as e:
            raise Exception(f"Failed to get claims context: {str(e)}")
    
    async def get_user_documents_context(self, db: Session, user_id: uuid.UUID) -> List[Dict[str, Any]]:
        """Get user's documents for chat context"""
        try:
            from server.models.models import Document
            
            documents = db.query(Document).filter(Document.user_id == user_id).all()
            
            docs_context = []
            for doc in documents:
                docs_context.append({
                    "document_id": str(doc.id),
                    "filename": doc.filename,
                    "document_type": doc.document_type,
                    "is_processed": doc.is_processed,
                    "extracted_data": doc.extracted_data or {},
                    "upload_date": doc.created_at.isoformat()
                })
            
            return docs_context
            
        except Exception as e:
            raise Exception(f"Failed to get documents context: {str(e)}")
    
    async def get_user_policies_context(self, db: Session, user_id: uuid.UUID) -> List[Dict[str, Any]]:
        """Get user's insurance policies for chat context"""
        try:
            from models import InsurancePolicy
            
            policies = db.query(InsurancePolicy).filter(InsurancePolicy.user_id == user_id).all()
            
            policies_context = []
            for policy in policies:
                policies_context.append({
                    "policy_id": str(policy.id),
                    "policy_number": policy.policy_number,
                    "provider": policy.provider,
                    "coverage_type": policy.coverage_type,
                    "deductible": float(policy.deductible) if policy.deductible else 0,
                    "coverage_limit": float(policy.coverage_limit) if policy.coverage_limit else 0,
                    "is_active": policy.is_active
                })
            
            return policies_context
            
        except Exception as e:
            raise Exception(f"Failed to get policies context: {str(e)}")
    
    async def get_chat_suggestions(self, db: Session, user_id: uuid.UUID, context: Optional[str] = None) -> List[str]:
        """Get contextual chat suggestions"""
        try:
            suggestions = [
                "How much will my insurance cover for this claim?",
                "What documents do I need to submit?",
                "Can you explain my policy benefits?",
                "How long does claim processing take?",
                "What is my deductible and copay?"
            ]
            
            # Add context-specific suggestions
            if context == "claim":
                suggestions.extend([
                    "Help me estimate my claim amount",
                    "What's the status of my current claims?",
                    "How to appeal a denied claim?"
                ])
            elif context == "document":
                suggestions.extend([
                    "Analyze my uploaded medical documents",
                    "What information was extracted from my bills?",
                    "Are my documents complete for filing?"
                ])
            
            return suggestions[:8]  # Return max 8 suggestions
            
        except Exception as e:
            raise Exception(f"Failed to get chat suggestions: {str(e)}")
    
    async def submit_chat_feedback(self, db: Session, message_id: uuid.UUID, user_id: uuid.UUID, rating: int, feedback: Optional[str] = None) -> bool:
        """Submit feedback for a chat response"""
        try:
            # Note: Conversation model not found, using ConversationMessage onlyMessage, ChatFeedback
            
            # Verify message exists and user has access
            message = db.query(ConversationMessage).join(Conversation).filter(
                ConversationMessage.id == message_id,
                Conversation.user_id == user_id
            ).first()
            
            if not message:
                return False
            
            # Create or update feedback
            existing_feedback = db.query(ChatFeedback).filter(
                ChatFeedback.message_id == message_id,
                ChatFeedback.user_id == user_id
            ).first()
            
            if existing_feedback:
                existing_feedback.rating = rating
                existing_feedback.feedback = feedback
                existing_feedback.updated_at = datetime.utcnow()
            else:
                chat_feedback = ChatFeedback(
                    id=uuid.uuid4(),
                    message_id=message_id,
                    user_id=user_id,
                    rating=rating,
                    feedback=feedback,
                    created_at=datetime.utcnow()
                )
                db.add(chat_feedback)
            
            db.commit()
            return True
            
        except Exception as e:
            db.rollback()
            raise Exception(f"Failed to submit chat feedback: {str(e)}")
    
    async def flag_message(self, db: Session, message_id: uuid.UUID, user_id: uuid.UUID, reason: str) -> bool:
        """Flag inappropriate chat message"""
        try:
            # Note: Conversation model not found, using ConversationMessage onlyMessage, MessageFlag
            
            # Verify message exists and user has access
            message = db.query(ConversationMessage).join(Conversation).filter(
                ConversationMessage.id == message_id,
                Conversation.user_id == user_id
            ).first()
            
            if not message:
                return False
            
            # Create flag
            flag = MessageFlag(
                id=uuid.uuid4(),
                message_id=message_id,
                user_id=user_id,
                reason=reason,
                created_at=datetime.utcnow()
            )
            
            db.add(flag)
            db.commit()
            return True
            
        except Exception as e:
            db.rollback()
            raise Exception(f"Failed to flag message: {str(e)}")
    
    # Private helper methods
    
    async def _get_or_create_conversation(self, db: Session, user_id: uuid.UUID, session_id: Optional[str] = None):
        """Get existing conversation or create new one"""
        from models import Conversation
        
        if session_id:
            conversation = db.query(Conversation).filter(
                Conversation.id == session_id,
                Conversation.user_id == user_id
            ).first()
            if conversation:
                return conversation
        
        # Create new conversation
        conversation = Conversation(
            id=uuid.uuid4(),
            user_id=user_id,
            title="New Chat",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(conversation)
        return conversation
    
    async def _build_user_context(self, db: Session, user_id: uuid.UUID) -> Dict[str, Any]:
        """Build comprehensive user context for AI"""
        context = {
            "claims": await self.get_user_claims_context(db, user_id),
            "documents": await self.get_user_documents_context(db, user_id),
            "policies": await self.get_user_policies_context(db, user_id)
        }
        return context
    
    async def _get_conversation_history(self, db: Session, conversation_id: uuid.UUID, limit: int = 10) -> List[Dict[str, str]]:
        """Get recent conversation history"""
        from models import ConversationMessage
        
        messages = db.query(ConversationMessage).filter(
            ConversationMessage.conversation_id == conversation_id
        ).order_by(ConversationMessage.created_at.desc()).limit(limit).all()
        
        history = []
        for msg in reversed(messages):  # Reverse to get chronological order
            history.append({
                "role": msg.role,
                "content": msg.content
            })
        
        return history
    
    async def _build_ai_prompt(self, user_message: str, user_context: Dict[str, Any], history: List[Dict[str, str]]) -> str:
        """Build comprehensive AI prompt with context"""
        prompt = f"""
You are a helpful health insurance claim assistant. Help users with:
1. Understanding their medical documents
2. Estimating claim amounts
3. Filing insurance claims
4. Answering questions about coverage

User Context:
- Claims: {user_context.get('claims', [])}
- Documents: {user_context.get('documents', [])}
- Policies: {user_context.get('policies', [])}

Conversation History:
{history}

Current User Message: {user_message}

Provide helpful, accurate information about health insurance claims.
If asked about claim estimation, provide a detailed breakdown.
If documents were uploaded, reference the specific information from them.
"""
        return prompt
    
    def _should_estimate_claim(self, message: str) -> bool:
        """Check if message requires claim estimation"""
        keywords = ['estimate', 'cost', 'coverage', 'claim amount', 'how much', 'deductible', 'copay']
        return any(keyword in message.lower() for keyword in keywords)
    
    async def _generate_claim_estimation(self, db: Session, user_id: uuid.UUID) -> Optional[Dict[str, Any]]:
        """Generate claim estimation based on user data"""
        try:
            from business_logic.claim_services import calculate_claim_estimate
            
            # Get user documents
            user_docs = await self.get_user_documents_context(db, user_id)
            
            if not user_docs:
                return None
            
            # Convert to format expected by existing function
            user_documents = {}
            for doc in user_docs:
                user_documents[doc['document_id']] = {
                    'data': doc['extracted_data']
                }
            
            return await calculate_claim_estimate(user_documents)
            
        except Exception as e:
            return {"error": f"Failed to generate estimation: {str(e)}"}


# Create singleton instance
chat_service = ChatService()

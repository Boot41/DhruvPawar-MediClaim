"""
Chat Business Logic Service
Handles AI chat functionality, conversation management, and context processing.
"""

from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import uuid
import json

from server.schemas.conversation_schema import ChatMessage, ChatResponse, ConversationMessageResponse
from server.utils.gemini_client import call_gemini, safe_parse_json


class ChatService:
    """Service class for chat and conversation operations"""
    
    async def process_chat_message(self, db: Session, message: ChatMessage, current_user) -> ChatResponse:
        """Process incoming chat message and generate AI response via Gemini"""
        try:
            from server.models.models import ConversationMessage

            # Get or create conversation session
            conversation = await self._get_or_create_conversation(db, current_user.id, message.session_id)

            # Get user context (claims, documents, policies)
            user_context = await self._build_user_context(db, current_user.id)

            # Get recent conversation history
            history = await self._get_conversation_history(db, conversation.id, limit=10)

            # Build AI prompt
            ai_prompt = await self._build_ai_prompt(message.message, user_context, history)

            # Call Gemini LLM
            resp = await call_gemini(ai_prompt)
            ai_response_raw = resp.get("text", "")
            parsed_response = safe_parse_json(ai_response_raw)
            ai_response = parsed_response if parsed_response else ai_response_raw

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
                content=ai_response if isinstance(ai_response, str) else json.dumps(ai_response),
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

    # ---------------------- Existing methods ----------------------

    async def start_chat_session(self, db: Session, user_id: uuid.UUID, claim_id: Optional[uuid.UUID] = None) -> Dict[str, Any]:
        """Start a new chat session"""
        from server.models.models import Conversation
        try:
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
        from server.models.models import Conversation, ConversationMessage
        try:
            conversations = db.query(Conversation).filter(
                Conversation.user_id == user_id
            ).order_by(Conversation.updated_at.desc()).all()
            sessions = []
            for conv in conversations:
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

    # ---------------------- Helper & private methods ----------------------

    async def _get_or_create_conversation(self, db: Session, user_id: uuid.UUID, session_id: Optional[str] = None):
        """Get existing conversation or create new one"""
        from server.models.models import Conversation
        if session_id:
            conversation = db.query(Conversation).filter(
                Conversation.id == session_id,
                Conversation.user_id == user_id
            ).first()
            if conversation:
                return conversation
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
        return {
            "claims": await self.get_user_claims_context(db, user_id),
            "documents": await self.get_user_documents_context(db, user_id),
            "policies": await self.get_user_policies_context(db, user_id)
        }

    async def _get_conversation_history(self, db: Session, conversation_id: uuid.UUID, limit: int = 10) -> List[Dict[str, str]]:
        """Get recent conversation history"""
        from server.models.models import ConversationMessage
        messages = db.query(ConversationMessage).filter(
            ConversationMessage.conversation_id == conversation_id
        ).order_by(ConversationMessage.created_at.desc()).limit(limit).all()
        return [{"role": msg.role, "content": msg.content} for msg in reversed(messages)]

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

# Create singleton instance
chat_service = ChatService()

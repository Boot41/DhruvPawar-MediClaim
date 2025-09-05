"""
Database models for the insurance claim processing system
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, JSON, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    documents = relationship("Document", back_populates="user")
    sessions = relationship("UserSession", back_populates="user")
    claims = relationship("Claim", back_populates="user")

class UserSession(Base):
    __tablename__ = "user_sessions"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    session_token = Column(String, unique=True, index=True, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="sessions")
    documents = relationship("Document", back_populates="session")
    chat_messages = relationship("ChatMessage", back_populates="session")
    claims = relationship("Claim", back_populates="session")

class Document(Base):
    __tablename__ = "documents"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    session_id = Column(String, ForeignKey("user_sessions.id"), nullable=True)
    filename = Column(String, nullable=False)  # UUID filename for storage
    original_filename = Column(String, nullable=False)  # Human-readable filename
    file_path = Column(String, nullable=False)
    file_type = Column(String, nullable=False)  # 'policy', 'invoice', 'medical_record'
    file_size = Column(Integer, nullable=False)
    upload_status = Column(String, default="uploaded")  # 'uploaded', 'processing', 'processed', 'failed'
    extracted_data = Column(JSON, nullable=True)
    chunk_data = Column(JSON, nullable=True)  # Store chunked document data
    created_at = Column(DateTime, default=datetime.utcnow)
    processed_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="documents")
    session = relationship("UserSession", back_populates="documents")
    claim_documents = relationship("ClaimDocument", back_populates="document")

class DocumentChunk(Base):
    __tablename__ = "document_chunks"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = Column(String, ForeignKey("documents.id"), nullable=False)
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    chunk_metadata = Column(JSON, nullable=True)
    chunk_type = Column(String, nullable=True)  # 'coverage_info', 'billing_info', etc.
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    document = relationship("Document")

class ChatMessage(Base):
    __tablename__ = "chat_messages"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String, ForeignKey("user_sessions.id"), nullable=False)
    message_type = Column(String, nullable=False)  # 'user', 'agent', 'system'
    content = Column(Text, nullable=False)
    agent_name = Column(String, nullable=True)  # Which agent responded
    message_metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    session = relationship("UserSession", back_populates="chat_messages")

class Claim(Base):
    __tablename__ = "claims"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    session_id = Column(String, ForeignKey("user_sessions.id"), nullable=False)
    vendor_id = Column(String, ForeignKey("vendors.id"), nullable=True)  # Optional vendor association
    status = Column(String, default="initiated")  # 'initiated', 'processing', 'form_generated', 'submitted', 'approved', 'rejected'
    claim_data = Column(JSON, nullable=True)  # Structured claim data
    form_data = Column(JSON, nullable=True)  # Generated form data
    form_preview = Column(Text, nullable=True)  # HTML preview of form
    missing_fields = Column(JSON, nullable=True)  # Fields that need user input
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    submitted_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="claims")
    session = relationship("UserSession", back_populates="claims")
    vendor = relationship("Vendor", back_populates="claims")
    claim_documents = relationship("ClaimDocument", back_populates="claim")

class ClaimDocument(Base):
    __tablename__ = "claim_documents"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    claim_id = Column(String, ForeignKey("claims.id"), nullable=False)
    document_id = Column(String, ForeignKey("documents.id"), nullable=False)
    document_type = Column(String, nullable=False)  # 'policy', 'invoice', 'supporting'
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    claim = relationship("Claim", back_populates="claim_documents")
    document = relationship("Document", back_populates="claim_documents")

class Vendor(Base):
    __tablename__ = "vendors"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False, unique=True)
    display_name = Column(String, nullable=False)
    form_template_url = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    claims = relationship("Claim", back_populates="vendor")

class WorkflowState(Base):
    __tablename__ = "workflow_states"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String, ForeignKey("user_sessions.id"), nullable=False)
    current_step = Column(String, nullable=False)  # 'document_upload', 'chat', 'claim_generation', 'form_preview', 'submission'
    step_data = Column(JSON, nullable=True)
    conversation_history = Column(JSON, nullable=True)
    agent_context = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    session = relationship("UserSession")

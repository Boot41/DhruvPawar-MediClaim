from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Boolean, Float, ForeignKey, LargeBinary
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime
import os

# Database configuration
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///./medclaim.db')

if DATABASE_URL.startswith('sqlite'):
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Database Models
class User(Base):
    __tablename__ = "users"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    phone = Column(String)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    sessions = relationship("UserSession", back_populates="user")
    documents = relationship("Document", back_populates="user")
    claims = relationship("Claim", back_populates="user")

class UserSession(Base):
    __tablename__ = "user_sessions"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    session_token = Column(String, unique=True, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="sessions")
    workflow_states = relationship("WorkflowState", back_populates="session")

class Document(Base):
    __tablename__ = "documents"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    file_type = Column(String, nullable=False)  # 'policy', 'invoice', 'claim_form'
    mime_type = Column(String, nullable=False)
    file_size = Column(Integer, nullable=False)
    upload_status = Column(String, default='uploaded')  # uploaded, processing, processed, failed
    extracted_data = Column(Text)  # JSON string of extracted data
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="documents")
    claims = relationship("Claim", back_populates="policy_document")

class Vendor(Base):
    __tablename__ = "vendors"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, unique=True, nullable=False)
    display_name = Column(String, nullable=False)
    logo_url = Column(String)
    form_template_path = Column(String)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    claims = relationship("Claim", back_populates="vendor")

class Claim(Base):
    __tablename__ = "claims"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    vendor_id = Column(String, ForeignKey("vendors.id"))
    policy_document_id = Column(String, ForeignKey("documents.id"))
    
    # Claim details
    claim_number = Column(String, unique=True)
    status = Column(String, default='draft')  # draft, submitted, processing, approved, rejected
    total_amount = Column(Float)
    covered_amount = Column(Float)
    out_of_pocket_amount = Column(Float)
    deductible_applied = Column(Float)
    
    # Policy data (JSON)
    policy_data = Column(Text)
    invoice_data = Column(Text)
    coverage_analysis = Column(Text)
    
    # Form data
    filled_form_path = Column(String)
    form_status = Column(String, default='pending')  # pending, generated, downloaded
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="claims")
    vendor = relationship("Vendor", back_populates="claims")
    policy_document = relationship("Document", back_populates="claims")
    claim_documents = relationship("ClaimDocument", back_populates="claim")

class ClaimDocument(Base):
    __tablename__ = "claim_documents"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    claim_id = Column(String, ForeignKey("claims.id"), nullable=False)
    document_id = Column(String, ForeignKey("documents.id"), nullable=False)
    document_type = Column(String, nullable=False)  # 'invoice', 'prescription', 'discharge_summary'
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    claim = relationship("Claim", back_populates="claim_documents")
    document = relationship("Document")

class WorkflowState(Base):
    __tablename__ = "workflow_states"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String, ForeignKey("user_sessions.id"), nullable=False)
    current_step = Column(String, nullable=False)  # 'policy_upload', 'document_analysis', etc.
    step_data = Column(Text)  # JSON string of step-specific data
    conversation_history = Column(Text)  # JSON array of messages
    agent_context = Column(Text)  # JSON string of agent state
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    session = relationship("UserSession", back_populates="workflow_states")

class ChatMessage(Base):
    __tablename__ = "chat_messages"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String, ForeignKey("user_sessions.id"), nullable=False)
    message_type = Column(String, nullable=False)  # 'user', 'agent', 'system'
    content = Column(Text, nullable=False)
    message_metadata = Column(Text)  # JSON string for additional data
    created_at = Column(DateTime, default=datetime.utcnow)

# Database dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Create tables
def create_tables():
    Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    create_tables()
    print("Database tables created successfully!")

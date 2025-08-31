from sqlalchemy import Column, String, Integer, Float, DateTime, JSON, ForeignKey, Text, Boolean, Enum, DECIMAL, Date
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
from server.config.database import Base
import uuid
import enum

# Enums for better data integrity
class UserRole(str, enum.Enum):
    admin = "admin"
    agent = "agent"
    customer = "customer"

class DocumentType(enum.Enum):
    MEDICAL_BILL = "medical_bill"
    PRESCRIPTION = "prescription"
    LAB_REPORT = "lab_report"
    DISCHARGE_SUMMARY = "discharge_summary"
    INSURANCE_CARD = "insurance_card"
    ID_DOCUMENT = "id_document"
    OTHER = "other"

class ClaimStatus(enum.Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    DENIED = "denied"
    PAID = "paid"
    APPEALED = "appealed"
    CLOSED = "closed"

class PaymentStatus(enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"

# Core User Management
class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    phone = Column(String(20), index=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    date_of_birth = Column(Date)
    address = Column(Text)
    role = Column(Enum(UserRole), default=UserRole.customer)
    is_active = Column(Boolean, default=True)
    password_hash = Column(String(255), nullable=False)
    last_login = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    insurance_policies = relationship("InsurancePolicy", back_populates="user")
    claims = relationship("Claim", back_populates="user")
    documents = relationship("Document", back_populates="user")
    conversations = relationship("ConversationMessage", back_populates="user")

# Insurance Provider and Policy Management
class InsuranceProvider(Base):
    __tablename__ = "insurance_providers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(200), nullable=False)
    code = Column(String(50), unique=True, nullable=False)
    contact_email = Column(String(255))
    contact_phone = Column(String(20))
    address = Column(Text)
    api_endpoint = Column(String(500))  # For API integrations
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    policies = relationship("InsurancePolicy", back_populates="provider")

class InsurancePolicy(Base):
    __tablename__ = "insurance_policies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    provider_id = Column(UUID(as_uuid=True), ForeignKey("insurance_providers.id"), nullable=False)
    policy_number = Column(String(100), unique=True, nullable=False)
    group_number = Column(String(100))
    policy_type = Column(String(100))  # Individual, Family, Group, etc.
    coverage_start_date = Column(Date, nullable=False)
    coverage_end_date = Column(Date)
    annual_deductible = Column(DECIMAL(10, 2), default=0.00)
    annual_out_of_pocket_max = Column(DECIMAL(10, 2))
    copay_amount = Column(DECIMAL(10, 2), default=0.00)
    coverage_percentage = Column(Float, default=0.80)  # 80% coverage
    is_active = Column(Boolean, default=True)
    policy_details = Column(JSON)  # Store complex policy rules
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="insurance_policies")
    provider = relationship("InsuranceProvider", back_populates="policies")
    claims = relationship("Claim", back_populates="policy")

# Healthcare Providers
class HealthcareProvider(Base):
    __tablename__ = "healthcare_providers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(200), nullable=False)
    npi_number = Column(String(10), unique=True)  # National Provider Identifier
    specialty = Column(String(100))
    address = Column(Text)
    phone = Column(String(20))
    email = Column(String(255))
    tax_id = Column(String(20))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    claims = relationship("Claim", back_populates="healthcare_provider")
    services = relationship("MedicalService", back_populates="provider")

# Document Management
class Document(Base):
    __tablename__ = "documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    claim_id = Column(UUID(as_uuid=True), ForeignKey("claims.id"), nullable=True)  # Can be null for pre-claim docs
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer)
    mime_type = Column(String(100))
    document_type = Column(Enum(DocumentType), nullable=False)
    extracted_data = Column(JSON)  # AI-extracted information
    extraction_confidence = Column(Float, default=0.0)
    is_processed = Column(Boolean, default=False)
    is_verified = Column(Boolean, default=False)  # Human verification
    upload_source = Column(String(50), default="web")  # web, mobile, email, etc.
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)  # <-- Added

    # Relationships
    user = relationship("User", back_populates="documents")
    claim = relationship("Claim", back_populates="documents")

# Claims Management
class Claim(Base):
    __tablename__ = "claims"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    claim_number = Column(String(50), unique=True, nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    policy_id = Column(UUID(as_uuid=True), ForeignKey("insurance_policies.id"), nullable=False)
    healthcare_provider_id = Column(UUID(as_uuid=True), ForeignKey("healthcare_providers.id"))
    
    # Claim details
    status = Column(Enum(ClaimStatus), default=ClaimStatus.DRAFT)
    claim_type = Column(String(50))  # medical, pharmacy, vision, dental
    diagnosis_code = Column(String(20))  # ICD-10 codes
    diagnosis_description = Column(Text)
    
    # Dates
    date_of_service_start = Column(Date)
    date_of_service_end = Column(Date)
    submission_date = Column(DateTime)
    decision_date = Column(DateTime)
    
    # Financial information
    total_billed_amount = Column(DECIMAL(12, 2), default=0.00)
    total_allowed_amount = Column(DECIMAL(12, 2), default=0.00)
    insurance_paid_amount = Column(DECIMAL(12, 2), default=0.00)
    patient_responsibility = Column(DECIMAL(12, 2), default=0.00)
    deductible_applied = Column(DECIMAL(10, 2), default=0.00)
    copay_applied = Column(DECIMAL(10, 2), default=0.00)
    coinsurance_applied = Column(DECIMAL(10, 2), default=0.00)
    
    # Processing information
    processed_by = Column(String(100))  # Agent or system
    denial_reason = Column(Text)
    notes = Column(Text)
    external_claim_id = Column(String(100))  # For insurance provider integration
    
    # AI-generated estimates
    ai_estimated_coverage = Column(DECIMAL(12, 2))
    ai_estimated_patient_cost = Column(DECIMAL(12, 2))
    ai_confidence_score = Column(Float)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="claims")
    policy = relationship("InsurancePolicy", back_populates="claims")
    healthcare_provider = relationship("HealthcareProvider", back_populates="claims")
    documents = relationship("Document", back_populates="claim")
    services = relationship("MedicalService", back_populates="claim")
    status_history = relationship("ClaimStatusHistory", back_populates="claim")
    payments = relationship("Payment", back_populates="claim")

# Medical Services (Line items on claims)
class MedicalService(Base):
    __tablename__ = "medical_services"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    claim_id = Column(UUID(as_uuid=True), ForeignKey("claims.id"), nullable=False)
    provider_id = Column(UUID(as_uuid=True), ForeignKey("healthcare_providers.id"))
    
    # Service details
    service_code = Column(String(20), nullable=False)  # CPT, HCPCS codes
    service_description = Column(Text)
    service_date = Column(Date, nullable=False)
    quantity = Column(Integer, default=1)
    unit_price = Column(DECIMAL(10, 2), nullable=False)
    total_charge = Column(DECIMAL(10, 2), nullable=False)
    
    # Processing results
    allowed_amount = Column(DECIMAL(10, 2))
    paid_amount = Column(DECIMAL(10, 2))
    denial_reason = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    claim = relationship("Claim", back_populates="services")
    provider = relationship("HealthcareProvider", back_populates="services")

# Claim Status History for audit trail
class ClaimStatusHistory(Base):
    __tablename__ = "claim_status_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    claim_id = Column(UUID(as_uuid=True), ForeignKey("claims.id"), nullable=False)
    old_status = Column(Enum(ClaimStatus))
    new_status = Column(Enum(ClaimStatus), nullable=False)
    changed_by = Column(String(100))
    change_reason = Column(Text)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    claim = relationship("Claim", back_populates="status_history")

# Payment tracking
class Payment(Base):
    __tablename__ = "payments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    claim_id = Column(UUID(as_uuid=True), ForeignKey("claims.id"), nullable=False)
    payment_type = Column(String(50))  # insurance_payment, patient_payment, refund
    amount = Column(DECIMAL(10, 2), nullable=False)
    payment_date = Column(Date)
    payment_method = Column(String(50))  # check, eft, cash, credit_card
    reference_number = Column(String(100))
    status = Column(Enum(PaymentStatus), default=PaymentStatus.PENDING)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    claim = relationship("Claim", back_populates="payments")

# Conversation/Chat Management
class ConversationMessage(Base):
    __tablename__ = "conversation_messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    claim_id = Column(UUID(as_uuid=True), ForeignKey("claims.id"), nullable=True)  # Optional claim context
    session_id = Column(String(100))  # Group messages by conversation session
    role = Column(String(20), nullable=False)  # user, assistant, system
    message_type = Column(String(50), default="text")  # text, image, file, estimate
    content = Column(Text, nullable=False)
    metadata_json = Column("metadata", JSON)  # Store additional data like AI confidence, extracted entities
    parent_message_id = Column(UUID(as_uuid=True), ForeignKey("conversation_messages.id"))
    is_flagged = Column(Boolean, default=False)  # For moderation
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="conversations")
    claim = relationship("Claim")
    replies = relationship("ConversationMessage", remote_side=[id])

# AI Processing Jobs (for async processing)
class ProcessingJob(Base):
    __tablename__ = "processing_jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_type = Column(String(50), nullable=False)  # document_extraction, claim_estimation, etc.
    entity_id = Column(UUID(as_uuid=True))  # ID of the document, claim, etc. being processed
    entity_type = Column(String(50))  # document, claim, etc.
    status = Column(String(20), default="pending")  # pending, processing, completed, failed
    input_data = Column(JSON)
    output_data = Column(JSON)
    error_message = Column(Text)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

# Audit Log for compliance and debugging
class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    action = Column(String(100), nullable=False)  # create, update, delete, view
    entity_type = Column(String(50), nullable=False)  # claim, document, user, etc.
    entity_id = Column(UUID(as_uuid=True))
    old_values = Column(JSON)
    new_values = Column(JSON)
    ip_address = Column(String(45))
    user_agent = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User")

# System Configuration
class SystemConfig(Base):
    __tablename__ = "system_config"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    config_key = Column(String(100), unique=True, nullable=False)
    config_value = Column(JSON)
    description = Column(Text)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
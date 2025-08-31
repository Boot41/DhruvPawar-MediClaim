# Central import file for all schemas - for backward compatibility
# Import all schemas from their respective modules

# Base schemas and enums
from server.schemas.base_schema import (
    BaseSchema, DocumentType, ClaimStatus, PaymentStatus,
    PaginatedResponse, ApiResponse, HealthCheckResponse
)

# User schemas
from server.schemas.user_schema import (
    UserRole, UserBase, UserCreate, UserUpdate, UserResponse, 
    UserLogin, UserProfile
)

# Insurance schemas
from server.schemas.insurance_schema import (
    InsuranceProviderBase, InsuranceProviderCreate, InsuranceProviderUpdate, 
    InsuranceProviderResponse, InsurancePolicyBase, InsurancePolicyCreate, 
    InsurancePolicyUpdate, InsurancePolicyResponse
)

# Healthcare schemas
from server.schemas.healthcare_schema import (
    HealthcareProviderBase, HealthcareProviderCreate, HealthcareProviderUpdate,
    HealthcareProviderResponse
)

# Document schemas
from server.schemas.document_schema import (
    DocumentBase, DocumentCreate, DocumentUpdate, DocumentResponse,
    DocumentUploadResponse
)

# Claim schemas
from server.schemas.claim_schema import (
    MedicalServiceBase, MedicalServiceCreate, MedicalServiceUpdate, MedicalServiceResponse,
    ClaimBase, ClaimCreate, ClaimUpdate, ClaimResponse,
    ClaimEstimateRequest, ClaimEstimateResponse
)

# Payment schemas
from server.schemas.payment_schema import (
    PaymentBase, PaymentCreate, PaymentUpdate, PaymentResponse
)

# Conversation schemas
from server.schemas.conversation_schema import (
    ConversationMessageBase, ConversationMessageCreate, ConversationMessageResponse,
    ChatMessage, ChatResponse
)

# Processing schemas
from server.schemas.processing_schema import (
    ProcessingJobBase, ProcessingJobCreate, ProcessingJobUpdate, ProcessingJobResponse
)
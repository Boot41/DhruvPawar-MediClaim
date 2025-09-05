"""
Test cases for Pydantic schemas
"""
import pytest
from datetime import datetime
from pydantic import ValidationError

from schemas import (
    UserCreate, UserResponse, UserLogin, Token,
    DocumentUpload, DocumentResponse, DocumentChunkResponse,
    ClaimInitiate, ClaimStatus, ClaimFormPreview, ClaimSubmission,
    VendorResponse, WorkflowState, CoverageAnalysis, CoverageRequest,
    ChatMessage, ChatResponse, SuccessResponse, ErrorResponse, HealthCheck
)


class TestUserSchemas:
    """Test user-related schemas."""
    
    def test_user_create_valid(self):
        """Test UserCreate with valid data."""
        user_data = {
            "email": "test@example.com",
            "password": "testpassword123",
            "full_name": "Test User"
        }
        user = UserCreate(**user_data)
        assert user.email == "test@example.com"
        assert user.password == "testpassword123"
        assert user.full_name == "Test User"
    
    def test_user_create_invalid_email(self):
        """Test UserCreate with invalid email."""
        user_data = {
            "email": "invalid-email",
            "password": "testpassword123",
            "full_name": "Test User"
        }
        with pytest.raises(ValidationError):
            UserCreate(**user_data)
    
    def test_user_response(self):
        """Test UserResponse schema."""
        user_data = {
            "id": "test-id-123",
            "email": "test@example.com",
            "full_name": "Test User",
            "is_active": True,
            "created_at": datetime.utcnow()
        }
        user = UserResponse(**user_data)
        assert user.id == "test-id-123"
        assert user.email == "test@example.com"
        assert user.is_active is True


class TestDocumentSchemas:
    """Test document-related schemas."""
    
    def test_document_upload_valid(self):
        """Test DocumentUpload with valid data."""
        doc_data = {
            "file_type": "policy",
            "session_id": "test-session-123"
        }
        doc = DocumentUpload(**doc_data)
        assert doc.file_type == "policy"
        assert doc.session_id == "test-session-123"
    
    def test_document_response(self):
        """Test DocumentResponse schema."""
        doc_data = {
            "id": "doc-123",
            "filename": "test.pdf",
            "original_filename": "test.pdf",
            "file_type": "policy",
            "upload_status": "uploaded",
            "extracted_data": {"test": "data"},
            "total_chunks": 5,
            "created_at": datetime.utcnow()
        }
        doc = DocumentResponse(**doc_data)
        assert doc.id == "doc-123"
        assert doc.filename == "test.pdf"
        assert doc.file_type == "policy"
        assert doc.upload_status == "uploaded"


class TestClaimSchemas:
    """Test claim-related schemas."""
    
    def test_claim_initiate_valid(self):
        """Test ClaimInitiate with valid data."""
        claim_data = {
            "session_id": "test-session"
        }
        claim = ClaimInitiate(**claim_data)
        assert claim.session_id == "test-session"
    
    def test_claim_status(self):
        """Test ClaimStatus schema."""
        claim_data = {
            "claim_id": "test-claim-123",
            "status": "initiated",
            "created_at": datetime.utcnow(),
            "claim_data": {"test": "data"}
        }
        claim = ClaimStatus(**claim_data)
        assert claim.claim_id == "test-claim-123"
        assert claim.status == "initiated"
        assert claim.claim_data == {"test": "data"}
    
    def test_claim_form_preview(self):
        """Test ClaimFormPreview schema."""
        form_data = {
            "form_data": {"test": "data"},
            "preview_html": "<html>test</html>",
            "missing_fields": []
        }
        form = ClaimFormPreview(**form_data)
        assert form.form_data == {"test": "data"}
        assert form.preview_html == "<html>test</html>"
        assert form.missing_fields == []


class TestVendorSchemas:
    """Test vendor-related schemas."""
    
    def test_vendor_response(self):
        """Test VendorResponse schema."""
        vendor_data = {
            "id": "vendor-123",
            "name": "test_insurance",
            "display_name": "Test Insurance Company",
            "form_template_url": "https://example.com/template.pdf",
            "is_active": True
        }
        vendor = VendorResponse(**vendor_data)
        assert vendor.id == "vendor-123"
        assert vendor.name == "test_insurance"
        assert vendor.display_name == "Test Insurance Company"
        assert vendor.is_active is True


class TestWorkflowSchemas:
    """Test workflow-related schemas."""
    
    def test_workflow_state(self):
        """Test WorkflowState schema."""
        workflow_data = {
            "current_step": "document_upload",
            "step_data": {"test": "data"},
            "conversation_history": [{"role": "user", "content": "test"}]
        }
        workflow = WorkflowState(**workflow_data)
        assert workflow.current_step == "document_upload"
        assert workflow.step_data == {"test": "data"}


class TestCoverageSchemas:
    """Test coverage-related schemas."""
    
    def test_coverage_analysis(self):
        """Test CoverageAnalysis schema."""
        coverage_data = {
            "total_cost": 1000.0,
            "deductible_applied": 100.0,
            "insurance_covers": 800.0,
            "out_of_pocket": 200.0,
            "coverage_percentage": 80.0
        }
        coverage = CoverageAnalysis(**coverage_data)
        assert coverage.total_cost == 1000.0
        assert coverage.deductible_applied == 100.0
        assert coverage.insurance_covers == 800.0
        assert coverage.out_of_pocket == 200.0
        assert coverage.coverage_percentage == 80.0
    
    def test_coverage_request(self):
        """Test CoverageRequest schema."""
        request_data = {
            "session_id": "test-session",
            "policy_data": {"test": "policy"},
            "invoice_data": {"test": "invoice"}
        }
        request = CoverageRequest(**request_data)
        assert request.session_id == "test-session"
        assert request.policy_data == {"test": "policy"}
        assert request.invoice_data == {"test": "invoice"}


class TestChatSchemas:
    """Test chat-related schemas."""
    
    def test_chat_message(self):
        """Test ChatMessage schema."""
        message_data = {
            "message": "Test message",
            "session_id": "test-session"
        }
        message = ChatMessage(**message_data)
        assert message.message == "Test message"
        assert message.session_id == "test-session"
    
    def test_chat_response(self):
        """Test ChatResponse schema."""
        response_data = {
            "response": "Test response",
            "agent_name": "chat_assistant",
            "metadata": {"test": "data"},
            "timestamp": datetime.utcnow()
        }
        response = ChatResponse(**response_data)
        assert response.response == "Test response"
        assert response.agent_name == "chat_assistant"
        assert response.metadata == {"test": "data"}
        assert response.timestamp is not None


class TestUtilitySchemas:
    """Test utility schemas."""
    
    def test_success_response(self):
        """Test SuccessResponse schema."""
        response_data = {
            "success": True,
            "message": "Operation successful",
            "data": {"test": "data"}
        }
        response = SuccessResponse(**response_data)
        assert response.success is True
        assert response.message == "Operation successful"
        assert response.data == {"test": "data"}
    
    def test_error_response(self):
        """Test ErrorResponse schema."""
        error_data = {
            "success": False,
            "error": "Something went wrong",
            "details": {"test": "error"}
        }
        error = ErrorResponse(**error_data)
        assert error.success is False
        assert error.error == "Something went wrong"
        assert error.details == {"test": "error"}
    
    def test_health_check(self):
        """Test HealthCheck schema."""
        health_data = {
            "status": "healthy",
            "version": "1.0.0",
            "database": "connected",
            "agents": "active",
            "timestamp": datetime.utcnow()
        }
        health = HealthCheck(**health_data)
        assert health.status == "healthy"
        assert health.version == "1.0.0"
        assert health.database == "connected"
        assert health.agents == "active"
        assert health.timestamp is not None
"""
Test cases for Pydantic schemas
"""
import pytest
from datetime import datetime
from pydantic import ValidationError

from schemas import (
    UserCreate, UserResponse, UserLogin, Token,
    DocumentUpload, DocumentResponse, DocumentChunkResponse,
    ClaimCreate, ClaimResponse, VendorResponse, WorkflowStateResponse,
    ChatMessageCreate, ChatMessageResponse
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
            "id": 1,
            "email": "test@example.com",
            "full_name": "Test User",
            "is_active": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        user = UserResponse(**user_data)
        assert user.id == 1
        assert user.email == "test@example.com"
        assert user.is_active is True


class TestDocumentSchemas:
    """Test document-related schemas."""
    
    def test_document_upload_valid(self):
        """Test DocumentUpload with valid data."""
        doc_data = {
            "file_type": "policy",
            "filename": "test.pdf"
        }
        doc = DocumentUpload(**doc_data)
        assert doc.file_type == "policy"
        assert doc.filename == "test.pdf"
    
    def test_document_response(self):
        """Test DocumentResponse schema."""
        doc_data = {
            "id": 1,
            "filename": "test.pdf",
            "original_filename": "test.pdf",
            "file_type": "policy",
            "file_size": 1024,
            "upload_status": "uploaded",
            "created_at": datetime.utcnow()
        }
        doc = DocumentResponse(**doc_data)
        assert doc.id == 1
        assert doc.filename == "test.pdf"
        assert doc.file_type == "policy"
        assert doc.file_size == 1024


class TestClaimSchemas:
    """Test claim-related schemas."""
    
    def test_claim_create_valid(self):
        """Test ClaimCreate with valid data."""
        claim_data = {
            "claim_data": {"test": "data"},
            "form_data": {"test": "data"}
        }
        claim = ClaimCreate(**claim_data)
        assert claim.claim_data == {"test": "data"}
        assert claim.form_data == {"test": "data"}
    
    def test_claim_response(self):
        """Test ClaimResponse schema."""
        claim_data = {
            "id": 1,
            "status": "initiated",
            "claim_data": {"test": "data"},
            "form_data": {"test": "data"},
            "created_at": datetime.utcnow()
        }
        claim = ClaimResponse(**claim_data)
        assert claim.id == 1
        assert claim.status == "initiated"
        assert claim.claim_data == {"test": "data"}


class TestVendorSchemas:
    """Test vendor-related schemas."""
    
    def test_vendor_response(self):
        """Test VendorResponse schema."""
        vendor_data = {
            "id": 1,
            "name": "test_insurance",
            "display_name": "Test Insurance Company",
            "form_template_url": "https://example.com/template.pdf",
            "is_active": True,
            "created_at": datetime.utcnow()
        }
        vendor = VendorResponse(**vendor_data)
        assert vendor.id == 1
        assert vendor.name == "test_insurance"
        assert vendor.display_name == "Test Insurance Company"
        assert vendor.is_active is True


class TestWorkflowSchemas:
    """Test workflow-related schemas."""
    
    def test_workflow_state_response(self):
        """Test WorkflowStateResponse schema."""
        workflow_data = {
            "id": 1,
            "current_step": "document_upload",
            "step_data": {"test": "data"},
            "conversation_history": [{"role": "user", "content": "test"}],
            "created_at": datetime.utcnow()
        }
        workflow = WorkflowStateResponse(**workflow_data)
        assert workflow.id == 1
        assert workflow.current_step == "document_upload"
        assert workflow.step_data == {"test": "data"}


class TestChatSchemas:
    """Test chat-related schemas."""
    
    def test_chat_message_create_valid(self):
        """Test ChatMessageCreate with valid data."""
        message_data = {
            "message_type": "user",
            "content": "Test message"
        }
        message = ChatMessageCreate(**message_data)
        assert message.message_type == "user"
        assert message.content == "Test message"
    
    def test_chat_message_response(self):
        """Test ChatMessageResponse schema."""
        message_data = {
            "id": 1,
            "message_type": "user",
            "content": "Test message",
            "agent_name": None,
            "created_at": datetime.utcnow()
        }
        message = ChatMessageResponse(**message_data)
        assert message.id == 1
        assert message.message_type == "user"
        assert message.content == "Test message"
        assert message.agent_name is None
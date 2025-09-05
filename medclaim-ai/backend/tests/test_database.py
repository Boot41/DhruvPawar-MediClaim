"""
Test cases for database models and operations
"""
import pytest
from datetime import datetime, timedelta
from sqlalchemy.exc import IntegrityError

from database import User, UserSession, Document, DocumentChunk, Claim, Vendor, WorkflowState, ChatMessage


class TestUserModel:
    """Test User model functionality."""
    
    def test_create_user(self, db_session):
        """Test creating a user."""
        user = User(
            email="test@example.com",
            hashed_password="hashed_password",
            full_name="Test User",
            is_active=True
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        
        assert user.id is not None
        assert user.email == "test@example.com"
        assert user.full_name == "Test User"
        assert user.is_active is True
        assert user.created_at is not None
        assert user.updated_at is not None
    
    def test_user_email_unique(self, db_session, test_user):
        """Test that user email must be unique."""
        duplicate_user = User(
            email=test_user.email,
            hashed_password="password",
            full_name="Duplicate User"
        )
        db_session.add(duplicate_user)
        
        with pytest.raises(IntegrityError):
            db_session.commit()
    
    def test_user_default_values(self, db_session):
        """Test user default values."""
        user = User(
            email="test@example.com",
            hashed_password="hashed_password"
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        
        assert user.is_active is True
        assert user.created_at is not None
        assert user.updated_at is not None


class TestUserSessionModel:
    """Test UserSession model functionality."""
    
    def test_create_user_session(self, db_session, test_user):
        """Test creating a user session."""
        session = UserSession(
            user_id=test_user.id,
            session_token="test_token",
            is_active=True,
            expires_at=datetime.utcnow() + timedelta(hours=24)
        )
        db_session.add(session)
        db_session.commit()
        db_session.refresh(session)
        
        assert session.id is not None
        assert session.user_id == test_user.id
        assert session.session_token == "test_token"
        assert session.is_active is True
        assert session.expires_at > datetime.utcnow()
    
    def test_user_session_relationship(self, db_session, test_user):
        """Test user session relationship to user."""
        session = UserSession(
            user_id=test_user.id,
            session_token="test_token",
            is_active=True,
            expires_at=datetime.utcnow() + timedelta(hours=24)
        )
        db_session.add(session)
        db_session.commit()
        db_session.refresh(session)
        
        # Test relationship
        assert session.user is not None
        assert session.user.id == test_user.id
        assert session in test_user.sessions


class TestDocumentModel:
    """Test Document model functionality."""
    
    def test_create_document(self, db_session, test_user, test_session):
        """Test creating a document."""
        document = Document(
            user_id=test_user.id,
            session_id=test_session.id,
            filename="test.pdf",
            original_filename="test.pdf",
            file_path="/uploads/test.pdf",
            file_type="policy",
            file_size=1024,
            upload_status="uploaded"
        )
        db_session.add(document)
        db_session.commit()
        db_session.refresh(document)
        
        assert document.id is not None
        assert document.user_id == test_user.id
        assert document.session_id == test_session.id
        assert document.filename == "test.pdf"
        assert document.file_type == "policy"
        assert document.file_size == 1024
        assert document.upload_status == "uploaded"
    
    def test_document_relationships(self, db_session, test_user, test_session):
        """Test document relationships."""
        document = Document(
            user_id=test_user.id,
            session_id=test_session.id,
            filename="test.pdf",
            original_filename="test.pdf",
            file_path="/uploads/test.pdf",
            file_type="policy",
            file_size=1024
        )
        db_session.add(document)
        db_session.commit()
        db_session.refresh(document)
        
        # Test relationships
        assert document.user is not None
        assert document.user.id == test_user.id
        assert document.session is not None
        assert document.session.id == test_session.id


class TestDocumentChunkModel:
    """Test DocumentChunk model functionality."""
    
    def test_create_document_chunk(self, db_session, test_document):
        """Test creating a document chunk."""
        chunk = DocumentChunk(
            document_id=test_document.id,
            chunk_index=0,
            content="Test chunk content",
            metadata={"chunk_type": "policy_info"},
            chunk_type="policy_info"
        )
        db_session.add(chunk)
        db_session.commit()
        db_session.refresh(chunk)
        
        assert chunk.id is not None
        assert chunk.document_id == test_document.id
        assert chunk.chunk_index == 0
        assert chunk.content == "Test chunk content"
        assert chunk.metadata == {"chunk_type": "policy_info"}
        assert chunk.chunk_type == "policy_info"
    
    def test_document_chunk_relationship(self, db_session, test_document):
        """Test document chunk relationship to document."""
        chunk = DocumentChunk(
            document_id=test_document.id,
            chunk_index=0,
            content="Test chunk content",
            metadata={"chunk_type": "policy_info"},
            chunk_type="policy_info"
        )
        db_session.add(chunk)
        db_session.commit()
        db_session.refresh(chunk)
        
        # Test relationship
        assert chunk.document is not None
        assert chunk.document.id == test_document.id
        assert chunk in test_document.chunks


class TestClaimModel:
    """Test Claim model functionality."""
    
    def test_create_claim(self, db_session, test_user, test_session):
        """Test creating a claim."""
        claim = Claim(
            user_id=test_user.id,
            session_id=test_session.id,
            status="initiated",
            claim_data={"test": "data"},
            form_data={"test": "data"}
        )
        db_session.add(claim)
        db_session.commit()
        db_session.refresh(claim)
        
        assert claim.id is not None
        assert claim.user_id == test_user.id
        assert claim.session_id == test_session.id
        assert claim.status == "initiated"
        assert claim.claim_data == {"test": "data"}
        assert claim.form_data == {"test": "data"}
    
    def test_claim_relationships(self, db_session, test_user, test_session):
        """Test claim relationships."""
        claim = Claim(
            user_id=test_user.id,
            session_id=test_session.id,
            status="initiated"
        )
        db_session.add(claim)
        db_session.commit()
        db_session.refresh(claim)
        
        # Test relationships
        assert claim.user is not None
        assert claim.user.id == test_user.id
        assert claim.session is not None
        assert claim.session.id == test_session.id


class TestVendorModel:
    """Test Vendor model functionality."""
    
    def test_create_vendor(self, db_session):
        """Test creating a vendor."""
        vendor = Vendor(
            name="test_insurance",
            display_name="Test Insurance Company",
            form_template_url="https://example.com/template.pdf",
            is_active=True
        )
        db_session.add(vendor)
        db_session.commit()
        db_session.refresh(vendor)
        
        assert vendor.id is not None
        assert vendor.name == "test_insurance"
        assert vendor.display_name == "Test Insurance Company"
        assert vendor.form_template_url == "https://example.com/template.pdf"
        assert vendor.is_active is True
    
    def test_vendor_default_values(self, db_session):
        """Test vendor default values."""
        vendor = Vendor(
            name="test_insurance",
            display_name="Test Insurance Company"
        )
        db_session.add(vendor)
        db_session.commit()
        db_session.refresh(vendor)
        
        assert vendor.is_active is True
        assert vendor.created_at is not None
        assert vendor.updated_at is not None


class TestWorkflowStateModel:
    """Test WorkflowState model functionality."""
    
    def test_create_workflow_state(self, db_session, test_session):
        """Test creating a workflow state."""
        workflow = WorkflowState(
            session_id=test_session.id,
            current_step="document_upload",
            step_data={"test": "data"},
            conversation_history=[{"role": "user", "content": "test"}]
        )
        db_session.add(workflow)
        db_session.commit()
        db_session.refresh(workflow)
        
        assert workflow.id is not None
        assert workflow.session_id == test_session.id
        assert workflow.current_step == "document_upload"
        assert workflow.step_data == {"test": "data"}
        assert workflow.conversation_history == [{"role": "user", "content": "test"}]
    
    def test_workflow_state_relationship(self, db_session, test_session):
        """Test workflow state relationship to session."""
        workflow = WorkflowState(
            session_id=test_session.id,
            current_step="document_upload"
        )
        db_session.add(workflow)
        db_session.commit()
        db_session.refresh(workflow)
        
        # Test relationship
        assert workflow.session is not None
        assert workflow.session.id == test_session.id


class TestChatMessageModel:
    """Test ChatMessage model functionality."""
    
    def test_create_chat_message(self, db_session, test_session):
        """Test creating a chat message."""
        message = ChatMessage(
            session_id=test_session.id,
            message_type="user",
            content="Test message",
            agent_name=None
        )
        db_session.add(message)
        db_session.commit()
        db_session.refresh(message)
        
        assert message.id is not None
        assert message.session_id == test_session.id
        assert message.message_type == "user"
        assert message.content == "Test message"
        assert message.agent_name is None
    
    def test_chat_message_relationship(self, db_session, test_session):
        """Test chat message relationship to session."""
        message = ChatMessage(
            session_id=test_session.id,
            message_type="user",
            content="Test message"
        )
        db_session.add(message)
        db_session.commit()
        db_session.refresh(message)
        
        # Test relationship
        assert message.session is not None
        assert message.session.id == test_session.id
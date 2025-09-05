"""
Test cases for database models
"""
import pytest
from datetime import datetime, timedelta
from sqlalchemy.exc import IntegrityError

from database import User, UserSession, Document, DocumentChunk, Claim, Vendor, WorkflowState, ChatMessage as DBChatMessage


class TestUserModel:
    """Test User model functionality."""
    
    def test_create_user(self, db_session):
        """Test creating a user."""
        user = User(
            email="test@example.com",
            hashed_password="hashed_password",
            full_name="Test User"
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
    
    def test_user_email_unique(self, db_session):
        """Test user email uniqueness constraint."""
        user1 = User(
            email="test@example.com",
            hashed_password="hashed_password1",
            full_name="Test User 1"
        )
        user2 = User(
            email="test@example.com",
            hashed_password="hashed_password2",
            full_name="Test User 2"
        )
        
        db_session.add(user1)
        db_session.commit()
        
        db_session.add(user2)
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
            session_token="test-session-token",
            is_active=True,
            expires_at=datetime.utcnow() + timedelta(hours=24)
        )
        db_session.add(session)
        db_session.commit()
        db_session.refresh(session)
        
        assert session.id is not None
        assert session.user_id == test_user.id
        assert session.session_token == "test-session-token"
        assert session.is_active is True
        assert session.expires_at is not None
    
    def test_user_session_relationship(self, db_session, test_user):
        """Test user session relationship."""
        session = UserSession(
            user_id=test_user.id,
            session_token="test-session-token",
            is_active=True,
            expires_at=datetime.utcnow() + timedelta(hours=24)
        )
        db_session.add(session)
        db_session.commit()
        db_session.refresh(session)
        
        # Test relationship
        assert session.user == test_user


class TestDocumentModel:
    """Test Document model functionality."""
    
    def test_create_document(self, db_session, test_user, test_session):
        """Test creating a document."""
        document = Document(
            user_id=test_user.id,
            session_id=test_session.id,
            filename="test.pdf",
            original_filename="original_test.pdf",
            file_path="/uploads/test.pdf",
            file_type="policy",
            file_size=1024
        )
        db_session.add(document)
        db_session.commit()
        db_session.refresh(document)
        
        assert document.id is not None
        assert document.user_id == test_user.id
        assert document.session_id == test_session.id
        assert document.filename == "test.pdf"
        assert document.original_filename == "original_test.pdf"
        assert document.file_type == "policy"
        assert document.file_size == 1024
    
    def test_document_relationships(self, db_session, test_user, test_session):
        """Test document relationships."""
        document = Document(
            user_id=test_user.id,
            session_id=test_session.id,
            filename="test.pdf",
            original_filename="original_test.pdf",
            file_path="/uploads/test.pdf",
            file_type="policy",
            file_size=1024
        )
        db_session.add(document)
        db_session.commit()
        db_session.refresh(document)
        
        # Test relationships
        assert document.user == test_user
        assert document.session == test_session


class TestDocumentChunkModel:
    """Test DocumentChunk model functionality."""
    
    def test_create_document_chunk(self, db_session, test_document):
        """Test creating a document chunk."""
        chunk = DocumentChunk(
            document_id=test_document.id,
            chunk_index=0,
            content="This is a test chunk",
            chunk_metadata={"type": "coverage_info"},
            chunk_type="coverage_info"
        )
        db_session.add(chunk)
        db_session.commit()
        db_session.refresh(chunk)
        
        assert chunk.id is not None
        assert chunk.document_id == test_document.id
        assert chunk.chunk_index == 0
        assert chunk.content == "This is a test chunk"
        assert chunk.chunk_type == "coverage_info"
        assert chunk.created_at is not None
    
    def test_document_chunk_relationship(self, db_session, test_document):
        """Test document chunk relationship."""
        chunk = DocumentChunk(
            document_id=test_document.id,
            chunk_index=0,
            content="This is a test chunk",
            chunk_metadata={"type": "coverage_info"},
            chunk_type="coverage_info"
        )
        db_session.add(chunk)
        db_session.commit()
        db_session.refresh(chunk)
        
        # Test relationship
        assert chunk.document == test_document


class TestClaimModel:
    """Test Claim model functionality."""
    
    def test_create_claim(self, db_session, test_user, test_session):
        """Test creating a claim."""
        claim = Claim(
            user_id=test_user.id,
            session_id=test_session.id,
            status="initiated",
            claim_data={"test": "data"},
            form_data={"form": "data"}
        )
        db_session.add(claim)
        db_session.commit()
        db_session.refresh(claim)
        
        assert claim.id is not None
        assert claim.user_id == test_user.id
        assert claim.session_id == test_session.id
        assert claim.status == "initiated"
        assert claim.claim_data == {"test": "data"}
        assert claim.form_data == {"form": "data"}
        assert claim.created_at is not None
    
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
        assert claim.user == test_user
        assert claim.session == test_session


class TestVendorModel:
    """Test Vendor model functionality."""
    
    def test_create_vendor(self, db_session):
        """Test creating a vendor."""
        vendor = Vendor(
            name="test_insurance",
            display_name="Test Insurance Company",
            form_template_url="http://example.com/template.pdf"
        )
        db_session.add(vendor)
        db_session.commit()
        db_session.refresh(vendor)
        
        assert vendor.id is not None
        assert vendor.name == "test_insurance"
        assert vendor.display_name == "Test Insurance Company"
        assert vendor.form_template_url == "http://example.com/template.pdf"
        assert vendor.is_active is True
        assert vendor.created_at is not None
    
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


class TestWorkflowStateModel:
    """Test WorkflowState model functionality."""
    
    def test_create_workflow_state(self, db_session, test_session):
        """Test creating a workflow state."""
        workflow = WorkflowState(
            session_id=test_session.id,
            current_step="document_upload",
            step_data={"uploaded_files": 2},
            conversation_history={"messages": []},
            agent_context={"current_agent": "document_analyzer"}
        )
        db_session.add(workflow)
        db_session.commit()
        db_session.refresh(workflow)
        
        assert workflow.id is not None
        assert workflow.session_id == test_session.id
        assert workflow.current_step == "document_upload"
        assert workflow.step_data == {"uploaded_files": 2}
        assert workflow.created_at is not None
        assert workflow.updated_at is not None
    
    def test_workflow_state_relationship(self, db_session, test_session):
        """Test workflow state relationship."""
        workflow = WorkflowState(
            session_id=test_session.id,
            current_step="document_upload"
        )
        db_session.add(workflow)
        db_session.commit()
        db_session.refresh(workflow)
        
        # Test relationship
        assert workflow.session == test_session


class TestChatMessageModel:
    """Test ChatMessage model functionality."""
    
    def test_create_chat_message(self, db_session, test_session):
        """Test creating a chat message."""
        message = DBChatMessage(
            session_id=test_session.id,
            message_type="user",
            content="Hello, I need help with my claim",
            agent_name="chat_assistant",
            message_metadata={"timestamp": "2024-01-01T00:00:00Z"}
        )
        db_session.add(message)
        db_session.commit()
        db_session.refresh(message)
        
        assert message.id is not None
        assert message.session_id == test_session.id
        assert message.message_type == "user"
        assert message.content == "Hello, I need help with my claim"
        assert message.agent_name == "chat_assistant"
        assert message.created_at is not None
    
    def test_chat_message_relationship(self, db_session, test_session):
        """Test chat message relationship."""
        message = DBChatMessage(
            session_id=test_session.id,
            message_type="user",
            content="Hello, I need help with my claim"
        )
        db_session.add(message)
        db_session.commit()
        db_session.refresh(message)
        
        # Test relationship
        assert message.session == test_session
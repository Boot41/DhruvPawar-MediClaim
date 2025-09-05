"""
Pytest configuration and fixtures for medclaim-ai backend tests
"""
import pytest
import asyncio
import tempfile
import os
import shutil
from typing import Generator, AsyncGenerator
from unittest.mock import Mock, AsyncMock, patch
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Import the main app and database models
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app
from database import Base, User, UserSession, Document, DocumentChunk, Claim, Vendor, WorkflowState, ChatMessage
from database_connection import get_db
from auth import get_password_hash, create_access_token
from schemas import UserCreate, UserLogin

# Test database URL
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_medclaim.db"

# Create test engine
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database session for each test."""
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    # Create session
    session = TestingSessionLocal()
    
    try:
        yield session
    finally:
        session.close()
        # Drop all tables after test
        Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client(db_session):
    """Create a test client with database dependency override."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

@pytest.fixture
def test_user(db_session):
    """Create a test user."""
    user = User(
        email="test@example.com",
        hashed_password=get_password_hash("testpassword"),
        full_name="Test User",
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture
def test_user_2(db_session):
    """Create a second test user."""
    user = User(
        email="test2@example.com",
        hashed_password=get_password_hash("testpassword2"),
        full_name="Test User 2",
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture
def test_user_inactive(db_session):
    """Create an inactive test user."""
    user = User(
        email="inactive@example.com",
        hashed_password=get_password_hash("testpassword"),
        full_name="Inactive User",
        is_active=False
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture
def auth_headers(test_user):
    """Create authentication headers for test user."""
    token = create_access_token(data={"sub": test_user.id})
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def test_session(db_session, test_user):
    """Create a test user session."""
    session = UserSession(
        user_id=test_user.id,
        session_token="test-session-token",
        is_active=True
    )
    db_session.add(session)
    db_session.commit()
    db_session.refresh(session)
    return session

@pytest.fixture
def test_document(db_session, test_user, test_session):
    """Create a test document."""
    document = Document(
        user_id=test_user.id,
        session_id=test_session.id,
        filename="test-document.pdf",
        original_filename="test-document.pdf",
        file_path="/uploads/documents/test-document.pdf",
        file_type="policy",
        file_size=1024,
        upload_status="processed",
        extracted_data={"policy_number": "POL123", "insurer_name": "Test Insurance"}
    )
    db_session.add(document)
    db_session.commit()
    db_session.refresh(document)
    return document

@pytest.fixture
def test_document_chunks(db_session, test_document):
    """Create test document chunks."""
    chunks = []
    for i in range(3):
        chunk = DocumentChunk(
            document_id=test_document.id,
            chunk_index=i,
            content=f"Test chunk content {i}",
            metadata={"chunk_type": "policy_info", "chunk_size": 100},
            chunk_type="policy_info"
        )
        db_session.add(chunk)
        chunks.append(chunk)
    
    db_session.commit()
    for chunk in chunks:
        db_session.refresh(chunk)
    return chunks

@pytest.fixture
def test_vendor(db_session):
    """Create a test vendor."""
    vendor = Vendor(
        name="test_insurance",
        display_name="Test Insurance Company",
        form_template_url="https://example.com/template.pdf",
        is_active=True
    )
    db_session.add(vendor)
    db_session.commit()
    db_session.refresh(vendor)
    return vendor

@pytest.fixture
def test_claim(db_session, test_user, test_session):
    """Create a test claim."""
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
    return claim

@pytest.fixture
def test_workflow_state(db_session, test_session):
    """Create a test workflow state."""
    workflow = WorkflowState(
        session_id=test_session.id,
        current_step="document_upload",
        step_data={"test": "data"},
        conversation_history=[{"role": "user", "content": "test message"}]
    )
    db_session.add(workflow)
    db_session.commit()
    db_session.refresh(workflow)
    return workflow

@pytest.fixture
def temp_upload_dir():
    """Create a temporary upload directory for testing."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)

@pytest.fixture
def mock_file():
    """Create a mock file for testing uploads."""
    mock_file = Mock()
    mock_file.filename = "test.pdf"
    mock_file.content_type = "application/pdf"
    mock_file.size = 1024
    mock_file.read = AsyncMock(return_value=b"test file content")
    mock_file.seek = Mock()
    return mock_file

@pytest.fixture
def mock_agent_service():
    """Mock the agent service for testing."""
    with patch('main.agent_service') as mock:
        mock.process_document = AsyncMock(return_value={
            "success": True,
            "extracted_data": {"test": "data"},
            "total_chunks": 3
        })
        mock.chat_with_agent = AsyncMock(return_value={
            "success": True,
            "response": "Test response",
            "agent_name": "test_agent"
        })
        mock.generate_claim_form = AsyncMock(return_value={
            "success": True,
            "form_data": {"test": "form"},
            "preview_html": "<html>test</html>",
            "missing_fields": []
        })
        mock.generate_synthetic_claim_form = AsyncMock(return_value={
            "success": True,
            "form_data": {"test": "synthetic"},
            "preview_html": "<html>synthetic</html>",
            "missing_fields": [],
            "pdf_path": "/test/path.pdf",
            "pdf_filename": "test.pdf"
        })
        mock.generate_vendor_claim_form = AsyncMock(return_value={
            "success": True,
            "form_data": {"test": "vendor"},
            "preview_html": "<html>vendor</html>",
            "missing_fields": [],
            "pdf_path": "/test/vendor.pdf",
            "pdf_filename": "vendor.pdf"
        })
        yield mock

@pytest.fixture
def mock_file_handler():
    """Mock the file handler for testing."""
    with patch('main.file_handler') as mock:
        mock.save_file = AsyncMock(return_value={
            "success": True,
            "filename": "test.pdf",
            "original_filename": "test.pdf",
            "file_path": "/uploads/test.pdf",
            "file_size": 1024
        })
        yield mock

@pytest.fixture
def sample_pdf_content():
    """Sample PDF content for testing."""
    return b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n/Contents 4 0 R\n>>\nendobj\n4 0 obj\n<<\n/Length 44\n>>\nstream\nBT\n/F1 12 Tf\n72 720 Td\n(Test PDF Content) Tj\nET\nendstream\nendobj\nxref\n0 5\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \n0000000204 00000 n \ntrailer\n<<\n/Size 5\n/Root 1 0 R\n>>\nstartxref\n297\n%%EOF"

@pytest.fixture
def sample_document_processor():
    """Mock document processor for testing."""
    with patch('document_processor.document_processor') as mock:
        mock.process_insurance_document = AsyncMock(return_value={
            "success": True,
            "document_id": "test-doc-id",
            "document_type": "policy",
            "text": "Sample policy text",
            "chunks": [
                {
                    "chunk_index": 0,
                    "content": "Policy chunk 1",
                    "metadata": {"chunk_type": "policy_info"}
                }
            ],
            "total_chunks": 1,
            "parser": "basic"
        })
        yield mock

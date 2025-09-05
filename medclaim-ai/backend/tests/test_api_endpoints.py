"""
Test cases for API endpoints
"""
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from main import app


class TestAuthEndpoints:
    """Test authentication endpoints."""
    
    def test_register_user_success(self, client):
        """Test successful user registration."""
        user_data = {
            "email": "test@example.com",
            "password": "testpassword123",
            "full_name": "Test User"
        }
        response = client.post("/auth/register", json=user_data)
        assert response.status_code == 201
        assert "id" in response.json()
        assert response.json()["email"] == "test@example.com"
    
    def test_register_user_duplicate_email(self, client, test_user):
        """Test registration with duplicate email."""
        user_data = {
            "email": test_user.email,
            "password": "testpassword123",
            "full_name": "Test User"
        }
        response = client.post("/auth/register", json=user_data)
        assert response.status_code == 400
        assert "email already registered" in response.json()["detail"]
    
    def test_login_success(self, client, test_user):
        """Test successful login."""
        login_data = {
            "username": test_user.email,
            "password": "testpassword123"
        }
        response = client.post("/auth/login", data=login_data)
        assert response.status_code == 200
        assert "access_token" in response.json()
        assert response.json()["token_type"] == "bearer"
    
    def test_login_invalid_credentials(self, client):
        """Test login with invalid credentials."""
        login_data = {
            "username": "nonexistent@example.com",
            "password": "wrongpassword"
        }
        response = client.post("/auth/login", data=login_data)
        assert response.status_code == 401
        assert "incorrect email or password" in response.json()["detail"]


class TestDocumentEndpoints:
    """Test document endpoints."""
    
    def test_upload_document_success(self, client, auth_headers, test_session):
        """Test successful document upload."""
        with patch("file_handler.file_handler.validate_file") as mock_validate:
            mock_validate.return_value = {"filename": "test.pdf", "file_size": 1024}
            response = client.post(
                "/api/documents/upload",
                headers=auth_headers,
                data={"file_type": "policy", "session_id": test_session.id},
                files={"file": ("test.pdf", b"test content", "application/pdf")}
            )
            assert response.status_code == 201
            assert "filename" in response.json()
    
    def test_upload_document_invalid_file_type(self, client, auth_headers, test_session):
        """Test document upload with invalid file type."""
        response = client.post(
            "/api/documents/upload",
            headers=auth_headers,
            data={"file_type": "invalid", "session_id": test_session.id},
            files={"file": ("test.txt", b"test content", "text/plain")}
        )
        assert response.status_code == 400
    
    def test_get_documents(self, client, auth_headers, test_session):
        """Test getting user documents."""
        response = client.get(
            f"/api/documents?session_id={test_session.id}",
            headers=auth_headers
        )
        assert response.status_code == 200
        assert isinstance(response.json(), list)
    
    def test_get_document_summary(self, client, auth_headers, test_session):
        """Test getting document summary."""
        response = client.get(
            f"/api/documents/summary?session_id={test_session.id}",
            headers=auth_headers
        )
        assert response.status_code == 200


class TestClaimEndpoints:
    """Test claim endpoints."""
    
    def test_generate_claim_form(self, client, auth_headers, test_session):
        """Test generating claim form."""
        response = client.post(
            f"/api/claims/generate-form?session_id={test_session.id}",
            headers=auth_headers
        )
        assert response.status_code == 200
        assert "form_preview" in response.json()
    
    def test_generate_synthetic_claim(self, client, auth_headers, test_session):
        """Test generating synthetic claim."""
        response = client.post(
            f"/api/claims/generate-synthetic?session_id={test_session.id}",
            headers=auth_headers
        )
        assert response.status_code == 200
        assert "form_preview" in response.json()
    
    def test_generate_vendor_claim(self, client, auth_headers, test_session):
        """Test generating vendor-specific claim."""
        response = client.post(
            f"/api/claims/generate-vendor?session_id={test_session.id}",
            headers=auth_headers
        )
        assert response.status_code == 200
        assert "form_preview" in response.json()
    
    def test_submit_claim(self, client, auth_headers, test_session):
        """Test submitting claim."""
        claim_data = {
            "claim_data": {"test": "data"},
            "form_data": {"test": "data"}
        }
        response = client.post(
            f"/api/claims/submit?session_id={test_session.id}",
            headers=auth_headers,
            json=claim_data
        )
        assert response.status_code == 200
        assert "success" in response.json()


class TestChatEndpoints:
    """Test chat endpoints."""
    
    def test_send_message_success(self, client, auth_headers, test_session):
        """Test successful message sending."""
        message_data = {
            "message": "Hello, I need help with my claim",
            "session_id": test_session.id
        }
        response = client.post(
            "/api/chat",
            headers=auth_headers,
            json=message_data
        )
        assert response.status_code == 200
        assert "response" in response.json()
    
    def test_get_chat_history(self, client, auth_headers, test_session):
        """Test getting chat history."""
        response = client.get(
            f"/api/chat/history/{test_session.id}",
            headers=auth_headers
        )
        assert response.status_code == 200
        assert isinstance(response.json(), list)


class TestVendorEndpoints:
    """Test vendor endpoints."""
    
    def test_get_vendors(self, client, auth_headers):
        """Test getting vendors."""
        response = client.get("/api/vendors", headers=auth_headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)


class TestWorkflowEndpoints:
    """Test workflow endpoints."""
    
    def test_get_workflow_state(self, client, auth_headers, test_session):
        """Test getting workflow state."""
        response = client.get(
            f"/api/workflow/{test_session.id}",
            headers=auth_headers
        )
        assert response.status_code == 200
        assert "current_step" in response.json()
    
    def test_update_workflow_state(self, client, auth_headers, test_session):
        """Test updating workflow state."""
        update_data = {
            "current_step": "claim_generation",
            "step_data": {"test": "data"}
        }
        response = client.post(
            f"/api/workflow/{test_session.id}/update",
            headers=auth_headers,
            json=update_data
        )
        assert response.status_code == 200
        assert "success" in response.json()
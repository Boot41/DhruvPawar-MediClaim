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
        response = client.post("/api/auth/register", json=user_data)
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
        response = client.post("/api/auth/register", json=user_data)
        assert response.status_code == 400
        assert "email already registered" in response.json()["detail"]
    
    def test_login_success(self, client, test_user):
        """Test successful login."""
        login_data = {
            "username": test_user.email,
            "password": "testpassword123"
        }
        response = client.post("/api/auth/login", data=login_data)
        assert response.status_code == 200
        assert "access_token" in response.json()
        assert response.json()["token_type"] == "bearer"
    
    def test_login_invalid_credentials(self, client):
        """Test login with invalid credentials."""
        login_data = {
            "username": "nonexistent@example.com",
            "password": "wrongpassword"
        }
        response = client.post("/api/auth/login", data=login_data)
        assert response.status_code == 401
        assert "incorrect email or password" in response.json()["detail"]


class TestDocumentEndpoints:
    """Test document endpoints."""
    
    def test_upload_document_success(self, client, auth_headers, test_session):
        """Test successful document upload."""
        with patch("main.upload_file", return_value="test.pdf"):
            response = client.post(
                "/api/documents/upload",
                headers=auth_headers,
                data={"file_type": "policy", "session_id": test_session.id},
                files={"file": ("test.pdf", b"test content", "application/pdf")}
            )
            assert response.status_code == 201
            assert response.json()["filename"] == "test.pdf"
    
    def test_upload_document_invalid_file_type(self, client, auth_headers, test_session):
        """Test document upload with invalid file type."""
        response = client.post(
            "/api/documents/upload",
            headers=auth_headers,
            data={"file_type": "invalid", "session_id": test_session.id},
            files={"file": ("test.txt", b"test content", "text/plain")}
        )
        assert response.status_code == 400
        assert "Invalid file type" in response.json()["detail"]
    
    def test_get_documents(self, client, auth_headers, test_session):
        """Test getting user documents."""
        response = client.get(
            f"/api/documents/?session_id={test_session.id}",
            headers=auth_headers
        )
        assert response.status_code == 200
        assert isinstance(response.json(), list)
    
    def test_delete_document_success(self, client, auth_headers, test_document):
        """Test successful document deletion."""
        response = client.delete(
            f"/api/documents/{test_document.id}",
            headers=auth_headers
        )
        assert response.status_code == 200
        assert response.json()["message"] == "Document deleted successfully"
    
    def test_delete_document_not_found(self, client, auth_headers):
        """Test deleting non-existent document."""
        response = client.delete(
            "/api/documents/999",
            headers=auth_headers
        )
        assert response.status_code == 404
        assert "Document not found" in response.json()["detail"]


class TestClaimEndpoints:
    """Test claim endpoints."""
    
    def test_create_claim_success(self, client, auth_headers, test_session):
        """Test successful claim creation."""
        claim_data = {
            "claim_data": {"test": "data"},
            "form_data": {"test": "data"}
        }
        response = client.post(
            f"/api/claims/?session_id={test_session.id}",
            headers=auth_headers,
            json=claim_data
        )
        assert response.status_code == 201
        assert response.json()["status"] == "initiated"
    
    def test_get_claims(self, client, auth_headers, test_session):
        """Test getting user claims."""
        response = client.get(
            f"/api/claims/?session_id={test_session.id}",
            headers=auth_headers
        )
        assert response.status_code == 200
        assert isinstance(response.json(), list)
    
    def test_get_claim_by_id(self, client, auth_headers, test_claim):
        """Test getting claim by ID."""
        response = client.get(
            f"/api/claims/{test_claim.id}",
            headers=auth_headers
        )
        assert response.status_code == 200
        assert response.json()["id"] == test_claim.id
    
    def test_update_claim_status(self, client, auth_headers, test_claim):
        """Test updating claim status."""
        update_data = {"status": "processing"}
        response = client.put(
            f"/api/claims/{test_claim.id}",
            headers=auth_headers,
            json=update_data
        )
        assert response.status_code == 200
        assert response.json()["status"] == "processing"


class TestChatEndpoints:
    """Test chat endpoints."""
    
    def test_send_message_success(self, client, auth_headers, test_session):
        """Test successful message sending."""
        message_data = {
            "message_type": "user",
            "content": "Hello, I need help with my claim"
        }
        response = client.post(
            f"/api/chat/send?session_id={test_session.id}",
            headers=auth_headers,
            json=message_data
        )
        assert response.status_code == 200
        assert "message" in response.json()
    
    def test_get_chat_history(self, client, auth_headers, test_session):
        """Test getting chat history."""
        response = client.get(
            f"/api/chat/history?session_id={test_session.id}",
            headers=auth_headers
        )
        assert response.status_code == 200
        assert isinstance(response.json(), list)
"""
Integration test cases for the medclaim-ai backend
"""
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from main import app
from database import User, UserSession, Document, Claim


class TestUserWorkflow:
    """Test complete user workflow."""
    
    def test_user_registration_and_login(self, client):
        """Test user registration and login flow."""
        # Register user
        user_data = {
            "email": "test@example.com",
            "password": "testpassword123",
            "full_name": "Test User"
        }
        response = client.post("/api/auth/register", json=user_data)
        assert response.status_code == 201
        
        # Login user
        login_data = {
            "username": "test@example.com",
            "password": "testpassword123"
        }
        response = client.post("/api/auth/login", data=login_data)
        assert response.status_code == 200
        assert "access_token" in response.json()
    
    def test_document_upload_workflow(self, client, auth_headers):
        """Test document upload workflow."""
        # Create session
        response = client.post("/api/sessions/", headers=auth_headers)
        assert response.status_code == 201
        session_id = response.json()["id"]
        
        # Upload document
        with patch("main.upload_file", return_value="test.pdf"):
            response = client.post(
                "/api/documents/upload",
                headers=auth_headers,
                data={"file_type": "policy", "session_id": session_id},
                files={"file": ("test.pdf", b"test content", "application/pdf")}
            )
            assert response.status_code == 201
            assert response.json()["filename"] == "test.pdf"
    
    def test_claim_creation_workflow(self, client, auth_headers, test_session):
        """Test claim creation workflow."""
        # Create claim
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
    
    def test_chat_workflow(self, client, auth_headers, test_session):
        """Test chat workflow."""
        # Send message
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
    
    def test_workflow_state_management(self, client, auth_headers, test_session):
        """Test workflow state management."""
        # Get workflow state
        response = client.get(
            f"/api/workflow/state?session_id={test_session.id}",
            headers=auth_headers
        )
        assert response.status_code == 200
        assert "current_step" in response.json()
        
        # Update workflow state
        update_data = {
            "current_step": "document_upload",
            "step_data": {"test": "data"}
        }
        response = client.put(
            f"/api/workflow/state?session_id={test_session.id}",
            headers=auth_headers,
            json=update_data
        )
        assert response.status_code == 200
        assert response.json()["current_step"] == "document_upload"
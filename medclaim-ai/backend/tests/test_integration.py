"""
Integration tests for the complete workflow
"""
import pytest
from unittest.mock import patch, Mock
from fastapi.testclient import TestClient

from main import app


class TestUserWorkflow:
    """Test complete user workflow integration."""
    
    def test_user_registration_and_login(self, client):
        """Test user registration and login workflow."""
        # Register a new user
        user_data = {
            "email": "integration@example.com",
            "password": "testpassword123",
            "full_name": "Integration Test User"
        }
        
        register_response = client.post("/auth/register", json=user_data)
        assert register_response.status_code == 201
        
        # Login with the registered user
        login_data = {
            "username": user_data["email"],
            "password": user_data["password"]
        }
        
        login_response = client.post("/auth/login", data=login_data)
        assert login_response.status_code == 200
        assert "access_token" in login_response.json()
        
        return login_response.json()["access_token"]
    
    def test_document_upload_workflow(self, client, auth_headers, test_session):
        """Test document upload workflow."""
        with patch("file_handler.file_handler.validate_file") as mock_validate:
            mock_validate.return_value = {
                "success": True,
                "filename": "test_policy.pdf",
                "file_size": 1024,
                "file_type": "application/pdf"
            }
            
            response = client.post(
                "/api/documents/upload",
                headers=auth_headers,
                data={"file_type": "policy", "session_id": test_session.id},
                files={"file": ("test_policy.pdf", b"test content", "application/pdf")}
            )
            
            assert response.status_code == 201
            assert "filename" in response.json()
    
    def test_claim_creation_workflow(self, client, auth_headers, test_session):
        """Test claim creation workflow."""
        # First generate a claim form
        with patch("agent_service.agent_service.generate_claim_form") as mock_generate:
            mock_generate.return_value = {
                "success": True,
                "form_data": {"patient_name": "John Doe", "policy_number": "POL123"}
            }
            
            response = client.post(
                f"/api/claims/generate-form?session_id={test_session.id}",
                headers=auth_headers
            )
            
            assert response.status_code == 200
            assert "form_preview" in response.json()
        
        # Then submit the claim
        claim_data = {
            "claim_data": {"patient_name": "John Doe", "policy_number": "POL123"},
            "form_data": {"form": "data"}
        }
        
        response = client.post(
            f"/api/claims/submit?session_id={test_session.id}",
            headers=auth_headers,
            json=claim_data
        )
        
        assert response.status_code == 200
        assert "success" in response.json()
    
    def test_chat_workflow(self, client, auth_headers, test_session):
        """Test chat workflow."""
        with patch("agent_service.agent_service.chat_with_agent") as mock_chat:
            mock_chat.return_value = {
                "success": True,
                "response": "Hello! How can I help you with your insurance claim?"
            }
            
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
    
    def test_workflow_state_management(self, client, auth_headers, test_session):
        """Test workflow state management."""
        # Get current workflow state
        response = client.get(
            f"/api/workflow/{test_session.id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        assert "current_step" in response.json()
        
        # Update workflow state
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
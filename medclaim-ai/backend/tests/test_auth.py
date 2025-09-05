"""
Test cases for authentication functionality
"""
import pytest
from unittest.mock import patch, Mock
from fastapi.security import HTTPAuthorizationCredentials
from fastapi import HTTPException

from auth import (
    get_password_hash, verify_password, create_access_token, 
    verify_token, get_current_user, require_active_user
)
from database import User


class TestPasswordHashing:
    """Test password hashing functionality."""
    
    def test_verify_password_correct(self):
        """Test password verification with correct password."""
        password = "testpassword123"
        hashed = get_password_hash(password)
        
        assert verify_password(password, hashed) is True
    
    def test_verify_password_incorrect(self):
        """Test password verification with incorrect password."""
        password = "testpassword123"
        wrong_password = "wrongpassword"
        hashed = get_password_hash(password)
        
        assert verify_password(wrong_password, hashed) is False
    
    def test_get_password_hash(self):
        """Test password hashing."""
        password = "testpassword123"
        hashed = get_password_hash(password)
        
        assert hashed != password
        assert len(hashed) > 0
        assert isinstance(hashed, str)


class TestTokenOperations:
    """Test JWT token operations."""
    
    def test_create_access_token(self):
        """Test access token creation."""
        data = {"sub": "test@example.com"}
        token = create_access_token(data)
        
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0
    
    def test_verify_token_valid(self):
        """Test token verification with valid token."""
        data = {"sub": "test@example.com"}
        token = create_access_token(data)
        
        payload = verify_token(token)
        
        assert payload is not None
        assert payload["sub"] == "test@example.com"
    
    def test_verify_token_invalid(self):
        """Test token verification with invalid token."""
        invalid_token = "invalid.token.here"
        
        payload = verify_token(invalid_token)
        
        assert payload is None


class TestUserAuthentication:
    """Test user authentication functionality."""
    
    def test_get_current_user_success(self, db_session, test_user):
        """Test getting current user with valid token."""
        # Create a valid token with user ID (not email)
        data = {"sub": test_user.id}  # Changed from email to user ID
        token = create_access_token(data)
        
        # Create mock credentials
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
        
        # Test the function
        user = get_current_user(credentials, db_session)
        
        assert user is not None
        assert user.email == test_user.email
        assert user.id == test_user.id
    
    def test_get_current_user_not_found(self, db_session):
        """Test getting current user with non-existent user ID."""
        # Create a token for non-existent user ID
        data = {"sub": "nonexistent-user-id"}
        token = create_access_token(data)
        
        # Create mock credentials
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
        
        # Test the function - should raise HTTPException
        with pytest.raises(HTTPException) as exc_info:
            get_current_user(credentials, db_session)
        
        assert exc_info.value.status_code == 401
    
    def test_require_active_user_success(self, test_user):
        """Test requiring active user with active user."""
        result = require_active_user(test_user)
        
        assert result == test_user
    
    def test_require_active_user_inactive(self, db_session):
        """Test requiring active user with inactive user."""
        # Create an inactive user
        inactive_user = User(
            email="inactive@example.com",
            hashed_password="hashed_password",
            full_name="Inactive User",
            is_active=False
        )
        db_session.add(inactive_user)
        db_session.commit()
        db_session.refresh(inactive_user)
        
        # Test the function - should raise HTTPException
        with pytest.raises(HTTPException) as exc_info:
            require_active_user(inactive_user)
        
        assert exc_info.value.status_code == 400
        assert "inactive" in exc_info.value.detail.lower()
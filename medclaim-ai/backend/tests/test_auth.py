"""
Test cases for authentication functionality
"""
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
from jose import jwt
from passlib.context import CryptContext

from auth import (
    verify_password, get_password_hash, create_access_token,
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


class TestTokenOperations:
    """Test JWT token operations."""
    
    def test_create_access_token(self):
        """Test creating access token."""
        data = {"sub": "test@example.com"}
        token = create_access_token(data)
        assert isinstance(token, str)
        assert len(token) > 0
    
    def test_verify_token_valid(self):
        """Test verifying valid token."""
        data = {"sub": "test@example.com"}
        token = create_access_token(data)
        payload = verify_token(token)
        assert payload is not None
        assert payload["sub"] == "test@example.com"
    
    def test_verify_token_invalid(self):
        """Test verifying invalid token."""
        invalid_token = "invalid.token.here"
        payload = verify_token(invalid_token)
        assert payload is None


class TestUserAuthentication:
    """Test user authentication functions."""
    
    def test_get_current_user_success(self, db_session, test_user):
        """Test getting current user successfully."""
        with patch('auth.verify_token', return_value={"sub": test_user.email}):
            user = get_current_user(db_session, test_user.email)
            assert user is not None
            assert user.id == test_user.id
            assert user.email == test_user.email
    
    def test_get_current_user_not_found(self, db_session):
        """Test getting current user when user not found."""
        with patch('auth.verify_token', return_value={"sub": "nonexistent@example.com"}):
            user = get_current_user(db_session, "nonexistent@example.com")
            assert user is None
    
    def test_require_active_user_success(self, test_user):
        """Test requiring active user with active user."""
        user = require_active_user(test_user)
        assert user is not None
        assert user.id == test_user.id
    
    def test_require_active_user_inactive(self, db_session):
        """Test requiring active user with inactive user."""
        inactive_user = User(
            email="inactive@example.com",
            hashed_password="hashed",
            is_active=False
        )
        db_session.add(inactive_user)
        db_session.commit()
        
        with pytest.raises(Exception):
            require_active_user(inactive_user)
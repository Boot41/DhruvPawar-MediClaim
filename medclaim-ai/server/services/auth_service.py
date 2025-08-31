"""
JWT Authentication Service
Handles JWT token generation, validation, and user authentication.
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from server.config.database import get_db
import os

# JWT Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

security = HTTPBearer()

class AuthService:
    """JWT Authentication Service"""

    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token"""
        to_encode = data.copy()
        expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify JWT token and return payload"""
        try:
            return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        except JWTError:
            return None

    async def authenticate_user(self, db: Session, email: str, password: str) -> Dict[str, Any]:
        """Authenticate user and return token data"""
        from server.business_logic.user_service import user_service  # local import to avoid circular dependency

        user = await user_service.get_user_by_email(db, email)
        if not user:
            raise HTTPException(status_code=401, detail="Invalid email or password")

        if not user.is_active:
            raise HTTPException(status_code=403, detail="Account is deactivated")

        if not await user_service.verify_password(password, user.password_hash):
            raise HTTPException(status_code=401, detail="Invalid email or password")

        await user_service.update_last_login(db, user.id)

        access_token = self.create_access_token(
            data={"sub": str(user.id), "email": user.email, "role": user.role.lower()}
        )

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "user": {
                "id": str(user.id),
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "role": user.role.lower()
            }
        }

    async def get_current_user(
        self,
        credentials: HTTPAuthorizationCredentials = Depends(security),
        db: Session = Depends(get_db)
    ):
        """Get current authenticated user"""
        payload = self.verify_token(credentials.credentials)
        if not payload:
            raise HTTPException(status_code=401, detail="Could not validate credentials")

        user_id: str = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")

        from server.business_logic.user_service import user_service
        user = await user_service.get_user_by_id(db, user_id)
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        if not user.is_active:
            raise HTTPException(status_code=403, detail="Account is deactivated")

        return user

    async def require_admin(self, current_user=Depends(get_current_user)):
        """Require admin role"""
        if current_user.role.lower() != "admin":
            raise HTTPException(status_code=403, detail="Admin access required")
        return current_user

    async def require_agent_or_admin(self, current_user=Depends(get_current_user)):
        """Require agent or admin role"""
        if current_user.role.lower() not in ["agent", "admin"]:
            raise HTTPException(status_code=403, detail="Agent or admin access required")
        return current_user


# Singleton instance
auth_service = AuthService()

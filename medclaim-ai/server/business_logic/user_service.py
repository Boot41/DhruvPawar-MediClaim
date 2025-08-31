# server/business_logic/user_service.py
from sqlalchemy.orm import Session
from datetime import datetime
import uuid
from passlib.context import CryptContext
from server.schemas.schemas import UserCreate
from server.services import auth_service


class UserService:
    """Service class for user operations"""

    def _hash_password(self, password: str) -> str:
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        return pwd_context.hash(password)

    async def create_user(self, db: Session, user_data: UserCreate):
        """Register new user"""
        from server.models.models import User
        existing_user = db.query(User).filter(User.email == user_data.email).first()
        if existing_user:
            raise Exception("User with this email already exists")

        hashed_password = self._hash_password(user_data.password)

        user = User(
            id=uuid.uuid4(),
            email=user_data.email,
            password_hash=hashed_password,
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            phone=user_data.phone,
            date_of_birth=user_data.date_of_birth,
            address=user_data.address,
            role=user_data.role if getattr(user_data, "role", None) else None,
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    async def get_user_by_email(self, db: Session, email: str):
        """Retrieve user by email"""
        from server.models.models import User
        return db.query(User).filter(User.email == email).first()


user_service = UserService()

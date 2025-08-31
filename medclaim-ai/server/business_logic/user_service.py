# server/business_logic/user_service.py
from sqlalchemy.orm import Session
from datetime import datetime
import uuid
from passlib.context import CryptContext
from server.schemas.schemas import UserCreate

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class UserService:
    """Service class for user operations"""

    def _hash_password(self, password: str) -> str:
        return pwd_context.hash(password)

    async def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify if provided password matches stored hash"""
        return pwd_context.verify(plain_password, hashed_password)

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
            role=user_data.role.lower() if getattr(user_data, "role", None) else None,
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

    async def get_user_by_id(self, db: Session, user_id: str):
        """Retrieve user by ID"""
        from server.models.models import User
        return db.query(User).filter(User.id == user_id).first()

    async def update_last_login(self, db: Session, user_id: str):
        """Update last login timestamp"""
        from server.models.models import User
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            user.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(user)
        return user


user_service = UserService()

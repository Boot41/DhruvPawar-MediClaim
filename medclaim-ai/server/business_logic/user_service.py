"""
User Business Logic Service
Handles user management, authentication, and profile operations.
"""

from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import uuid
import hashlib
from schemas import UserCreate, UserUpdate


class UserService:
    """Service class for user operations"""
    
    async def create_user(self, db: Session, user_data: UserCreate):
        """Create a new user account"""
        try:
            from models import User
            
            # Check if user already exists
            existing_user = db.query(User).filter(User.email == user_data.email).first()
            if existing_user:
                raise Exception("User with this email already exists")
            
            # Hash password (in production, use proper password hashing like bcrypt)
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
                role=user_data.role or "user",
                is_active=True,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            db.add(user)
            db.commit()
            db.refresh(user)
            
            return user
            
        except Exception as e:
            db.rollback()
            raise Exception(f"Failed to create user: {str(e)}")
    
    async def get_users(self, db: Session, page: int = 1, size: int = 50,
                       search: Optional[str] = None, role: Optional[str] = None,
                       is_active: Optional[bool] = None) -> Tuple[List, int]:
        """Get users with filtering and pagination"""
        try:
            from models import User
            
            query = db.query(User)
            
            # Apply filters
            if search:
                search_filter = f"%{search}%"
                query = query.filter(
                    (User.email.ilike(search_filter)) |
                    (User.first_name.ilike(search_filter)) |
                    (User.last_name.ilike(search_filter))
                )
            if role:
                query = query.filter(User.role == role)
            if is_active is not None:
                query = query.filter(User.is_active == is_active)
            
            # Get total count
            total = query.count()
            
            # Apply pagination
            users = query.order_by(User.created_at.desc()).offset(
                (page - 1) * size
            ).limit(size).all()
            
            return users, total
            
        except Exception as e:
            raise Exception(f"Failed to get users: {str(e)}")
    
    async def get_user_by_id(self, db: Session, user_id: uuid.UUID):
        """Get user by ID"""
        try:
            from models import User
            
            user = db.query(User).filter(User.id == user_id).first()
            return user
            
        except Exception as e:
            raise Exception(f"Failed to get user: {str(e)}")
    
    async def get_user_by_email(self, db: Session, email: str):
        """Get user by email"""
        try:
            from models import User
            
            user = db.query(User).filter(User.email == email).first()
            return user
            
        except Exception as e:
            raise Exception(f"Failed to get user by email: {str(e)}")
    
    async def update_user(self, db: Session, user_id: uuid.UUID, user_update: UserUpdate):
        """Update user by ID"""
        try:
            from models import User
            
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return None
            
            # Update fields
            update_data = user_update.dict(exclude_unset=True)
            
            # Handle password update separately
            if 'password' in update_data:
                update_data['password_hash'] = self._hash_password(update_data.pop('password'))
            
            for field, value in update_data.items():
                setattr(user, field, value)
            
            user.updated_at = datetime.utcnow()
            
            db.commit()
            db.refresh(user)
            
            return user
            
        except Exception as e:
            db.rollback()
            raise Exception(f"Failed to update user: {str(e)}")
    
    async def deactivate_user(self, db: Session, user_id: uuid.UUID) -> bool:
        """Deactivate user by ID"""
        try:
            from models import User
            
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return False
            
            user.is_active = False
            user.updated_at = datetime.utcnow()
            
            db.commit()
            return True
            
        except Exception as e:
            db.rollback()
            raise Exception(f"Failed to deactivate user: {str(e)}")
    
    async def activate_user(self, db: Session, user_id: uuid.UUID) -> bool:
        """Activate user by ID"""
        try:
            from models import User
            
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return False
            
            user.is_active = True
            user.updated_at = datetime.utcnow()
            
            db.commit()
            return True
            
        except Exception as e:
            db.rollback()
            raise Exception(f"Failed to activate user: {str(e)}")
    
    async def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        try:
            return self._hash_password(plain_password) == hashed_password
        except Exception:
            return False
    
    async def change_password(self, db: Session, user_id: uuid.UUID, old_password: str, new_password: str) -> bool:
        """Change user password"""
        try:
            from models import User
            
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return False
            
            # Verify old password
            if not await self.verify_password(old_password, user.password_hash):
                raise Exception("Invalid current password")
            
            # Update password
            user.password_hash = self._hash_password(new_password)
            user.updated_at = datetime.utcnow()
            
            db.commit()
            return True
            
        except Exception as e:
            db.rollback()
            raise Exception(f"Failed to change password: {str(e)}")
    
    async def get_user_profile_summary(self, db: Session, user_id: uuid.UUID) -> Dict[str, Any]:
        """Get user profile summary with related data counts"""
        try:
            from models import User, Claim, Document
            
            user = await self.get_user_by_id(db, user_id)
            if not user:
                raise Exception("User not found")
            
            # Get related data counts
            claims_count = db.query(Claim).filter(Claim.user_id == user_id).count()
            documents_count = db.query(Document).filter(Document.user_id == user_id).count()
            
            # Get recent activity
            recent_claims = db.query(Claim).filter(
                Claim.user_id == user_id
            ).order_by(Claim.created_at.desc()).limit(5).all()
            
            recent_documents = db.query(Document).filter(
                Document.user_id == user_id
            ).order_by(Document.created_at.desc()).limit(5).all()
            
            return {
                "user_info": {
                    "id": str(user.id),
                    "email": user.email,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "role": user.role,
                    "is_active": user.is_active,
                    "created_at": user.created_at.isoformat(),
                    "last_login": user.last_login.isoformat() if user.last_login else None
                },
                "statistics": {
                    "total_claims": claims_count,
                    "total_documents": documents_count
                },
                "recent_activity": {
                    "recent_claims": [
                        {
                            "id": str(claim.id),
                            "claim_type": claim.claim_type,
                            "status": claim.status,
                            "amount": float(claim.amount) if claim.amount else 0,
                            "created_at": claim.created_at.isoformat()
                        } for claim in recent_claims
                    ],
                    "recent_documents": [
                        {
                            "id": str(doc.id),
                            "filename": doc.filename,
                            "document_type": doc.document_type,
                            "is_processed": doc.is_processed,
                            "created_at": doc.created_at.isoformat()
                        } for doc in recent_documents
                    ]
                }
            }
            
        except Exception as e:
            raise Exception(f"Failed to get user profile summary: {str(e)}")
    
    async def update_last_login(self, db: Session, user_id: uuid.UUID):
        """Update user's last login timestamp"""
        try:
            from models import User
            
            user = db.query(User).filter(User.id == user_id).first()
            if user:
                user.last_login = datetime.utcnow()
                db.commit()
                
        except Exception as e:
            # Don't raise exception for login timestamp update failures
            pass
    
    async def get_user_statistics(self, db: Session) -> Dict[str, Any]:
        """Get overall user statistics"""
        try:
            from models import User
            
            total_users = db.query(User).count()
            active_users = db.query(User).filter(User.is_active == True).count()
            
            # Get user counts by role
            role_counts = db.query(User.role, db.func.count(User.id)).group_by(User.role).all()
            
            # Get registration trends (last 30 days)
            from datetime import timedelta
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)
            recent_registrations = db.query(User).filter(
                User.created_at >= thirty_days_ago
            ).count()
            
            return {
                "total_users": total_users,
                "active_users": active_users,
                "inactive_users": total_users - active_users,
                "role_distribution": dict(role_counts),
                "recent_registrations": recent_registrations,
                "activity_rate": (active_users / total_users * 100) if total_users > 0 else 0
            }
            
        except Exception as e:
            raise Exception(f"Failed to get user statistics: {str(e)}")
    
    # Private helper methods
    
    def _hash_password(self, password: str) -> str:
        """Hash password using SHA-256 (use bcrypt in production)"""
        # Note: In production, use bcrypt or similar secure hashing
        return hashlib.sha256(password.encode()).hexdigest()


# Create singleton instance
user_service = UserService()

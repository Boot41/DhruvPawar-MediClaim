from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from database import get_db
from services import auth_service
from business_logic import user_service
from schemas import (
    UserCreate, UserUpdate, UserResponse, UserLogin, UserProfile,
    ApiResponse, PaginatedResponse
)
import uuid

router = APIRouter(prefix="/users", tags=["Users"])

# ============================================================================
# AUTHENTICATION ENDPOINTS
# ============================================================================

@router.post("/register", response_model=ApiResponse)
async def register_user(user_data: UserCreate, db: Session = Depends(get_db)):
    """Register a new user"""
    try:
        user = await user_service.create_user(db, user_data)
        return ApiResponse(
            success=True,
            message="User registered successfully",
            data=UserResponse.from_orm(user)
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/login", response_model=ApiResponse)
async def login_user(login_data: UserLogin, db: Session = Depends(get_db)):
    """Authenticate user and return access token"""
    try:
        token_data = await auth_service.authenticate_user(db, login_data.email, login_data.password)
        return ApiResponse(
            success=True,
            message="Login successful",
            data=token_data
        )
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid credentials")

@router.post("/logout", response_model=ApiResponse)
async def logout_user(current_user = Depends(auth_service.get_current_user)):
    """Logout user (invalidate token)"""
    # In a real implementation, you might want to add token to blacklist
    return ApiResponse(
        success=True,
        message="Logged out successfully"
    )

# ============================================================================
# USER PROFILE ENDPOINTS
# ============================================================================

@router.get("/profile", response_model=UserProfile)
async def get_user_profile(current_user = Depends(auth_service.get_current_user)):
    """Get current user profile"""
    return UserProfile.from_orm(current_user)

@router.put("/profile", response_model=ApiResponse)
async def update_user_profile(
    user_update: UserUpdate, 
    current_user = Depends(auth_service.get_current_user),
    db: Session = Depends(get_db)
):
    """Update current user profile"""
    try:
        updated_user = await user_service.update_user(db, current_user.id, user_update)
        return ApiResponse(
            success=True,
            message="Profile updated successfully",
            data=UserResponse.from_orm(updated_user)
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# ============================================================================
# ADMIN USER MANAGEMENT ENDPOINTS
# ============================================================================

@router.get("/", response_model=PaginatedResponse)
async def get_users(
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100),
    search: Optional[str] = None,
    role: Optional[str] = None,
    is_active: Optional[bool] = None,
    current_user = Depends(auth_service.require_admin),
    db: Session = Depends(get_db)
):
    """Get all users (admin only)"""
    try:
        users, total = await user_service.get_users(
            db, page=page, size=size, search=search, role=role, is_active=is_active
        )
        return PaginatedResponse(
            items=[UserResponse.from_orm(user) for user in users],
            total=total,
            page=page,
            size=size,
            pages=(total + size - 1) // size
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{user_id}", response_model=UserResponse)
async def get_user_by_id(
    user_id: uuid.UUID,
    current_user = Depends(auth_service.require_admin),
    db: Session = Depends(get_db)
):
    """Get user by ID (admin only)"""
    try:
        user = await user_service.get_user_by_id(db, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return UserResponse.from_orm(user)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/{user_id}", response_model=ApiResponse)
async def update_user(
    user_id: uuid.UUID,
    user_update: UserUpdate,
    current_user = Depends(auth_service.require_admin),
    db: Session = Depends(get_db)
):
    """Update user by ID (admin only)"""
    try:
        updated_user = await user_service.update_user(db, user_id, user_update)
        if not updated_user:
            raise HTTPException(status_code=404, detail="User not found")
        return ApiResponse(
            success=True,
            message="User updated successfully",
            data=UserResponse.from_orm(updated_user)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{user_id}", response_model=ApiResponse)
async def deactivate_user(
    user_id: uuid.UUID,
    current_user = Depends(auth_service.require_admin),
    db: Session = Depends(get_db)
):
    """Deactivate user by ID (admin only)"""
    try:
        success = await user_service.deactivate_user(db, user_id)
        if not success:
            raise HTTPException(status_code=404, detail="User not found")
        return ApiResponse(
            success=True,
            message="User deactivated successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
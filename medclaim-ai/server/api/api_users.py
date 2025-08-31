# server/api/api_users.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from server.config.database import get_db
from server.business_logic import user_service
from server.services import auth_service
from server.schemas.schemas import (
    UserCreate, UserLogin, UserResponse, UserProfile, ApiResponse
)

router = APIRouter(prefix="/users", tags=["Users"])

@router.post("/register", response_model=ApiResponse)
async def register_user(user_data: UserCreate, db: Session = Depends(get_db)):
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
    try:
        token_data = await auth_service.authenticate_user(
            db, login_data.email, login_data.password
        )
        return ApiResponse(
            success=True,
            message="Login successful",
            data=token_data
        )
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid credentials")

@router.get("/profile", response_model=UserProfile)
async def get_user_profile(current_user=Depends(auth_service.get_current_user)):
    return UserProfile.from_orm(current_user)

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from database import get_db, check_db_connection
from schemas import HealthCheckResponse, ApiResponse
from services import gemini_service, auth_service
from business_logic import admin_service
import os

router = APIRouter(prefix="/admin", tags=["Administration"])

# ============================================================================
# HEALTH CHECK ENDPOINTS
# ============================================================================

@router.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """Health check endpoint"""
    try:
        # Check database connection
        db_healthy = check_db_connection()
        
        # Check Gemini API
        gemini_healthy = await gemini_service.test_connection()
        
        status = "healthy" if db_healthy and gemini_healthy else "unhealthy"
        
        return HealthCheckResponse(
            status=status,
            database=db_healthy,
            gemini_api=gemini_healthy
        )
        
    except Exception as e:
        return HealthCheckResponse(
            status="unhealthy",
            database=False,
            gemini_api=False
        )

@router.get("/health/database")
async def database_health():
    """Database specific health check"""
    try:
        healthy = check_db_connection()
        return {"database": "healthy" if healthy else "unhealthy"}
    except Exception as e:
        return {"database": "unhealthy", "error": str(e)}

@router.get("/health/ai")
async def ai_health():
    """AI service health check"""
    try:
        healthy = await gemini_service.test_connection()
        return {"ai_service": "healthy" if healthy else "unhealthy"}
    except Exception as e:
        return {"ai_service": "unhealthy", "error": str(e)}

# ============================================================================
# SYSTEM INFO ENDPOINTS
# ============================================================================

@router.get("/info")
async def system_info():
    """Get system information"""
    try:
        return {
            "version": "1.0.0",
            "environment": os.getenv("ENVIRONMENT", "development"),
            "features": {
                "document_processing": True,
                "ai_chat": True,
                "claim_estimation": True,
                "multi_user": True,
                "admin_panel": True
            },
            "limits": {
                "max_file_size": os.getenv("MAX_FILE_SIZE", "10485760"),
                "allowed_extensions": os.getenv("ALLOWED_EXTENSIONS", "pdf,jpg,jpeg,png,txt").split(","),
                "max_bulk_upload": 10
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# STATISTICS ENDPOINTS
# ============================================================================

@router.get("/stats/overview")
async def get_system_overview(
    current_user = Depends(auth_service.require_admin),
    db: Session = Depends(get_db)
):
    """Get system overview statistics"""
    try:
        stats = await admin_service.get_system_overview(db)
        return stats
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/stats/users")
async def get_user_statistics(
    current_user = Depends(auth_service.require_admin),
    db: Session = Depends(get_db)
):
    """Get user statistics"""
    try:
        stats = await admin_service.get_user_statistics(db)
        return stats
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/stats/claims")
async def get_claim_statistics(
    current_user = Depends(auth_service.require_admin),
    db: Session = Depends(get_db)
):
    """Get claim statistics"""
    try:
        stats = await admin_service.get_claim_statistics(db)
        return stats
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/stats/documents")
async def get_document_statistics(
    current_user = Depends(auth_service.require_admin),
    db: Session = Depends(get_db)
):
    """Get document processing statistics"""
    try:
        stats = await admin_service.get_document_statistics(db)
        return stats
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# ============================================================================
# MAINTENANCE ENDPOINTS
# ============================================================================

@router.post("/maintenance/cleanup")
async def cleanup_old_files(
    days: int = 30,
    current_user = Depends(auth_service.require_admin),
    db: Session = Depends(get_db)
):
    """Clean up old temporary files"""
    try:
        result = await admin_service.cleanup_old_files(db, days)
        return ApiResponse(
            success=True,
            message=f"Cleanup completed",
            data=result
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/maintenance/reprocess-documents")
async def reprocess_failed_documents(
    current_user = Depends(auth_service.require_admin),
    db: Session = Depends(get_db)
):
    """Reprocess failed document extractions"""
    try:
        result = await admin_service.reprocess_failed_documents(db)
        return ApiResponse(
            success=True,
            message="Reprocessing initiated",
            data=result
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# ============================================================================
# CONFIGURATION ENDPOINTS
# ============================================================================

@router.get("/config")
async def get_system_config(
    current_user = Depends(auth_service.require_admin),
    db: Session = Depends(get_db)
):
    """Get system configuration"""
    try:
        config = await admin_service.get_system_config(db)
        return config
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/config")
async def update_system_config(
    config_updates: dict,
    current_user = Depends(auth_service.require_admin),
    db: Session = Depends(get_db)
):
    """Update system configuration"""
    try:
        updated_config = await admin_service.update_system_config(db, config_updates)
        return ApiResponse(
            success=True,
            message="Configuration updated",
            data=updated_config
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
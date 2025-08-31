from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from database import get_db
from services import auth_service
from business_logic import claim_service
from schemas import (
    ClaimCreate, ClaimUpdate, ClaimResponse, ClaimEstimateRequest, ClaimEstimateResponse,
    ApiResponse, PaginatedResponse, ClaimStatus
)
import uuid

router = APIRouter(prefix="/claims", tags=["Claims"])

# ============================================================================
# CLAIM MANAGEMENT ENDPOINTS
# ============================================================================

@router.post("/", response_model=ApiResponse)
async def create_claim(
    claim_data: ClaimCreate,
    current_user = Depends(auth_service.get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new claim"""
    try:
        # Ensure user can only create claims for themselves (unless admin)
        if current_user.role != "admin" and claim_data.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Cannot create claim for another user")
        
        claim = await claim_service.create_claim(db, claim_data)
        return ApiResponse(
            success=True,
            message="Claim created successfully",
            data=ClaimResponse.from_orm(claim)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/", response_model=PaginatedResponse)
async def get_claims(
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100),
    status: Optional[ClaimStatus] = None,
    user_id: Optional[uuid.UUID] = None,
    claim_type: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    current_user = Depends(auth_service.get_current_user),
    db: Session = Depends(get_db)
):
    """Get claims with filtering and pagination"""
    try:
        # Non-admin users can only see their own claims
        if current_user.role != "admin":
            user_id = current_user.id
            
        claims, total = await claim_service.get_claims(
            db, 
            page=page, 
            size=size, 
            status=status,
            user_id=user_id,
            claim_type=claim_type,
            date_from=date_from,
            date_to=date_to
        )
        
        return PaginatedResponse(
            items=[ClaimResponse.from_orm(claim) for claim in claims],
            total=total,
            page=page,
            size=size,
            pages=(total + size - 1) // size
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{claim_id}", response_model=ClaimResponse)
async def get_claim_by_id(
    claim_id: uuid.UUID,
    current_user = Depends(auth_service.get_current_user),
    db: Session = Depends(get_db)
):
    """Get claim by ID"""
    try:
        claim = await claim_service.get_claim_by_id(db, claim_id)
        if not claim:
            raise HTTPException(status_code=404, detail="Claim not found")
            
        # Check access permissions
        if current_user.role != "admin" and claim.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")
            
        return ClaimResponse.from_orm(claim)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/{claim_id}", response_model=ApiResponse)
async def update_claim(
    claim_id: uuid.UUID,
    claim_update: ClaimUpdate,
    current_user = Depends(auth_service.get_current_user),
    db: Session = Depends(get_db)
):
    """Update claim by ID"""
    try:
        claim = await claim_service.get_claim_by_id(db, claim_id)
        if not claim:
            raise HTTPException(status_code=404, detail="Claim not found")
            
        # Check permissions - users can only update their own draft claims
        if current_user.role != "admin":
            if claim.user_id != current_user.id:
                raise HTTPException(status_code=403, detail="Access denied")
            if claim.status != ClaimStatus.DRAFT:
                raise HTTPException(status_code=400, detail="Can only update draft claims")
                
        updated_claim = await claim_service.update_claim(db, claim_id, claim_update)
        return ApiResponse(
            success=True,
            message="Claim updated successfully",
            data=ClaimResponse.from_orm(updated_claim)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{claim_id}/submit", response_model=ApiResponse)
async def submit_claim(
    claim_id: uuid.UUID,
    current_user = Depends(auth_service.get_current_user),
    db: Session = Depends(get_db)
):
    """Submit claim for processing"""
    try:
        claim = await claim_service.get_claim_by_id(db, claim_id)
        if not claim:
            raise HTTPException(status_code=404, detail="Claim not found")
            
        # Check permissions
        if current_user.role != "admin" and claim.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")
            
        submitted_claim = await claim_service.submit_claim(db, claim_id)
        return ApiResponse(
            success=True,
            message="Claim submitted successfully",
            data=ClaimResponse.from_orm(submitted_claim)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{claim_id}/process", response_model=ApiResponse)
async def process_claim(
    claim_id: uuid.UUID,
    current_user = Depends(auth_service.require_agent_or_admin),
    db: Session = Depends(get_db)
):
    """Process claim (agent/admin only)"""
    try:
        processed_claim = await claim_service.process_claim(db, claim_id, current_user.id)
        return ApiResponse(
            success=True,
            message="Claim processed successfully",
            data=ClaimResponse.from_orm(processed_claim)
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# ============================================================================
# CLAIM ESTIMATION ENDPOINTS
# ============================================================================

@router.post("/estimate", response_model=ClaimEstimateResponse)
async def estimate_claim_coverage(
    estimate_request: ClaimEstimateRequest,
    current_user = Depends(auth_service.get_current_user),
    db: Session = Depends(get_db)
):
    """Estimate claim coverage and patient responsibility"""
    try:
        # Non-admin users can only estimate their own claims
        if current_user.role != "admin":
            estimate_request.user_id = str(current_user.id)
            
        estimate = await claim_service.estimate_claim_coverage(db, estimate_request)
        return estimate
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{claim_id}/estimate", response_model=ClaimEstimateResponse)
async def get_claim_estimate(
    claim_id: uuid.UUID,
    current_user = Depends(auth_service.get_current_user),
    db: Session = Depends(get_db)
):
    """Get estimate for specific claim"""
    try:
        claim = await claim_service.get_claim_by_id(db, claim_id)
        if not claim:
            raise HTTPException(status_code=404, detail="Claim not found")
            
        # Check permissions
        if current_user.role != "admin" and claim.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")
            
        estimate = await claim_service.get_claim_estimate(db, claim_id)
        return estimate
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# ============================================================================
# CLAIM STATUS ENDPOINTS
# ============================================================================

@router.get("/{claim_id}/history", response_model=List[dict])
async def get_claim_status_history(
    claim_id: uuid.UUID,
    current_user = Depends(auth_service.get_current_user),
    db: Session = Depends(get_db)
):
    """Get claim status history"""
    try:
        claim = await claim_service.get_claim_by_id(db, claim_id)
        if not claim:
            raise HTTPException(status_code=404, detail="Claim not found")
            
        # Check permissions
        if current_user.role != "admin" and claim.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")
            
        history = await claim_service.get_claim_status_history(db, claim_id)
        return history
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{claim_id}/appeal", response_model=ApiResponse)
async def appeal_claim(
    claim_id: uuid.UUID,
    appeal_reason: str,
    current_user = Depends(auth_service.get_current_user),
    db: Session = Depends(get_db)
):
    """Appeal a denied claim"""
    try:
        claim = await claim_service.get_claim_by_id(db, claim_id)
        if not claim:
            raise HTTPException(status_code=404, detail="Claim not found")
            
        # Check permissions
        if current_user.role != "admin" and claim.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")
            
        if claim.status != ClaimStatus.DENIED:
            raise HTTPException(status_code=400, detail="Can only appeal denied claims")
            
        appealed_claim = await claim_service.appeal_claim(db, claim_id, appeal_reason)
        return ApiResponse(
            success=True,
            message="Claim appeal submitted successfully",
            data=ClaimResponse.from_orm(appealed_claim)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
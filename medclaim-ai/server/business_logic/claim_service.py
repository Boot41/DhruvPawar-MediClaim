"""
Claim Business Logic Service
Handles claim management, processing, estimation, and status tracking.
"""

from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import uuid
from server.schemas.claim_schema import ClaimCreate, ClaimUpdate, ClaimResponse, ClaimEstimateRequest, ClaimEstimateResponse
from server.schemas.base_schema import ClaimStatus


class ClaimService:
    """Service class for claim operations"""
    
    async def create_claim(self, db: Session, claim_data: ClaimCreate):
        """Create a new insurance claim"""
        try:
            from server.models.models import Claim
            
            claim = Claim(
                id=uuid.uuid4(),
                user_id=claim_data.user_id,
                claim_type=claim_data.claim_type,
                description=claim_data.description,
                amount=claim_data.amount,
                date_of_service=claim_data.date_of_service,
                provider_name=claim_data.provider_name,
                provider_address=claim_data.provider_address,
                diagnosis_code=claim_data.diagnosis_code,
                procedure_codes=claim_data.procedure_codes,
                status=ClaimStatus.DRAFT,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            db.add(claim)
            db.commit()
            db.refresh(claim)
            
            return claim
            
        except Exception as e:
            db.rollback()
            raise Exception(f"Failed to create claim: {str(e)}")
    
    async def get_claims(self, db: Session, page: int = 1, size: int = 50, 
                        status: Optional[ClaimStatus] = None, user_id: Optional[uuid.UUID] = None,
                        claim_type: Optional[str] = None, date_from: Optional[str] = None,
                        date_to: Optional[str] = None) -> Tuple[List, int]:
        """Get claims with filtering and pagination"""
        try:
            from server.models.models import Claim
            
            query = db.query(Claim)
            
            # Apply filters
            if user_id:
                query = query.filter(Claim.user_id == user_id)
            if status:
                query = query.filter(Claim.status == status)
            if claim_type:
                query = query.filter(Claim.claim_type == claim_type)
            if date_from:
                query = query.filter(Claim.date_of_service >= datetime.fromisoformat(date_from))
            if date_to:
                query = query.filter(Claim.date_of_service <= datetime.fromisoformat(date_to))
            
            # Get total count
            total = query.count()
            
            # Apply pagination
            claims = query.order_by(Claim.created_at.desc()).offset(
                (page - 1) * size
            ).limit(size).all()
            
            return claims, total
            
        except Exception as e:
            raise Exception(f"Failed to get claims: {str(e)}")
    
    async def get_claim_by_id(self, db: Session, claim_id: uuid.UUID):
        """Get claim by ID"""
        try:
            from server.models.models import Claim
            
            claim = db.query(Claim).filter(Claim.id == claim_id).first()
            return claim
            
        except Exception as e:
            raise Exception(f"Failed to get claim: {str(e)}")
    
    async def update_claim(self, db: Session, claim_id: uuid.UUID, claim_update: ClaimUpdate):
        """Update claim by ID"""
        try:
            from server.models.models import Claim
            
            claim = db.query(Claim).filter(Claim.id == claim_id).first()
            if not claim:
                raise Exception("Claim not found")
            
            # Update fields
            update_data = claim_update.dict(exclude_unset=True)
            for field, value in update_data.items():
                setattr(claim, field, value)
            
            claim.updated_at = datetime.utcnow()
            
            db.commit()
            db.refresh(claim)
            
            return claim
            
        except Exception as e:
            db.rollback()
            raise Exception(f"Failed to update claim: {str(e)}")
    
    async def submit_claim(self, db: Session, claim_id: uuid.UUID):
        """Submit claim for processing"""
        try:
            from server.models.models import Claim, ClaimStatusHistory
            
            claim = db.query(Claim).filter(Claim.id == claim_id).first()
            if not claim:
                raise Exception("Claim not found")
            
            if claim.status != ClaimStatus.DRAFT:
                raise Exception("Can only submit draft claims")
            
            # Update claim status
            old_status = claim.status
            claim.status = ClaimStatus.SUBMITTED
            claim.submitted_at = datetime.utcnow()
            claim.updated_at = datetime.utcnow()
            
            # Add status history
            status_history = ClaimStatusHistory(
                id=uuid.uuid4(),
                claim_id=claim_id,
                old_status=old_status,
                new_status=ClaimStatus.SUBMITTED,
                changed_by=claim.user_id,
                changed_at=datetime.utcnow(),
                notes="Claim submitted for processing"
            )
            db.add(status_history)
            
            db.commit()
            db.refresh(claim)
            
            return claim
            
        except Exception as e:
            db.rollback()
            raise Exception(f"Failed to submit claim: {str(e)}")
    
    async def process_claim(self, db: Session, claim_id: uuid.UUID, processor_id: uuid.UUID):
        """Process claim (agent/admin only)"""
        try:
            from server.models.models import Claim, ClaimStatusHistory
            
            claim = db.query(Claim).filter(Claim.id == claim_id).first()
            if not claim:
                raise Exception("Claim not found")
            
            if claim.status != ClaimStatus.SUBMITTED:
                raise Exception("Can only process submitted claims")
            
            # Update claim status
            old_status = claim.status
            claim.status = ClaimStatus.PROCESSING
            claim.processed_at = datetime.utcnow()
            claim.processed_by = processor_id
            claim.updated_at = datetime.utcnow()
            
            # Add status history
            status_history = ClaimStatusHistory(
                id=uuid.uuid4(),
                claim_id=claim_id,
                old_status=old_status,
                new_status=ClaimStatus.PROCESSING,
                changed_by=processor_id,
                changed_at=datetime.utcnow(),
                notes="Claim processing started"
            )
            db.add(status_history)
            
            # Here you would trigger the actual claim processing logic
            # For now, we'll simulate processing and approve the claim
            await self._simulate_claim_processing(db, claim)
            
            db.commit()
            db.refresh(claim)
            
            return claim
            
        except Exception as e:
            db.rollback()
            raise Exception(f"Failed to process claim: {str(e)}")
    
    async def estimate_claim_coverage(self, db: Session, estimate_request: ClaimEstimateRequest) -> ClaimEstimateResponse:
        """Estimate claim coverage and patient responsibility"""
        try:
            from server.models.models import User, InsurancePolicy
            
            # Get user and their insurance policy
            user = db.query(User).filter(User.id == estimate_request.user_id).first()
            if not user:
                raise Exception("User not found")
            
            policy = db.query(InsurancePolicy).filter(
                InsurancePolicy.user_id == user.id,
                InsurancePolicy.is_active == True
            ).first()
            
            if not policy:
                # Use default values if no policy found
                deductible = 1000.0
                coverage_percentage = 0.8
                copay = 25.0
                out_of_pocket_max = 5000.0
            else:
                deductible = float(policy.deductible or 1000)
                coverage_percentage = float(policy.coverage_percentage or 80) / 100
                copay = float(policy.copay or 25)
                out_of_pocket_max = float(policy.out_of_pocket_max or 5000)
            
            # Calculate coverage
            total_amount = float(estimate_request.total_amount)
            
            # Apply deductible
            amount_after_deductible = max(0, total_amount - deductible)
            
            # Calculate insurance coverage
            insurance_coverage = amount_after_deductible * coverage_percentage
            
            # Calculate patient responsibility
            patient_responsibility = total_amount - insurance_coverage + copay
            
            # Apply out-of-pocket maximum
            if patient_responsibility > out_of_pocket_max:
                insurance_coverage += (patient_responsibility - out_of_pocket_max)
                patient_responsibility = out_of_pocket_max
            
            return ClaimEstimateResponse(
                total_amount=total_amount,
                insurance_coverage=round(insurance_coverage, 2),
                patient_responsibility=round(patient_responsibility, 2),
                deductible=deductible,
                copay=copay,
                coverage_percentage=coverage_percentage * 100,
                out_of_pocket_max=out_of_pocket_max,
                estimated_approval_time="3-5 business days",
                confidence_score=0.85
            )
            
        except Exception as e:
            raise Exception(f"Failed to estimate claim coverage: {str(e)}")
    
    async def get_claim_estimate(self, db: Session, claim_id: uuid.UUID) -> ClaimEstimateResponse:
        """Get estimate for specific claim"""
        try:
            claim = await self.get_claim_by_id(db, claim_id)
            if not claim:
                raise Exception("Claim not found")
            
            estimate_request = ClaimEstimateRequest(
                user_id=str(claim.user_id),
                total_amount=float(claim.amount or 0),
                claim_type=claim.claim_type,
                procedure_codes=claim.procedure_codes or [],
                diagnosis_code=claim.diagnosis_code
            )
            
            return await self.estimate_claim_coverage(db, estimate_request)
            
        except Exception as e:
            raise Exception(f"Failed to get claim estimate: {str(e)}")
    
    async def get_claim_status_history(self, db: Session, claim_id: uuid.UUID) -> List[Dict[str, Any]]:
        """Get claim status history"""
        try:
            from server.models.models import ClaimStatusHistory, User
            
            history = db.query(ClaimStatusHistory).filter(
                ClaimStatusHistory.claim_id == claim_id
            ).order_by(ClaimStatusHistory.changed_at.desc()).all()
            
            history_list = []
            for entry in history:
                # Get user who made the change
                changed_by_user = db.query(User).filter(User.id == entry.changed_by).first()
                
                history_list.append({
                    "old_status": entry.old_status,
                    "new_status": entry.new_status,
                    "changed_at": entry.changed_at.isoformat(),
                    "changed_by": changed_by_user.email if changed_by_user else "System",
                    "notes": entry.notes
                })
            
            return history_list
            
        except Exception as e:
            raise Exception(f"Failed to get claim status history: {str(e)}")
    
    async def appeal_claim(self, db: Session, claim_id: uuid.UUID, appeal_reason: str):
        """Appeal a denied claim"""
        try:
            from server.models.models import Claim, ClaimStatusHistory, ClaimAppeal
            
            claim = db.query(Claim).filter(Claim.id == claim_id).first()
            if not claim:
                raise Exception("Claim not found")
            
            if claim.status != ClaimStatus.DENIED:
                raise Exception("Can only appeal denied claims")
            
            # Create appeal record
            appeal = ClaimAppeal(
                id=uuid.uuid4(),
                claim_id=claim_id,
                reason=appeal_reason,
                status="pending",
                created_at=datetime.utcnow()
            )
            db.add(appeal)
            
            # Update claim status
            old_status = claim.status
            claim.status = ClaimStatus.APPEALED
            claim.updated_at = datetime.utcnow()
            
            # Add status history
            status_history = ClaimStatusHistory(
                id=uuid.uuid4(),
                claim_id=claim_id,
                old_status=old_status,
                new_status=ClaimStatus.APPEALED,
                changed_by=claim.user_id,
                changed_at=datetime.utcnow(),
                notes=f"Claim appealed: {appeal_reason}"
            )
            db.add(status_history)
            
            db.commit()
            db.refresh(claim)
            
            return claim
            
        except Exception as e:
            db.rollback()
            raise Exception(f"Failed to appeal claim: {str(e)}")
    
    # Private helper methods
    
    async def _simulate_claim_processing(self, db: Session, claim):
        """Simulate claim processing logic"""
        try:
            from server.models.models import ClaimStatusHistory
            import random
            
            # Simulate processing time
            await asyncio.sleep(0.1)  # Simulate processing delay
            
            # Randomly approve or deny for simulation
            # In real implementation, this would involve complex business rules
            approval_chance = 0.85  # 85% approval rate
            
            if random.random() < approval_chance:
                new_status = ClaimStatus.APPROVED
                notes = "Claim approved after processing"
            else:
                new_status = ClaimStatus.DENIED
                notes = "Claim denied - requires additional documentation"
            
            # Update claim
            old_status = claim.status
            claim.status = new_status
            claim.updated_at = datetime.utcnow()
            
            # Add status history
            status_history = ClaimStatusHistory(
                id=uuid.uuid4(),
                claim_id=claim.id,
                old_status=old_status,
                new_status=new_status,
                changed_by=claim.processed_by,
                changed_at=datetime.utcnow(),
                notes=notes
            )
            db.add(status_history)
            
        except Exception as e:
            raise Exception(f"Failed to simulate claim processing: {str(e)}")


# Create singleton instance
claim_service = ClaimService()

"""
Admin Business Logic Service
Handles all administrative operations, system monitoring, and configuration management.
"""

from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
import os
from datetime import datetime, timedelta
from database import check_db_connection
from services import gemini_service


class AdminService:
    """Service class for administrative operations"""
    
    async def get_system_overview(self, db: Session) -> Dict[str, Any]:
        """Get comprehensive system overview statistics"""
        try:
            # Get basic counts from database
            from models import User, Claim, Document  # Import here to avoid circular imports
            
            total_users = db.query(User).count()
            active_users = db.query(User).filter(User.is_active == True).count()
            total_claims = db.query(Claim).count()
            pending_claims = db.query(Claim).filter(Claim.status == "pending").count()
            total_documents = db.query(Document).count()
            processed_documents = db.query(Document).filter(Document.is_processed == True).count()
            
            return {
                "users": {
                    "total": total_users,
                    "active": active_users,
                    "inactive": total_users - active_users
                },
                "claims": {
                    "total": total_claims,
                    "pending": pending_claims,
                    "processed": total_claims - pending_claims
                },
                "documents": {
                    "total": total_documents,
                    "processed": processed_documents,
                    "pending": total_documents - processed_documents
                },
                "system_health": {
                    "database": check_db_connection(),
                    "ai_service": await gemini_service.test_connection()
                }
            }
        except Exception as e:
            raise Exception(f"Failed to get system overview: {str(e)}")
    
    async def get_user_statistics(self, db: Session) -> Dict[str, Any]:
        """Get detailed user statistics"""
        try:
            from models import User
            
            # Get user counts by role
            user_roles = db.query(User.role, db.func.count(User.id)).group_by(User.role).all()
            
            # Get registration trends (last 30 days)
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)
            recent_registrations = db.query(User).filter(
                User.created_at >= thirty_days_ago
            ).count()
            
            return {
                "total_users": db.query(User).count(),
                "active_users": db.query(User).filter(User.is_active == True).count(),
                "roles": dict(user_roles),
                "recent_registrations": recent_registrations,
                "registration_trend": "positive"  # Could be calculated based on historical data
            }
        except Exception as e:
            raise Exception(f"Failed to get user statistics: {str(e)}")
    
    async def get_claim_statistics(self, db: Session) -> Dict[str, Any]:
        """Get detailed claim statistics"""
        try:
            from models import Claim
            
            # Get claim counts by status
            claim_statuses = db.query(Claim.status, db.func.count(Claim.id)).group_by(Claim.status).all()
            
            # Get claim amounts
            total_amount = db.query(db.func.sum(Claim.amount)).scalar() or 0
            avg_amount = db.query(db.func.avg(Claim.amount)).scalar() or 0
            
            # Get recent claims (last 7 days)
            seven_days_ago = datetime.utcnow() - timedelta(days=7)
            recent_claims = db.query(Claim).filter(
                Claim.created_at >= seven_days_ago
            ).count()
            
            return {
                "total_claims": db.query(Claim).count(),
                "statuses": dict(claim_statuses),
                "financial": {
                    "total_amount": float(total_amount),
                    "average_amount": float(avg_amount)
                },
                "recent_activity": {
                    "claims_last_7_days": recent_claims
                }
            }
        except Exception as e:
            raise Exception(f"Failed to get claim statistics: {str(e)}")
    
    async def get_document_statistics(self, db: Session) -> Dict[str, Any]:
        """Get detailed document processing statistics"""
        try:
            from models import Document
            
            # Get document counts by type
            doc_types = db.query(Document.document_type, db.func.count(Document.id)).group_by(Document.document_type).all()
            
            # Get processing statistics
            total_docs = db.query(Document).count()
            processed_docs = db.query(Document).filter(Document.is_processed == True).count()
            verified_docs = db.query(Document).filter(Document.is_verified == True).count()
            
            # Get recent uploads (last 24 hours)
            yesterday = datetime.utcnow() - timedelta(hours=24)
            recent_uploads = db.query(Document).filter(
                Document.created_at >= yesterday
            ).count()
            
            return {
                "total_documents": total_docs,
                "processed_documents": processed_docs,
                "verified_documents": verified_docs,
                "processing_rate": (processed_docs / total_docs * 100) if total_docs > 0 else 0,
                "document_types": dict(doc_types),
                "recent_activity": {
                    "uploads_last_24h": recent_uploads
                }
            }
        except Exception as e:
            raise Exception(f"Failed to get document statistics: {str(e)}")
    
    async def cleanup_old_files(self, db: Session, days: int = 30) -> Dict[str, Any]:
        """Clean up old temporary files and orphaned records"""
        try:
            from models import Document
            import os
            from pathlib import Path
            
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            # Find old documents
            old_documents = db.query(Document).filter(
                Document.created_at < cutoff_date,
                Document.is_processed == False
            ).all()
            
            deleted_files = 0
            deleted_records = 0
            
            for doc in old_documents:
                try:
                    # Delete physical file if exists
                    if doc.file_path and os.path.exists(doc.file_path):
                        os.remove(doc.file_path)
                        deleted_files += 1
                    
                    # Delete database record
                    db.delete(doc)
                    deleted_records += 1
                except Exception as e:
                    continue
            
            db.commit()
            
            return {
                "deleted_files": deleted_files,
                "deleted_records": deleted_records,
                "cutoff_date": cutoff_date.isoformat()
            }
        except Exception as e:
            db.rollback()
            raise Exception(f"Failed to cleanup old files: {str(e)}")
    
    async def reprocess_failed_documents(self, db: Session) -> Dict[str, Any]:
        """Reprocess documents that failed initial processing"""
        try:
            from models import Document
            
            # Find failed documents
            failed_docs = db.query(Document).filter(
                Document.is_processed == False,
                Document.processing_error.isnot(None)
            ).all()
            
            reprocessed_count = 0
            success_count = 0
            
            for doc in failed_docs:
                try:
                    # Reset processing status
                    doc.is_processed = False
                    doc.processing_error = None
                    doc.updated_at = datetime.utcnow()
                    
                    # Here you would trigger the document processing pipeline
                    # For now, just mark as ready for reprocessing
                    reprocessed_count += 1
                    
                except Exception as e:
                    continue
            
            db.commit()
            
            return {
                "total_failed_documents": len(failed_docs),
                "reprocessed_count": reprocessed_count,
                "success_count": success_count
            }
        except Exception as e:
            db.rollback()
            raise Exception(f"Failed to reprocess documents: {str(e)}")
    
    async def get_system_config(self, db: Session) -> Dict[str, Any]:
        """Get current system configuration"""
        try:
            from models import SystemConfig
            
            # Get all configuration settings
            configs = db.query(SystemConfig).all()
            config_dict = {config.key: config.value for config in configs}
            
            # Add environment variables
            config_dict.update({
                "environment": os.getenv("ENVIRONMENT", "development"),
                "max_file_size": os.getenv("MAX_FILE_SIZE", "10485760"),
                "allowed_extensions": os.getenv("ALLOWED_EXTENSIONS", "pdf,jpg,jpeg,png,txt").split(","),
                "ai_model": os.getenv("AI_MODEL", "gemini-1.5-pro"),
                "database_url": "***HIDDEN***"  # Don't expose sensitive data
            })
            
            return config_dict
        except Exception as e:
            raise Exception(f"Failed to get system config: {str(e)}")
    
    async def update_system_config(self, db: Session, config_updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update system configuration settings"""
        try:
            from models import SystemConfig
            
            updated_configs = {}
            
            for key, value in config_updates.items():
                # Find existing config or create new one
                config = db.query(SystemConfig).filter(SystemConfig.key == key).first()
                
                if config:
                    config.value = str(value)
                    config.updated_at = datetime.utcnow()
                else:
                    config = SystemConfig(
                        key=key,
                        value=str(value),
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow()
                    )
                    db.add(config)
                
                updated_configs[key] = value
            
            db.commit()
            
            return updated_configs
        except Exception as e:
            db.rollback()
            raise Exception(f"Failed to update system config: {str(e)}")


# Create singleton instance
admin_service = AdminService()

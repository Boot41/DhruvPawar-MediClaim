"""
Document Business Logic Service
Handles document upload, processing, analysis, and management.
"""

from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import uuid
import os
import shutil
from pathlib import Path
from fastapi import UploadFile
from fastapi.responses import FileResponse
from schemas import DocumentUpdate, DocumentType, DocumentUploadResponse


class DocumentService:
    """Service class for document operations"""
    
    def __init__(self):
        self.upload_dir = Path("uploads")
        self.upload_dir.mkdir(exist_ok=True)
        self.allowed_extensions = {'pdf', 'jpg', 'jpeg', 'png', 'txt'}
        self.max_file_size = 10 * 1024 * 1024  # 10MB
    
    async def upload_and_process_document(self, db: Session, file: UploadFile, 
                                        user_id: uuid.UUID, claim_id: Optional[uuid.UUID] = None,
                                        document_type: DocumentType = DocumentType.OTHER) -> Dict[str, Any]:
        """Upload and process a medical document"""
        try:
            # Validate file
            if not file.filename:
                raise Exception("No file provided")
            
            file_extension = file.filename.split('.')[-1].lower()
            if file_extension not in self.allowed_extensions:
                raise Exception(f"File type {file_extension} not allowed. Supported: {self.allowed_extensions}")
            
            # Check file size
            file.file.seek(0, 2)  # Seek to end
            file_size = file.file.tell()
            file.file.seek(0)  # Reset to beginning
            
            if file_size > self.max_file_size:
                raise Exception(f"File too large. Maximum size: {self.max_file_size / (1024*1024)}MB")
            
            # Generate unique filename
            unique_filename = f"{uuid.uuid4()}_{file.filename}"
            file_path = self.upload_dir / unique_filename
            
            # Save uploaded file
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            # Create document record
            from models import Document
            
            document = Document(
                id=uuid.uuid4(),
                user_id=user_id,
                claim_id=claim_id,
                filename=file.filename,
                file_path=str(file_path),
                file_size=file_size,
                document_type=document_type,
                is_processed=False,
                is_verified=False,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            db.add(document)
            db.commit()
            db.refresh(document)
            
            # Process document asynchronously
            extracted_data = await self._process_document_by_type(file_path, file_extension)
            
            # Update document with extracted data
            document.extracted_data = extracted_data
            document.is_processed = True
            document.processing_completed_at = datetime.utcnow()
            document.updated_at = datetime.utcnow()
            
            db.commit()
            
            return {
                "document_id": str(document.id),
                "filename": file.filename,
                "extracted_data": extracted_data,
                "message": "Document processed successfully"
            }
            
        except Exception as e:
            db.rollback()
            # Clean up file if it was created
            if 'file_path' in locals() and file_path.exists():
                file_path.unlink()
            raise Exception(f"Failed to upload and process document: {str(e)}")
    
    async def get_documents(self, db: Session, user_id: Optional[uuid.UUID] = None,
                          page: int = 1, size: int = 50, document_type: Optional[DocumentType] = None,
                          claim_id: Optional[uuid.UUID] = None, is_processed: Optional[bool] = None,
                          is_verified: Optional[bool] = None) -> Tuple[List, int]:
        """Get documents with filtering and pagination"""
        try:
            from models import Document
            
            query = db.query(Document)
            
            # Apply filters
            if user_id:
                query = query.filter(Document.user_id == user_id)
            if document_type:
                query = query.filter(Document.document_type == document_type)
            if claim_id:
                query = query.filter(Document.claim_id == claim_id)
            if is_processed is not None:
                query = query.filter(Document.is_processed == is_processed)
            if is_verified is not None:
                query = query.filter(Document.is_verified == is_verified)
            
            # Get total count
            total = query.count()
            
            # Apply pagination
            documents = query.order_by(Document.created_at.desc()).offset(
                (page - 1) * size
            ).limit(size).all()
            
            return documents, total
            
        except Exception as e:
            raise Exception(f"Failed to get documents: {str(e)}")
    
    async def get_document_by_id(self, db: Session, document_id: uuid.UUID):
        """Get document by ID"""
        try:
            from models import Document
            
            document = db.query(Document).filter(Document.id == document_id).first()
            return document
            
        except Exception as e:
            raise Exception(f"Failed to get document: {str(e)}")
    
    async def update_document(self, db: Session, document_id: uuid.UUID, document_update: DocumentUpdate):
        """Update document metadata"""
        try:
            from models import Document
            
            document = db.query(Document).filter(Document.id == document_id).first()
            if not document:
                raise Exception("Document not found")
            
            # Update fields
            update_data = document_update.dict(exclude_unset=True)
            for field, value in update_data.items():
                setattr(document, field, value)
            
            document.updated_at = datetime.utcnow()
            
            db.commit()
            db.refresh(document)
            
            return document
            
        except Exception as e:
            db.rollback()
            raise Exception(f"Failed to update document: {str(e)}")
    
    async def delete_document(self, db: Session, document_id: uuid.UUID) -> bool:
        """Delete document and its file"""
        try:
            from models import Document
            
            document = db.query(Document).filter(Document.id == document_id).first()
            if not document:
                return False
            
            # Delete physical file
            if document.file_path and os.path.exists(document.file_path):
                os.remove(document.file_path)
            
            # Delete database record
            db.delete(document)
            db.commit()
            
            return True
            
        except Exception as e:
            db.rollback()
            raise Exception(f"Failed to delete document: {str(e)}")
    
    async def reprocess_document(self, db: Session, document_id: uuid.UUID):
        """Reprocess document with AI extraction"""
        try:
            from models import Document
            
            document = db.query(Document).filter(Document.id == document_id).first()
            if not document:
                raise Exception("Document not found")
            
            if not os.path.exists(document.file_path):
                raise Exception("Document file not found")
            
            # Reset processing status
            document.is_processed = False
            document.processing_error = None
            document.updated_at = datetime.utcnow()
            
            # Reprocess document
            file_extension = document.filename.split('.')[-1].lower()
            extracted_data = await self._process_document_by_type(Path(document.file_path), file_extension)
            
            # Update document with new extracted data
            document.extracted_data = extracted_data
            document.is_processed = True
            document.processing_completed_at = datetime.utcnow()
            document.updated_at = datetime.utcnow()
            
            db.commit()
            db.refresh(document)
            
            return document
            
        except Exception as e:
            db.rollback()
            # Log processing error
            document = db.query(Document).filter(Document.id == document_id).first()
            if document:
                document.processing_error = str(e)
                document.updated_at = datetime.utcnow()
                db.commit()
            raise Exception(f"Failed to reprocess document: {str(e)}")
    
    async def verify_document(self, db: Session, document_id: uuid.UUID, verifier_id: uuid.UUID):
        """Verify document extraction (agent/admin only)"""
        try:
            from models import Document
            
            document = db.query(Document).filter(Document.id == document_id).first()
            if not document:
                return None
            
            document.is_verified = True
            document.verified_by = verifier_id
            document.verified_at = datetime.utcnow()
            document.updated_at = datetime.utcnow()
            
            db.commit()
            db.refresh(document)
            
            return document
            
        except Exception as e:
            db.rollback()
            raise Exception(f"Failed to verify document: {str(e)}")
    
    async def get_document_file(self, document) -> FileResponse:
        """Get document file for download"""
        try:
            if not document.file_path or not os.path.exists(document.file_path):
                raise Exception("Document file not found")
            
            return FileResponse(
                path=document.file_path,
                filename=document.filename,
                media_type='application/octet-stream'
            )
            
        except Exception as e:
            raise Exception(f"Failed to get document file: {str(e)}")
    
    async def get_document_analysis(self, db: Session, document_id: uuid.UUID) -> Dict[str, Any]:
        """Get detailed document analysis and extracted data"""
        try:
            document = await self.get_document_by_id(db, document_id)
            if not document:
                raise Exception("Document not found")
            
            analysis = {
                "document_info": {
                    "id": str(document.id),
                    "filename": document.filename,
                    "document_type": document.document_type,
                    "file_size": document.file_size,
                    "upload_date": document.created_at.isoformat(),
                    "is_processed": document.is_processed,
                    "is_verified": document.is_verified
                },
                "extracted_data": document.extracted_data or {},
                "processing_info": {
                    "processed_at": document.processing_completed_at.isoformat() if document.processing_completed_at else None,
                    "verified_at": document.verified_at.isoformat() if document.verified_at else None,
                    "processing_error": document.processing_error
                }
            }
            
            # Add confidence score if available
            if document.extracted_data and "confidence" in document.extracted_data:
                analysis["confidence_score"] = document.extracted_data["confidence"]
            
            return analysis
            
        except Exception as e:
            raise Exception(f"Failed to get document analysis: {str(e)}")
    
    # Private helper methods
    
    async def _process_document_by_type(self, file_path: Path, file_extension: str) -> Dict[str, Any]:
        """Process document based on its type"""
        try:
            if file_extension in ['jpg', 'jpeg', 'png']:
                return await self._process_image_document(file_path)
            elif file_extension == 'pdf':
                return await self._process_pdf_document(file_path)
            elif file_extension == 'txt':
                return await self._process_text_document(file_path)
            else:
                return {"error": f"Unsupported file type: {file_extension}", "confidence": 0}
                
        except Exception as e:
            return {"error": f"Failed to process document: {str(e)}", "confidence": 0}
    
    async def _process_image_document(self, file_path: Path) -> Dict[str, Any]:
        """Process image document using AI"""
        try:
            from PIL import Image
            import google.generativeai as genai
            import json
            
            # Configure Gemini (should be done at startup)
            model = genai.GenerativeModel('gemini-1.5-pro')
            
            image = Image.open(file_path)
            prompt = """
            Analyze this medical document and extract the following information in JSON format:
            {
                "document_type": "medical_bill|prescription|lab_report|discharge_summary|insurance_card|other",
                "patient_info": {
                    "name": "patient name if found",
                    "date_of_birth": "DOB if found",
                    "id": "patient ID if found"
                },
                "provider_info": {
                    "name": "healthcare provider name",
                    "address": "provider address if found",
                    "phone": "provider phone if found"
                },
                "date_of_service": "date when service was provided",
                "services": [
                    {
                        "description": "service description",
                        "code": "medical code if found",
                        "amount": "cost amount"
                    }
                ],
                "total_amount": "total bill amount",
                "diagnosis": "diagnosis or condition if found",
                "medications": ["list of medications if any"],
                "insurance_info": "insurance related information if found",
                "confidence": "your confidence level (0-1) in the extraction accuracy"
            }
            If this is not a medical document, set document_type as "other" and provide a brief description.
            """
            
            response = model.generate_content([prompt, image])
            
            try:
                extracted_data = json.loads(response.text.strip())
            except json.JSONDecodeError:
                extracted_data = {
                    "document_type": "unknown", 
                    "raw_text": response.text, 
                    "confidence": 0.5
                }
            
            return extracted_data
            
        except Exception as e:
            return {"error": f"Failed to process image: {str(e)}", "confidence": 0}
    
    async def _process_pdf_document(self, file_path: Path) -> Dict[str, Any]:
        """Process PDF document by converting to image first"""
        try:
            import fitz  # PyMuPDF
            from PIL import Image
            import io
            
            doc = fitz.open(file_path)
            page = doc[0]  # Process first page
            pix = page.get_pixmap()
            img_data = pix.tobytes("png")
            image = Image.open(io.BytesIO(img_data))
            
            # Save temporary image
            temp_image_path = file_path.parent / f"temp_{uuid.uuid4()}.png"
            image.save(temp_image_path)
            
            # Process as image
            result = await self._process_image_document(temp_image_path)
            
            # Clean up
            temp_image_path.unlink()
            doc.close()
            
            return result
            
        except Exception as e:
            return {"error": f"Failed to process PDF: {str(e)}", "confidence": 0}
    
    async def _process_text_document(self, file_path: Path) -> Dict[str, Any]:
        """Process text document using AI"""
        try:
            import google.generativeai as genai
            import json
            
            # Configure Gemini (should be done at startup)
            model = genai.GenerativeModel('gemini-1.5-pro')
            
            with open(file_path, 'r', encoding='utf-8') as f:
                text_content = f.read()
            
            prompt = f"""
            Analyze this medical text document and extract relevant information:

            {text_content}

            Extract the information in the same JSON format as requested for image documents.
            Focus on medical information like patient details, provider info, services, amounts, etc.
            """
            
            response = model.generate_content(prompt)
            
            try:
                extracted_data = json.loads(response.text.strip())
            except json.JSONDecodeError:
                extracted_data = {
                    "document_type": "text", 
                    "raw_text": response.text, 
                    "confidence": 0.5
                }
            
            return extracted_data
            
        except Exception as e:
            return {"error": f"Failed to process text: {str(e)}", "confidence": 0}


# Create singleton instance
document_service = DocumentService()

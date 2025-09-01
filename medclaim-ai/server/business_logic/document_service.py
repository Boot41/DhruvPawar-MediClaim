from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import uuid
import os
from pathlib import Path
from fastapi import UploadFile
from server.schemas.document_schema import DocumentResponse, DocumentUpdate, DocumentUploadResponse
from server.schemas.base_schema import DocumentType

# Import orchestrator agent
from server.orchestrator.adk_workflow import ADKDocumentPipeline


class AsyncDocumentService:
    def __init__(self):
        self.upload_dir = Path("uploads")
        self.upload_dir.mkdir(exist_ok=True)
        self.allowed_extensions = {'pdf', 'jpg', 'jpeg', 'png', 'txt'}
        self.max_file_size = 10 * 1024 * 1024  # 10MB

    async def upload_and_process_document(
        self,
        db: AsyncSession,
        file: UploadFile,
        user_id: uuid.UUID,
        claim_id: Optional[uuid.UUID] = None,
        document_type: DocumentType = DocumentType.OTHER
    ) -> Dict[str, Any]:
        from server.models.models import Document

        try:
            # Validate file
            if not file.filename:
                raise Exception("No file provided")

            file_ext = file.filename.split('.')[-1].lower()
            if file_ext not in self.allowed_extensions:
                raise Exception(f"File type {file_ext} not allowed.")

            # Save file
            contents = await file.read()
            if len(contents) > self.max_file_size:
                raise Exception("File too large")

            unique_filename = f"{uuid.uuid4()}_{file.filename}"
            file_path = self.upload_dir / unique_filename
            with open(file_path, "wb") as f:
                f.write(contents)

            # Create DB record
            doc = Document(
                id=uuid.uuid4(),
                user_id=user_id,
                claim_id=claim_id,
                filename=file.filename,
                file_path=str(file_path),
                file_size=len(contents),
                document_type=document_type,
                is_processed=False,
                is_verified=False,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.add(doc)
            await db.commit()
            await db.refresh(doc)

            # Process document via agent orchestrator
            pipeline = ADKDocumentPipeline()
            extracted_data = await pipeline.run(file_path, policy_clauses="")

            # Update DB
            doc.extracted_data = extracted_data
            doc.is_processed = True
            doc.processing_completed_at = datetime.now()
            doc.updated_at = datetime.now()
            await db.commit()
            await db.refresh(doc)

            return {
                "document_id": str(doc.id),
                "filename": file.filename,
                "extracted_data": extracted_data,
                "message": "Document processed successfully"
            }

        except Exception as e:
            await db.rollback()
            if 'file_path' in locals() and file_path.exists():
                file_path.unlink()
            raise Exception(f"Failed to upload and process document: {str(e)}")

    async def get_documents(
        self,
        db: AsyncSession,
        user_id: Optional[uuid.UUID] = None,
        page: int = 1,
        size: int = 50,
        document_type: Optional[DocumentType] = None,
        claim_id: Optional[uuid.UUID] = None,
        is_processed: Optional[bool] = None,
        is_verified: Optional[bool] = None
    ) -> Tuple[List, int]:
        from server.models.models import Document

        query = select(Document)
        if user_id:
            query = query.where(Document.user_id == user_id)
        if document_type:
            query = query.where(Document.document_type == document_type)
        if claim_id:
            query = query.where(Document.claim_id == claim_id)
        if is_processed is not None:
            query = query.where(Document.is_processed == is_processed)
        if is_verified is not None:
            query = query.where(Document.is_verified == is_verified)

        # Total count
        count_query = query.with_only_columns(func.count()).order_by(None)
        total_count = (await db.execute(count_query)).scalar() or 0

        # Pagination
        query = query.offset((page - 1) * size).limit(size)
        result = await db.execute(query)
        documents = result.scalars().all()

        return documents, total_count

    async def get_document_by_id(self, db: AsyncSession, document_id: uuid.UUID):
        from server.models.models import Document
        result = await db.execute(select(Document).where(Document.id == document_id))
        return result.scalars().first()

    async def update_document(self, db: AsyncSession, document_id: uuid.UUID, document_update: DocumentUpdate):
        from server.models.models import Document
        doc = await self.get_document_by_id(db, document_id)
        if not doc:
            raise Exception("Document not found")
        for field, value in document_update.dict(exclude_unset=True).items():
            setattr(doc, field, value)
        doc.updated_at = datetime.utcnow()
        db.add(doc)
        await db.commit()
        await db.refresh(doc)
        return doc

    async def delete_document(self, db: AsyncSession, document_id: uuid.UUID) -> bool:
        from server.models.models import Document
        doc = await self.get_document_by_id(db, document_id)
        if not doc:
            return False
        if doc.file_path and os.path.exists(doc.file_path):
            os.remove(doc.file_path)
        await db.delete(doc)
        await db.commit()
        return True


# Singleton instance
document_service = AsyncDocumentService()

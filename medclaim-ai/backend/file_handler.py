"""
File handling utilities for document uploads and processing
"""
import os
import aiofiles
import uuid
from typing import Optional, Dict, Any
from fastapi import UploadFile, HTTPException
from PIL import Image
import magic
import base64
from pathlib import Path
import json
from datetime import datetime

# Allowed file types
ALLOWED_EXTENSIONS = {
    'pdf': 'application/pdf',
    'jpg': 'image/jpeg',
    'jpeg': 'image/jpeg',
    'png': 'image/png',
    'gif': 'image/gif'
}

MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", "10485760"))  # 10MB

class FileHandler:
    def __init__(self, upload_dir: str = "./uploads"):
        self.upload_dir = Path(upload_dir)
        self.upload_dir.mkdir(exist_ok=True)
        
        # Create subdirectories
        (self.upload_dir / "documents").mkdir(exist_ok=True)
        (self.upload_dir / "forms").mkdir(exist_ok=True)
        (self.upload_dir / "generated_forms").mkdir(exist_ok=True)
        (self.upload_dir / "temp").mkdir(exist_ok=True)

    async def validate_file(self, file: UploadFile) -> Dict[str, Any]:
        """Validate uploaded file for security and format."""
        print(f"Validating file: {file.filename}, content_type: {file.content_type}")

        # Check file size
        file_size = 0
        content = await file.read()
        file_size = len(content)
        await file.seek(0)  # Reset file pointer

        print(f"File size: {file_size} bytes")
        if file_size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"File too large. Maximum size is {MAX_FILE_SIZE} bytes"
            )

        # Check file extension
        if not file.filename:
            raise HTTPException(status_code=400, detail="No filename provided")
        
        file_extension = file.filename.split('.')[-1].lower()
        if file_extension not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"File type not allowed. Allowed types: {list(ALLOWED_EXTENSIONS.keys())}"
            )

        # Check MIME type
        try:
            mime_type = magic.from_buffer(content, mime=True)
            print(f"Detected MIME type: {mime_type}")
            
            # More lenient MIME type checking
            expected_mime = ALLOWED_EXTENSIONS.get(file_extension)
            if expected_mime and expected_mime not in mime_type and mime_type not in expected_mime:
                # Allow some flexibility in MIME type detection
                if file_extension == 'pdf' and 'pdf' in mime_type.lower():
                    pass  # Allow PDF files even if MIME type is slightly different
                elif file_extension in ['jpg', 'jpeg'] and 'jpeg' in mime_type.lower():
                    pass  # Allow JPEG files
                elif file_extension == 'png' and 'png' in mime_type.lower():
                    pass  # Allow PNG files
                else:
                    print(f"Warning: MIME type mismatch. Expected: {expected_mime}, Got: {mime_type}")
        except Exception as e:
            print(f"Warning: Could not detect MIME type: {e}")
            # Continue with extension-based validation

        return {
            "filename": file.filename,
            "file_size": file_size,
            "file_extension": file_extension,
            "mime_type": mime_type if 'mime_type' in locals() else "unknown"
        }

    async def save_file(self, file: UploadFile, user_id: str, document_type: str) -> Dict[str, Any]:
        """Save uploaded file to disk."""
        try:
            # Validate file first
            validation = await self.validate_file(file)
            
            # Generate unique filename
            file_id = str(uuid.uuid4())
            file_extension = validation["file_extension"]
            filename = f"{file_id}.{file_extension}"
            file_path = self.upload_dir / "documents" / filename
            
            # Save file
            async with aiofiles.open(file_path, 'wb') as f:
                content = await file.read()
                await f.write(content)
            
            return {
                "success": True,
                "file_id": file_id,
                "filename": filename,
                "file_path": str(file_path),
                "file_size": validation["file_size"],
                "file_extension": file_extension,
                "document_type": document_type
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def get_file_as_base64(self, file_path: str) -> str:
        """Get file content as base64 string."""
        try:
            with open(file_path, 'rb') as f:
                content = f.read()
                return base64.b64encode(content).decode('utf-8')
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error reading file: {str(e)}")

    async def save_generated_form(self, form_content: bytes, claim_id: str, vendor_name: str) -> str:
        """Save generated PDF form."""
        safe_vendor = "".join(c for c in vendor_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
        safe_vendor = safe_vendor.replace(' ', '_')
        
        filename = f"claim_{claim_id}_{safe_vendor}.pdf"
        file_path = self.upload_dir / "forms" / filename
        
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(form_content)
        
        return str(file_path)

    async def cleanup_old_files(self, older_than_hours: int = 24):
        """Clean up temporary files older than specified hours."""
        import time
        temp_dir = self.upload_dir / "temp"
        current_time = time.time()
        
        for file_path in temp_dir.glob("*"):
            if file_path.is_file():
                file_age = current_time - file_path.stat().st_mtime
                if file_age > (older_than_hours * 3600):
                    try:
                        file_path.unlink()
                    except Exception:
                        pass

# Global file handler instance
file_handler = FileHandler()

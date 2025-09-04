import os
import aiofiles
import uuid
from typing import Optional, Dict, Any, List
from fastapi import UploadFile, HTTPException
from PIL import Image
import magic
import base64
from pathlib import Path
import json

# Allowed file types
ALLOWED_EXTENSIONS = {
    'pdf': 'application/pdf',
    'jpg': 'image/jpeg',
    'jpeg': 'image/jpeg',
    'png': 'image/png',
    'gif': 'image/gif'
}

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

class FileHandler:
    def __init__(self, upload_dir: str = "./uploads"):
        self.upload_dir = Path(upload_dir)
        self.upload_dir.mkdir(exist_ok=True)
        
        # Create subdirectories
        (self.upload_dir / "documents").mkdir(exist_ok=True)
        (self.upload_dir / "forms").mkdir(exist_ok=True)
        (self.upload_dir / "temp").mkdir(exist_ok=True)

    async def validate_file(self, file: UploadFile) -> Dict[str, Any]:
        """Validate uploaded file for security and format."""
        print(f"Validating file: {file.filename}, content_type: {file.content_type}")
        
        # Check file size
        content = await file.read()
        await file.seek(0)  # Reset file pointer
        print(f"File size: {len(content)} bytes")
        
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"File too large. Maximum size is {MAX_FILE_SIZE // (1024*1024)}MB"
            )
        
        # Check file extension
        file_ext = file.filename.split('.')[-1].lower() if '.' in file.filename else ''
        if file_ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"File type not allowed. Allowed types: {list(ALLOWED_EXTENSIONS.keys())}"
            )
        
        # Verify MIME type
        try:
            mime_type = magic.from_buffer(content, mime=True)
            expected_mime = ALLOWED_EXTENSIONS[file_ext]
            print(f"Detected MIME type: {mime_type}, Expected: {expected_mime}")
            
            if mime_type != expected_mime:
                # Be more lenient with PDF detection as magic can be inconsistent
                if file_ext == 'pdf' and 'pdf' in mime_type.lower():
                    mime_type = expected_mime
                elif file_ext in ['jpg', 'jpeg'] and 'jpeg' in mime_type.lower():
                    mime_type = expected_mime  
                elif file_ext == 'png' and 'png' in mime_type.lower():
                    mime_type = expected_mime
                else:
                    print(f"MIME type mismatch: expected {expected_mime}, got {mime_type}")
                    raise HTTPException(
                        status_code=400,
                        detail=f"File content doesn't match extension. Expected {expected_mime}, got {mime_type}"
                    )
        except Exception as e:
            print(f"Error detecting MIME type: {e}")
            # Fallback to file extension validation only
            mime_type = ALLOWED_EXTENSIONS[file_ext]
        
        return {
            "content": content,
            "mime_type": mime_type,
            "file_size": len(content),
            "extension": file_ext
        }

    async def save_file(self, file: UploadFile, file_type: str, user_id: str) -> Dict[str, Any]:
        """Save uploaded file and return file info."""
        validation_result = await self.validate_file(file)
        
        # Generate unique filename
        file_id = str(uuid.uuid4())
        file_ext = validation_result["extension"]
        safe_filename = f"{file_id}.{file_ext}"
        
        # Determine subdirectory based on file type
        subdir = "documents" if file_type in ["policy", "invoice"] else "forms"
        file_path = self.upload_dir / subdir / safe_filename
        
        # Save file
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(validation_result["content"])
        
        return {
            "file_id": file_id,
            "filename": file.filename,
            "safe_filename": safe_filename,
            "file_path": str(file_path),
            "mime_type": validation_result["mime_type"],
            "file_size": validation_result["file_size"],
            "file_type": file_type
        }

    def get_file_as_base64(self, file_path: str) -> str:
        """Convert file to base64 string for processing."""
        try:
            with open(file_path, 'rb') as f:
                content = f.read()
                return base64.b64encode(content).decode('utf-8')
        except Exception as e:
            raise HTTPException(
                status_code=404,
                detail=f"File not found or cannot be read: {str(e)}"
            )

    def delete_file(self, file_path: str) -> bool:
        """Delete a file safely."""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                return True
            return False
        except Exception:
            return False

    def cleanup_temp_files(self, older_than_hours: int = 24):
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

    async def save_generated_form(self, form_content: bytes, claim_id: str, vendor_name: str) -> str:
        """Save generated PDF form."""
        safe_vendor = "".join(c for c in vendor_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
        safe_vendor = safe_vendor.replace(' ', '_')
        
        filename = f"claim_{claim_id}_{safe_vendor}.pdf"
        file_path = self.upload_dir / "forms" / filename
        
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(form_content)
        
        return str(file_path)

# Global file handler instance
file_handler = FileHandler()

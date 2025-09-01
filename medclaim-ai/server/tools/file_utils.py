from pathlib import Path
import uuid
import os

def save_upload_file(file_bytes: bytes, upload_dir: Path, original_filename: str) -> Path:
    """Save uploaded file and return path"""
    upload_dir.mkdir(exist_ok=True)
    unique_filename = f"{uuid.uuid4()}_{original_filename}"
    file_path = upload_dir / unique_filename
    with open(file_path, "wb") as f:
        f.write(file_bytes)
    return file_path

def delete_file(file_path: Path):
    """Delete a file if it exists"""
    if file_path.exists():
        os.remove(file_path)

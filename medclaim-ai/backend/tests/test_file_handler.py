"""
Test cases for file handler functionality
"""
import pytest
from unittest.mock import patch, Mock, AsyncMock
from fastapi import UploadFile
import io

from file_handler import FileHandler


class TestFileHandler:
    """Test FileHandler class functionality."""
    
    def test_init(self):
        """Test FileHandler initialization."""
        handler = FileHandler()
        assert handler.upload_dir is not None
        assert handler.upload_dir.exists()
    
    @pytest.mark.asyncio
    async def test_validate_file_success(self):
        """Test successful file validation."""
        handler = FileHandler()
        
        # Create a mock file
        file_content = b"test pdf content"
        file = UploadFile(
            filename="test.pdf",
            file=io.BytesIO(file_content),
            content_type="application/pdf"
        )
        
        result = await handler.validate_file(file)
        
        assert result["success"] is True
        assert result["filename"] == "test.pdf"
        assert result["file_size"] == len(file_content)
        assert result["file_type"] == "application/pdf"
    
    @pytest.mark.asyncio
    async def test_validate_file_invalid_type(self):
        """Test file validation with invalid type."""
        handler = FileHandler()
        
        # Create a mock file with invalid type
        file_content = b"test content"
        file = UploadFile(
            filename="test.txt",
            file=io.BytesIO(file_content),
            content_type="text/plain"
        )
        
        with pytest.raises(Exception):
            await handler.validate_file(file)
    
    @pytest.mark.asyncio
    async def test_validate_file_too_large(self):
        """Test file validation with file too large."""
        handler = FileHandler()
        
        # Create a mock file that's too large
        large_content = b"x" * (handler.MAX_FILE_SIZE + 1)
        file = UploadFile(
            filename="large.pdf",
            file=io.BytesIO(large_content),
            content_type="application/pdf"
        )
        
        with pytest.raises(Exception):
            await handler.validate_file(file)
    
    @pytest.mark.asyncio
    async def test_save_file_success(self):
        """Test successful file saving."""
        handler = FileHandler()
        
        # Create a mock file
        file_content = b"test pdf content"
        file = UploadFile(
            filename="test.pdf",
            file=io.BytesIO(file_content),
            content_type="application/pdf"
        )
        
        result = await handler.save_file(file, "user123", "policy")
        
        assert result["success"] is True
        assert "file_path" in result
        assert "filename" in result
        assert result["file_type"] == "policy"
    
    def test_get_file_as_base64(self):
        """Test getting file as base64."""
        handler = FileHandler()
        
        # Create a test file
        test_content = b"test content"
        test_file = handler.upload_dir / "test.txt"
        test_file.write_bytes(test_content)
        
        try:
            result = handler.get_file_as_base64(str(test_file))
            assert result is not None
            assert isinstance(result, str)
        finally:
            # Clean up
            if test_file.exists():
                test_file.unlink()
    
    @pytest.mark.asyncio
    async def test_save_generated_form(self):
        """Test saving generated form."""
        handler = FileHandler()
        
        form_content = b"generated form content"
        result = await handler.save_generated_form(form_content, "claim123", "test_vendor")
        
        assert result is not None
        assert isinstance(result, str)
        # Check if file was created
        form_path = handler.upload_dir / "generated_forms" / result
        assert form_path.exists()
        
        # Clean up
        if form_path.exists():
            form_path.unlink()
    
    @pytest.mark.asyncio
    async def test_cleanup_old_files(self):
        """Test cleaning up old files."""
        handler = FileHandler()
        
        # This test just ensures the method runs without error
        # In a real test, you'd create old files and verify they're deleted
        await handler.cleanup_old_files(older_than_hours=0)
        
        # If we get here without exception, the test passes
        assert True
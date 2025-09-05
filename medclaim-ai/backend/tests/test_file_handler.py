"""
Test cases for file handling functionality
"""
import pytest
from unittest.mock import patch, MagicMock, mock_open
from fastapi import UploadFile
from io import BytesIO

from file_handler import FileHandler


class TestFileHandler:
    """Test FileHandler functionality."""
    
    def test_init(self):
        """Test FileHandler initialization."""
        handler = FileHandler()
        assert handler is not None
    
    def test_get_file_extension(self):
        """Test getting file extension."""
        handler = FileHandler()
        
        # Test PDF file
        assert handler.get_file_extension("test.pdf") == "pdf"
        
        # Test JPG file
        assert handler.get_file_extension("test.jpg") == "jpg"
        
        # Test file without extension
        assert handler.get_file_extension("test") == ""
    
    def test_validate_file_type(self):
        """Test file type validation."""
        handler = FileHandler()
        
        # Test valid PDF
        assert handler.validate_file_type("test.pdf", "application/pdf") is True
        
        # Test invalid type
        assert handler.validate_file_type("test.txt", "application/pdf") is False
    
    def test_validate_file_size(self):
        """Test file size validation."""
        handler = FileHandler()
        
        # Test valid size
        assert handler.validate_file_size(1024, max_size=5000) is True
        
        # Test invalid size
        assert handler.validate_file_size(10000, max_size=5000) is False
    
    @patch('file_handler.magic.from_buffer')
    def test_detect_file_type(self, mock_magic):
        """Test file type detection."""
        handler = FileHandler()
        mock_magic.return_value = "application/pdf"
        
        file_content = b"PDF content"
        file_type = handler.detect_file_type(file_content)
        
        assert file_type == "application/pdf"
        mock_magic.assert_called_once_with(file_content)
    
    def test_generate_unique_filename(self):
        """Test unique filename generation."""
        handler = FileHandler()
        
        filename = handler.generate_unique_filename("test.pdf")
        assert filename.endswith(".pdf")
        assert "test" in filename
        assert len(filename) > len("test.pdf")
    
    def test_create_upload_directory(self):
        """Test upload directory creation."""
        handler = FileHandler()
        
        with patch('file_handler.os.makedirs') as mock_makedirs:
            handler.create_upload_directory("test_dir")
            mock_makedirs.assert_called_once_with("test_dir", exist_ok=True)
    
    def test_save_uploaded_file(self):
        """Test saving uploaded file."""
        handler = FileHandler()
        
        with patch("builtins.open", mock_open()) as mock_file:
            with patch('file_handler.os.path.exists', return_value=True):
                file_content = b"test content"
                result = handler.save_uploaded_file(file_content, "test.pdf")
                
                assert result == "test.pdf"
                mock_file.assert_called_once()
    
    def test_delete_file(self):
        """Test file deletion."""
        handler = FileHandler()
        
        with patch('file_handler.os.remove') as mock_remove:
            handler.delete_file("test.pdf")
            mock_remove.assert_called_once_with("test.pdf")
    
    def test_get_file_size(self):
        """Test getting file size."""
        handler = FileHandler()
        
        with patch('file_handler.os.path.getsize', return_value=1024):
            size = handler.get_file_size("test.pdf")
            assert size == 1024
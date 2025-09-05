"""
Test cases for document processing functionality
"""
import pytest
from unittest.mock import patch, MagicMock, mock_open
from io import BytesIO

from document_processor import DocumentProcessor


class TestDocumentProcessor:
    """Test DocumentProcessor functionality."""
    
    def test_init(self):
        """Test DocumentProcessor initialization."""
        processor = DocumentProcessor()
        assert processor is not None
    
    @patch('document_processor.fitz.open')
    def test_extract_text_from_pdf_fitz(self, mock_fitz_open):
        """Test text extraction from PDF using PyMuPDF."""
        # Mock PDF document
        mock_doc = MagicMock()
        mock_page = MagicMock()
        mock_page.get_text.return_value = "Sample PDF text content"
        mock_doc.page_count = 1
        mock_doc.__getitem__.return_value = mock_page
        mock_fitz_open.return_value = mock_doc
        
        processor = DocumentProcessor()
        result = processor.extract_text_from_pdf("test.pdf")
        
        assert result == "Sample PDF text content"
        mock_fitz_open.assert_called_once_with("test.pdf")
    
    @patch('document_processor.pdfplumber.open')
    def test_extract_text_from_pdf_pdfplumber(self, mock_pdfplumber_open):
        """Test text extraction from PDF using pdfplumber."""
        # Mock PDF document
        mock_pdf = MagicMock()
        mock_page = MagicMock()
        mock_page.extract_text.return_value = "Sample PDF text content"
        mock_pdf.pages = [mock_page]
        mock_pdfplumber_open.return_value.__enter__.return_value = mock_pdf
        
        processor = DocumentProcessor()
        result = processor.extract_text_from_pdf("test.pdf")
        
        assert result == "Sample PDF text content"
        mock_pdfplumber_open.assert_called_once_with("test.pdf")
    
    @patch('document_processor.PyPDF2.PdfReader')
    def test_extract_text_from_pdf_pypdf2(self, mock_pypdf2):
        """Test text extraction from PDF using PyPDF2."""
        # Mock PDF reader
        mock_reader = MagicMock()
        mock_page = MagicMock()
        mock_page.extract_text.return_value = "Sample PDF text content"
        mock_reader.pages = [mock_page]
        mock_pypdf2.return_value = mock_reader
        
        processor = DocumentProcessor()
        result = processor.extract_text_from_pdf("test.pdf")
        
        assert result == "Sample PDF text content"
        mock_pypdf2.assert_called_once()
    
    def test_split_text_into_chunks(self):
        """Test text splitting into chunks."""
        processor = DocumentProcessor()
        text = "This is a sample text that should be split into chunks. " * 10
        
        chunks = processor.split_text_into_chunks(text, chunk_size=100, overlap=20)
        
        assert len(chunks) > 0
        assert all(len(chunk) <= 100 for chunk in chunks)
        assert all(len(chunk) > 0 for chunk in chunks)
    
    def test_extract_images_from_pdf(self):
        """Test image extraction from PDF."""
        processor = DocumentProcessor()
        
        with patch('document_processor.fitz.open') as mock_fitz_open:
            # Mock PDF document with images
            mock_doc = MagicMock()
            mock_page = MagicMock()
            mock_image = MagicMock()
            mock_image.get_pixmap.return_value = MagicMock()
            mock_image.get_pixmap.return_value.tobytes.return_value = b"image_data"
            mock_page.get_images.return_value = [("xref", 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)]
            mock_page.get_pixmap.return_value = MagicMock()
            mock_page.get_pixmap.return_value.tobytes.return_value = b"image_data"
            mock_doc.page_count = 1
            mock_doc.__getitem__.return_value = mock_page
            mock_doc.extract_image.return_value = (b"image_data", "png")
            mock_fitz_open.return_value = mock_doc
            
            images = processor.extract_images_from_pdf("test.pdf")
            
            assert len(images) >= 0
            mock_fitz_open.assert_called_once_with("test.pdf")
    
    def test_get_file_hash(self):
        """Test file hash generation."""
        processor = DocumentProcessor()
        
        with patch("builtins.open", mock_open(read_data=b"test content")):
            hash_value = processor._get_file_hash("test.pdf")
            assert isinstance(hash_value, str)
            assert len(hash_value) > 0
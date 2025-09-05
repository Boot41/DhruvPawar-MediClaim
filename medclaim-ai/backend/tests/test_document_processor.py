"""
Test cases for document processor functionality
"""
import pytest
from unittest.mock import patch, Mock, AsyncMock
import tempfile
import os

from document_processor import DocumentProcessor


class TestDocumentProcessor:
    """Test DocumentProcessor class functionality."""
    
    def test_init(self):
        """Test DocumentProcessor initialization."""
        processor = DocumentProcessor()
        assert processor.chunk_size == 1000
        assert processor.chunk_overlap == 200
        assert processor.documents is not None
    
    def test_extract_text_from_pdf_fitz(self):
        """Test PDF text extraction using PyMuPDF."""
        processor = DocumentProcessor()
        
        # Create a temporary PDF file for testing
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_file:
            # Write some dummy PDF content
            tmp_file.write(b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n")
            tmp_file.flush()
            file_path = tmp_file.name
        
        try:
            with patch('fitz.open') as mock_fitz:
                mock_doc = Mock()
                mock_page = Mock()
                mock_page.get_text.return_value = "Sample PDF text content"
                mock_doc.__iter__.return_value = [mock_page]
                mock_doc.page_count = 1
                mock_fitz.return_value = mock_doc
                
                result = processor.extract_text_from_pdf(file_path)
                assert result == "Sample PDF text content"
        finally:
            if os.path.exists(file_path):
                os.unlink(file_path)
    
    def test_extract_text_from_pdf_pdfplumber(self):
        """Test PDF text extraction using pdfplumber."""
        processor = DocumentProcessor()
        
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_file:
            tmp_file.write(b"%PDF-1.4\n")
            tmp_file.flush()
            file_path = tmp_file.name
        
        try:
            with patch('pdfplumber.open') as mock_plumber:
                mock_pdf = Mock()
                mock_page = Mock()
                mock_page.extract_text.return_value = "Sample PDF text content\n"
                mock_pdf.pages = [mock_page]
                mock_plumber.return_value.__enter__.return_value = mock_pdf
                
                result = processor.extract_text_from_pdf(file_path)
                assert "Sample PDF text content" in result
        finally:
            if os.path.exists(file_path):
                os.unlink(file_path)
    
    def test_extract_text_from_pdf_pypdf2(self):
        """Test PDF text extraction using PyPDF2."""
        processor = DocumentProcessor()
        
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_file:
            tmp_file.write(b"%PDF-1.4\n")
            tmp_file.flush()
            file_path = tmp_file.name
        
        try:
            with patch('PyPDF2.PdfReader') as mock_reader:
                mock_pdf = Mock()
                mock_page = Mock()
                mock_page.extract_text.return_value = "Sample PDF text content"
                mock_pdf.pages = [mock_page]
                mock_reader.return_value = mock_pdf
                
                result = processor.extract_text_from_pdf(file_path)
                assert result == "Sample PDF text content"
        finally:
            if os.path.exists(file_path):
                os.unlink(file_path)
    
    def test_chunk_document(self):
        """Test document chunking."""
        processor = DocumentProcessor()
        
        text = "This is a sample document with multiple sentences. " * 50  # Make it long enough to chunk
        document_id = "test_doc_123"
        metadata = {"type": "policy", "filename": "test.pdf"}
        
        chunks = processor.chunk_document(text, document_id, metadata)
        
        assert len(chunks) > 0
        assert all("content" in chunk for chunk in chunks)
        assert all("metadata" in chunk for chunk in chunks)
        assert all(chunk["metadata"]["document_id"] == document_id for chunk in chunks)
    
    def test_create_document_chunks(self):
        """Test creating document chunks."""
        processor = DocumentProcessor()
        
        text = "This is a sample document with multiple sentences. " * 50
        document_type = "policy"
        
        chunks = processor.create_document_chunks(text, document_type)
        
        assert len(chunks) > 0
        assert all("content" in chunk for chunk in chunks)
        assert all("chunk_type" in chunk for chunk in chunks)
    
    def test_get_file_hash(self):
        """Test file hash generation."""
        processor = DocumentProcessor()
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as tmp_file:
            tmp_file.write("test content")
            tmp_file.flush()
            file_path = tmp_file.name
        
        try:
            file_hash = processor._get_file_hash(file_path)
            assert file_hash is not None
            assert isinstance(file_hash, str)
            assert len(file_hash) > 0
        finally:
            if os.path.exists(file_path):
                os.unlink(file_path)
    
    def test_determine_chunk_type(self):
        """Test chunk type determination."""
        processor = DocumentProcessor()
        
        # Test policy content
        policy_content = "Policy Number: POL123\nCoverage Amount: $100,000"
        chunk_type = processor._determine_chunk_type(policy_content, "policy")
        assert chunk_type in ["coverage_info", "policy_details", "general"]
        
        # Test invoice content
        invoice_content = "Invoice #12345\nAmount Due: $500.00"
        chunk_type = processor._determine_chunk_type(invoice_content, "invoice")
        assert chunk_type in ["billing_info", "invoice_details", "general"]
    
    def test_get_chunk_summary(self):
        """Test chunk summary generation."""
        processor = DocumentProcessor()
        
        chunks = [
            {"content": "Policy information", "chunk_type": "coverage_info"},
            {"content": "Billing details", "chunk_type": "billing_info"},
            {"content": "General information", "chunk_type": "general"}
        ]
        
        summary = processor.get_chunk_summary(chunks)
        
        assert "total_chunks" in summary
        assert "chunk_types" in summary
        assert summary["total_chunks"] == 3
        assert "coverage_info" in summary["chunk_types"]
        assert "billing_info" in summary["chunk_types"]
        assert "general" in summary["chunk_types"]
    
    def test_list_documents(self):
        """Test listing documents."""
        processor = DocumentProcessor()
        
        # Add a test document
        processor.documents["test_doc"] = {
            "id": "test_doc",
            "filename": "test.pdf",
            "content": "test content"
        }
        
        documents = processor.list_documents()
        
        assert len(documents) == 1
        assert documents[0]["id"] == "test_doc"
        assert documents[0]["filename"] == "test.pdf"
    
    def test_delete_document(self):
        """Test document deletion."""
        processor = DocumentProcessor()
        
        # Add a test document
        processor.documents["test_doc"] = {
            "id": "test_doc",
            "filename": "test.pdf",
            "content": "test content"
        }
        
        # Delete the document
        processor.delete_document("test_doc")
        
        # Verify it's deleted
        assert "test_doc" not in processor.documents
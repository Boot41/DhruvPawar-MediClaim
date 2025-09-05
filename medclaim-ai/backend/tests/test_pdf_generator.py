"""
Test cases for PDF generator functionality
"""
import pytest
from unittest.mock import patch, Mock
import tempfile
import os

from pdf_generator import PDFGenerator


class TestPDFGenerator:
    """Test PDFGenerator class functionality."""
    
    def test_init(self):
        """Test PDFGenerator initialization."""
        generator = PDFGenerator()
        assert generator.styles is not None
        assert hasattr(generator, 'setup_custom_styles')
    
    def test_generate_synthetic_claim_pdf(self):
        """Test generating synthetic claim PDF."""
        generator = PDFGenerator()
        
        form_data = {
            "patient_name": "John Doe",
            "policy_number": "POL123",
            "claim_amount": 1000.50,
            "date_of_service": "2024-01-15"
        }
        
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_file:
            output_path = tmp_file.name
        
        try:
            result = generator.generate_synthetic_claim_pdf(form_data, output_path)
            assert result == output_path
            assert os.path.exists(output_path)
            assert os.path.getsize(output_path) > 0
        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)
    
    def test_generate_vendor_claim_pdf(self):
        """Test generating vendor-specific claim PDF."""
        generator = PDFGenerator()
        
        form_data = {
            "patient_name": "Jane Smith",
            "policy_number": "POL456",
            "claim_amount": 2000.75,
            "date_of_service": "2024-01-20"
        }
        
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_file:
            output_path = tmp_file.name
        
        try:
            result = generator.generate_vendor_claim_pdf(form_data, "test_vendor", output_path)
            assert result == output_path
            assert os.path.exists(output_path)
            assert os.path.getsize(output_path) > 0
        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)
    
    def test_download_star_health_template(self):
        """Test downloading Star Health template."""
        generator = PDFGenerator()
        
        with patch('requests.get') as mock_get:
            mock_response = Mock()
            mock_response.content = b"template content"
            mock_response.status_code = 200
            mock_get.return_value = mock_response
            
            result = generator.download_star_health_template()
            assert result is not None
            assert isinstance(result, str)
    
    def test_generate_star_health_claim_pdf(self):
        """Test generating Star Health claim PDF."""
        generator = PDFGenerator()
        
        form_data = {
            "patient_name": "Bob Johnson",
            "policy_number": "STAR789",
            "claim_amount": 1500.25,
            "date_of_service": "2024-01-25"
        }
        
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_file:
            output_path = tmp_file.name
        
        try:
            result = generator.generate_star_health_claim_pdf(form_data, output_path)
            assert result == output_path
            assert os.path.exists(output_path)
            assert os.path.getsize(output_path) > 0
        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)
    
    def test_generate_star_health_style_pdf(self):
        """Test generating Star Health style PDF."""
        generator = PDFGenerator()
        
        form_data = {
            "patient_name": "Alice Brown",
            "policy_number": "STAR101",
            "claim_amount": 3000.00,
            "date_of_service": "2024-01-30"
        }
        
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_file:
            output_path = tmp_file.name
        
        try:
            result = generator.generate_star_health_style_pdf(form_data, output_path)
            assert result == output_path
            assert os.path.exists(output_path)
            assert os.path.getsize(output_path) > 0
        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)
    
    def test_generate_pdf_from_template(self):
        """Test generating PDF from template URL."""
        generator = PDFGenerator()
        
        form_data = {
            "patient_name": "Charlie Wilson",
            "policy_number": "TEMP202",
            "claim_amount": 2500.50,
            "date_of_service": "2024-02-01"
        }
        
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_file:
            output_path = tmp_file.name
        
        try:
            with patch('requests.get') as mock_get:
                mock_response = Mock()
                mock_response.content = b"template content"
                mock_response.status_code = 200
                mock_get.return_value = mock_response
                
                result = generator.generate_pdf_from_template(
                    form_data, "http://example.com/template.pdf", output_path
                )
                assert result == output_path
                assert os.path.exists(output_path)
                assert os.path.getsize(output_path) > 0
        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)
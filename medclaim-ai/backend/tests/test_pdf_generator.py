"""
Test cases for PDF generation functionality
"""
import pytest
from unittest.mock import patch, MagicMock
from io import BytesIO

from pdf_generator import PDFGenerator


class TestPDFGenerator:
    """Test PDFGenerator functionality."""
    
    def test_init(self):
        """Test PDFGenerator initialization."""
        generator = PDFGenerator()
        assert generator is not None
    
    @patch('pdf_generator.Canvas')
    def test_create_synthetic_claim_form(self, mock_canvas):
        """Test creating synthetic claim form."""
        generator = PDFGenerator()
        mock_canvas_instance = MagicMock()
        mock_canvas.return_value.__enter__.return_value = mock_canvas_instance
        
        result = generator.create_synthetic_claim_form({
            "patient_name": "John Doe",
            "policy_number": "POL123456",
            "claim_amount": 1000.00
        })
        
        assert result is not None
        assert isinstance(result, bytes)
        assert len(result) > 0
        mock_canvas.assert_called_once()
    
    @patch('pdf_generator.Canvas')
    def test_create_vendor_specific_form(self, mock_canvas):
        """Test creating vendor-specific form."""
        generator = PDFGenerator()
        mock_canvas_instance = MagicMock()
        mock_canvas.return_value.__enter__.return_value = mock_canvas_instance
        
        result = generator.create_vendor_specific_form("test_insurance", {
            "patient_name": "John Doe",
            "policy_number": "POL123456",
            "claim_amount": 1000.00
        })
        
        assert result is not None
        assert isinstance(result, bytes)
        assert len(result) > 0
        mock_canvas.assert_called_once()
    
    def test_get_form_template_url(self):
        """Test getting form template URL."""
        generator = PDFGenerator()
        
        # Test with known vendor
        url = generator.get_form_template_url("test_insurance")
        assert url is not None
        assert isinstance(url, str)
        
        # Test with unknown vendor
        url = generator.get_form_template_url("unknown_vendor")
        assert url is None
    
    def test_validate_claim_data(self):
        """Test validating claim data."""
        generator = PDFGenerator()
        
        # Test valid data
        valid_data = {
            "patient_name": "John Doe",
            "policy_number": "POL123456",
            "claim_amount": 1000.00
        }
        assert generator.validate_claim_data(valid_data) is True
        
        # Test invalid data
        invalid_data = {
            "patient_name": "",
            "policy_number": "POL123456",
            "claim_amount": -100.00
        }
        assert generator.validate_claim_data(invalid_data) is False
    
    def test_format_currency(self):
        """Test currency formatting."""
        generator = PDFGenerator()
        
        # Test positive amount
        formatted = generator.format_currency(1000.50)
        assert formatted == "$1,000.50"
        
        # Test zero amount
        formatted = generator.format_currency(0)
        assert formatted == "$0.00"
        
        # Test negative amount
        formatted = generator.format_currency(-100.25)
        assert formatted == "-$100.25"
    
    def test_get_vendor_config(self):
        """Test getting vendor configuration."""
        generator = PDFGenerator()
        
        # Test with known vendor
        config = generator.get_vendor_config("test_insurance")
        assert config is not None
        assert "form_template_url" in config
        
        # Test with unknown vendor
        config = generator.get_vendor_config("unknown_vendor")
        assert config is None
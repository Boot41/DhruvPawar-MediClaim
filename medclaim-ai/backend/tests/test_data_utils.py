"""
Test cases for data utility functions
"""
import pytest
import re


def clean_numerical_value(value):
    """
    Clean numerical values by removing currency symbols and percentage signs.
    
    Args:
        value: String or number that may contain currency symbols or percentage signs
        
    Returns:
        float: Cleaned numerical value
    """
    if isinstance(value, (int, float)):
        return float(value)
    
    if isinstance(value, str):
        # Remove currency symbols, commas, and percentage signs
        cleaned = re.sub(r'[$,%]', '', value.strip())
        try:
            return float(cleaned)
        except ValueError:
            return 0.0
    
    return 0.0


class TestDataUtils:
    """Test data utility functions."""
    
    def test_clean_numerical_value_with_currency(self):
        """Test cleaning values with currency symbols."""
        assert clean_numerical_value("$1,000.50") == 1000.50
        assert clean_numerical_value("$500") == 500.0
        assert clean_numerical_value("$0.00") == 0.0
    
    def test_clean_numerical_value_with_percentage(self):
        """Test cleaning values with percentage signs."""
        assert clean_numerical_value("20%") == 20.0
        assert clean_numerical_value("15.5%") == 15.5
        assert clean_numerical_value("0%") == 0.0
    
    def test_clean_numerical_value_with_commas(self):
        """Test cleaning values with commas."""
        assert clean_numerical_value("1,000,000") == 1000000.0
        assert clean_numerical_value("500,000.75") == 500000.75
    
    def test_clean_numerical_value_already_numeric(self):
        """Test cleaning already numeric values."""
        assert clean_numerical_value(1000.50) == 1000.50
        assert clean_numerical_value(500) == 500.0
        assert clean_numerical_value(0) == 0.0
    
    def test_clean_numerical_value_invalid_input(self):
        """Test cleaning invalid input."""
        assert clean_numerical_value("invalid") == 0.0
        assert clean_numerical_value("") == 0.0
        assert clean_numerical_value(None) == 0.0
    
    def test_clean_coverage_data(self):
        """Test cleaning coverage data with mixed formats."""
        coverage_data = {
            "coverage_amount": "$500,000",
            "deductible": "$10,000.00",
            "copay_percentage": "20%",
            "total_amount": "1,000.50"
        }
        
        cleaned_data = {
            "coverage_amount": clean_numerical_value(coverage_data["coverage_amount"]),
            "deductible": clean_numerical_value(coverage_data["deductible"]),
            "copay_percentage": clean_numerical_value(coverage_data["copay_percentage"]),
            "total_amount": clean_numerical_value(coverage_data["total_amount"])
        }
        
        assert cleaned_data["coverage_amount"] == 500000.0
        assert cleaned_data["deductible"] == 10000.0
        assert cleaned_data["copay_percentage"] == 20.0
        assert cleaned_data["total_amount"] == 1000.50

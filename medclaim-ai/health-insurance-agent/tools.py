# health_insurance_agent/tools.py
from typing import Dict, List
import re
from google.adk.tools import FunctionTool
import requests

# Tool: Lookup policy details
#BACKEND_API_URL = "http://localhost:8000"
def policy_lookup_tool(policy_number: str, user_id: str) -> Dict:
    """
    Retrieves policy details given a policy number and user ID.
    """
    # Mock policy database; replace with real API/database
    mock_policies = {
        "POL123456": {
            "user_id":"user001",
            "policyholder_name": "John Doe",
            "coverage_limit": 500000,
            "deductible": 2500,
            "copay_percentage": 20,
            "coverage_types": ["hospitalization", "outpatient", "prescription", "diagnostic"],
            "policy_status": "active",
            "premium": 1200,
            "family_members": ["John Doe", "Jane Doe"]
        },
        "POL789012": {
            "user_id":"user002",
            "policyholder_name": "Dhruv Pawar",
            "coverage_limit": 100000,
            "deductible": 5000,
            "copay_percentage": 25,
            "coverage_types": ["hospitalization", "outpatient", "prescription", "diagnostic"],
            "policy_status": "active",
            "premium": 1500,
            "family_members": ["Vreen Pawar", "Jane Doe", "John Doe"]
        }
    }
    return mock_policies.get(policy_number, {"error": "Policy not found"})
# Tool: Calculate coverage and out-of-pocket
def coverage_calculator_tool(treatment_cost: float, policy_number: str) -> Dict:
    """
    Calculates coverage amounts and out-of-pocket costs for a given treatment and policy.
    """
    policy = policy_lookup_tool(policy_number, '')
    if 'error' in policy:
        return policy
    deductible = policy["deductible"]
    copay_pct = policy["copay_percentage"] / 100
    coverage_limit = policy["coverage_limit"]
    if treatment_cost <= deductible:
        out_of_pocket = treatment_cost
        insurance_covers = 0
    else:
        remaining_cost = treatment_cost - deductible
        insurance_covers = min(remaining_cost * (1 - copay_pct), coverage_limit)
        out_of_pocket = treatment_cost - insurance_covers
    return {
        "treatment_cost": treatment_cost,
        "insurance_covers": round(insurance_covers, 2),
        "out_of_pocket": round(out_of_pocket, 2),
        "deductible_applied": min(deductible, treatment_cost)
    }

# Tool: Analyze uploaded medical bill (simulate OCR)
#def ocr_tool(document_text: str) -> Dict:
#    """
#    Simulates OCR by extracting procedure codes and costs from bill text.
#    """
#    procedure_codes = re.findall(r'\\b\\d{5}\\b', document_text)
#    costs = [float(cost.replace(',', '')) for cost in re.findall(r'\\$(\\d+(?:,\\d{3})*(?:\\.\\d{2})?)', document_text)]
#    return {"procedure_codes": procedure_codes, "costs": costs, "total_cost": sum(costs)}
def ocr_tool(document_b64: str) -> Dict:
    """
    Accepts a base64-encoded string of the document image.
    Decodes it, performs OCR, and extracts information.
    """
    try:
        # Decode base64 string to bytes
        document_bytes = base64.b64decode(document_b64)
        image = Image.open(io.BytesIO(document_bytes))
        
        # Perform OCR
        extracted_text = pytesseract.image_to_string(image)
        
        # Extract data
        patient_name = extract_patient_name(extracted_text)
        dates = extract_dates(extracted_text)
        procedure_codes = re.findall(r'\b\d{5}\b', extracted_text)
        costs = [float(cost.replace(',', '')) for cost in re.findall(r'\$(\d+(?:,\d{3})*(?:\.\d{2})?)', extracted_text)]
        total_cost = sum(costs)
        
        return {
            "extracted_text": extracted_text,
            "patient_name": patient_name,
            "dates": dates,
            "procedure_codes": procedure_codes,
            "costs": costs,
            "total_cost": total_cost
        }
    except Exception as e:
        return {"error": f"OCR processing failed: {str(e)}"}

def extract_patient_name(ocr_text: str) -> str:
    match = re.search(r'(?:Patient Name|Name|Patient):?\s*([A-Za-z,.\s]+)', ocr_text, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return "Unknown"

def extract_dates(ocr_text: str) -> list:
    date_pattern = r'\b(?:\d{1,2}[-/]\d{1,2}[-/]\d{2,4}|\d{4}[-/]\d{1,2}[-/]\d{1,2})\b'
    return re.findall(date_pattern, ocr_text)

# Tool: Validate if procedures are covered
def eligibility_api_tool(procedure_codes: List[str], policy_number: str) -> Dict:
    """
    Validates if given procedure codes are covered under the policy.
    """
    # Mock covered procedures
    covered = {
    "99213": {"name": "Office or other outpatient visit", "coverage": 100},
    "80053": {"name": "Comprehensive metabolic panel", "coverage": 80},
    "93000": {"name": "Electrocardiogram", "coverage": 90},
    "36415": {"name": "Collection of venous blood", "coverage": 100},
    "85025": {"name": "Complete blood count", "coverage": 90},
    "84443": {"name": "Thyroid stimulating hormone", "coverage": 85},
    "93010": {"name": "Electrocardiogram interpretation", "coverage": 80},
    "90791": {"name": "Psychiatric diagnostic evaluation", "coverage": 70},
    "71020": {"name": "Chest X-ray", "coverage": 90},
    "99214": {"name": "Office or other outpatient visit (extended)", "coverage": 100},
    "70551": {"name": "MRI Scan", "coverage": 90},
}
    results = []
    for code in procedure_codes:
        coverage = covered.get(code, 0)
        results.append({"procedure_code": code, "covered": bool(coverage), "coverage_percentage": coverage})
    return {"results": results}

# Tool: Generate filled claim form
def form_generation_tool(patient_data: dict, medical_data: dict, policy_data: dict) -> Dict:
    """
    Creates and fills insurance claim form based on patient, medical, and policy data.
    """
    claim_form = {
        "claim_number": "CLM-" + policy_data.get("policyholder_name", "UNKNOWN")[:3].upper() + "-001",
        "patient_info": patient_data,
        "policy_number": policy_data.get("policyholder_name", "UNKNOWN"),
        "medical_details": medical_data
    }
    return claim_form

# Tool: Simulate claim submission to API
def insurance_api_tool(claim_form: dict) -> Dict:
    """
    Simulates submission to insurance provider.
    """
    return {"status": "submitted", "tracking_number": "TRK-12345678"}

# Tool: Get claim status
def claim_status_tool(tracking_number: str) -> Dict:
    """
    Gets claim status from provider.
    """
    mock_status = {
        "TRK-12345678": {"status": "Processing", "last_updated": "2025-09-02"}
    }
    return mock_status.get(tracking_number, {"error": "Tracking number not found"})

# Register as FunctionTool objects if needed
policy_lookup_func_tool = FunctionTool(func=policy_lookup_tool)
coverage_calculator_func_tool = FunctionTool(func=coverage_calculator_tool)
ocr_func_tool = FunctionTool(func=ocr_tool)
eligibility_func_tool = FunctionTool(func=eligibility_api_tool)
form_generation_func_tool = FunctionTool(func=form_generation_tool)
insurance_api_func_tool = FunctionTool(func=insurance_api_tool)
claim_status_func_tool = FunctionTool(func=claim_status_tool)

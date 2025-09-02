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
def ocr_tool(document_text: str) -> Dict:
    """
    Simulates OCR by extracting procedure codes and costs from bill text.
    """
    procedure_codes = re.findall(r'\\b\\d{5}\\b', document_text)
    costs = [float(cost.replace(',', '')) for cost in re.findall(r'\\$(\\d+(?:,\\d{3})*(?:\\.\\d{2})?)', document_text)]
    return {"procedure_codes": procedure_codes, "costs": costs, "total_cost": sum(costs)}

# Tool: Validate if procedures are covered
def eligibility_api_tool(procedure_codes: List[str], policy_number: str) -> Dict:
    """
    Validates if given procedure codes are covered under the policy.
    """
    # Mock covered procedures
    covered = {"99213": 100, "80053": 80}
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

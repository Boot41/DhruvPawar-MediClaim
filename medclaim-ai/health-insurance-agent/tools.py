"""Custom tools for health insurance claim processing"""
from typing import Dict, List
import json
import re

def policy_lookup_tool(policy_number: str, user_id: str) -> Dict:
    """Retrieves policy details from insurance database"""
    # Mock policy data - replace with actual database call
    mock_policies = {
        "POL123456": {
            "policy_number": policy_number,
            "policyholder_name": "John Doe",
            "coverage_limit": 500000,
            "deductible": 2500,
            "copay_percentage": 20,
            "coverage_types": ["hospitalization", "outpatient", "prescription", "diagnostic"],
            "policy_status": "active",
            "premium": 1200,
            "family_members": ["John Doe", "Jane Doe", "Little Doe"]
        },
        "POL789012": {
            "policy_number": policy_number,
            "policyholder_name": "Alice Smith",
            "coverage_limit": 300000,
            "deductible": 1500,
            "copay_percentage": 15,
            "coverage_types": ["hospitalization", "outpatient", "prescription"],
            "policy_status": "active",
            "premium": 800,
            "family_members": ["Alice Smith"]
        }
    }
    
    if policy_number in mock_policies:
        return {
            "status": "success",
            "policy_data": mock_policies[policy_number]
        }
    else:
        return {
            "status": "error",
            "message": f"Policy {policy_number} not found. Please check the policy number."
        }

def coverage_calculator_tool(treatment_cost: float, policy_number: str) -> Dict:
    """Calculates coverage amounts and out-of-pocket costs"""
    # Get policy details first
    policy_result = policy_lookup_tool(policy_number, "current_user")
    
    if policy_result["status"] == "error":
        return policy_result
    
    policy = policy_result["policy_data"]
    deductible = policy["deductible"]
    copay_pct = policy["copay_percentage"] / 100
    coverage_limit = policy["coverage_limit"]
    
    if treatment_cost <= deductible:
        out_of_pocket = treatment_cost
        insurance_covers = 0
        deductible_applied = treatment_cost
    else:
        remaining_cost = treatment_cost - deductible
        insurance_covers = min(remaining_cost * (1 - copay_pct), coverage_limit)
        out_of_pocket = treatment_cost - insurance_covers
        deductible_applied = deductible
    
    return {
        "status": "success",
        "calculation": {
            "treatment_cost": treatment_cost,
            "insurance_covers": round(insurance_covers, 2),
            "out_of_pocket": round(out_of_pocket, 2),
            "deductible_applied": deductible_applied,
            "copay_percentage": policy["copay_percentage"]
        }
    }

def check_claim_eligibility(procedure_codes: List[str], policy_number: str) -> Dict:
    """Check if medical procedures are covered under the policy"""
    # Mock covered procedures - replace with actual database
    covered_procedures = {
        "99213": {"name": "Office Visit", "coverage": 100},
        "99214": {"name": "Extended Office Visit", "coverage": 100},
        "80053": {"name": "Comprehensive Blood Panel", "coverage": 80},
        "36415": {"name": "Blood Draw", "coverage": 100},
        "85025": {"name": "Complete Blood Count", "coverage": 90},
        "84443": {"name": "Blood Sugar Test", "coverage": 90},
        "93000": {"name": "ECG", "coverage": 85}
    }
    
    policy_result = policy_lookup_tool(policy_number, "current_user")
    if policy_result["status"] == "error":
        return policy_result
    
    eligibility_results = []
    for code in procedure_codes:
        if code in covered_procedures:
            eligibility_results.append({
                "procedure_code": code,
                "procedure_name": covered_procedures[code]["name"],
                "covered": True,
                "coverage_percentage": covered_procedures[code]["coverage"]
            })
        else:
            eligibility_results.append({
                "procedure_code": code,
                "procedure_name": "Unknown Procedure",
                "covered": False,
                "coverage_percentage": 0
            })
    
    return {
        "status": "success",
        "eligibility_results": eligibility_results
    }

def generate_claim_estimate(medical_bill_text: str, policy_number: str) -> Dict:
    """Extract information from medical bill text and generate claim estimate"""
    # Simple regex parsing - replace with OCR/NLP in production
    
    # Extract procedure codes
    procedure_codes = re.findall(r'\b\d{5}\b', medical_bill_text)
    
    # Extract costs
    cost_matches = re.findall(r'\$(\d+(?:,\d{3})*(?:\.\d{2})?)', medical_bill_text)
    costs = [float(cost.replace(',', '')) for cost in cost_matches]
    total_cost = sum(costs) if costs else 0
    
    if not procedure_codes or total_cost == 0:
        return {
            "status": "error",
            "message": "Could not extract procedure codes or costs from the medical bill. Please provide a clearer bill or enter details manually."
        }
    
    # Check eligibility
    eligibility = check_claim_eligibility(procedure_codes, policy_number)
    if eligibility["status"] == "error":
        return eligibility
    
    # Calculate coverage
    coverage_calc = coverage_calculator_tool(total_cost, policy_number)
    if coverage_calc["status"] == "error":
        return coverage_calc
    
    return {
        "status": "success",
        "bill_analysis": {
            "extracted_procedures": eligibility["eligibility_results"],
            "total_bill_amount": total_cost,
            "coverage_calculation": coverage_calc["calculation"]
        }
    }

def get_claim_status(tracking_number: str) -> Dict:
    """Get status of submitted claim"""
    # Mock claim statuses
    mock_claims = {
        "CLM-ABC12345": {
            "status": "Processing",
            "submission_date": "2025-08-15",
            "estimated_completion": "2025-08-22",
            "current_stage": "Medical Review"
        },
        "CLM-XYZ67890": {
            "status": "Approved",
            "submission_date": "2025-08-10",
            "completion_date": "2025-08-18",
            "approved_amount": 1850.00,
            "payment_date": "2025-08-20"
        }
    }
    
    if tracking_number in mock_claims:
        return {
            "status": "success",
            "claim_details": mock_claims[tracking_number]
        }
    else:
        return {
            "status": "error",
            "message": f"Claim with tracking number {tracking_number} not found."
        }

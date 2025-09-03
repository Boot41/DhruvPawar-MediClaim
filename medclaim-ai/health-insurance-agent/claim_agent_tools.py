from typing import Dict, Any
from google.adk.tools import FunctionTool

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



#get popular vendors tool

# Preloaded popular vendors
POPULAR_VENDORS = [
    {
        "name": "Star Health Insurance",
        "form_url": "https://d28c6jni2fmamz.cloudfront.net/CLAIMFORM_89ec9742bd.pdf"
    },
    {
        "name": "HDFC ERGO",
        "form_url": "https://www.hdfcergo.com/docs/default-source/downloads/claim-forms/myoptima-secure---cf.pdf"
    },
    {
        "name": "ICICI Lombard",
        "form_url": "https://www.icicilombard.com/docs/default-source/default-document-library/claim_form_ihealthcare.pdf"
    },
    {
        "name": "New India Assurance",
        "form_url": "https://www.newindia.co.in/assets/docs/know-more/health/arogya-sanjeevani/e&o-claim-form.pdf"
    },
    {
        "name": "Max Bupa (Niva Bupa)",
        "form_url": "https://transactions.nivabupa.com/pages/doc/claim_form/ReimbursementClaimForm.pdf"
    }
]


def get_popular_vendors() -> Dict[str, Any]:
    """
    Returns a list of popular health insurance vendors
    and their claim form URLs.
    """
    return {"vendors": POPULAR_VENDORS}


get_popular_vendors_tool = FunctionTool(func=get_popular_vendors)
form_generation_func_tool = FunctionTool(func=form_generation_tool)
insurance_api_func_tool = FunctionTool(func=insurance_api_tool)
claim_status_func_tool = FunctionTool(func=claim_status_tool)

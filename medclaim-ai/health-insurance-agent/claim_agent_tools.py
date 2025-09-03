from typing import Dict, Any
from google.adk.tools import FunctionTool, google_search
from google.adk.agents import LlmAgent

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




# --- LLM Agent for Google Search ---
vendor_search_llm_agent = LlmAgent(
    name="VendorClaimFormSearcher",
    model="gemini-2.5-flash",
    instruction="""
    You are an assistant that finds official health insurance claim form URLs.
    When given a vendor name, search the web using the google_search tool and return:
    1. Vendor Name
    2. Official Claim Form URL (PDF if possible)
    If no official form is found, reply with 'No URL found'.
    """,
    tools=[google_search],
    output_key="claim_form_url"
)

# --- Production-ready Tool ---
def vendor_search_tool(vendor_name: str) -> Dict[str, Any]:
    """
    Returns the official claim form URL for a given vendor.
    1. Checks preloaded popular vendors first.
    2. If not found, performs Google search using LLM agent.
    """
    # Check preloaded vendors
    for vendor in POPULAR_VENDORS:
        if vendor_name.lower() in vendor["name"].lower():
            return {"vendor_name": vendor["name"], "form_url": vendor["form_url"], "source": "preloaded"}

    # If not preloaded, use Google search
    query = f"{vendor_name} official health insurance claim form PDF site:{vendor_name.lower().replace(' ', '')}.com"
    search_response = vendor_search_llm_agent.run({"query": query})

    form_url = search_response.get("claim_form_url", "No URL found")
    return {"vendor_name": vendor_name, "form_url": form_url, "source": "google_search" if form_url != "No URL found" else "not_found"}

# Wrap as FunctionTool for ADK integration
vendor_search_func_tool = FunctionTool(func=vendor_search_tool)
get_popular_vendors_tool = FunctionTool(func=get_popular_vendors)
form_generation_func_tool = FunctionTool(func=form_generation_tool)
insurance_api_func_tool = FunctionTool(func=insurance_api_tool)
claim_status_func_tool = FunctionTool(func=claim_status_tool)

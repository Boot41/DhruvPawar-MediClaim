from typing import Dict, Any
from google.adk.tools import FunctionTool, google_search
from google.adk.agents import LlmAgent
from PyPDF2 import PdfReader
import json
from pdfrw import PdfReader, PdfWriter, PageMerge
from reportlab.pdfgen import canvas
from io import BytesIO
import requests
import os

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
    # Step 1: Check preloaded vendors
    for vendor in POPULAR_VENDORS:
        if vendor_name.lower() in vendor["name"].lower():
            return {
                "vendor_name": vendor["name"],
                "form_url": vendor["form_url"],
                "source": "preloaded"
            }

    # Step 2: Construct Google search query
    query = f"{vendor_name} official health insurance claim form PDF"

    try:
        llm_response_text = vendor_search_llm_agent.call({"query": query})["text"]
        # Try parsing as JSON
        search_response = json.loads(llm_response_text)
        form_url = search_response.get("claim_form_url")
        if not form_url:
            # Optional: extract first URL from text if JSON is empty or invalid
            urls = re.findall(r'https?://\S+', llm_response_text)
            form_url = urls[0] if urls else None
    except Exception as e:
        return {
            "vendor_name": vendor_name,
            "form_url": None,
            "source": "error",
            "error_message": str(e)
        }

    return {
        "vendor_name": vendor_name,
        "form_url": form_url,
        "source": "google_search" if form_url else "not_found"
    }
###########################

vendor_search_func_tool = FunctionTool(func=vendor_search_tool)
get_popular_vendors_tool = FunctionTool(func=get_popular_vendors)

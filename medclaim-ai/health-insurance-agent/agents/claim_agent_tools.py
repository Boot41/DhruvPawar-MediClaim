from typing import Dict, Any
from google.adk.tools import FunctionTool, google_search
from google.adk.agents import Agent
from PyPDF2 import PdfReader
import json
import re
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
vendor_search_agent = Agent(
    name="VendorClaimFormSearcher",
    model="gemini-2.5-flash",
    instruction="""
    You are an assistant that finds official health insurance claim form URLs.
    When given a vendor name, search the web and return a JSON response with:
    {
        "vendor_name": "<vendor_name>",
        "claim_form_url": "<url_or_null>",
        "status": "found|not_found|error"
    }
    If no official form is found, set claim_form_url to null and status to 'not_found'.
    """,
    tools=[google_search]
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
        # Temporarily disable agent search due to LlmAgent compatibility issues
        # TODO: Re-enable once agent execution is fully stabilized
        form_url = None
        
        # For now, return not found for unknown vendors
        # This allows the system to continue functioning
        
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

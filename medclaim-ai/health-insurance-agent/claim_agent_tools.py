from typing import Dict, Any
from google.adk.tools import FunctionTool, google_search
from google.adk.agents import LlmAgent
from PyPDF2 import PdfReader
import json
from pdfrw import PdfReader, PdfWriter, PageMerge
from reportlab.pdfgen import canvas
from io import BytesIO
import requests
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

def test_pdf_download_tool(pdf_url: str) -> Dict[str, Any]:
    """
    Downloads a PDF from the given URL and verifies it is a valid PDF.

    Args:
        pdf_url (str): The URL of the PDF to download.

    Returns:
        Dict[str, Any]: Status and basic info about the PDF or error message.
    """
    try:
        # Download PDF
        response = requests.get(pdf_url, timeout=10)
        if response.status_code != 200:
            return {"success": False, "error": f"Failed to download PDF, status code {response.status_code}"}

        content_type = response.headers.get("Content-Type", "").lower()
        if "pdf" not in content_type:
            return {"success": False, "error": f"URL did not return a PDF (Content-Type: {content_type})"}

        # Validate PDF
        pdf_bytes = io.BytesIO(response.content)
        try:
            reader = PdfReader(pdf_bytes)
            num_pages = len(reader.pages)
        except Exception as e:
            return {"success": False, "error": f"Downloaded file is not a valid PDF: {str(e)}"}

        return {"success": True, "num_pages": num_pages, "size_bytes": len(response.content)}

    except requests.RequestException as e:
        return {"success": False, "error": f"Request failed: {str(e)}"}
#####################################################################


# --- Add this to your tools file ---

def fill_local_pdf_tool(
    vendor_name: str,
    user_data: Dict[str, str],
    output_pdf_path: str,
    field_coordinates: Dict[str, tuple]
) -> Dict[str, Any]:
    """
    Fills a local vendor PDF form with provided user data.
    Returns a result dictionary with:
      - success: bool
      - filled_pdf_path: str (local path)
      - filled_pdf_base64: str (base64 encoded content for download)
      - error: str (if any)
    """
    try:
        LOCAL_VENDOR_PDFS = {
            "HDFC ERGO": "./claim_forms/hdfc_ergo.pdf",
            "Star Health Insurance": "./claim_forms/star_health.pdf",
            "ICICI Lombard": "./claim_forms/icici_lombard.pdf",
            "New India Assurance": "./claim_forms/new_india_assurance.pdf",
            "Max Bupa (Niva Bupa)": "./claim_forms/max_bupa.pdf"
        }
        if vendor_name not in LOCAL_VENDOR_PDFS:
            return {"success": False, "error": f"Vendor PDF not found for '{vendor_name}'"}
        template_pdf_path = LOCAL_VENDOR_PDFS[vendor_name]
        if not os.path.exists(template_pdf_path):
            return {"success": False, "error": f"Template PDF not found at '{template_pdf_path}'"}

        # Read template PDF
        template_pdf = PdfReader(template_pdf_path)
        page_count = len(template_pdf.pages)

        # Create overlay pages
        overlay_pages = []
        for page_num in range(page_count):
            packet = BytesIO()
            c = canvas.Canvas(packet)
            c.setFont("Helvetica", 10)
            for field, value in user_data.items():
                if field in field_coordinates and field_coordinates[field][2] == page_num:
                    x, y, _ = field_coordinates[field]
                    c.drawString(x, y, str(value))
            c.save()
            packet.seek(0)
            overlay_page = PdfReader(fdata=packet.read()).pages[0]
            overlay_pages.append(overlay_page)

        # Merge overlay onto template
        for page_num, page in enumerate(template_pdf.pages):
            if page_num < len(overlay_pages):
                PageMerge(page).add(overlay_pages[page_num]).render()

        # Write filled PDF to file
        PdfWriter(output_pdf_path, trailer=template_pdf).write()

        # Read written PDF bytes and base64 encode for easy transmission
        with open(output_pdf_path, "rb") as f:
            pdf_bytes = f.read()
        pdf_b64 = base64.b64encode(pdf_bytes).decode("utf-8")

        return {
            "success": True,
            "filled_pdf_path": output_pdf_path,
            "filled_pdf_base64": pdf_b64,
            "message": "Form filled successfully"
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

# Wrap as ADK FunctionTool
fill_local_pdf_func_tool = FunctionTool(func=fill_local_pdf_tool)
test_pdf_download_func_tool = FunctionTool(func=test_pdf_download_tool)
vendor_search_func_tool = FunctionTool(func=vendor_search_tool)
get_popular_vendors_tool = FunctionTool(func=get_popular_vendors)
form_generation_func_tool = FunctionTool(func=form_generation_tool)
insurance_api_func_tool = FunctionTool(func=insurance_api_tool)
claim_status_func_tool = FunctionTool(func=claim_status_tool)

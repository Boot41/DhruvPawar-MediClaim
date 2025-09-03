import os
import requests
from google.adk.tools import FunctionTool
from typing import List, Dict, Any, Tuple
import fitz  # PyMuPDF
import io
from PyPDF2 import PdfReader
from google.adk.agents import LlmAgent
import json
import base64
from io import BytesIO
from pdfrw import PdfReader, PdfWriter, PageMerge
from reportlab.pdfgen import canvas
from .claim_forms import *

LOCAL_VENDOR_PDFS = {
    "HDFC ERGO": hdfc_ergo,
    "Star Health Insurance": star_health,
    "ICICI Lombard": icici_lombard,
    "New India Assurance": new_india_assurance,
    "Max Bupa (Niva Bupa)": max_bupa
}

def retrieve_pdf_tool(vendor_name: str) -> Dict[str, Any]:
    """Retrieve PDF from local repo or attempt download if missing."""
    # Check local first
    if vendor_name in LOCAL_VENDOR_PDFS and os.path.isfile(LOCAL_VENDOR_PDFS[vendor_name]):
        return {
            "success": True,
            "pdf_path": LOCAL_VENDOR_PDFS[vendor_name],
            "source": "local"
        }
    
    # Fallback: search URL from vendor list or via LLM (not implemented here)
    return {
        "success": False,
        "error": f"Local PDF for vendor '{vendor_name}' not found."
    }


def test_pdf_download_tool(pdf_url: str) -> Dict[str, Any]:
    """Download and validate PDF from URL."""
    try:
        resp = requests.get(pdf_url, timeout=15)
        resp.raise_for_status()
    except Exception as e:
        return {"success": False, "error": f"Download failed: {str(e)}"}
    
    content_type = resp.headers.get("Content-Type", "").lower()
    if "pdf" not in content_type:
        return {"success": False, "error": "URL did not return a PDF content type."}
    
    try:
        pdf_bytes = io.BytesIO(resp.content)
        reader = PdfReader(pdf_bytes)
        num_pages = len(reader.pages)
    except Exception as e:
        return {"success": False, "error": f"Invalid PDF file: {str(e)}"}
    
    return {"success": True, "num_pages": num_pages, "content": resp.content}



def extract_form_fields_tool(pdf_path: str) -> Dict[str, Any]:
    """Extract fillable form fields metadata from PDF."""
    try:
        doc = fitz.open(pdf_path)
        fields = []
        for page_num in range(len(doc)):
            widgets = doc[page_num].widgets()
            if not widgets:
                continue
            for w in widgets:
                fields.append({
                    "name": w.field_name,
                    "type": w.field_type,
                    "page": page_num,
                    "rect": w.rect,  # bbox coordinates
                    "flags": w.field_flags if hasattr(w, 'field_flags') else None
                })
        return {"success": True, "fields": fields}
    except Exception as e:
        return {"success": False, "error": str(e)}

# Initialize a specialized LLM agent for mapping
field_mapping_llm_agent = LlmAgent(
    name="FieldMappingAgent",
    model="gemini-2.5-flash",
    instruction="""
You are an expert assistant that maps user data keys to PDF form fields.

Inputs:
- A list of PDF form fields including field names, labels, and types.
- Structured user data keys and example values.
- Vendor name for context.

Output:
Return a JSON object mapping PDF field names to user data keys for filling. 
If no suitable mapping is found for a PDF field, omit it.

Example output:
{
  "InsuredName": "patient_name",
  "PolicyID": "policy_number",
  "AdmissionDate": "admission_date"
}
    """,
    output_key="mapping_json"
)

def map_data_to_fields_tool(
    user_data: Dict[str, Any],
    form_fields: List[Dict[str, Any]],
    vendor_name: str
) -> Dict[str, Any]:
    """
    Calls the LLM to generate field-to-data mappings.
    """
    try:
        # Prepare a simplified JSON input to LLM
        simplified_fields = [
            {"name": f["name"], "type": f.get("type", "Unknown")}
            for f in form_fields
        ]
        prompt_input = {
            "vendor_name": vendor_name,
            "user_data_keys": list(user_data.keys()),
            "form_fields": simplified_fields
        }
        
        # Call LLM agent
        response = field_mapping_llm_agent.call({"prompt_input": json.dumps(prompt_input)})
        mapping_text = response.get("text") or response.get("mapping_json")
        
        # Load JSON mapping from LLM response
        mapping = json.loads(mapping_text)
        
        # Validate keys in returned mapping
        valid_mapping = {pdf_field: user_data[key] for pdf_field, key in mapping.items() if key in user_data}
        
        return {"success": True, "mapping": valid_mapping}
    
    except Exception as e:
        return {"success": False, "error": f"LLM mapping failed: {str(e)}"}



def fill_local_pdf_tool(
    vendor_name: str,
    user_data: Dict[str, str],
    output_pdf_path: str,
    field_coordinates: Dict[str, Tuple[float, float, int]]
) -> Dict[str, Any]:
    """Fill local PDF form with user data over field coordinates."""
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

        template_pdf = PdfReader(template_pdf_path)
        page_count = len(template_pdf.pages)

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

        for page_num, page in enumerate(template_pdf.pages):
            if page_num < len(overlay_pages):
                PageMerge(page).add(overlay_pages[page_num]).render()

        PdfWriter(output_pdf_path, trailer=template_pdf).write()

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

fill_local_pdf_func_tool = FunctionTool(func=fill_local_pdf_tool)


def identify_missing_fields_tool(
    required_fields: List[str],
    filled_data: Dict[str, Any]
) -> Dict[str, Any]:
    missing = [field for field in required_fields if not filled_data.get(field)]
    return {
        "success": True,
        "missing_fields": missing
    }


def generate_missing_data_prompt_tool(missing_fields: List[str]) -> Dict[str, str]:
    if not missing_fields:
        return {"prompt": "All required fields are filled."}
    
    prompt = "Please provide the following missing information to complete your claim form:\n"
    for field in missing_fields:
        prompt += f"- {field.replace('_', ' ').title()}\n"
    return {"prompt": prompt.strip()}

generate_missing_data_prompt_func_tool = FunctionTool(func=generate_missing_data_prompt_tool)
retrieve_pdf_func_tool = FunctionTool(func=retrieve_pdf_tool)
test_pdf_download_func_tool = FunctionTool(func=test_pdf_download_tool)
extract_form_fields_func_tool = FunctionTool(func=extract_form_fields_tool)
map_data_to_fields_func_tool = FunctionTool(func=map_data_to_fields_tool)
fill_local_pdf_func_tool = FunctionTool(func=fill_local_pdf_tool)
identify_missing_fields_func_tool = FunctionTool(func=identify_missing_fields_tool)


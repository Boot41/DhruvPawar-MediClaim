# health_insurance_agent/tools.py
from typing import Dict, List
import re
from google.adk.tools import FunctionTool, google_search
import base64
import io
from PIL import Image
import pytesseract
from typing import Dict, Any
import json
from typing import Dict, Any

"""
Dynamic Insurance Tools:
Pipeline to extract, normalize, calculate and submit insurance claims
based only on uploaded documents (policy + invoice).
"""

# =============== OCR / Extraction Tools ===============

def ocr_extract_text(document_b64: str) -> str:
    """Extracts raw text from base64-encoded PDF/image."""
    try:
        document_bytes = base64.b64decode(document_b64)
        image = Image.open(io.BytesIO(document_bytes))
        return pytesseract.image_to_string(image)
    except Exception as e:
        return f"OCR failed: {str(e)}"

def extract_policy_data(policy_text: str) -> Dict:
    """
    Extracts structured fields from a policy document text.
    Uses regex / heuristics now, can be replaced with LLM parsing later.
    """
    data = {}

    # Coverage limit
    match = re.search(r'Coverage Limit[:\s]+₹?([\d,]+)', policy_text, re.I)
    if match:
        data["coverage_limit"] = int(match.group(1).replace(",", ""))

    # Deductible
    match = re.search(r'Deductible[:\s]+₹?([\d,]+)', policy_text, re.I)
    if match:
        data["deductible"] = int(match.group(1).replace(",", ""))

    # Copay
    match = re.search(r'Copay[:\s]+(\d+)%', policy_text, re.I)
    if match:
        data["copay_percentage"] = int(match.group(1))

    # Room rent
    match = re.search(r'Room Rent Limit[:\s]+₹?([\d,]+)', policy_text, re.I)
    if match:
        data["room_rent_limit"] = int(match.group(1).replace(",", ""))

    data.setdefault("coverage_limit", 500000)
    data.setdefault("deductible", 0)
    data.setdefault("copay_percentage", 0)

    return data


def extract_invoice_data(invoice_text: str) -> Dict:
    """
    Extracts structured fields from a hospital invoice text.
    Returns line items with procedure codes + costs.
    """
    line_items = []

    # Procedure codes (CPT / ICD)
    procedure_codes = re.findall(r'\b\d{4,5}\b', invoice_text)

    # Costs
    costs = [float(c.replace(",", "")) for c in re.findall(r'₹?(\d+(?:,\d{3})*(?:\.\d{2})?)', invoice_text)]

    # Pair them if possible
    for i, cost in enumerate(costs):
        code = procedure_codes[i] if i < len(procedure_codes) else "UNKNOWN"
        line_items.append({"procedure_code": code, "cost": cost})

    total_cost = sum(costs)

    # Extract room rent separately if present
    match = re.search(r'Room Rent[:\s]+₹?(\d+(?:,\d{3})*)', invoice_text, re.I)
    room_rent = int(match.group(1).replace(",", "")) if match else None

    return {
        "line_items": line_items,
        "total_cost": total_cost,
        "room_rent": room_rent
    }


# =============== Dynamic Coverage Calculator ===============

def dynamic_coverage_calculator(policy_data: str, invoice_data: str) -> Dict[str, Any]:
    """
    Calculate coverage eligibility based on policy and invoice data (expects JSON strings).
    Uses deductible, copay, and coverage limit logic from the old calculator.
    """
    # Parse JSON strings
    try:
        policy_data = json.loads(policy_data)
    except Exception:
        raise ValueError("policy_data must be valid JSON")

    try:
        invoice_data = json.loads(invoice_data)
    except Exception:
        raise ValueError("invoice_data must be valid JSON")

    # Extract policy values (old logic preserved)
    deductible = policy_data.get("deductible", 0)
    copay_pct = policy_data.get("copay_percentage", 0) / 100
    coverage_limit = policy_data.get("coverage_limit", float("inf"))

    # Extract invoice values
    total_cost = invoice_data.get("total_cost", 0)

    # --- Core Insurance Calculation Logic (from old tool) ---
    if total_cost <= deductible:
        out_of_pocket = total_cost
        insurance_covers = 0
    else:
        remaining_cost = total_cost - deductible
        insurance_covers = min(remaining_cost * (1 - copay_pct), coverage_limit)
        out_of_pocket = total_cost - insurance_covers

    # Track which services were covered (optional enrichment)
    covered_services = policy_data.get("covered_services", [])
    patient_services = invoice_data.get("services", {})
    eligible_services = [s for s in patient_services if s in covered_services]

    return {
        "total_cost": total_cost,
        "insurance_covers": round(insurance_covers, 2),
        "out_of_pocket": round(out_of_pocket, 2),
        "deductible_applied": min(deductible, total_cost),
        "eligible_services": eligible_services
    }

###############################################################################################
ocr_func_tool = FunctionTool(func=ocr_extract_text)
policy_extract_func_tool = FunctionTool(func=extract_policy_data)
invoice_extract_func_tool = FunctionTool(func=extract_invoice_data)
coverage_calc_func_tool = FunctionTool(func=dynamic_coverage_calculator)
import os
import requests
import re
from google.adk.tools import FunctionTool
from typing import List, Dict, Any, Tuple
import fitz  # PyMuPDF
import io
from PyPDF2 import PdfReader
from google.adk.agents import Agent
import json
import base64
from io import BytesIO
from pdfrw import PdfReader, PdfWriter, PageMerge
from reportlab.pdfgen import canvas

LOCAL_VENDOR_PDFS = {
    "HDFC ERGO": "./claim_forms/hdfc_ergo.pdf",
    "Star Health Insurance": "./claim_forms/star_health.pdf",
    "ICICI Lombard": "./claim_forms/icici_lombard.pdf",
    "New India Assurance": "./claim_forms/new_india_assurance.pdf",
    "Max Bupa (Niva Bupa)": "./claim_forms/max_bupa.pdf"
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
    """Extract fillable form fields metadata from PDF, with fallback for non-fillable PDFs."""
    try:
        doc = fitz.open(pdf_path)
        fields = []
        
        # Try to extract fillable form fields first
        for page_num in range(len(doc)):
            widgets = doc[page_num].widgets()
            if not widgets:
                continue
            for w in widgets:
                fields.append({
                    "name": w.field_name,
                    "type": w.field_type,
                    "page": page_num,
                    "rect": w.rect,
                    "flags": w.field_flags if hasattr(w, 'field_flags') else None
                })
        
        # If no fillable fields found, extract text regions for coordinate-based filling
        if not fields:
            text_fields = extract_text_regions_from_pdf(doc)
            return {"success": True, "fields": [], "text_regions": text_fields, "fillable": False}
            
        return {"success": True, "fields": fields, "fillable": True}
    except Exception as e:
        return {"success": False, "error": str(e)}

def extract_text_regions_from_pdf(doc) -> List[Dict[str, Any]]:
    """Extract text regions from PDF with enhanced accuracy for field mapping."""
    text_regions = []
    
    # Enhanced field patterns with priority scoring
    field_patterns = [
        # High priority patterns (exact matches)
        {"pattern": r'(?i)^\s*(patient\s+name|insured\s+name|name\s+of\s+patient)\s*[:\-_]?\s*$', "priority": 10, "field_type": "patient_name"},
        {"pattern": r'(?i)^\s*(policy\s+number|policy\s+no\.?|policy\s+#)\s*[:\-_]?\s*$', "priority": 10, "field_type": "policy_number"},
        {"pattern": r'(?i)^\s*(hospital\s+name|facility\s+name)\s*[:\-_]?\s*$', "priority": 10, "field_type": "hospital_name"},
        {"pattern": r'(?i)^\s*(total\s+amount|claim\s+amount|amount)\s*[:\-_]?\s*$', "priority": 10, "field_type": "total_cost"},
        {"pattern": r'(?i)^\s*(admission\s+date|date\s+of\s+admission|service\s+date)\s*[:\-_]?\s*$', "priority": 10, "field_type": "admission_date"},
        {"pattern": r'(?i)^\s*(phone|mobile|contact\s+number)\s*[:\-_]?\s*$', "priority": 10, "field_type": "phone_number"},
        {"pattern": r'(?i)^\s*(address|patient\s+address)\s*[:\-_]?\s*$', "priority": 10, "field_type": "address"},
        
        # Medium priority patterns (partial matches)
        {"pattern": r'(?i)(name)\s*[:\-_]?\s*$', "priority": 7, "field_type": "patient_name"},
        {"pattern": r'(?i)(policy)\s*[:\-_]?\s*$', "priority": 7, "field_type": "policy_number"},
        {"pattern": r'(?i)(hospital)\s*[:\-_]?\s*$', "priority": 7, "field_type": "hospital_name"},
        {"pattern": r'(?i)(amount|total)\s*[:\-_]?\s*$', "priority": 7, "field_type": "total_cost"},
        {"pattern": r'(?i)(date)\s*[:\-_]?\s*$', "priority": 5, "field_type": "admission_date"},
        {"pattern": r'(?i)(phone|mobile)\s*[:\-_]?\s*$', "priority": 7, "field_type": "phone_number"},
        {"pattern": r'(?i)(address)\s*[:\-_]?\s*$', "priority": 7, "field_type": "address"},
    ]
    
    for page_num in range(len(doc)):
        page = doc[page_num]
        text_dict = page.get_text("dict")
        
        for block in text_dict["blocks"]:
            if "lines" in block:
                for line in block["lines"]:
                    for span in line["spans"]:
                        text = span["text"].strip()
                        if text and len(text) > 2:  # Ignore very short text
                            bbox = span["bbox"]
                            
                            # Check against all patterns and find best match
                            best_match = None
                            best_priority = 0
                            
                            for pattern_info in field_patterns:
                                if re.search(pattern_info["pattern"], text):
                                    if pattern_info["priority"] > best_priority:
                                        best_match = pattern_info
                                        best_priority = pattern_info["priority"]
                            
                            if best_match:
                                # Calculate more accurate input area based on text analysis
                                input_area = calculate_input_area(bbox, text, page)
                                
                                text_regions.append({
                                    "text": text,
                                    "page": page_num,
                                    "bbox": bbox,
                                    "field_type": best_match["field_type"],
                                    "priority": best_priority,
                                    "estimated_input_area": input_area
                                })
    
    # Sort by priority (highest first) and remove duplicates
    text_regions.sort(key=lambda x: x["priority"], reverse=True)
    unique_regions = []
    seen_field_types = set()
    
    for region in text_regions:
        if region["field_type"] not in seen_field_types:
            unique_regions.append(region)
            seen_field_types.add(region["field_type"])
    
    return unique_regions

def calculate_input_area(bbox, text, page) -> Dict[str, float]:
    """Calculate more accurate input area based on text analysis."""
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    # Analyze surrounding area for better positioning
    page_width = page.rect.width
    page_height = page.rect.height
    
    # Smart positioning based on text characteristics
    if ":" in text or "-" in text:
        # Text likely ends with colon/dash, input area should be right after
        input_x = bbox[2] + 10
        input_width = min(200, page_width - input_x - 20)
    else:
        # Text might be above or beside input area
        input_x = bbox[2] + 5
        input_width = min(150, page_width - input_x - 20)
    
    # Ensure input area stays within page bounds
    input_x = max(10, min(input_x, page_width - input_width - 10))
    
    return {
        "x": input_x,
        "y": bbox[1],
        "width": input_width,
        "height": max(text_height, 15)  # Minimum height for readability
    }

# Initialize a specialized agent for mapping
field_mapping_agent = Agent(
    name="FieldMappingAgent",
    model="gemini-2.5-flash",
    instruction="""
You are an expert assistant that maps user data to PDF form fields or text regions.

Return a JSON object mapping field identifiers to user data keys:
{
  "field_identifier": "user_data_key",
  "coordinates": {"x": 100, "y": 200, "page": 0}
}

For non-fillable PDFs, use text region information to determine coordinates.
    """
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
        
        # Use fallback mapping for now due to agent compatibility issues
        # TODO: Re-enable agent mapping once execution is stabilized
        mapping = create_fallback_mapping(user_data, form_fields)
        
        # Validate keys in returned mapping
        valid_mapping = {pdf_field: user_data[key] for pdf_field, key in mapping.items() if key in user_data}
        
        return {"success": True, "mapping": valid_mapping}
    
    except Exception as e:
        return {"success": False, "error": f"Mapping failed: {str(e)}"}



def fill_local_pdf_tool(
    vendor_name: str,
    user_data: Dict[str, str],
    output_pdf_path: str,
    field_coordinates: Dict[str, Tuple[float, float, int]] = None
) -> Dict[str, Any]:
    """Fill local PDF form with user data using intelligent coordinate placement."""
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

        # If no coordinates provided, use text region extraction to find positions
        if not field_coordinates:
            field_coordinates = get_smart_coordinates(template_pdf_path, user_data)
            
        # Use PyMuPDF for enhanced text overlay with validation
        import fitz
        doc = fitz.open(template_pdf_path)
        
        # Track successful placements for reporting
        placed_fields = []
        failed_fields = []
        
        # Add text overlays to each page with enhanced formatting
        for page_num in range(len(doc)):
            page = doc[page_num]
            
            for field, value in user_data.items():
                if field in field_coordinates:
                    coord_info = field_coordinates[field]
                    if len(coord_info) >= 3 and coord_info[2] == page_num:
                        x, y = coord_info[0], coord_info[1]
                        
                        try:
                            # Validate coordinates are within page bounds
                            if x < 0 or y < 0 or x > page.rect.width or y > page.rect.height:
                                # Adjust coordinates to fit within page
                                x = max(10, min(x, page.rect.width - 200))
                                y = max(20, min(y, page.rect.height - 20))
                            
                            # Choose appropriate font size based on content length
                            text_value = str(value)
                            if len(text_value) > 30:
                                fontsize = 8
                            elif len(text_value) > 20:
                                fontsize = 9
                            else:
                                fontsize = 10
                            
                            # Insert text with better formatting
                            page.insert_text(
                                (x, y + 12),  # Better baseline adjustment
                                text_value,
                                fontsize=fontsize,
                                color=(0, 0, 0),  # Black text
                                fontname="helv",  # Helvetica
                                render_mode=0  # Fill text
                            )
                            
                            # Optional: Add a subtle background for better readability
                            if len(text_value) > 15:  # Only for longer text
                                bg_rect = fitz.Rect(x-2, y, x + len(text_value) * fontsize * 0.6, y + 14)
                                page.draw_rect(bg_rect, color=(1, 1, 1), fill=(1, 1, 1), width=0.5)
                                # Re-insert text over background
                                page.insert_text(
                                    (x, y + 12),
                                    text_value,
                                    fontsize=fontsize,
                                    color=(0, 0, 0),
                                    fontname="helv"
                                )
                            
                            placed_fields.append(field)
                            
                        except Exception as e:
                            failed_fields.append((field, str(e)))
                            # Try fallback positioning
                            try:
                                fallback_y = 50 + len(placed_fields) * 20
                                page.insert_text(
                                    (50, fallback_y),
                                    f"{field}: {value}",
                                    fontsize=9,
                                    color=(0.5, 0, 0),  # Dark red for fallback
                                    fontname="helv"
                                )
                                placed_fields.append(field)
                            except:
                                pass
        
        # Save the modified PDF
        doc.save(output_pdf_path)
        doc.close()
        
        # Read and encode the result
        with open(output_pdf_path, "rb") as f:
            pdf_bytes = f.read()
        pdf_b64 = base64.b64encode(pdf_bytes).decode("utf-8")

        return {
            "success": True,
            "filled_pdf_path": output_pdf_path,
            "filled_pdf_base64": pdf_b64,
            "message": f"Form filled successfully: {len(placed_fields)}/{len(user_data)} fields placed",
            "coordinates_used": field_coordinates,
            "placed_fields": placed_fields,
            "failed_fields": failed_fields,
            "accuracy_score": len(placed_fields) / len(user_data) * 100 if user_data else 0
        }
        
    except Exception as e:
        return {"success": False, "error": f"PDF filling failed: {str(e)}"}

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

def create_fallback_mapping(user_data: Dict[str, Any], form_fields: List[Dict[str, Any]]) -> Dict[str, str]:
    """Create a basic fallback mapping when LLM mapping fails."""
    mapping = {}
    user_keys = list(user_data.keys())
    
    # Simple keyword matching
    field_mappings = {
        'name': ['patient_name', 'policyholder_name', 'insured_name'],
        'policy': ['policy_number', 'policy_no'],
        'phone': ['phone_number', 'mobile', 'contact'],
        'address': ['address', 'patient_address'],
        'amount': ['total_cost', 'claim_amount'],
        'date': ['admission_date', 'service_date', 'date_of_birth']
    }
    
    for field in form_fields:
        field_name = field.get('name', '').lower()
        for keyword, possible_keys in field_mappings.items():
            if keyword in field_name:
                for key in possible_keys:
                    if key in user_keys:
                        mapping[field['name']] = key
                        break
                break
    
    return mapping

def get_smart_coordinates(pdf_path: str, user_data: Dict[str, str]) -> Dict[str, Tuple[float, float, int]]:
    """Generate highly accurate coordinates using enhanced text region analysis."""
    try:
        # Extract text regions with enhanced accuracy
        fields_result = extract_form_fields_tool(pdf_path)
        coordinates = {}
        
        if fields_result.get("success") and "text_regions" in fields_result:
            text_regions = fields_result["text_regions"]
            
            # Direct field type mapping (most accurate)
            direct_mappings = {
                "patient_name": "patient_name",
                "policy_number": "policy_number", 
                "total_cost": "total_cost",
                "hospital_name": "hospital_name",
                "admission_date": "admission_date",
                "phone_number": "phone_number",
                "address": "address"
            }
            
            # First pass: Direct field type matching
            for region in text_regions:
                field_type = region.get("field_type")
                if field_type in direct_mappings and direct_mappings[field_type] in user_data:
                    input_area = region["estimated_input_area"]
                    coordinates[direct_mappings[field_type]] = (
                        input_area["x"],
                        input_area["y"] + 5,  # Slight vertical adjustment for better alignment
                        region["page"]
                    )
            
            # Second pass: Fuzzy matching for unmapped fields
            fuzzy_mappings = {
                "patient_name": ["name", "patient", "insured", "proposer", "employee"],
                "policy_number": ["policy", "number", "certificate"],
                "total_cost": ["amount", "total", "cost", "claim", "bill"],
                "hospital_name": ["hospital", "facility", "clinic", "medical"],
                "admission_date": ["date", "admission", "service", "treatment"],
                "phone_number": ["phone", "mobile", "contact", "telephone"],
                "address": ["address", "location", "residence"]
            }
            
            for user_field in user_data:
                if user_field not in coordinates and user_field in fuzzy_mappings:
                    keywords = fuzzy_mappings[user_field]
                    best_match = None
                    best_score = 0
                    
                    for region in text_regions:
                        region_text = region["text"].lower()
                        # Calculate match score based on keyword presence and priority
                        score = 0
                        for keyword in keywords:
                            if keyword in region_text:
                                score += region.get("priority", 1)
                                if region_text.startswith(keyword):
                                    score += 2  # Bonus for starting with keyword
                        
                        if score > best_score:
                            best_match = region
                            best_score = score
                    
                    if best_match:
                        input_area = best_match["estimated_input_area"]
                        coordinates[user_field] = (
                            input_area["x"],
                            input_area["y"] + 5,
                            best_match["page"]
                        )
        
        # Enhanced fallback with better spacing
        missing_fields = [field for field in user_data if field not in coordinates]
        if missing_fields:
            # Use a more sophisticated fallback layout
            fallback_coords = generate_fallback_layout(pdf_path, missing_fields)
            coordinates.update(fallback_coords)
                
        return coordinates
        
    except Exception as e:
        # Return enhanced fallback coordinates
        return generate_fallback_layout(pdf_path, list(user_data.keys()))

def generate_fallback_layout(pdf_path: str, fields: List[str]) -> Dict[str, Tuple[float, float, int]]:
    """Generate well-spaced fallback coordinates when smart detection fails."""
    coordinates = {}
    
    try:
        # Get PDF dimensions for better layout
        doc = fitz.open(pdf_path)
        page = doc[0]
        page_width = page.rect.width
        page_height = page.rect.height
        doc.close()
        
        # Calculate optimal layout
        margin = 50
        start_y = 100
        line_height = 25
        
        # Two-column layout if many fields
        if len(fields) > 6:
            col1_x = margin
            col2_x = page_width / 2 + margin
            
            for i, field in enumerate(fields):
                if i % 2 == 0:  # Left column
                    x = col1_x
                    y = start_y + (i // 2) * line_height
                else:  # Right column
                    x = col2_x
                    y = start_y + (i // 2) * line_height
                
                coordinates[field] = (x, y, 0)
        else:
            # Single column layout
            x = margin
            for i, field in enumerate(fields):
                y = start_y + i * line_height
                coordinates[field] = (x, y, 0)
                
    except Exception:
        # Ultimate fallback
        for i, field in enumerate(fields):
            coordinates[field] = (100, 100 + i * 20, 0)
    
    return coordinates

def validate_pdf_coordinates(pdf_path: str, coordinates: Dict[str, tuple]) -> Dict[str, Any]:
    """Validate that coordinates are within PDF page bounds."""
    try:
        doc = fitz.open(pdf_path)
        validated_coords = {}
        
        for field, (x, y, page_num) in coordinates.items():
            if page_num < len(doc):
                page = doc[page_num]
                page_rect = page.rect
                
                # Ensure coordinates are within page bounds
                x = max(0, min(x, page_rect.width - 100))  # Leave space for text
                y = max(0, min(y, page_rect.height - 20))   # Leave space for text height
                
                validated_coords[field] = (x, y, page_num)
            else:
                validated_coords[field] = (100, 100, 0)  # Default safe position
        
        doc.close()
        return {"success": True, "coordinates": validated_coords}
    except Exception as e:
        return {"success": False, "error": str(e)}

# Function tools
generate_missing_data_prompt_func_tool = FunctionTool(func=generate_missing_data_prompt_tool)
retrieve_pdf_func_tool = FunctionTool(func=retrieve_pdf_tool)
test_pdf_download_func_tool = FunctionTool(func=test_pdf_download_tool)
extract_form_fields_func_tool = FunctionTool(func=extract_form_fields_tool)
map_data_to_fields_func_tool = FunctionTool(func=map_data_to_fields_tool)
fill_local_pdf_func_tool = FunctionTool(func=fill_local_pdf_tool)
identify_missing_fields_func_tool = FunctionTool(func=identify_missing_fields_tool)
validate_pdf_coordinates_func_tool = FunctionTool(func=validate_pdf_coordinates)


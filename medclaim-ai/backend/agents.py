"""
Google ADK Agents for Insurance Document Processing
Specialized agents for different aspects of insurance claim processing
"""
import os
from dotenv import load_dotenv
from google.adk.agents import Agent
from google.adk.tools import FunctionTool
from google.adk.tools.agent_tool import AgentTool
from typing import Dict, Any, List
import json

# Load environment variables
load_dotenv()

# Get Google API key
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY environment variable is required")

# =============== TOOLS ===============

def extract_document_data_tool(document_chunks: str) -> Dict[str, Any]:
    """Extract structured data from document chunks."""
    try:
        chunks = json.loads(document_chunks)
        extracted_data = {
            "policy_number": None,
            "insurer_name": None,
            "coverage_amount": None,
            "deductible": None,
            "copay_percentage": None,
            "patient_name": None,
            "hospital_name": None,
            "total_amount": None,
            "service_date": None,
            "procedures": []
        }
        
        # Process each chunk to extract relevant information
        for chunk in chunks:
            content = chunk.get("content", "").lower()
            chunk_type = chunk.get("metadata", {}).get("chunk_type", "")
            
            # Extract policy information
            if "policy" in chunk_type or "coverage" in chunk_type:
                # Add extraction logic here
                pass
            
            # Extract invoice information
            elif "patient" in chunk_type or "billing" in chunk_type:
                # Add extraction logic here
                pass
        
        return {"success": True, "extracted_data": extracted_data}
    except Exception as e:
        return {"success": False, "error": str(e)}

def calculate_coverage_tool(policy_data: str, invoice_data: str) -> Dict[str, Any]:
    """Calculate insurance coverage based on policy and invoice data."""
    try:
        policy = json.loads(policy_data)
        invoice = json.loads(invoice_data)
        
        # Basic coverage calculation
        total_cost = invoice.get("total_amount", 0)
        deductible = policy.get("deductible", 0)
        copay_pct = policy.get("copay_percentage", 0) / 100
        coverage_limit = policy.get("coverage_amount", float('inf'))
        
        if total_cost <= deductible:
            out_of_pocket = total_cost
            insurance_covers = 0
        else:
            remaining_cost = total_cost - deductible
            insurance_covers = min(remaining_cost * (1 - copay_pct), coverage_limit)
            out_of_pocket = total_cost - insurance_covers
        
        return {
            "success": True,
            "coverage_analysis": {
                "total_cost": total_cost,
                "deductible_applied": min(deductible, total_cost),
                "insurance_covers": round(insurance_covers, 2),
                "out_of_pocket": round(out_of_pocket, 2),
                "coverage_percentage": round((insurance_covers / total_cost) * 100, 2) if total_cost > 0 else 0
            }
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

def generate_claim_form_tool(claim_data: str) -> Dict[str, Any]:
    """Generate a claim form based on extracted data."""
    try:
        data = json.loads(claim_data)
        
        # Generate form fields
        form_fields = {
            "patient_name": data.get("patient_name", ""),
            "policy_number": data.get("policy_number", ""),
            "insurer_name": data.get("insurer_name", ""),
            "hospital_name": data.get("hospital_name", ""),
            "service_date": data.get("service_date", ""),
            "total_amount": data.get("total_amount", ""),
            "procedures": data.get("procedures", []),
            "coverage_amount": data.get("coverage_amount", ""),
            "deductible": data.get("deductible", ""),
            "copay_percentage": data.get("copay_percentage", "")
        }
        
        return {
            "success": True,
            "form_data": form_fields,
            "preview_html": generate_form_preview(form_fields)
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

def generate_form_preview(form_data: Dict[str, Any]) -> str:
    """Generate HTML preview of the claim form."""
    html = f"""
    <div class="claim-form-preview">
        <h3>Insurance Claim Form Preview</h3>
        <div class="form-section">
            <h4>Patient Information</h4>
            <p><strong>Name:</strong> {form_data.get('patient_name', 'N/A')}</p>
            <p><strong>Policy Number:</strong> {form_data.get('policy_number', 'N/A')}</p>
            <p><strong>Insurer:</strong> {form_data.get('insurer_name', 'N/A')}</p>
        </div>
        <div class="form-section">
            <h4>Medical Information</h4>
            <p><strong>Hospital:</strong> {form_data.get('hospital_name', 'N/A')}</p>
            <p><strong>Service Date:</strong> {form_data.get('service_date', 'N/A')}</p>
            <p><strong>Total Amount:</strong> ₹{form_data.get('total_amount', 'N/A')}</p>
        </div>
        <div class="form-section">
            <h4>Coverage Information</h4>
            <p><strong>Coverage Amount:</strong> ₹{form_data.get('coverage_amount', 'N/A')}</p>
            <p><strong>Deductible:</strong> ₹{form_data.get('deductible', 'N/A')}</p>
            <p><strong>Co-pay:</strong> {form_data.get('copay_percentage', 'N/A')}%</p>
        </div>
    </div>
    """
    return html

# Create function tools
extract_data_tool = FunctionTool(func=extract_document_data_tool)
coverage_calc_tool = FunctionTool(func=calculate_coverage_tool)
claim_form_tool = FunctionTool(func=generate_claim_form_tool)

# =============== AGENTS ===============

# 1. Document Analysis Agent
document_analyzer_agent = Agent(
    name="document_analyzer",
    model="gemini-2.5-flash",
    instruction="""
    You are a specialized insurance document analyzer. Your role is to:
    
    1. Analyze complete insurance documents (policies, invoices, medical records)
    2. Extract key information from the entire document content holistically
    3. Identify document types and relevant sections across the whole document
    4. Provide structured data extraction in JSON format
    
    When analyzing documents:
    - You have access to the COMPLETE document content, not just chunks
    - Analyze the entire document to understand context and relationships
    - Focus on policy numbers, coverage amounts, deductibles, copays
    - Extract patient information, hospital details, service dates
    - Identify procedures, treatments, and billing information
    - Look for information that might be spread across different sections
    - Return ONLY valid JSON with the extracted data
    
    For POLICY documents, extract:
    - policy_number: The policy identification number
    - insurer_name: The insurance company or plan name
    - coverage_amount: The total coverage/sum insured amount
    - deductible: The deductible amount
    - copay_percentage: The copay percentage
    
    For INVOICE documents, extract:
    - patient_name: The patient's name
    - hospital_name: The hospital or medical facility name
    - total_amount: The total bill amount
    - service_date: The date of service/treatment
    - procedures: List of procedures/treatments performed
    
    Be thorough and accurate in your analysis. If information is unclear or not found, use "N/A" for strings and 0 for numbers.
    """,
    tools=[extract_data_tool])

# 2. Coverage Analysis Agent
coverage_analyzer_agent = Agent(
    name="coverage_analyzer", 
    model="gemini-2.5-flash",
    instruction="""
    You are an insurance coverage specialist. Your role is to:
    
    1. Analyze insurance policies and coverage details
    2. Calculate coverage eligibility and amounts
    3. Explain insurance terminology and concepts
    4. Provide coverage recommendations
    
    When analyzing coverage:
    - Calculate what the insurance will cover vs. out-of-pocket costs
    - Explain deductibles, copays, and coverage limits
    - Identify covered vs. excluded services
    - Use the calculate_coverage_tool for precise calculations
    
    Provide clear, understandable explanations of insurance concepts.
    """,
    tools=[coverage_calc_tool])

# 3. Chat Assistant Agent
chat_assistant_agent = Agent(
    name="chat_assistant",
    model="gemini-2.5-flash", 
    instruction="""
    You are a friendly and knowledgeable insurance assistant. Your role is to:
    
    1. Answer questions about insurance policies and coverage
    2. Explain insurance terminology in simple terms
    3. Help users understand their documents
    4. Guide users through the claim filing process
    
    When chatting with users:
    - Be conversational and helpful
    - Use simple language to explain complex insurance concepts
    - Ask clarifying questions when needed
    - Provide accurate information based on uploaded documents
    - Be empathetic and understanding of user concerns
    
    Always be professional, accurate, and helpful.
    """,
    tools=[extract_data_tool, coverage_calc_tool])

# 4. Claim Form Generator Agent
claim_form_agent = Agent(
    name="claim_form_generator",
    model="gemini-2.5-flash",
    instruction="""
    You are a claim form generation specialist. Your role is to:
    
    1. Generate insurance claim forms based on document data
    2. Populate form fields with extracted information
    3. Identify missing information and request it from users
    4. Create form previews for user approval
    
    When generating claim forms:
    - Use all available document data to populate forms
    - Clearly identify any missing required fields
    - Create professional, accurate form previews
    - Use the generate_claim_form_tool to create structured forms
    
    Ensure all forms are complete and accurate before submission.
    """,
    tools=[claim_form_tool, extract_data_tool]
)

# 5. Root Coordinator Agent
root_agent = Agent(
    name="root_coordinator",
    model="gemini-2.5-flash",
    instruction="""
    You are the main coordinator for the insurance claim processing system. Your role is to:
    
    1. Route user requests to appropriate specialized agents
    2. Coordinate between different agents when needed
    3. Provide overall system guidance and support
    4. Handle complex multi-step processes
    
    Available agents:
    - document_analyzer: For analyzing uploaded documents
    - coverage_analyzer: For coverage calculations and explanations
    - chat_assistant: For general questions and support
    - claim_form_generator: For generating claim forms
    
    Route requests appropriately and coordinate responses from multiple agents when needed.
    """,
    tools=[
        AgentTool(agent=document_analyzer_agent),
        AgentTool(agent=coverage_analyzer_agent),
        AgentTool(agent=chat_assistant_agent),
        AgentTool(agent=claim_form_agent)
    ])

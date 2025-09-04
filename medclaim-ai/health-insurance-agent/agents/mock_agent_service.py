import json
import asyncio
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from database import WorkflowState, ChatMessage, Claim, Document, Vendor
from tools import extract_policy_data, extract_invoice_data, dynamic_coverage_calculator
from file_handler import file_handler
import base64

class MockAgentService:
    """Mock agent service that simulates AI processing without Google ADK dependency"""
    
    def __init__(self):
        self.agents = {
            "root": "system_coordinator",
            "policy_guidance": "policy_guidance_agent",
            "document_analyzer": "document_analyzer_agent",
            "coverage_eligibility": "coverage_eligibility_agent",
            "claim_processor": "claim_processor_agent",
            "form_automation": "form_automation_agent"
        }

    async def process_document(self, document_path: str, document_type: str, user_id: str, db: Session) -> Dict[str, Any]:
        """Process uploaded document using mock AI processing."""
        try:
            # Simulate processing delay
            await asyncio.sleep(1)
            
            if document_type == "policy":
                # Mock policy data extraction
                extracted_data = {
                    "coverage_limit": 500000,
                    "deductible": 5000,
                    "copay_percentage": 20,
                    "room_rent_limit": 5000,
                    "policy_number": "POL123456789",
                    "insurer": "Star Health Insurance",
                    "covered_services": ["Hospitalization", "Surgery", "ICU", "Consultation"]
                }
                
            elif document_type == "invoice":
                # Mock invoice data extraction
                extracted_data = {
                    "line_items": [
                        {"procedure_code": "99213", "cost": 15000, "description": "Consultation"},
                        {"procedure_code": "80053", "cost": 8000, "description": "Lab Tests"},
                        {"procedure_code": "99232", "cost": 25000, "description": "Hospital Stay"},
                        {"procedure_code": "36415", "cost": 2000, "description": "Blood Draw"}
                    ],
                    "total_cost": 50000,
                    "room_rent": 5000,
                    "hospital_name": "Apollo Hospital",
                    "patient_name": "John Doe",
                    "admission_date": "2024-01-15",
                    "discharge_date": "2024-01-18"
                }
                
            else:
                raise ValueError(f"Unsupported document type: {document_type}")
            
            return {
                "success": True,
                "extracted_data": extracted_data,
                "agent_response": {
                    "content": f"Successfully processed {document_type} document",
                    "confidence": 0.95
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "extracted_data": None
            }

    async def calculate_coverage(self, policy_data: Dict[str, Any], invoice_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate coverage using the coverage eligibility logic."""
        try:
            # Convert data to JSON strings as expected by the tool
            policy_json = json.dumps(policy_data)
            invoice_json = json.dumps(invoice_data)
            
            # Use the dynamic coverage calculator
            coverage_result = dynamic_coverage_calculator(policy_json, invoice_json)
            
            # Add percentage calculation
            if coverage_result["total_cost"] > 0:
                coverage_percentage = (coverage_result["insurance_covers"] / coverage_result["total_cost"]) * 100
            else:
                coverage_percentage = 0
            
            coverage_result["coverage_percentage"] = round(coverage_percentage, 2)
            coverage_result["policy_details"] = policy_data
            coverage_result["invoice_details"] = invoice_data
            
            return {
                "success": True,
                "coverage_analysis": coverage_result
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "coverage_analysis": None
            }

    async def get_vendors(self) -> List[Dict[str, Any]]:
        """Get list of available insurance vendors."""
        vendors = [
            {
                "id": "hdfc_ergo",
                "name": "HDFC ERGO",
                "display_name": "HDFC ERGO General Insurance",
                "logo_url": None,
                "is_active": True
            },
            {
                "id": "star_health",
                "name": "Star Health Insurance",
                "display_name": "Star Health & Allied Insurance",
                "logo_url": None,
                "is_active": True
            },
            {
                "id": "icici_lombard",
                "name": "ICICI Lombard",
                "display_name": "ICICI Lombard General Insurance",
                "logo_url": None,
                "is_active": True
            },
            {
                "id": "new_india",
                "name": "New India Assurance",
                "display_name": "The New India Assurance Company",
                "logo_url": None,
                "is_active": True
            },
            {
                "id": "max_bupa",
                "name": "Max Bupa (Niva Bupa)",
                "display_name": "Niva Bupa Health Insurance",
                "logo_url": None,
                "is_active": True
            }
        ]
        return vendors

    async def generate_claim_form(self, claim_id: str, vendor_name: str, claim_data: Dict[str, Any], db: Session) -> Dict[str, Any]:
        """Generate filled claim form using mock form automation."""
        try:
            # Simulate form generation
            await asyncio.sleep(2)
            
            # Mock form generation success
            mock_form_path = f"./uploads/forms/claim_{claim_id}_{vendor_name.replace(' ', '_')}.pdf"
            
            # Create a simple mock PDF (in real implementation, this would be actual form filling)
            with open(mock_form_path, 'w') as f:
                f.write(f"Mock claim form for {vendor_name}\nClaim ID: {claim_id}\nGenerated at: {asyncio.get_event_loop().time()}")
            
            return {
                "success": True,
                "form_path": mock_form_path,
                "download_url": f"/forms/{claim_id}/download"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    async def process_chat_message(self, message: str, session_id: str, db: Session) -> Dict[str, Any]:
        """Process chat message using mock AI agent."""
        try:
            # Get current workflow state
            workflow_state = db.query(WorkflowState).filter(
                WorkflowState.session_id == session_id
            ).order_by(WorkflowState.updated_at.desc()).first()
            
            current_step = workflow_state.current_step if workflow_state else "initial"
            
            # Generate contextual responses based on current step
            responses = {
                "initial": "Hello! I'm your AI insurance claim assistant. I'll help you process your insurance claim step by step. To get started, please upload your insurance policy document.",
                "policy_uploaded": "Great! I've processed your policy document. Now please upload your medical bill or invoice so I can calculate your coverage.",
                "invoice_uploaded": "Perfect! I've analyzed both documents. Let me calculate your coverage details.",
                "coverage_calculated": "Based on your policy and medical bills, I've calculated your coverage. Would you like to proceed with selecting an insurance vendor to file your claim?",
                "vendor_selected": "Excellent! I'll now generate your claim form with all the details filled in. This may take a moment.",
                "form_generated": "Your claim form has been generated successfully! You can download it and submit it to your insurance provider."
            }
            
            # Default response
            response_text = responses.get(current_step, 
                f"I understand you said: '{message}'. How can I help you with your insurance claim today? Please upload your policy document if you haven't already.")
            
            # Determine next step based on message content
            next_step = None
            if "upload" in message.lower() and "policy" in message.lower():
                next_step = "policy_upload"
            elif "upload" in message.lower() and ("bill" in message.lower() or "invoice" in message.lower()):
                next_step = "invoice_upload"
            elif "coverage" in message.lower() or "calculate" in message.lower():
                next_step = "coverage_analysis"
            elif "vendor" in message.lower() or "insurance" in message.lower():
                next_step = "vendor_selection"
            elif "form" in message.lower() or "generate" in message.lower():
                next_step = "form_generation"
            
            # Save chat messages
            user_message = ChatMessage(
                session_id=session_id,
                message_type="user",
                content=message,
                message_metadata=json.dumps({"timestamp": str(asyncio.get_event_loop().time())})
            )
            
            agent_message = ChatMessage(
                session_id=session_id,
                message_type="agent",
                content=response_text,
                message_metadata=json.dumps({"mock_agent": True, "current_step": current_step})
            )
            
            db.add(user_message)
            db.add(agent_message)
            db.commit()
            
            return {
                "success": True,
                "response": response_text,
                "metadata": {"mock_agent": True, "current_step": current_step},
                "next_step": next_step
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "response": "I apologize, but I encountered an error processing your message. Please try again."
            }

    async def update_workflow_state(self, session_id: str, step: str, step_data: Dict[str, Any], db: Session):
        """Update workflow state for a session."""
        try:
            workflow_state = db.query(WorkflowState).filter(
                WorkflowState.session_id == session_id
            ).order_by(WorkflowState.updated_at.desc()).first()
            
            if workflow_state:
                workflow_state.current_step = step
                workflow_state.step_data = json.dumps(step_data)
                workflow_state.updated_at = asyncio.get_event_loop().time()
            else:
                workflow_state = WorkflowState(
                    session_id=session_id,
                    current_step=step,
                    step_data=json.dumps(step_data),
                    conversation_history=json.dumps([]),
                    agent_context=json.dumps({})
                )
                db.add(workflow_state)
            
            db.commit()
            
        except Exception as e:
            print(f"Error updating workflow state: {e}")

# Global mock agent service instance
mock_agent_service = MockAgentService()

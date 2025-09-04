import json
import asyncio
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from backend.database import WorkflowState, ChatMessage, Claim, Document, Vendor
from agents.agent import root_agent, policy_guidance_agent, document_analyzer_agent, coverage_eligibility_agent, claim_processor_agent, form_automation_agent
from agents.tools import extract_policy_data, extract_invoice_data, dynamic_coverage_calculator
from agents.form_automation_tools import retrieve_pdf_tool, fill_local_pdf_func_tool
from agents.claim_agent_tools import get_popular_vendors_tool, vendor_search_func_tool
from backend.file_handler import file_handler
import base64

class AgentService:
    def __init__(self):
        self.agents = {
            "root": root_agent,
            "policy_guidance": policy_guidance_agent,
            "document_analyzer": document_analyzer_agent,
            "coverage_eligibility": coverage_eligibility_agent,
            "claim_processor": claim_processor_agent,
            "form_automation": form_automation_agent
        }

    async def process_document(self, document_path: str, document_type: str, user_id: str, db: Session) -> Dict[str, Any]:
        """Process uploaded document using appropriate agent."""
        try:
            # Convert document to base64 for agent processing
            document_b64 = file_handler.get_file_as_base64(document_path)
            
            if document_type == "policy":
                # Use policy guidance agent
                result = await self._run_agent_async("policy_guidance", {
                    "document": document_b64,
                    "task": "extract_policy_data"
                })
                
                # Extract structured data
                extracted_data = extract_policy_data(result.get("text", ""))
                
            elif document_type == "invoice":
                # Use document analyzer agent
                result = await self._run_agent_async("document_analyzer", {
                    "document": document_b64,
                    "task": "extract_invoice_data"
                })
                
                # Extract structured data
                extracted_data = extract_invoice_data(result.get("text", ""))
                
            else:
                raise ValueError(f"Unsupported document type: {document_type}")
            
            return {
                "success": True,
                "extracted_data": extracted_data,
                "agent_response": result
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "extracted_data": None
            }

    async def calculate_coverage(self, policy_data: Dict[str, Any], invoice_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate coverage using the coverage eligibility agent."""
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
        try:
            # Use the get_popular_vendors_tool
            vendors_result = get_popular_vendors_tool.func()
            
            # Format for API response
            vendors = []
            for vendor_name in vendors_result.get("vendors", []):
                vendors.append({
                    "id": vendor_name.lower().replace(" ", "_"),
                    "name": vendor_name,
                    "display_name": vendor_name,
                    "logo_url": None,
                    "is_active": True
                })
            
            return vendors
            
        except Exception as e:
            return []

    async def generate_claim_form(self, claim_id: str, vendor_name: str, claim_data: Dict[str, Any], db: Session) -> Dict[str, Any]:
        """Generate filled claim form using form automation agent."""
        try:
            # Retrieve PDF template for vendor
            pdf_result = retrieve_pdf_tool(vendor_name)
            
            if not pdf_result.get("success"):
                return {
                    "success": False,
                    "error": f"No form template found for vendor: {vendor_name}"
                }
            
            pdf_path = pdf_result["pdf_path"]
            
            # Prepare data for form filling
            form_data = {
                "policy_data": claim_data.get("policy_data", {}),
                "invoice_data": claim_data.get("invoice_data", {}),
                "coverage_analysis": claim_data.get("coverage_analysis", {}),
                "claim_id": claim_id
            }
            
            # Use form automation agent to fill the form
            fill_result = await self._run_agent_async("form_automation", {
                "pdf_path": pdf_path,
                "form_data": form_data,
                "task": "fill_claim_form"
            })
            
            if fill_result.get("success"):
                # Save the generated form
                form_content = fill_result.get("pdf_content")
                if form_content:
                    saved_path = await file_handler.save_generated_form(
                        form_content, claim_id, vendor_name
                    )
                    
                    return {
                        "success": True,
                        "form_path": saved_path,
                        "download_url": f"/api/forms/{claim_id}/download"
                    }
            
            return {
                "success": False,
                "error": "Failed to generate form"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    async def process_chat_message(self, message: str, session_id: str, db: Session) -> Dict[str, Any]:
        """Process chat message using the root agent."""
        try:
            # Get current workflow state
            workflow_state = db.query(WorkflowState).filter(
                WorkflowState.session_id == session_id
            ).order_by(WorkflowState.updated_at.desc()).first()
            
            # Prepare context
            context = {
                "message": message,
                "current_step": workflow_state.current_step if workflow_state else "initial",
                "conversation_history": json.loads(workflow_state.conversation_history) if workflow_state and workflow_state.conversation_history else [],
                "agent_context": json.loads(workflow_state.agent_context) if workflow_state and workflow_state.agent_context else {}
            }
            
            # Process with root agent
            response = await self._run_agent_async("root", context)
            
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
                content=response.get("content", ""),
                message_metadata=json.dumps(response.get("metadata", {}))
            )
            
            db.add(user_message)
            db.add(agent_message)
            db.commit()
            
            return {
                "success": True,
                "response": response.get("content", ""),
                "metadata": response.get("metadata", {}),
                "next_step": response.get("next_step")
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

    async def _run_agent_async(self, agent_name: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Run agent asynchronously."""
        try:
            agent = self.agents.get(agent_name)
            if not agent:
                raise ValueError(f"Agent {agent_name} not found")
            
            # Run agent in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, self._run_agent_sync, agent, context)
            
            return result
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "content": "I apologize, but I encountered an error. Please try again."
            }

    def _run_agent_sync(self, agent, context: Dict[str, Any]) -> Dict[str, Any]:
        """Run agent synchronously."""
        try:
            # Format context for agent
            if "message" in context:
                prompt = context["message"]
            elif "task" in context:
                prompt = f"Please {context['task']} for the provided document."
            else:
                prompt = "Please help with this request."
            
            # Run agent
            response = agent.run(prompt)
            
            return {
                "success": True,
                "content": response.content if hasattr(response, 'content') else str(response),
                "metadata": getattr(response, 'metadata', {}),
                "next_step": getattr(response, 'next_step', None)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "content": "I apologize, but I encountered an error processing your request."
            }

# Global agent service instance
agent_service = AgentService()

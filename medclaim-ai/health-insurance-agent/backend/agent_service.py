import json
import asyncio
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from backend.database import WorkflowState, ChatMessage, Claim, Document, Vendor
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent import root_agent, policy_guidance_agent, document_analyzer_agent, coverage_eligibility_agent, claim_processor_agent, form_automation_agent
from tools import extract_policy_data, extract_invoice_data, dynamic_coverage_calculator
from form_automation_tools import retrieve_pdf_tool, fill_local_pdf_func_tool
from claim_agent_tools import get_popular_vendors_tool, vendor_search_func_tool
from backend.file_handler import file_handler
import base64
# Google ADK imports for proper agent execution
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
from datetime import datetime

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
        
        # Initialize ADK components
        self.session_service = InMemorySessionService()
        self.app_name = "medclaim_ai"
        
        # Initialize runners for each agent
        self.runners = {}
        for agent_name, agent in self.agents.items():
            self.runners[agent_name] = Runner(
                agent=agent,
                app_name=self.app_name,
                session_service=self.session_service
            )

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

    async def generate_document_response(self, document_type: str, extracted_data: Dict[str, Any], session_id: str, db: Session) -> Dict[str, Any]:
        """Generate a conversational response about the processed document."""
        try:
            # Create a summary message based on document type and extracted data
            if document_type == "policy":
                response_message = self._create_policy_summary(extracted_data)
            elif document_type == "invoice":
                response_message = self._create_invoice_summary(extracted_data)
            else:
                response_message = "I've successfully processed your document and extracted the relevant information."
            
            # Save the agent response as a chat message
            agent_message = ChatMessage(
                session_id=session_id,
                message_type="agent",
                content=response_message,
                message_metadata=json.dumps({
                    "document_type": document_type,
                    "extracted_data": extracted_data,
                    "timestamp": str(datetime.now().timestamp())
                })
            )
            
            db.add(agent_message)
            db.commit()
            
            return {
                "success": True,
                "response": response_message,
                "metadata": {"document_type": document_type}
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "response": "I've processed your document, but encountered an issue generating a summary."
            }

    def _create_policy_summary(self, policy_data: Dict[str, Any]) -> str:
        """Create a conversational summary of policy data."""
        summary_parts = ["📋 **Policy Document Processed Successfully!**\n"]
        
        if policy_data.get("policy_number"):
            summary_parts.append(f"**Policy Number:** {policy_data['policy_number']}")
        
        if policy_data.get("insurer_name"):
            summary_parts.append(f"**Insurer:** {policy_data['insurer_name']}")
        
        if policy_data.get("coverage_amount"):
            summary_parts.append(f"**Coverage Amount:** ₹{policy_data['coverage_amount']:,}")
        
        if policy_data.get("deductible"):
            summary_parts.append(f"**Deductible:** ₹{policy_data['deductible']:,}")
        
        if policy_data.get("copay_percentage"):
            summary_parts.append(f"**Co-pay:** {policy_data['copay_percentage']}%")
        
        summary_parts.append("\n✅ I can now help you calculate coverage for medical bills using this policy information.")
        
        return "\n".join(summary_parts)

    def _create_invoice_summary(self, invoice_data: Dict[str, Any]) -> str:
        """Create a conversational summary of invoice data."""
        summary_parts = ["🧾 **Medical Invoice Processed Successfully!**\n"]
        
        if invoice_data.get("hospital_name"):
            summary_parts.append(f"**Hospital:** {invoice_data['hospital_name']}")
        
        if invoice_data.get("patient_name"):
            summary_parts.append(f"**Patient:** {invoice_data['patient_name']}")
        
        if invoice_data.get("total_amount"):
            summary_parts.append(f"**Total Amount:** ₹{invoice_data['total_amount']:,}")
        
        if invoice_data.get("procedures"):
            procedures = invoice_data['procedures']
            if isinstance(procedures, list) and procedures:
                summary_parts.append(f"**Procedures:** {', '.join(procedures[:3])}")
                if len(procedures) > 3:
                    summary_parts.append(f"... and {len(procedures) - 3} more")
        
        if invoice_data.get("date_of_service"):
            summary_parts.append(f"**Service Date:** {invoice_data['date_of_service']}")
        
        summary_parts.append("\n✅ I can now calculate your insurance coverage if you have a policy document uploaded.")
        
        return "\n".join(summary_parts)

    async def update_workflow_state(self, session_id: str, step: str, step_data: Dict[str, Any], db: Session):
        """Update workflow state for a session."""
        try:
            workflow_state = db.query(WorkflowState).filter(
                WorkflowState.session_id == session_id
            ).order_by(WorkflowState.updated_at.desc()).first()
            
            if workflow_state:
                workflow_state.current_step = step
                workflow_state.step_data = json.dumps(step_data)
                workflow_state.updated_at = datetime.now()
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
        """Run agent asynchronously using Google ADK Runner."""
        try:
            # Get the runner for the agent
            runner = self.runners.get(agent_name)
            if not runner:
                raise ValueError(f"Agent {agent_name} not found")
            
            # Format context for agent
            if "message" in context:
                prompt = context["message"]
            elif "task" in context:
                prompt = f"Please {context['task']} for the provided document."
            else:
                prompt = "Please help with this request."
            
            # Create user content for Google ADK
            user_content = types.Content(
                role='user',
                parts=[types.Part(text=prompt)]
            )
            
            # Generate unique session ID
            session_id = f"session_{agent_name}_{datetime.now().timestamp()}"
            user_id = context.get("user_id", "default_user")
            
            # Create session
            await self.session_service.create_session(
                app_name=self.app_name,
                user_id=user_id,
                session_id=session_id
            )
            
            # Run agent and get response
            final_response = "No response received"
            async for event in runner.run_async(
                user_id=user_id,
                session_id=session_id,
                new_message=user_content
            ):
                if event.is_final_response() and event.content and event.content.parts:
                    # Extract text from all parts, handling different part types
                    text_parts = []
                    for part in event.content.parts:
                        if hasattr(part, 'text') and part.text:
                            text_parts.append(part.text)
                    
                    if text_parts:
                        final_response = ' '.join(text_parts)
                    break
            
            return {
                "success": True,
                "content": final_response,
                "metadata": {"session_id": session_id},
                "next_step": None
            }
            
        except Exception as e:
            print(f"Agent execution error: {e}")  # Add logging for debugging
            return {
                "success": False,
                "error": str(e),
                "content": f"Agent error: {str(e)}"
            }

# Global agent service instance
agent_service = AgentService()
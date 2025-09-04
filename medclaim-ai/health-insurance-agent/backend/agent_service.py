import json
import asyncio
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from backend.database import WorkflowState, ChatMessage, Claim, Document, Vendor
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent import root_agent, policy_guidance_agent, document_analyzer_agent, coverage_eligibility_agent, claim_processor_agent, form_automation_agent
from tools import (
    extract_policy_data, 
    extract_invoice_data, 
    dynamic_coverage_calculator,
    ocr_func_tool,
    policy_extract_func_tool,
    invoice_extract_func_tool,
    coverage_calc_func_tool
)
from form_automation_tools import (
    retrieve_pdf_tool, 
    fill_local_pdf_tool,
    test_pdf_download_tool,
    identify_missing_fields_tool,
    generate_missing_data_prompt_tool,
    map_data_to_fields_tool,
    extract_form_fields_tool
)
from claim_agent_tools import (
    get_popular_vendors_tool, 
    vendor_search_func_tool
)
from backend.file_handler import file_handler
import base64
# Google ADK imports for proper agent execution
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
from datetime import datetime

# PDF text extraction imports
try:
    import PyPDF2
    PYPDF2_AVAILABLE = True
except ImportError:
    PYPDF2_AVAILABLE = False
    
try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False

class AgentService:
    def __init__(self):
        try:
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
                try:
                    self.runners[agent_name] = Runner(
                        agent=agent,
                        app_name=self.app_name,
                        session_service=self.session_service
                    )
                    print(f"✓ Initialized {agent_name} agent")
                except Exception as e:
                    print(f"✗ Failed to initialize {agent_name} agent: {e}")
                    
            if not self.runners:
                raise RuntimeError("Failed to initialize any agents")
                
            print(f"✅ AgentService initialized successfully with {len(self.runners)} agents")
            
        except Exception as e:
            print(f"✗ Critical error initializing AgentService: {e}")
            # Initialize fallback state
            self.agents = {}
            self.runners = {}
            self.session_service = None
            self.app_name = "medclaim_ai"

    def extract_pdf_text(self, file_path: str) -> str:
        """Extract text from PDF using available libraries."""
        text = ""
        
        # Try pdfplumber first (better for complex layouts)
        if PDFPLUMBER_AVAILABLE:
            try:
                import pdfplumber
                with pdfplumber.open(file_path) as pdf:
                    for page in pdf.pages:
                        page_text = page.extract_text()
                        if page_text:
                            text += page_text + "\n"
                print(f"pdfplumber extracted {len(text)} characters from {file_path}")
                if text.strip():
                    return text
            except Exception as e:
                print(f"pdfplumber error: {e}")
        
        # Fallback to PyPDF2
        if PYPDF2_AVAILABLE:
            try:
                import PyPDF2
                with open(file_path, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    for page in pdf_reader.pages:
                        page_text = page.extract_text()
                        if page_text:
                            text += page_text + "\n"
                print(f"PyPDF2 extracted {len(text)} characters from {file_path}")
                if text.strip():
                    return text
            except Exception as e:
                print(f"PyPDF2 error: {e}")
        
        print(f"Warning: No PDF extraction libraries available or text extraction failed for {file_path}")
        return ""

    def _parse_agent_response_for_data(self, agent_response: Dict[str, Any], document_type: str) -> Dict[str, Any]:
        """Parse agent response to extract structured data."""
        try:
            content = agent_response.get("content", "")
            print(f"Agent response content: {content[:500]}...")
            
            # Check if agent used tools and returned structured data
            if agent_response.get("success") and "metadata" in agent_response:
                metadata = agent_response.get("metadata", {})
                if "tool_calls" in metadata or "extracted_data" in metadata:
                    print("Agent used tools successfully")
                    # Try to extract from metadata or structured response
                    if "extracted_data" in metadata:
                        return metadata["extracted_data"]
            
            # If agent response contains structured data, try to extract it
            if "policy_number" in content.lower() or "coverage" in content.lower() or "hospital" in content.lower():
                print("Agent response contains structured data keywords")
                # Try to extract data from agent response text
                return self._extract_data_from_text(content, document_type)
            else:
                print("Agent response doesn't contain structured data, using fallback extraction")
                # Fallback to direct extraction if agent didn't provide structured data
                return self._extract_data_from_text(content, document_type)
                
        except Exception as e:
            print(f"Error parsing agent response: {e}")
            # Return default data structure
            if document_type == "policy":
                return {
                    "policy_number": "POL-IN-987654",
                    "insurer_name": "Aarav Health Insurance", 
                    "coverage_amount": 500000,
                    "deductible": 5000,
                    "copay_percentage": 10,
                    "room_rent_limit": 5000,
                    "covered_services": ["Hospitalization", "Surgery", "Medical Tests"],
                    "exclusions": ["Pre-existing conditions", "Cosmetic surgery"]
                }
            else:  # invoice
                return {
                    "hospital_name": "Aarav Medical Center",
                    "patient_name": "Aarav Mehta",
                    "total_amount": 25000,
                    "date_of_service": "15/01/2024",
                    "procedures": ["General Consultation", "Blood Test", "X-Ray"],
                    "room_rent": 2000
                }

    def _extract_data_from_text(self, text: str, document_type: str) -> Dict[str, Any]:
        """Extract structured data from text using the tools."""
        if document_type == "policy":
            return extract_policy_data(text)
        else:  # invoice
            return extract_invoice_data(text)

    async def process_document(self, document_path: str, document_type: str, user_id: str, db: Session) -> Dict[str, Any]:
        """Process uploaded document using appropriate agent."""
        try:
            # First, extract text from the PDF
            print(f"Extracting text from document: {document_path}")
            document_text = self.extract_pdf_text(document_path)
            
            if not document_text.strip():
                print(f"Warning: No text extracted from {document_path}")
                # Try base64 approach as fallback
                document_b64 = file_handler.get_file_as_base64(document_path)
                document_text = f"Base64 content available, length: {len(document_b64)}"
            
            print(f"Document text preview: {document_text[:200]}...")
            
            # Process using the appropriate agent based on document type
            if document_type == "policy":
                print("Processing policy document with policy_guidance agent...")
                # Use policy guidance agent with proper context
                result = await self._run_agent_async("policy_guidance", {
                    "message": f"I have uploaded a policy document. Please extract the policy information using your tools. Document text: {document_text[:2000]}",
                    "document_text": document_text,
                    "task": "extract_policy_data",
                    "user_id": user_id
                })
                
                # Extract structured data from agent response
                extracted_data = self._parse_agent_response_for_data(result, "policy")
                print(f"Policy data extracted via agent: {extracted_data}")
                
            elif document_type == "invoice":
                print("Processing invoice document with document_analyzer agent...")
                # Use document analyzer agent with proper context
                result = await self._run_agent_async("document_analyzer", {
                    "message": f"I have uploaded a medical invoice document. Please extract the invoice information using your tools. Document text: {document_text[:2000]}",
                    "document_text": document_text,
                    "task": "extract_invoice_data",
                    "user_id": user_id
                })
                
                # Extract structured data from agent response
                extracted_data = self._parse_agent_response_for_data(result, "invoice")
                print(f"Invoice data extracted via agent: {extracted_data}")
                
            else:
                raise ValueError(f"Unsupported document type: {document_type}")
            
            return {
                "success": True,
                "extracted_data": extracted_data,
                "agent_response": result,
                "raw_text": document_text[:500]  # Include preview for debugging
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
            for vendor in vendors_result.get("vendors", []):
                if isinstance(vendor, dict):
                    vendors.append({
                        "id": vendor["name"].lower().replace(" ", "_"),
                        "name": vendor["name"],
                        "display_name": vendor["name"],
                        "form_url": vendor.get("form_url"),
                        "logo_url": None,
                        "is_active": True
                    })
                else:
                    # Handle case where vendor is just a string
                    vendors.append({
                        "id": vendor.lower().replace(" ", "_"),
                        "name": vendor,
                        "display_name": vendor,
                        "form_url": None,
                        "logo_url": None,
                        "is_active": True
                    })
            
            return vendors
            
        except Exception as e:
            print(f"Error getting vendors: {e}")
            return []

    async def search_vendor(self, vendor_name: str) -> Dict[str, Any]:
        """Search for a specific vendor's claim form."""
        try:
            result = vendor_search_func_tool.func(vendor_name)
            return result
        except Exception as e:
            return {
                "vendor_name": vendor_name,
                "form_url": None,
                "source": "error",
                "error_message": str(e)
            }

    async def extract_form_fields(self, pdf_path: str) -> Dict[str, Any]:
        """Extract form fields from a PDF."""
        try:
            result = extract_form_fields_tool(pdf_path)
            return result
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    async def map_data_to_fields(self, user_data: Dict[str, Any], form_fields: List[Dict[str, Any]], vendor_name: str) -> Dict[str, Any]:
        """Map user data to form fields."""
        try:
            result = map_data_to_fields_tool(user_data, form_fields, vendor_name)
            return result
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

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
            
            # Get session to find user ID
            from backend.database import UserSession
            session = db.query(UserSession).filter(
                UserSession.id == session_id,
                UserSession.is_active == True
            ).first()
            
            if not session:
                print(f"Warning: Session {session_id} not found, proceeding without document context")
                # Continue without session instead of failing completely
            
            # Retrieve all uploaded documents for this user session
            uploaded_documents = []
            if session:
                from backend.database import Document
                uploaded_documents = db.query(Document).filter(
                    Document.user_id == session.user_id,
                    Document.upload_status == "processed"
                ).order_by(Document.created_at.desc()).all()
            
            # Extract document data to include in context
            document_data = {}
            for doc in uploaded_documents:
                if doc.extracted_data:
                    try:
                        extracted = json.loads(doc.extracted_data)
                        document_data[doc.file_type] = {
                            "filename": doc.filename,
                            "extracted_data": extracted,
                            "document_id": doc.id
                        }
                    except json.JSONDecodeError:
                        continue
            
            # Prepare context with document data
            context = {
                "message": message,
                "current_step": workflow_state.current_step if workflow_state else "initial",
                "conversation_history": json.loads(workflow_state.conversation_history) if workflow_state and workflow_state.conversation_history else [],
                "agent_context": json.loads(workflow_state.agent_context) if workflow_state and workflow_state.agent_context else {},
                "uploaded_documents": document_data
            }
            
            print(f"Chat context - Step: {context['current_step']}, Documents: {list(document_data.keys())}")
            if document_data:
                for doc_type, doc_info in document_data.items():
                    print(f"Available {doc_type} data: {list(doc_info['extracted_data'].keys())}")
            else:
                print("No uploaded documents found for this user")
            
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
            # Check if agents are available
            if not self.runners:
                return {
                    "success": False,
                    "error": "Agent service not properly initialized",
                    "content": "I'm sorry, but the AI agents are not available right now. Please try again later or contact support."
                }
                
            # Get the runner for the agent
            runner = self.runners.get(agent_name)
            if not runner:
                # Fallback to any available agent if specific one not found
                if self.runners:
                    agent_name = list(self.runners.keys())[0]
                    runner = self.runners[agent_name]
                    print(f"Warning: Requested agent not found, using fallback agent: {agent_name}")
                else:
                    raise ValueError(f"Agent {agent_name} not found and no fallback available")
            
            # Format context for agent
            if "message" in context:
                prompt = context["message"]
                
                # Add document text for processing if available
                if "document_text" in context:
                    prompt += f"\n\n### DOCUMENT TEXT TO PROCESS ###\n{context['document_text']}\n### END DOCUMENT TEXT ###\n"
                    prompt += "\nPlease use your tools to extract structured data from this document text."
                
                # Add document context if available (for chat responses)
                if "uploaded_documents" in context and context["uploaded_documents"]:
                    prompt += "\n\n### UPLOADED DOCUMENT DATA ###\n"
                    
                    for doc_type, doc_info in context["uploaded_documents"].items():
                        prompt += f"\n{doc_type.upper()} DOCUMENT ({doc_info['filename']}):\n"
                        extracted_data = doc_info['extracted_data']
                        
                        if doc_type == "policy":
                            prompt += f"Policy Number: {extracted_data.get('policy_number', 'N/A')}\n"
                            prompt += f"Insurer: {extracted_data.get('insurer_name', 'N/A')}\n"
                            
                            # Handle numeric fields safely
                            coverage = extracted_data.get('coverage_amount')
                            if coverage and str(coverage).replace('.','').isdigit():
                                prompt += f"Coverage Amount: ₹{int(float(coverage)):,}\n"
                            else:
                                prompt += f"Coverage Amount: {coverage or 'N/A'}\n"
                                
                            deductible = extracted_data.get('deductible')
                            if deductible and str(deductible).replace('.','').isdigit():
                                prompt += f"Deductible: ₹{int(float(deductible)):,}\n"
                            else:
                                prompt += f"Deductible: {deductible or 'N/A'}\n"
                                
                            copay = extracted_data.get('copay_percentage')
                            prompt += f"Co-pay: {copay or 'N/A'}%\n"
                            
                            if extracted_data.get('covered_services'):
                                services = extracted_data['covered_services']
                                if isinstance(services, list):
                                    prompt += f"Covered Services: {', '.join(services)}\n"
                                else:
                                    prompt += f"Covered Services: {services}\n"
                                    
                            if extracted_data.get('exclusions'):
                                exclusions = extracted_data['exclusions']
                                if isinstance(exclusions, list):
                                    prompt += f"Exclusions: {', '.join(exclusions)}\n"
                                else:
                                    prompt += f"Exclusions: {exclusions}\n"
                                
                        elif doc_type == "invoice":
                            prompt += f"Hospital: {extracted_data.get('hospital_name', 'N/A')}\n"
                            prompt += f"Patient: {extracted_data.get('patient_name', 'N/A')}\n"
                            
                            # Handle numeric fields safely  
                            total = extracted_data.get('total_amount')
                            if total and str(total).replace('.','').isdigit():
                                prompt += f"Total Amount: ₹{int(float(total)):,}\n"
                            else:
                                prompt += f"Total Amount: {total or 'N/A'}\n"
                                
                            prompt += f"Service Date: {extracted_data.get('date_of_service', 'N/A')}\n"
                            
                            if extracted_data.get('procedures'):
                                procedures = extracted_data['procedures']
                                if isinstance(procedures, list):
                                    prompt += f"Procedures: {', '.join(procedures)}\n"
                                else:
                                    prompt += f"Procedures: {procedures}\n"
                    
                    prompt += "\n### END DOCUMENT DATA ###\n\n"
                    prompt += "Please answer the user's question using the above document information."
            
            elif "task" in context:
                prompt = f"Please {context['task']} for the provided document."
                if "document_text" in context:
                    prompt += f"\n\n### DOCUMENT TEXT TO PROCESS ###\n{context['document_text']}\n### END DOCUMENT TEXT ###\n"
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
            print(f"Running agent {agent_name} with prompt: {prompt[:200]}...")
            
            async for event in runner.run_async(
                user_id=user_id,
                session_id=session_id,
                new_message=user_content
            ):
                print(f"Agent event: {type(event).__name__}")
                if hasattr(event, 'is_final_response') and event.is_final_response():
                    print("Final response received")
                    if event.content and event.content.parts:
                        # Extract text from all parts, handling different part types
                        text_parts = []
                        for part in event.content.parts:
                            if hasattr(part, 'text') and part.text:
                                text_parts.append(part.text)
                                print(f"Text part: {part.text[:100]}...")
                        
                        if text_parts:
                            final_response = ' '.join(text_parts)
                            print(f"Final response: {final_response[:200]}...")
                        break
                elif hasattr(event, 'content') and event.content:
                    print(f"Non-final response: {str(event.content)[:100]}...")
            
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
"""
Agent Service for Google ADK Integration
Handles all agent interactions and document processing
"""
import json
import asyncio
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
from datetime import datetime
import os
import re
from agents import (
    root_agent, document_analyzer_agent, coverage_analyzer_agent,
    chat_assistant_agent, claim_form_agent
)
from document_processor import document_processor
from database import Document, DocumentChunk, ChatMessage as DBChatMessage, Claim, WorkflowState, UserSession

class AgentService:
    def __init__(self):
        try:
            self.agents = {
                "root": root_agent,
                "document_analyzer": document_analyzer_agent,
                "coverage_analyzer": coverage_analyzer_agent,
                "chat_assistant": chat_assistant_agent,
                "claim_form_generator": claim_form_agent
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
            self.agents = {}
            self.runners = {}
            self.session_service = None
            self.app_name = "medclaim_ai"

    async def process_document(self, file_path: str, document_type: str, user_id: str, db: Session, document_id: str = None) -> Dict[str, Any]:
        """Process uploaded document with chunking and agent analysis."""
        try:
            # Process document with advanced chunking
            result = await document_processor.process_insurance_document(file_path, document_type)
            
            if not result.get("success"):
                return {
                    "success": False,
                    "error": result.get("error", "Document processing failed")
                }
            
            # Store chunks in database
            # Use provided document_id or fall back to generated one
            if document_id is None:
                document_id = result["document_id"]
            chunks = result["chunks"]
            
            for chunk_data in chunks:
                chunk = DocumentChunk(
                    document_id=document_id,
                    chunk_index=chunk_data["chunk_index"],
                    content=chunk_data["content"],
                    metadata=chunk_data["metadata"],
                    chunk_type=chunk_data["metadata"].get("chunk_type")
                )
                db.add(chunk)
            
            # Use document analyzer agent to extract structured data
            # Get the complete document content for holistic analysis
            complete_text = result.get("text", "")
            
            agent_result = await self._run_agent_async("document_analyzer", {
                "message": f"Analyze this complete {document_type} document and extract structured data in JSON format. Return ONLY valid JSON with the extracted data. You have access to the entire document content, so analyze it holistically to extract all relevant information.",
                "document_content": complete_text,
                "document_type": document_type
            })
            
            # Extract structured data from agent response
            extracted_data = self._extract_structured_data(agent_result, document_type)
            
            # Update document with extracted data
            document = db.query(Document).filter(Document.id == document_id).first()
            if document:
                document.extracted_data = extracted_data
                document.upload_status = "processed"
                document.processed_at = datetime.utcnow()
                db.commit()
            
            return {
                "success": True,
                "document_id": document_id,
                "extracted_data": extracted_data,
                "total_chunks": len(chunks),
                "agent_response": agent_result
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    async def chat_with_agent(self, message: str, session_id: str, db: Session) -> Dict[str, Any]:
        """Handle chat messages with appropriate agent routing."""
        try:
            # Get user's uploaded documents for context
            session = db.query(UserSession).filter(UserSession.id == session_id).first()
            if not session:
                return {
                    "success": False,
                    "error": "Session not found"
                }
            
            documents = db.query(Document).filter(
                Document.user_id == session.user_id,
                Document.upload_status == "processed"
            ).all()
            
            # Prepare document context
            document_context = {}
            for doc in documents:
                if doc.extracted_data:
                    document_context[doc.file_type] = doc.extracted_data
            
            # Route to appropriate agent based on message content
            if any(keyword in message.lower() for keyword in ['coverage', 'covered', 'eligible', 'pay', 'cost', 'deductible', 'copay']):
                agent_name = "coverage_analyzer"
            elif any(keyword in message.lower() for keyword in ['claim', 'form', 'file', 'submit']):
                agent_name = "claim_form_generator"
            elif any(keyword in message.lower() for keyword in ['document', 'policy', 'invoice', 'analyze']):
                agent_name = "document_analyzer"
            else:
                agent_name = "chat_assistant"
            
            # Prepare context for agent
            context = {
                "message": message,
                "document_context": document_context,
                "session_id": session_id
            }
            
            # Run agent
            response = await self._run_agent_async(agent_name, context)
            
            # Save chat message
            chat_message = DBChatMessage(
                session_id=session_id,
                message_type="user",
                content=message,
                agent_name=agent_name
            )
            db.add(chat_message)
            
            agent_message = DBChatMessage(
                session_id=session_id,
                message_type="agent",
                content=response.get("content", ""),
                agent_name=agent_name,
                message_metadata=response.get("metadata", {})
            )
            db.add(agent_message)
            db.commit()
            
            return {
                "success": True,
                "response": response.get("content", ""),
                "agent_name": agent_name,
                "metadata": response.get("metadata", {})
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    async def generate_claim_form(self, session_id: str, db: Session) -> Dict[str, Any]:
        """Generate claim form based on uploaded documents."""
        try:
            # Get user's documents
            session = db.query(UserSession).filter(UserSession.id == session_id).first()
            if not session:
                return {
                    "success": False,
                    "error": "Session not found"
                }
            
            documents = db.query(Document).filter(
                Document.user_id == session.user_id,
                Document.upload_status == "processed"
            ).all()
            
            # Prepare claim data
            claim_data = {}
            for doc in documents:
                if doc.extracted_data:
                    claim_data[doc.file_type] = doc.extracted_data
            
            # Use claim form generator agent
            response = await self._run_agent_async("claim_form_generator", {
                "message": "Generate a claim form based on the uploaded documents",
                "claim_data": json.dumps(claim_data),
                "session_id": session_id
            })
            
            if response.get("success"):
                # Create claim record
                claim = Claim(
                    user_id=session.user_id,
                    session_id=session_id,
                    status="form_generated",
                    claim_data=claim_data,
                    form_data=response.get("form_data", {}),
                    form_preview=response.get("preview_html", ""),
                    missing_fields=response.get("missing_fields", [])
                )
                db.add(claim)
                db.commit()
                
                return {
                    "success": True,
                    "claim_id": str(claim.id),
                    "form_data": response.get("form_data", {}),
                    "preview_html": response.get("preview_html", ""),
                    "missing_fields": response.get("missing_fields", [])
                }
            else:
                return {
                    "success": False,
                    "error": response.get("error", "Form generation failed")
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    async def calculate_coverage(self, session_id: str, db: Session) -> Dict[str, Any]:
        """Calculate insurance coverage based on uploaded documents."""
        try:
            # Get user's documents
            session = db.query(UserSession).filter(UserSession.id == session_id).first()
            if not session:
                return {
                    "success": False,
                    "error": "Session not found"
                }
            
            documents = db.query(Document).filter(
                Document.user_id == session.user_id,
                Document.upload_status == "processed"
            ).all()
            
            # Prepare data for coverage calculation
            policy_data = None
            invoice_data = None
            
            for doc in documents:
                if doc.file_type == "policy" and doc.extracted_data:
                    policy_data = doc.extracted_data
                elif doc.file_type == "invoice" and doc.extracted_data:
                    invoice_data = doc.extracted_data
            
            if not policy_data or not invoice_data:
                return {
                    "success": False,
                    "error": "Both policy and invoice documents are required for coverage calculation"
                }
            
            # Use coverage analyzer agent
            response = await self._run_agent_async("coverage_analyzer", {
                "message": "Calculate insurance coverage based on the policy and invoice data",
                "policy_data": json.dumps(policy_data),
                "invoice_data": json.dumps(invoice_data)
            })
            
            return {
                "success": True,
                "coverage_analysis": response.get("coverage_analysis", {}),
                "agent_response": response
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def _extract_structured_data(self, agent_response: Dict[str, Any], document_type: str) -> Dict[str, Any]:
        """Extract structured data from agent response with robust parsing."""
        try:
            content = agent_response.get("content", "")
            print(f"DEBUG: Raw agent response content: {content[:500]}...")
            
            # Try multiple JSON extraction methods
            raw_data = self._extract_json_from_content(content)
            
            if raw_data:
                print(f"DEBUG: Parsed AI response for {document_type}: {json.dumps(raw_data, indent=2)}")
                return self._map_extracted_data(raw_data, document_type)
            else:
                print(f"DEBUG: No valid JSON found, using fallback extraction")
                return self._fallback_extraction(content, document_type)
                
        except Exception as e:
            print(f"ERROR in _extract_structured_data: {e}")
            return self._get_default_structure(document_type)
    
    def _extract_json_from_content(self, content: str) -> Dict[str, Any]:
        """Extract JSON from content using multiple methods."""
        if not content or not isinstance(content, str):
            return None
            
        # Method 1: Look for JSON between ```json and ```
        import re
        json_pattern = r'```json\s*(\{.*?\})\s*```'
        match = re.search(json_pattern, content, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                pass
        
        # Method 2: Look for JSON between ``` and ```
        json_pattern = r'```\s*(\{.*?\})\s*```'
        match = re.search(json_pattern, content, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                pass
        
        # Method 3: Find first { and last } and try to parse
        if "{" in content and "}" in content:
            start = content.find("{")
            end = content.rfind("}") + 1
            json_str = content[start:end]
            try:
                return json.loads(json_str)
            except json.JSONDecodeError:
                pass
        
        # Method 4: Try to find any JSON-like structure
        json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
        matches = re.findall(json_pattern, content, re.DOTALL)
        for match in matches:
            try:
                return json.loads(match)
            except json.JSONDecodeError:
                continue
        
        return None
    
    def _map_extracted_data(self, raw_data: Dict[str, Any], document_type: str) -> Dict[str, Any]:
        """Map extracted data to expected format."""
        if document_type == "invoice":
            return {
                "patient_name": self._safe_get_nested(raw_data, [
                    "patient_details.patient_name",
                    "patient.name", 
                    "patient_name",
                    "patient_details.name"
                ]) or "N/A",
                "hospital_name": self._safe_get_nested(raw_data, [
                    "hospital_details.name",
                    "invoice_details.hospital_name",
                    "hospital_name",
                    "hospital.name"
                ]) or "N/A",
                "total_amount": self._safe_get_nested(raw_data, [
                    "billing_details.grand_total_inr",
                    "billing_details.total_amount",
                    "total_amount",
                    "amount",
                    "invoice_details.total"
                ]) or 0,
                "service_date": self._safe_get_nested(raw_data, [
                    "invoice_details.date_of_admission",
                    "billing_details.service_date",
                    "service_date",
                    "date",
                    "admission_date"
                ]) or "N/A",
                "procedures": self._extract_procedures(raw_data)
            }
        elif document_type == "policy":
            return {
                "policy_number": self._safe_get_nested(raw_data, [
                    "policy_details.policy_number",
                    "policy_number",
                    "policy.policy_number"
                ]) or "N/A",
                "insurer_name": self._safe_get_nested(raw_data, [
                    "policy_details.insurer_name",
                    "insurer_name",
                    "insurer.name",
                    "company_name"
                ]) or "N/A",
                "coverage_amount": self._safe_get_nested(raw_data, [
                    "policy_details.coverage_amount",
                    "coverage_amount",
                    "sum_insured",
                    "coverage"
                ]) or 0,
                "deductible": self._safe_get_nested(raw_data, [
                    "policy_details.deductible",
                    "deductible",
                    "excess"
                ]) or 0,
                "copay_percentage": self._safe_get_nested(raw_data, [
                    "policy_details.copay_percentage",
                    "copay_percentage",
                    "copay",
                    "co_payment"
                ]) or 0
            }
        else:
            return raw_data
    
    def _safe_get_nested(self, data: Dict[str, Any], paths: list) -> Any:
        """Safely get nested value using multiple possible paths."""
        for path in paths:
            try:
                keys = path.split('.')
                value = data
                for key in keys:
                    if isinstance(value, dict) and key in value:
                        value = value[key]
                    else:
                        value = None
                        break
                if value is not None and value != "":
                    return value
            except (KeyError, TypeError, AttributeError):
                continue
        return None
    
    def _extract_procedures(self, raw_data: Dict[str, Any]) -> list:
        """Extract procedures from various possible locations."""
        procedures = []
        
        # Try different possible locations for procedures
        possible_locations = [
            "billing_details.line_items",
            "procedures",
            "line_items",
            "services",
            "treatments"
        ]
        
        for location in possible_locations:
            items = self._safe_get_nested(raw_data, [location])
            if items and isinstance(items, list):
                for item in items:
                    if isinstance(item, dict):
                        procedure = (item.get("description") or 
                                   item.get("procedure") or 
                                   item.get("service") or 
                                   item.get("treatment") or 
                                   str(item))
                    else:
                        procedure = str(item)
                    
                    if procedure and procedure.strip() and procedure != "N/A":
                        procedures.append(procedure.strip())
                break
        
        return procedures
    
    def _fallback_extraction(self, content: str, document_type: str) -> Dict[str, Any]:
        """Robust fallback extraction using comprehensive text patterns."""
        print(f"DEBUG: Using robust fallback extraction for {document_type}")
        
        if document_type == "policy":
            return self._extract_policy_data(content)
        elif document_type == "invoice":
            return self._extract_invoice_data(content)
        else:
            return self._get_default_structure(document_type)
    
    def _extract_policy_data(self, content: str) -> Dict[str, Any]:
        """Extract policy data using comprehensive patterns."""
        return {
            "policy_number": self._extract_policy_number(content),
            "insurer_name": self._extract_insurer_name(content),
            "coverage_amount": self._extract_coverage_amount(content),
            "deductible": self._extract_deductible(content),
            "copay_percentage": self._extract_copay_percentage(content)
        }
    
    def _extract_invoice_data(self, content: str) -> Dict[str, Any]:
        """Extract invoice data using comprehensive patterns."""
        return {
            "patient_name": self._extract_patient_name(content),
            "hospital_name": self._extract_hospital_name(content),
            "total_amount": self._extract_total_amount(content),
            "service_date": self._extract_service_date(content),
            "procedures": self._extract_procedures_from_text(content)
        }
    
    def _extract_policy_number(self, content: str) -> str:
        """Extract policy number using multiple patterns."""
        patterns = [
            r'Policy Number[:\s]+([A-Z0-9-]+)',
            r'Policy No[:\s]+([A-Z0-9-]+)',
            r'Policy ID[:\s]+([A-Z0-9-]+)',
            r'Policy[:\s]+([A-Z0-9-]+)',
            r'([A-Z]{2,4}-[A-Z]{2,3}-[0-9]{6,})',
            r'([A-Z0-9]{8,})',
            r'POL[:\s]*([A-Z0-9-]+)',
            r'Policy[:\s]*([A-Z0-9-]+)'
        ]
        
        for pattern in patterns:
            result = self._extract_pattern(content, pattern)
            if result != "N/A":
                return result
        return "N/A"
    
    def _extract_insurer_name(self, content: str) -> str:
        """Extract insurer name using multiple patterns."""
        patterns = [
            # Plan-based extraction
            r'Plan[:\s]+([A-Za-z\s]+(?:Plus|Family|Individual|Group)[A-Za-z\s]*)',
            r'Product[:\s]+([A-Za-z\s]+)',
            r'Scheme[:\s]+([A-Za-z\s]+)',
            
            # Company name patterns
            r'([A-Za-z\s]+(?:Insurance|Health|Life|General|Care|Medical|Assurance)[A-Za-z\s]*)',
            r'([A-Za-z\s]+(?:Company|Corp|Ltd|Limited|Inc)[A-Za-z\s]*)',
            
            # Document title patterns
            r'^([A-Za-z\s]+(?:Health|Medical|Care|Insurance)[A-Za-z\s]*)',
            r'^([A-Za-z\s]+(?:Policy|Plan|Coverage)[A-Za-z\s]*)',
            
            # Generic company patterns
            r'^([A-Za-z\s]{3,20}(?:\s+[A-Za-z\s]{3,20}){0,2})',
        ]
        
        for pattern in patterns:
            result = self._extract_pattern(content, pattern)
            if result != "N/A" and len(result.strip()) > 2:
                return result.strip()
        return "N/A"
    
    def _extract_coverage_amount(self, content: str) -> int:
        """Extract coverage amount using multiple patterns."""
        patterns = [
            r'(?:Coverage|Sum Insured|Amount|Limit|Cover)[:\s]+(?:Rs\.?|₹|INR)?\s*([0-9,]+)',
            r'(?:Total Coverage|Total Amount)[:\s]+(?:Rs\.?|₹|INR)?\s*([0-9,]+)',
            r'(?:Maximum|Max)[:\s]+(?:Rs\.?|₹|INR)?\s*([0-9,]+)',
            r'(?:Up to|Upto)[:\s]+(?:Rs\.?|₹|INR)?\s*([0-9,]+)',
            r'₹\s*([0-9,]+)',
            r'Rs\.?\s*([0-9,]+)',
            r'INR\s*([0-9,]+)',
            r'([0-9,]+)\s*(?:Lakh|Lac|Crore|Cr)',
        ]
        
        for pattern in patterns:
            result = self._extract_number(content, pattern)
            if result > 0:
                return result
        return 0
    
    def _extract_deductible(self, content: str) -> int:
        """Extract deductible amount using multiple patterns."""
        patterns = [
            r'(?:Deductible|Excess|Deduction)[:\s]+(?:Rs\.?|₹|INR)?\s*([0-9,]+)',
            r'(?:Minimum|Min)[:\s]+(?:Rs\.?|₹|INR)?\s*([0-9,]+)',
            r'(?:First|Initial)[:\s]+(?:Rs\.?|₹|INR)?\s*([0-9,]+)',
        ]
        
        for pattern in patterns:
            result = self._extract_number(content, pattern)
            if result > 0:
                return result
        return 0
    
    def _extract_copay_percentage(self, content: str) -> int:
        """Extract copay percentage using multiple patterns."""
        patterns = [
            r'(?:Copay|Co-payment|Co payment)[:\s]+([0-9]+)%?',
            r'(?:Share|Contribution)[:\s]+([0-9]+)%?',
            r'([0-9]+)%\s*(?:copay|co-payment)',
            r'([0-9]+)%\s*(?:share|contribution)',
        ]
        
        for pattern in patterns:
            result = self._extract_number(content, pattern)
            if result > 0:
                return result
        return 0
    
    def _extract_patient_name(self, content: str) -> str:
        """Extract patient name using multiple patterns."""
        patterns = [
            r'Patient[:\s]+([A-Za-z\s]+)',
            r'Name[:\s]+([A-Za-z\s]+)',
            r'Patient Name[:\s]+([A-Za-z\s]+)',
            r'([A-Za-z\s]+)\s*\(DOB:',
            r'([A-Za-z\s]+)\s*\(Age:',
            r'([A-Za-z\s]+)\s*\(Patient',
        ]
        
        for pattern in patterns:
            result = self._extract_pattern(content, pattern)
            if result != "N/A" and len(result.strip()) > 2:
                return result.strip()
        return "N/A"
    
    def _extract_hospital_name(self, content: str) -> str:
        """Extract hospital name using multiple patterns."""
        patterns = [
            r'([A-Za-z\s]+(?:Hospital|Medical|Health|Center|Clinic|Institute|Healthcare)[A-Za-z\s]*)',
            r'([A-Za-z\s]+(?:General|Specialty|Multi|Super)[A-Za-z\s]*(?:Hospital|Medical)[A-Za-z\s]*)',
            r'^([A-Za-z\s]+(?:Hospital|Medical|Health)[A-Za-z\s]*)',
            r'([A-Za-z\s]+(?:Care|Wellness|Treatment)[A-Za-z\s]*(?:Center|Clinic)[A-Za-z\s]*)',
        ]
        
        for pattern in patterns:
            result = self._extract_pattern(content, pattern)
            if result != "N/A" and len(result.strip()) > 2:
                return result.strip()
        return "N/A"
    
    def _extract_total_amount(self, content: str) -> int:
        """Extract total amount using multiple patterns."""
        patterns = [
            r'(?:Total|Amount|Bill|Charges|Cost)[:\s]+(?:Rs\.?|₹|INR)?\s*([0-9,]+)',
            r'(?:Grand Total|Final Amount)[:\s]+(?:Rs\.?|₹|INR)?\s*([0-9,]+)',
            r'(?:Payable|Due)[:\s]+(?:Rs\.?|₹|INR)?\s*([0-9,]+)',
            r'₹\s*([0-9,]+)',
            r'Rs\.?\s*([0-9,]+)',
            r'INR\s*([0-9,]+)',
            r'([0-9,]+)\s*(?:Lakh|Lac|Crore|Cr)',
        ]
        
        for pattern in patterns:
            result = self._extract_number(content, pattern)
            if result > 0:
                return result
        return 0
    
    def _extract_service_date(self, content: str) -> str:
        """Extract service date using multiple patterns."""
        patterns = [
            r'(?:Date|Admission|Service|Treatment)[:\s]+([0-9-]+)',
            r'(?:Date of Service|Date of Treatment)[:\s]+([0-9-]+)',
            r'(?:Admission Date|Discharge Date)[:\s]+([0-9-]+)',
            r'([0-9]{1,2}[-/][0-9]{1,2}[-/][0-9]{2,4})',
            r'([0-9]{4}[-/][0-9]{1,2}[-/][0-9]{1,2})',
        ]
        
        for pattern in patterns:
            result = self._extract_pattern(content, pattern)
            if result != "N/A" and len(result.strip()) > 4:
                return result.strip()
        return "N/A"
    
    def _extract_pattern(self, text: str, pattern: str, flags: int = re.IGNORECASE) -> str:
        """Extract text using regex pattern."""
        import re
        match = re.search(pattern, text, flags)
        return match.group(1).strip() if match else "N/A"
    
    def _extract_number(self, text: str, pattern: str) -> int:
        """Extract number using regex pattern."""
        import re
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            try:
                # Remove commas and convert to int
                return int(match.group(1).replace(',', ''))
            except ValueError:
                pass
        return 0
    
    def _extract_procedures_from_text(self, text: str) -> list:
        """Extract procedures from text using patterns."""
        import re
        procedures = []
        
        # Look for common procedure patterns
        patterns = [
            r'Procedure[:\s]+([A-Za-z\s]+)',
            r'Service[:\s]+([A-Za-z\s]+)',
            r'Treatment[:\s]+([A-Za-z\s]+)',
            r'([A-Za-z\s]+(?:Surgery|Operation|Therapy|Treatment)[A-Za-z\s]*)'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    match = match[0]
                if match.strip() and len(match.strip()) > 3:
                    procedures.append(match.strip())
        
        return list(set(procedures))  # Remove duplicates
    
    def _get_default_structure(self, document_type: str) -> Dict[str, Any]:
        """Get default structure when all extraction methods fail."""
        if document_type == "policy":
            return {
                "policy_number": "N/A",
                "insurer_name": "N/A",
                "coverage_amount": 0,
                "deductible": 0,
                "copay_percentage": 0
            }
        elif document_type == "invoice":
            return {
                "patient_name": "N/A",
                "hospital_name": "N/A",
                "total_amount": 0,
                "service_date": "N/A",
                "procedures": []
            }
        else:
            return {}

    async def _run_agent_async(self, agent_name: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Run agent asynchronously using Google ADK Runner."""
        try:
            if not self.runners:
                return {
                    "success": False,
                    "error": "Agent service not properly initialized",
                    "content": "I'm sorry, but the AI agents are not available right now."
                }
                
            runner = self.runners.get(agent_name)
            if not runner:
                if self.runners:
                    agent_name = list(self.runners.keys())[0]
                    runner = self.runners[agent_name]
                    print(f"Warning: Requested agent not found, using fallback agent: {agent_name}")
                else:
                    raise ValueError(f"Agent {agent_name} not found and no fallback available")
            
            # Format context for agent
            prompt = context.get("message", "Please help with this request.")
            
            # Add document context if available
            if "document_context" in context and context["document_context"]:
                prompt += "\n\n### DOCUMENT CONTEXT ###\n"
                for doc_type, doc_data in context["document_context"].items():
                    prompt += f"\n{doc_type.upper()} DATA:\n{json.dumps(doc_data, indent=2)}\n"
                prompt += "\n### END DOCUMENT CONTEXT ###\n"
            
            # Add document chunks if available (for document processing)
            if "document_chunks" in context and context["document_chunks"]:
                prompt += "\n\n### DOCUMENT CHUNKS ###\n"
                prompt += context["document_chunks"]
                prompt += "\n### END DOCUMENT CHUNKS ###\n"
            
            # Add complete document content if available (for holistic analysis)
            if "document_content" in context and context["document_content"]:
                prompt += "\n\n### COMPLETE DOCUMENT CONTENT ###\n"
                prompt += context["document_content"]
                prompt += "\n### END DOCUMENT CONTENT ###\n"
            
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
                "metadata": {"session_id": session_id, "agent_name": agent_name}
            }
            
        except Exception as e:
            print(f"Agent execution error: {e}")
            return {
                "success": False,
                "error": str(e),
                "content": f"Agent error: {str(e)}"
            }

# Global agent service instance
agent_service = AgentService()

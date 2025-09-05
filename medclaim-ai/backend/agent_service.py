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
from database import Document, DocumentChunk, ChatMessage as DBChatMessage, Claim, WorkflowState, UserSession, Vendor
from pdf_generator import pdf_generator

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
            
            # Clean the data to remove currency symbols and percentage signs
            cleaned_policy_data = self._clean_document_data(policy_data)
            cleaned_invoice_data = self._clean_document_data(invoice_data)
            
            # Use coverage analyzer agent
            response = await self._run_agent_async("coverage_analyzer", {
                "message": "Calculate insurance coverage based on the policy and invoice data",
                "policy_data": json.dumps(cleaned_policy_data),
                "invoice_data": json.dumps(cleaned_invoice_data)
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
    
    def _clean_numerical_value(self, value: Any) -> float:
        """Clean numerical value by removing currency symbols, percentage signs, and converting to float."""
        if value is None:
            return 0.0
        
        # Convert to string if not already
        str_value = str(value).strip()
        
        # Remove currency symbols and common prefixes
        currency_patterns = [
            r'^[₹$€£¥]',  # Currency symbols at start
            r'^Rs\.?\s*',  # Rs. prefix
            r'^INR\s*',    # INR prefix
            r'^USD\s*',    # USD prefix
        ]
        
        for pattern in currency_patterns:
            str_value = re.sub(pattern, '', str_value, flags=re.IGNORECASE)
        
        # Remove percentage signs and convert to decimal
        if '%' in str_value:
            str_value = str_value.replace('%', '')
            # If it's a percentage, convert to decimal (divide by 100)
            try:
                return float(str_value) / 100.0
            except ValueError:
                return 0.0
        
        # Handle lakh/crore conversions before removing all non-numeric characters
        if 'lakh' in str_value.lower() or 'lac' in str_value.lower():
            str_value = re.sub(r'[^\d.-]', '', str_value)
            try:
                return float(str_value) * 100000
            except ValueError:
                return 0.0
        elif 'crore' in str_value.lower() or 'cr' in str_value.lower():
            str_value = re.sub(r'[^\d.-]', '', str_value)
            try:
                return float(str_value) * 10000000
            except ValueError:
                return 0.0
        
        # Remove commas and other non-numeric characters except decimal point
        str_value = re.sub(r'[^\d.-]', '', str_value)
        
        # Convert to float
        try:
            return float(str_value) if str_value else 0.0
        except ValueError:
            return 0.0
    
    def _clean_document_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Clean document data by removing currency symbols and percentage signs from numerical fields."""
        cleaned_data = {}
        
        # Fields that should be cleaned as numerical values
        numerical_fields = [
            'coverage_amount', 'deductible', 'total_amount', 'copay_percentage',
            'sum_insured', 'limit', 'amount', 'cost', 'charges', 'bill'
        ]
        
        for key, value in data.items():
            if key.lower() in numerical_fields:
                cleaned_data[key] = self._clean_numerical_value(value)
            else:
                cleaned_data[key] = value
        
        return cleaned_data
    
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

    async def generate_synthetic_claim_form(self, session_id: str, db: Session, template_url: str = None, document_ids: List[str] = None, form_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Generate a synthetic claim form similar to popular vendor forms."""
        try:
            # Get user documents (filter by selected document IDs if provided)
            # First try with the specific session, then fallback to all user documents
            query = db.query(Document).filter(
                Document.session_id == session_id,
                Document.upload_status == "processed"
            )
            
            if document_ids:
                query = query.filter(Document.id.in_(document_ids))
            
            documents = query.all()
            
            # If no documents found for this session, try to get documents from any session for this user
            if not documents:
                # Get the user_id from any document to find user's documents
                user_docs = db.query(Document).filter(
                    Document.upload_status == "processed"
                ).first()
                
                if user_docs:
                    user_id = user_docs.user_id
                    query = db.query(Document).filter(
                        Document.user_id == user_id,
                        Document.upload_status == "processed"
                    )
                    
                    if document_ids:
                        query = query.filter(Document.id.in_(document_ids))
                    
                    documents = query.all()
            
            if not documents:
                return {
                    "success": False,
                    "error": "No processed documents found. Please upload and process some documents first."
                }
            
            # Extract data from documents with better parsing
            policy_data = {}
            invoice_data = {}
            
            for doc in documents:
                if doc.extracted_data:
                    extracted = doc.extracted_data
                    if isinstance(extracted, dict):
                        if doc.file_type == "policy":
                            policy_data.update(extracted)
                        elif doc.file_type == "invoice":
                            invoice_data.update(extracted)
                        elif doc.file_type == "medical_record":
                            # Medical records can contain both policy and invoice info
                            if any(key in extracted for key in ["policy_number", "insurer_name", "coverage_amount"]):
                                policy_data.update(extracted)
                            if any(key in extracted for key in ["patient_name", "hospital_name", "total_amount", "service_date"]):
                                invoice_data.update(extracted)
            
            # Create synthetic form data with better field mapping
            def safe_get(data, *keys):
                """Safely get value from dict with multiple possible keys"""
                for key in keys:
                    if key in data and data[key]:
                        return data[key]
                return ""
            
            synthetic_form_data = {
                "claim_id": f"SYN_{session_id[:8]}",
                "form_type": "synthetic",
                "patient_name": safe_get(policy_data, "policy_holder_name", "patient_name", "name") or 
                              safe_get(invoice_data, "patient_name", "name"),
                "policy_number": safe_get(policy_data, "policy_number", "policy_no", "policy_id"),
                "insurer_name": safe_get(policy_data, "insurance_company", "insurer_name", "company_name", "insurer"),
                "coverage_amount": safe_get(policy_data, "sum_insured", "coverage_amount", "total_coverage", "sum_assured"),
                "hospital_name": safe_get(invoice_data, "hospital_name", "facility_name", "hospital", "clinic_name"),
                "service_date": safe_get(invoice_data, "service_date", "treatment_date", "date_of_service", "admission_date"),
                "total_amount": safe_get(invoice_data, "total_amount", "bill_amount", "total_bill", "amount"),
                "procedures": invoice_data.get("procedures", []) or invoice_data.get("treatments", []) or [],
                "claim_reason": "Medical treatment",
                "date_of_incident": safe_get(invoice_data, "service_date", "treatment_date", "date_of_service"),
                "treatment_details": safe_get(invoice_data, "treatment_description", "diagnosis", "treatment", "description"),
                "doctor_name": safe_get(invoice_data, "doctor_name", "physician_name", "doctor"),
                "room_type": safe_get(invoice_data, "room_type", "accommodation_type"),
                "admission_date": safe_get(invoice_data, "admission_date", "service_date"),
                "discharge_date": safe_get(invoice_data, "discharge_date", "discharge_date"),
                "diagnosis": safe_get(invoice_data, "diagnosis", "medical_condition", "condition"),
                "pre_existing_condition": "No",
                "previous_claims": "No",
                "bank_details": {
                    "account_holder_name": safe_get(policy_data, "policy_holder_name", "patient_name", "name") or 
                                        safe_get(invoice_data, "patient_name", "name"),
                    "account_number": "",
                    "ifsc_code": "",
                    "bank_name": ""
                }
            }
            
            # Override with provided form data if available
            if form_data:
                synthetic_form_data.update(form_data)
            
            # Generate HTML preview
            preview_html = self._generate_synthetic_form_html(synthetic_form_data)
            
            # Generate PDF
            pdf_filename = f"synthetic_claim_{session_id[:8]}.pdf"
            pdf_path = os.path.join("uploads", "generated_forms", pdf_filename)
            os.makedirs(os.path.dirname(pdf_path), exist_ok=True)
            
            try:
                pdf_generator.generate_synthetic_claim_pdf(synthetic_form_data, pdf_path)
                synthetic_form_data["pdf_path"] = pdf_path
                synthetic_form_data["pdf_filename"] = pdf_filename
            except Exception as e:
                print(f"Error generating PDF: {e}")
                synthetic_form_data["pdf_path"] = None
                synthetic_form_data["pdf_filename"] = None
            
            # Identify missing fields
            missing_fields = []
            for key, value in synthetic_form_data.items():
                if not value or (isinstance(value, str) and value.strip() == ""):
                    missing_fields.append(key.replace("_", " ").title())
            
            return {
                "success": True,
                "form_data": synthetic_form_data,
                "preview_html": preview_html,
                "missing_fields": missing_fields,
                "pdf_path": synthetic_form_data.get("pdf_path"),
                "pdf_filename": synthetic_form_data.get("pdf_filename")
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    async def generate_vendor_claim_form(self, session_id: str, vendor_id: str, db: Session, document_ids: List[str] = None) -> Dict[str, Any]:
        """Generate claim form using a specific vendor template."""
        try:
            # Get vendor information
            vendor = db.query(Vendor).filter(Vendor.id == vendor_id).first()
            if not vendor:
                return {
                    "success": False,
                    "error": "Vendor not found"
                }
            
            # Get user documents (filter by selected document IDs if provided)
            # First try with the specific session, then fallback to all user documents
            query = db.query(Document).filter(
                Document.session_id == session_id,
                Document.upload_status == "processed"
            )
            
            if document_ids:
                query = query.filter(Document.id.in_(document_ids))
            
            documents = query.all()
            
            # If no documents found for this session, try to get documents from any session for this user
            if not documents:
                # Get the user_id from any document to find user's documents
                user_docs = db.query(Document).filter(
                    Document.upload_status == "processed"
                ).first()
                
                if user_docs:
                    user_id = user_docs.user_id
                    query = db.query(Document).filter(
                        Document.user_id == user_id,
                        Document.upload_status == "processed"
                    )
                    
                    if document_ids:
                        query = query.filter(Document.id.in_(document_ids))
                    
                    documents = query.all()
            
            if not documents:
                return {
                    "success": False,
                    "error": "No processed documents found. Please upload and process some documents first."
                }
            
            # Extract data from documents
            policy_data = {}
            invoice_data = {}
            
            for doc in documents:
                if doc.file_type == "policy" and doc.extracted_data:
                    policy_data.update(doc.extracted_data)
                elif doc.file_type == "invoice" and doc.extracted_data:
                    invoice_data.update(doc.extracted_data)
            
            # Create vendor-specific form data
            vendor_form_data = {
                "claim_id": f"{vendor.name.upper()}_{session_id[:8]}",
                "form_type": "vendor",
                "vendor_name": vendor.display_name,
                "vendor_id": vendor_id,
                "patient_name": policy_data.get("policy_holder_name", ""),
                "policy_number": policy_data.get("policy_number", ""),
                "insurer_name": policy_data.get("insurance_company", ""),
                "coverage_amount": policy_data.get("sum_insured", ""),
                "hospital_name": invoice_data.get("hospital_name", ""),
                "service_date": invoice_data.get("service_date", ""),
                "total_amount": invoice_data.get("total_amount", ""),
                "procedures": invoice_data.get("procedures", []),
                "claim_reason": "Medical treatment",
                "date_of_incident": invoice_data.get("service_date", ""),
                "treatment_details": invoice_data.get("treatment_description", ""),
                "doctor_name": invoice_data.get("doctor_name", ""),
                "room_type": invoice_data.get("room_type", ""),
                "admission_date": invoice_data.get("admission_date", ""),
                "discharge_date": invoice_data.get("discharge_date", ""),
                "diagnosis": invoice_data.get("diagnosis", ""),
                "pre_existing_condition": "No",
                "previous_claims": "No",
                "bank_details": {
                    "account_holder_name": policy_data.get("policy_holder_name", ""),
                    "account_number": "",
                    "ifsc_code": "",
                    "bank_name": ""
                }
            }
            
            # Generate HTML preview
            preview_html = self._generate_vendor_form_html(vendor_form_data, vendor)
            
            # Generate PDF
            pdf_filename = f"{vendor.name}_claim_{session_id[:8]}.pdf"
            pdf_path = os.path.join("uploads", "generated_forms", pdf_filename)
            os.makedirs(os.path.dirname(pdf_path), exist_ok=True)
            
            try:
                if vendor.form_template_url and "d28c6jni2fmamz.cloudfront.net" in vendor.form_template_url:
                    # Use template-based generation for Star Health
                    pdf_generator.generate_pdf_from_template(vendor_form_data, vendor.form_template_url, pdf_path)
                else:
                    # Use standard vendor form generation
                    pdf_generator.generate_vendor_claim_pdf(vendor_form_data, vendor.display_name, pdf_path)
                
                vendor_form_data["pdf_path"] = pdf_path
                vendor_form_data["pdf_filename"] = pdf_filename
            except Exception as e:
                print(f"Error generating PDF: {e}")
                vendor_form_data["pdf_path"] = None
                vendor_form_data["pdf_filename"] = None
            
            # Identify missing fields
            missing_fields = []
            for key, value in vendor_form_data.items():
                if not value or (isinstance(value, str) and value.strip() == ""):
                    missing_fields.append(key.replace("_", " ").title())
            
            return {
                "success": True,
                "form_data": vendor_form_data,
                "preview_html": preview_html,
                "missing_fields": missing_fields,
                "pdf_path": vendor_form_data.get("pdf_path"),
                "pdf_filename": vendor_form_data.get("pdf_filename")
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def _generate_synthetic_form_html(self, form_data: Dict[str, Any]) -> str:
        """Generate HTML preview for synthetic claim form."""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Insurance Claim Form - Synthetic</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .form-section {{ margin-bottom: 20px; border: 1px solid #ddd; padding: 15px; }}
                .form-title {{ font-size: 18px; font-weight: bold; margin-bottom: 10px; color: #333; }}
                .field {{ margin-bottom: 10px; }}
                .field-label {{ font-weight: bold; display: inline-block; width: 200px; }}
                .field-value {{ display: inline-block; }}
                .section-title {{ font-size: 16px; font-weight: bold; margin: 15px 0 10px 0; color: #555; border-bottom: 1px solid #ccc; }}
            </style>
        </head>
        <body>
            <div class="form-section">
                <div class="form-title">MEDICAL INSURANCE CLAIM FORM</div>
                <div class="field">
                    <span class="field-label">Claim ID:</span>
                    <span class="field-value">{form_data.get('claim_id', 'N/A')}</span>
                </div>
                <div class="field">
                    <span class="field-label">Form Type:</span>
                    <span class="field-value">Synthetic Form</span>
                </div>
            </div>
            
            <div class="section-title">PATIENT INFORMATION</div>
            <div class="form-section">
                <div class="field">
                    <span class="field-label">Patient Name:</span>
                    <span class="field-value">{form_data.get('patient_name', 'N/A')}</span>
                </div>
                <div class="field">
                    <span class="field-label">Policy Number:</span>
                    <span class="field-value">{form_data.get('policy_number', 'N/A')}</span>
                </div>
            </div>
            
            <div class="section-title">INSURANCE INFORMATION</div>
            <div class="form-section">
                <div class="field">
                    <span class="field-label">Insurance Company:</span>
                    <span class="field-value">{form_data.get('insurer_name', 'N/A')}</span>
                </div>
                <div class="field">
                    <span class="field-label">Coverage Amount:</span>
                    <span class="field-value">₹{form_data.get('coverage_amount', 'N/A')}</span>
                </div>
            </div>
            
            <div class="section-title">MEDICAL INFORMATION</div>
            <div class="form-section">
                <div class="field">
                    <span class="field-label">Hospital/Facility:</span>
                    <span class="field-value">{form_data.get('hospital_name', 'N/A')}</span>
                </div>
                <div class="field">
                    <span class="field-label">Service Date:</span>
                    <span class="field-value">{form_data.get('service_date', 'N/A')}</span>
                </div>
                <div class="field">
                    <span class="field-label">Total Amount:</span>
                    <span class="field-value">₹{form_data.get('total_amount', 'N/A')}</span>
                </div>
                <div class="field">
                    <span class="field-label">Doctor Name:</span>
                    <span class="field-value">{form_data.get('doctor_name', 'N/A')}</span>
                </div>
                <div class="field">
                    <span class="field-label">Diagnosis:</span>
                    <span class="field-value">{form_data.get('diagnosis', 'N/A')}</span>
                </div>
            </div>
        </body>
        </html>
        """
        return html

    def _generate_vendor_form_html(self, form_data: Dict[str, Any], vendor) -> str:
        """Generate HTML preview for vendor-specific claim form."""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Insurance Claim Form - {vendor.display_name}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .form-section {{ margin-bottom: 20px; border: 1px solid #ddd; padding: 15px; }}
                .form-title {{ font-size: 18px; font-weight: bold; margin-bottom: 10px; color: #333; }}
                .field {{ margin-bottom: 10px; }}
                .field-label {{ font-weight: bold; display: inline-block; width: 200px; }}
                .field-value {{ display: inline-block; }}
                .section-title {{ font-size: 16px; font-weight: bold; margin: 15px 0 10px 0; color: #555; border-bottom: 1px solid #ccc; }}
                .vendor-header {{ background-color: #f0f0f0; padding: 10px; margin-bottom: 20px; }}
            </style>
        </head>
        <body>
            <div class="vendor-header">
                <div class="form-title">{vendor.display_name} - MEDICAL INSURANCE CLAIM FORM</div>
                <div class="field">
                    <span class="field-label">Claim ID:</span>
                    <span class="field-value">{form_data.get('claim_id', 'N/A')}</span>
                </div>
            </div>
            
            <div class="section-title">PATIENT INFORMATION</div>
            <div class="form-section">
                <div class="field">
                    <span class="field-label">Patient Name:</span>
                    <span class="field-value">{form_data.get('patient_name', 'N/A')}</span>
                </div>
                <div class="field">
                    <span class="field-label">Policy Number:</span>
                    <span class="field-value">{form_data.get('policy_number', 'N/A')}</span>
                </div>
            </div>
            
            <div class="section-title">INSURANCE INFORMATION</div>
            <div class="form-section">
                <div class="field">
                    <span class="field-label">Insurance Company:</span>
                    <span class="field-value">{form_data.get('insurer_name', 'N/A')}</span>
                </div>
                <div class="field">
                    <span class="field-label">Coverage Amount:</span>
                    <span class="field-value">₹{form_data.get('coverage_amount', 'N/A')}</span>
                </div>
            </div>
            
            <div class="section-title">MEDICAL INFORMATION</div>
            <div class="form-section">
                <div class="field">
                    <span class="field-label">Hospital/Facility:</span>
                    <span class="field-value">{form_data.get('hospital_name', 'N/A')}</span>
                </div>
                <div class="field">
                    <span class="field-label">Service Date:</span>
                    <span class="field-value">{form_data.get('service_date', 'N/A')}</span>
                </div>
                <div class="field">
                    <span class="field-label">Total Amount:</span>
                    <span class="field-value">₹{form_data.get('total_amount', 'N/A')}</span>
                </div>
                <div class="field">
                    <span class="field-label">Doctor Name:</span>
                    <span class="field-value">{form_data.get('doctor_name', 'N/A')}</span>
                </div>
                <div class="field">
                    <span class="field-label">Diagnosis:</span>
                    <span class="field-value">{form_data.get('diagnosis', 'N/A')}</span>
                </div>
            </div>
        </body>
        </html>
        """
        return html

# Global agent service instance
agent_service = AgentService()

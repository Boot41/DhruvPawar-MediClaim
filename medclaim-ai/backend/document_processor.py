"""
Advanced Document Processing and Chunking System
Handles documents with AI-powered parsing and intelligent chunking
"""
import os
import uuid
import re
import time
import hashlib
import json
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
import PyPDF2
import pdfplumber
import fitz  # PyMuPDF
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
import tiktoken
from datetime import datetime

# LlamaParse (LlamaIndex Cloud parser) - optional
try:
    from llama_parse import LlamaParse
    _LLAMAPARSE_AVAILABLE = True
except ImportError:
    _LLAMAPARSE_AVAILABLE = False

logger = logging.getLogger(__name__)

class DocumentProcessor:
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", ".", "!", "?", ",", " ", ""]
        )
        self.processed_documents = {}
        self.persistence_file = os.path.join(os.path.dirname(__file__), 'processed_documents.json')
        self._load_from_disk()
    
    def _load_from_disk(self) -> None:
        """Load cached processed documents from disk if available."""
        try:
            if os.path.exists(self.persistence_file):
                with open(self.persistence_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        self.processed_documents = data
                        logger.info(f"Loaded {len(self.processed_documents)} processed documents from cache")
        except Exception as e:
            logger.warning(f"Failed to load processed documents from disk: {e}")

    def _save_to_disk(self) -> None:
        """Persist processed documents to disk."""
        try:
            with open(self.persistence_file, 'w', encoding='utf-8') as f:
                json.dump(self.processed_documents, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.warning(f"Failed to save processed documents to disk: {e}")
    
    def extract_text_from_file(self, file_path: str) -> str:
        """Extract text from various file types."""
        file_ext = Path(file_path).suffix.lower()
        
        # Handle PDF files
        if file_ext == '.pdf':
            return self.extract_text_from_pdf(file_path)
        
        # Handle text files
        elif file_ext in ['.txt', '.text']:
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    text = file.read()
                print(f"✓ Extracted {len(text)} characters from text file")
                return text
            except Exception as e:
                print(f"Text file reading failed: {e}")
                return ""
        
        # Handle other formats (can be extended)
        else:
            print(f"⚠️ Unsupported file format: {file_ext}")
            return ""
    
    def extract_text_from_pdf(self, file_path: str) -> str:
        """Extract text from PDF using multiple methods for better accuracy."""
        text = ""
        
        # Method 1: Try pdfplumber first (better for complex layouts)
        try:
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
            if text.strip():
                print(f"✓ Extracted {len(text)} characters using pdfplumber")
                return text
        except Exception as e:
            print(f"pdfplumber failed: {e}")
        
        # Method 2: Fallback to PyPDF2
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
            if text.strip():
                print(f"✓ Extracted {len(text)} characters using PyPDF2")
                return text
        except Exception as e:
            print(f"PyPDF2 failed: {e}")
        
        print("⚠️ No text could be extracted from PDF")
        return ""
    
    def chunk_document(self, text: str, document_id: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Split document into manageable chunks with metadata."""
        if not text.strip():
            return []
        
        # Create langchain document
        doc = Document(page_content=text, metadata=metadata)
        
        # Split into chunks
        chunks = self.text_splitter.split_documents([doc])
        
        # Convert to our format
        processed_chunks = []
        for i, chunk in enumerate(chunks):
            chunk_data = {
                "chunk_id": f"{document_id}_chunk_{i}",
                "document_id": document_id,
                "chunk_index": i,
                "content": chunk.page_content,
                "metadata": {
                    **chunk.metadata,
                    "chunk_size": len(chunk.page_content),
                    "created_at": datetime.now().isoformat()
                }
            }
            processed_chunks.append(chunk_data)
        
        print(f"✓ Created {len(processed_chunks)} chunks from document {document_id}")
        return processed_chunks
    
    async def process_insurance_document(self, file_path: str, document_type: str) -> Dict[str, Any]:
        """Process insurance document using advanced AI-powered parsing."""
        try:
            # Check if document already processed (by file hash)
            file_hash = self._get_file_hash(file_path)
            if file_hash in self.processed_documents:
                logger.info(f"Using cached document for {file_path}")
                return self.processed_documents[file_hash]
            
            # Try LlamaParse first (if available)
            if _LLAMAPARSE_AVAILABLE:
                try:
                    result = await self._process_with_llamaparse(file_path, document_type)
                    if result["success"]:
                        self.processed_documents[file_hash] = result
                        self._save_to_disk()
                        return result
                except Exception as e:
                    logger.warning(f"LlamaParse failed, falling back to basic extraction: {e}")
            
            # Fallback to basic extraction
            result = await self._process_with_basic_extraction(file_path, document_type)
            self.processed_documents[file_hash] = result
            self._save_to_disk()
            return result
            
        except Exception as e:
            logger.error(f"Document processing failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _get_file_hash(self, file_path: str) -> str:
        """Generate hash for file to use as cache key."""
        try:
            with open(file_path, 'rb') as f:
                file_content = f.read()
            return hashlib.sha256(file_content).hexdigest()[:16]
        except Exception:
            return str(uuid.uuid4())[:16]
    
    async def _process_with_llamaparse(self, file_path: str, document_type: str) -> Dict[str, Any]:
        """Process document using LlamaParse AI service."""
        try:
            llama_key = os.getenv("LLAMA_CLOUD_API_KEY") or os.getenv("LLAMA_CLOUD_APIKEY")
            if not llama_key:
                raise RuntimeError("LLAMA_CLOUD_API_KEY not set")
            
            # Configure parser for markdown output
            parser = LlamaParse(
                api_key=llama_key,
                result_type="markdown",
                num_workers=1,
                verbose=True,
                do_not_cache=True,
                page_separator="---PAGE_BREAK---"
            )
            
            # Parse the document
            documents = parser.load_data(file_path)
            if not documents:
                raise ValueError("LlamaParse returned no documents")
            
            # Combine markdown content
            markdown_content = "\n".join([d.text for d in documents])
            
            # Fallback: If markdown is empty, try extracting plain text with PyMuPDF
            if not markdown_content.strip():
                try:
                    plain_text = self._extract_text_with_pymupdf(file_path)
                    if plain_text.strip():
                        markdown_content = plain_text
                        logger.info(f"Used PyMuPDF fallback text extraction for {file_path}")
                except Exception as fb_e:
                    logger.warning(f"Fallback text extraction failed for {file_path}: {fb_e}")
            
            # Extract images using PyMuPDF
            document_id = str(uuid.uuid4())
            image_info = self._extract_images(file_path, document_id)
            images = image_info["images"]
            image_md_links = image_info["markdown_links"]

            if image_md_links:
                markdown_content += "\n\n## Extracted Figures\n\n" + "\n\n".join(image_md_links)
            
            # Create intelligent chunks from markdown
            chunks = self._create_intelligent_chunks(markdown_content, document_type)
            
            result = {
                "success": True,
                "document_id": document_id,
                "document_type": document_type,
                "text": markdown_content,
                "chunks": chunks,
                "total_chunks": len(chunks),
                "parser": "llamaparse",
                "images": images
            }
            
            # Export markdown
            self._export_markdown(document_id, result)
            
            return result
            
        except Exception as e:
            logger.error(f"LlamaParse processing failed: {e}")
            raise
    
    async def _process_with_basic_extraction(self, file_path: str, document_type: str) -> Dict[str, Any]:
        """Fallback processing using basic text extraction."""
        try:
            # Extract text using existing methods
            text = self.extract_text_from_file(file_path)
            
            if not text.strip():
                return {
                    "success": False,
                    "error": "No text could be extracted from the document"
                }
            
            # Create document chunks
            chunks = self.create_document_chunks(text, document_type)
            
            # Extract images using PyMuPDF
            document_id = str(uuid.uuid4())
            image_info = self._extract_images(file_path, document_id)
            images = image_info["images"]
            
            result = {
                "success": True,
                "document_id": document_id,
                "document_type": document_type,
                "text": text,
                "chunks": chunks,
                "total_chunks": len(chunks),
                "parser": "basic",
                "images": images
            }
            
            # Export markdown
            self._export_markdown(document_id, result)
            
            return result
            
        except Exception as e:
            logger.error(f"Basic extraction failed: {e}")
            raise
    
    def create_document_chunks(self, text: str, document_type: str) -> List[Dict[str, Any]]:
        """Create document chunks using the existing chunking method."""
        document_id = str(uuid.uuid4())
        
        # Create metadata
        metadata = {
            "document_type": document_type,
            "total_characters": len(text),
            "processing_timestamp": datetime.now().isoformat()
        }
        
        # Create langchain document
        from langchain.schema import Document
        doc = Document(page_content=text, metadata=metadata)
        
        # Split into chunks
        chunks = self.text_splitter.split_documents([doc])
        
        # Convert to our format
        processed_chunks = []
        for i, chunk in enumerate(chunks):
            chunk_data = {
                "chunk_index": i,
                "content": chunk.page_content,
                "metadata": {
                    **chunk.metadata,
                    "chunk_size": len(chunk.page_content),
                    "created_at": datetime.now().isoformat(),
                    "chunk_type": self._determine_chunk_type(chunk.page_content, document_type)
                }
            }
            processed_chunks.append(chunk_data)
        
        return processed_chunks
    
    def _create_intelligent_chunks(self, markdown_content: str, document_type: str) -> List[Dict[str, Any]]:
        """Create intelligent chunks from markdown content."""
        chunks = []
        
        # Split by pages first
        pages = markdown_content.split("---PAGE_BREAK---")
        chunk_counter = 0
        
        for page_num, page_content in enumerate(pages):
            if not page_content.strip():
                continue
                
            page_number = page_num + 1
            
            # Split page content by sections and paragraphs
            paragraphs = re.split(r'(\n\s*\n|## |### )', page_content)
            current_content = ""
            
            for i, part in enumerate(paragraphs):
                if part.strip():
                    current_content += part
                
                # Create chunk when we hit a section break or end of content
                if (part.strip() == "" or i == len(paragraphs) - 1) and current_content.strip():
                    chunk_id = f"chunk_{chunk_counter}"
                    
                    # Determine chunk type based on content
                    chunk_type = self._determine_chunk_type(current_content, document_type)
                    
                    chunks.append({
                        "chunk_index": chunk_counter,
                        "content": current_content.strip(),
                        "metadata": {
                            "chunk_type": chunk_type,
                            "page": page_number,
                            "chunk_id": chunk_id
                        }
                    })
                    current_content = ""
                    chunk_counter += 1
        
        return chunks
    
    def _determine_chunk_type(self, content: str, document_type: str) -> str:
        """Determine the type of chunk based on content analysis."""
        content_lower = content.lower()
        
        if document_type == "policy":
            if any(keyword in content_lower for keyword in ["policy number", "policy no", "policy id"]):
                return "policy_info"
            elif any(keyword in content_lower for keyword in ["coverage", "sum insured", "amount"]):
                return "coverage_info"
            elif any(keyword in content_lower for keyword in ["deductible", "excess", "copay"]):
                return "terms_info"
            elif any(keyword in content_lower for keyword in ["terms", "conditions", "clause"]):
                return "terms_info"
            else:
                return "general_info"
        
        elif document_type == "invoice":
            if any(keyword in content_lower for keyword in ["patient", "name", "dob"]):
                return "patient_info"
            elif any(keyword in content_lower for keyword in ["hospital", "medical", "center", "clinic"]):
                return "facility_info"
            elif any(keyword in content_lower for keyword in ["procedure", "treatment", "service"]):
                return "procedure_info"
            elif any(keyword in content_lower for keyword in ["amount", "total", "bill", "charge"]):
                return "billing_info"
            else:
                return "general_info"
        
        return "general_info"
    
    def _extract_images(self, file_path: str, document_id: str) -> dict:
        """Extract images from a PDF using PyMuPDF and save them."""
        images = []
        markdown_links = []
        try:
            # Create images directory
            images_dir = os.path.join(os.path.dirname(__file__), "..", "processed", document_id, "images")
            os.makedirs(images_dir, exist_ok=True)

            doc = fitz.open(file_path)
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                image_list = page.get_images(full=True)
                for img_index, img in enumerate(image_list):
                    xref = img[0]
                    base_image = doc.extract_image(xref)
                    image_bytes = base_image["image"]
                    image_ext = base_image["ext"]

                    # Create safe filename
                    safe_filename = os.path.splitext(os.path.basename(file_path))[0]
                    image_name = f"{safe_filename}-p{page_num + 1}-{img_index}.{image_ext}"
                    image_path = os.path.join(images_dir, image_name)

                    with open(image_path, "wb") as f:
                        f.write(image_bytes)

                    images.append({
                        "image_id": f"{safe_filename}_p{page_num+1}_{img_index}",
                        "path": image_path,
                        "page": page_num + 1
                    })
                    markdown_links.append(f"![Figure from {safe_filename} page {page_num + 1}](./images/{image_name})")
            
            logger.info(f"Extracted {len(images)} images for document {document_id}")
        except Exception as e:
            logger.error(f"Error extracting images for document {document_id}: {e}")

        return {"images": images, "markdown_links": markdown_links}

    def _extract_text_with_pymupdf(self, file_path: str) -> str:
        """Extract plain text from a PDF using PyMuPDF as a best-effort fallback."""
        try:
            doc = fitz.open(file_path)
            parts = []
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                text = page.get_text("text") or ""
                # Add simple page marker
                parts.append(f"\n\n---PAGE {page_num+1}---\n\n{text.strip()}\n")
            return "\n".join(parts)
        except Exception as e:
            logger.error(f"PyMuPDF text extraction failed: {e}")
            return ""

    def _export_markdown(self, document_id: str, content: dict):
        """Export the processed content to a Markdown file."""
        try:
            if not content or "text" not in content or not content["text"]:
                logger.warning(f"No text content found for document {document_id} to export.")
                return

            # Create processed directory
            processed_dir = os.path.join(os.path.dirname(__file__), "..", "processed", document_id)
            os.makedirs(processed_dir, exist_ok=True)

            # Create filename from document type
            file_type = content.get("document_type", "document")
            out_md = os.path.join(processed_dir, f"{file_type}_{document_id}.md")

            with open(out_md, "w", encoding="utf-8") as f:
                f.write(content["text"])
            logger.info(f"Exported processed document to {out_md}")

        except Exception as e:
            logger.warning(f"Markdown export failed for {document_id}: {e}")

    def get_document_content(self, document_id: str) -> Dict[str, Any]:
        """Get processed document content"""
        return self.processed_documents.get(document_id, {})

    def list_documents(self) -> List[Dict[str, Any]]:
        """List all processed documents"""
        return [
            {
                "document_id": doc_id,
                "document_type": content.get("document_type", "unknown"),
                "parser": content.get("parser", "unknown"),
                "total_chunks": content.get("total_chunks", 0)
            }
            for doc_id, content in self.processed_documents.items()
        ]

    def delete_document(self, document_id: str):
        """Delete a processed document and its associated files."""
        if document_id in self.processed_documents:
            del self.processed_documents[document_id]
            
            # Also delete the processed folder
            processed_dir = os.path.join(os.path.dirname(__file__), "..", "processed", document_id)
            if os.path.exists(processed_dir):
                import shutil
                shutil.rmtree(processed_dir)
                logger.info(f"Deleted processed directory: {processed_dir}")
            
            logger.info(f"Deleted document {document_id} from memory.")
            # Persist state
            self._save_to_disk()

    async def process_pdf_from_url(self, pdf_url: str) -> str:
        """
        Download a PDF from URL, parse it with LlamaParse, and cache results under a stable document_id.
        The document_id is derived from a SHA256 hash of the URL, so repeated calls reuse the cache.
        """
        try:
            if not pdf_url.lower().startswith("http"):
                raise ValueError("pdf_url must be http/https")

            # Stable ID from URL hash
            url_hash = hashlib.sha256(pdf_url.encode("utf-8")).hexdigest()[:16]
            document_id = f"url_{url_hash}"

            # Return cached if exists
            if document_id in self.processed_documents:
                return document_id

            # Prepare paths
            processed_dir = os.path.join(os.path.dirname(__file__), "..", "processed", document_id)
            os.makedirs(processed_dir, exist_ok=True)
            local_pdf_path = os.path.join(processed_dir, "source.pdf")

            # Download PDF
            import requests
            timeout = int(os.getenv("PDF_FETCH_TIMEOUT_S", "60"))
            max_mb = int(os.getenv("PDF_MAX_MB", "50"))
            resp = requests.get(pdf_url, timeout=timeout, stream=True)
            resp.raise_for_status()

            total_bytes = 0
            with open(local_pdf_path, "wb") as f:
                for chunk in resp.iter_content(chunk_size=1024 * 64):
                    if chunk:
                        f.write(chunk)
                        total_bytes += len(chunk)
                        if total_bytes > max_mb * 1024 * 1024:
                            raise RuntimeError("PDF exceeds maximum allowed size")

            filename = os.path.basename(pdf_url.split("?")[0]) or "downloaded.pdf"

            # Process using existing flow
            result = await self.process_insurance_document(local_pdf_path, "policy")
            if result["success"]:
                result["document_id"] = document_id
                result["metadata"]["source_url"] = pdf_url
                self.processed_documents[document_id] = result
                self._save_to_disk()
                return document_id
            else:
                raise RuntimeError(f"Failed to process PDF from URL: {result.get('error')}")

        except Exception as e:
            logger.error(f"Error processing PDF from URL: {e}")
            raise
    
    def _create_policy_specific_chunks(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Create policy-specific chunks with enhanced metadata."""
        for chunk in chunks:
            content = chunk["content"].lower()
            
            # Identify chunk type based on content
            if any(keyword in content for keyword in ["coverage", "sum insured", "policy limit"]):
                chunk["metadata"]["chunk_type"] = "coverage_info"
            elif any(keyword in content for keyword in ["deductible", "excess", "out of pocket"]):
                chunk["metadata"]["chunk_type"] = "deductible_info"
            elif any(keyword in content for keyword in ["copay", "co-pay", "coinsurance"]):
                chunk["metadata"]["chunk_type"] = "copay_info"
            elif any(keyword in content for keyword in ["exclusion", "not covered", "limitation"]):
                chunk["metadata"]["chunk_type"] = "exclusion_info"
            elif any(keyword in content for keyword in ["premium", "payment", "billing"]):
                chunk["metadata"]["chunk_type"] = "premium_info"
            else:
                chunk["metadata"]["chunk_type"] = "general_info"
        
        return chunks
    
    def _create_invoice_specific_chunks(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Create invoice-specific chunks with enhanced metadata."""
        for chunk in chunks:
            content = chunk["content"].lower()
            
            # Identify chunk type based on content
            if any(keyword in content for keyword in ["patient", "name", "insured"]):
                chunk["metadata"]["chunk_type"] = "patient_info"
            elif any(keyword in content for keyword in ["hospital", "facility", "clinic"]):
                chunk["metadata"]["chunk_type"] = "facility_info"
            elif any(keyword in content for keyword in ["procedure", "treatment", "service"]):
                chunk["metadata"]["chunk_type"] = "procedure_info"
            elif any(keyword in content for keyword in ["amount", "total", "cost", "charge"]):
                chunk["metadata"]["chunk_type"] = "billing_info"
            elif any(keyword in content for keyword in ["date", "admission", "discharge"]):
                chunk["metadata"]["chunk_type"] = "date_info"
            else:
                chunk["metadata"]["chunk_type"] = "general_info"
        
        return chunks
    
    def get_chunk_summary(self, chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Get a summary of all chunks for quick overview."""
        total_chunks = len(chunks)
        total_characters = sum(chunk["metadata"]["chunk_size"] for chunk in chunks)
        
        chunk_types = {}
        for chunk in chunks:
            chunk_type = chunk["metadata"].get("chunk_type", "general_info")
            chunk_types[chunk_type] = chunk_types.get(chunk_type, 0) + 1
        
        return {
            "total_chunks": total_chunks,
            "total_characters": total_characters,
            "average_chunk_size": total_characters // total_chunks if total_chunks > 0 else 0,
            "chunk_type_distribution": chunk_types
        }

# Global processor instance
document_processor = DocumentProcessor()

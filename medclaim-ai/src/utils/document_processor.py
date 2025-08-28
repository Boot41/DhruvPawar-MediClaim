from __future__ import annotations
from typing import List
from tempfile import NamedTemporaryFile
import fitz  # PyMuPDF
from docling.document_converter import DocumentConverter
from langchain.text_splitter import RecursiveCharacterTextSplitter


class DocumentProcessor:
    """Handles PDF extraction and text chunking with PyMuPDF and Docling fallback."""
    
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
    
    def extract_text_from_pdf(self, file_bytes: bytes) -> str:
        """Extract text from PDF using PyMuPDF first, then Docling fallback if needed."""
        # Try PyMuPDF first (fast)
        text_content = ""
        try:
            with fitz.open(stream=file_bytes, filetype="pdf") as doc:
                for page in doc:
                    text_content += page.get_text() + "\n\n"
        except Exception:
            text_content = ""
        
        # If we got substantial text, return it
        if text_content and len(text_content.strip()) >= 500:
            return text_content.strip()
        
        # Fallback to Docling for better extraction
        try:
            converter = DocumentConverter()
            with NamedTemporaryFile(suffix=".pdf", delete=True) as tmp:
                tmp.write(file_bytes)
                tmp.flush()
                dl_doc = converter.convert(source=tmp.name).document
                markdown_content = dl_doc.export_to_markdown()
                if markdown_content and markdown_content.strip():
                    return markdown_content.strip()
        except Exception:
            pass
        
        # Return whatever we got from PyMuPDF (may be empty)
        return text_content.strip()
    
    def chunk_text(self, text: str) -> List[str]:
        """Split text into chunks using RecursiveCharacterTextSplitter."""
        if not text:
            return []
        return self.text_splitter.split_text(text)
    
    def process_pdf(self, file_bytes: bytes) -> List[str]:
        """Complete pipeline: extract text from PDF and chunk it."""
        text = self.extract_text_from_pdf(file_bytes)
        return self.chunk_text(text)

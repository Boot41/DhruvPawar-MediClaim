from typing import List, Dict, Any, Optional
from langchain_ollama import ChatOllama
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from config.settings import get_settings
from utils.document_processor import DocumentProcessor
from utils.vector_store import VectorStoreManager


class MedClaimRAGService:
    """RAG service for medical claim document processing and querying."""
    
    def __init__(self):
        self.settings = get_settings()
        self.document_processor = DocumentProcessor(
            chunk_size=self.settings.chunk_size,
            chunk_overlap=self.settings.chunk_overlap
        )
        self.vector_store = VectorStoreManager()
        
        # Initialize LLM
        self.llm = ChatOllama(
            model=self.settings.ollama_model,
            base_url=self.settings.ollama_base_url,
            temperature=0.2,
            request_timeout=self.settings.request_timeout,
        )
        
        # Create prompt template for medical claims
        self.prompt_template = PromptTemplate(
            input_variables=["context", "question"],
            template="""You are a medical claims AI assistant. Use the provided context to answer questions about medical claims, policies, and procedures.

Context from documents:
{context}

Question: {question}

Instructions:
- Only use information from the provided context
- If the answer is not in the context, say "I cannot find this information in the provided documents"
- For medical claims, focus on policy numbers, patient details, procedures, diagnosis codes, and claim amounts
- Provide specific references to document sections when possible
- Be precise and factual

Answer:"""
        )
        
        # Initialize QA chain
        self.qa_chain = None
        self._setup_qa_chain()
    
    def _setup_qa_chain(self):
        """Setup the QA chain with retriever."""
        retriever = self.vector_store.get_retriever()
        self.qa_chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=retriever,
            return_source_documents=True,
            chain_type_kwargs={"prompt": self.prompt_template}
        )
    
    def ingest_pdf(self, file_bytes: bytes, filename: str) -> Dict[str, Any]:
        """Process and ingest a PDF document."""
        try:
            # Extract and chunk text
            chunks = self.document_processor.process_pdf(file_bytes)
            
            if not chunks:
                return {
                    "filename": filename,
                    "status": "error",
                    "message": "No text could be extracted from the PDF",
                    "chunks_added": 0
                }
            
            # Add to vector store
            chunks_added = self.vector_store.add_documents(chunks, filename)
            
            # Refresh QA chain to include new documents
            self._setup_qa_chain()
            
            return {
                "filename": filename,
                "status": "success",
                "chunks_added": chunks_added,
                "message": f"Successfully processed {filename}"
            }
            
        except Exception as e:
            return {
                "filename": filename,
                "status": "error",
                "message": f"Error processing {filename}: {str(e)}",
                "chunks_added": 0
            }
    
    def query(self, question: str, filter_filenames: Optional[List[str]] = None) -> Dict[str, Any]:
        """Query the knowledge base with optional filename filtering."""
        try:
            # Use filtered retriever if filenames specified
            if filter_filenames:
                retriever = self.vector_store.get_filtered_retriever(filter_filenames)
                temp_qa_chain = RetrievalQA.from_chain_type(
                    llm=self.llm,
                    chain_type="stuff",
                    retriever=retriever,
                    return_source_documents=True,
                    chain_type_kwargs={"prompt": self.prompt_template}
                )
                result = temp_qa_chain.invoke({"query": question})
            else:
                result = self.qa_chain.invoke({"query": question})
            
            # Format response
            answer = result.get("result", "")
            source_docs = result.get("source_documents", [])
            
            sources = []
            for doc in source_docs:
                sources.append({
                    "content": doc.page_content[:500] + "..." if len(doc.page_content) > 500 else doc.page_content,
                    "metadata": doc.metadata,
                    "filename": doc.metadata.get("filename", "unknown")
                })
            
            return {
                "answer": answer,
                "sources": sources,
                "status": "success"
            }
            
        except Exception as e:
            return {
                "answer": f"Error processing query: {str(e)}",
                "sources": [],
                "status": "error"
            }
    
    def get_document_stats(self) -> Dict[str, Any]:
        """Get statistics about indexed documents."""
        try:
            # This is a simple implementation - in production you might want more detailed stats
            return {
                "status": "success",
                "message": "Vector store is operational"
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error getting stats: {str(e)}"
            }

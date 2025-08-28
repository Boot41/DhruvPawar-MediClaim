from typing import List, Dict, Any, Optional
from langchain_ollama import ChatOllama
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from config.settings import get_settings
from utils.document_processor import DocumentProcessor
from utils.vector_store import VectorStoreManager
import asyncio
from functools import lru_cache
import logging
import time


class MedClaimRAGService:
    """RAG service for medical claim document processing and querying."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.logger.info("Initializing MedClaimRAGService...")
        
        start_time = time.time()
        self.settings = get_settings()
        self.logger.info(f"Settings loaded: {self.settings.ollama_model}, context: {self.settings.num_ctx}")
        self.logger.info(f"Embedding model: {self.settings.embedding_model}")
        
        self.document_processor = DocumentProcessor(
            chunk_size=self.settings.chunk_size,
            chunk_overlap=self.settings.chunk_overlap
        )
        self.logger.info(f"Document processor initialized with chunk_size={self.settings.chunk_size}")
        
        vector_start = time.time()
        self.vector_store = VectorStoreManager()
        vector_time = time.time() - vector_start
        self.logger.info(f"Vector store initialized in {vector_time:.2f} seconds")
        
        # Initialize LLM with optimized settings
        llm_start = time.time()
        self.logger.info(f"Initializing LLM: {self.settings.ollama_model}")
        self.llm = ChatOllama(
            model=self.settings.ollama_model,
            base_url=self.settings.ollama_base_url,
            temperature=self.settings.temperature,
            request_timeout=self.settings.request_timeout,
            ollama_keep_alive=self.settings.ollama_keep_alive,
            num_ctx=self.settings.num_ctx,
            num_threads=self.settings.num_threads,
            max_tokens=self.settings.max_tokens,
            streaming=self.settings.streaming,
            # Performance optimizations
            num_predict=self.settings.max_tokens,
            repeat_penalty=1.1,
            top_k=40,
            top_p=0.9,
        )
        llm_time = time.time() - llm_start
        self.logger.info(f"LLM initialized in {llm_time:.2f} seconds")
        
        # Create optimized prompt template for medical claims
        self.prompt_template = PromptTemplate(
            input_variables=["context", "question"],
            template="""Answer the medical claim question using only the provided context.

Context: {context}

Question: {question}

Answer concisely with specific details (policy numbers, amounts, codes) if available:"""
        )
        
        # Initialize QA chain and cache for filtered chains
        self.qa_chain = None
        self._filtered_chains_cache = {}
        qa_start = time.time()
        self._setup_qa_chain()
        qa_time = time.time() - qa_start
        
        total_time = time.time() - start_time
        self.logger.info(f"QA chain setup completed in {qa_time:.2f} seconds")
        self.logger.info(f"MedClaimRAGService fully initialized in {total_time:.2f} seconds")
    
    def _setup_qa_chain(self):
        """Setup the QA chain with retriever."""
        self.logger.info("Setting up QA chain...")
        retriever = self.vector_store.get_retriever()
        self.qa_chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=retriever,
            return_source_documents=True,
            chain_type_kwargs={"prompt": self.prompt_template}
        )
        self.logger.info("QA chain setup completed")
    
    def ingest_pdf(self, file_bytes: bytes, filename: str) -> Dict[str, Any]:
        """Process and ingest a PDF document."""
        self.logger.info(f"Starting PDF ingestion for {filename}")
        start_time = time.time()
        
        try:
            # Extract and chunk text
            self.logger.info(f"Processing PDF content for {filename}")
            chunk_start = time.time()
            chunks = self.document_processor.process_pdf(file_bytes)
            chunk_time = time.time() - chunk_start
            self.logger.info(f"PDF chunking completed in {chunk_time:.2f} seconds, {len(chunks) if chunks else 0} chunks created")
            
            if not chunks:
                self.logger.warning(f"No text extracted from {filename}")
                return {
                    "filename": filename,
                    "status": "error",
                    "message": "No text could be extracted from the PDF",
                    "chunks_added": 0
                }
            
            # Add to vector store
            self.logger.info(f"Adding {len(chunks)} chunks to vector store for {filename}")
            vector_start = time.time()
            chunks_added = self.vector_store.add_documents(chunks, filename)
            vector_time = time.time() - vector_start
            self.logger.info(f"Vector store update completed in {vector_time:.2f} seconds")
            
            # Refresh QA chain and clear filtered chain cache
            self.logger.info("Refreshing QA chain after document ingestion")
            refresh_start = time.time()
            self._setup_qa_chain()
            self._filtered_chains_cache.clear()
            refresh_time = time.time() - refresh_start
            self.logger.info(f"QA chain refresh completed in {refresh_time:.2f} seconds")
            
            total_time = time.time() - start_time
            self.logger.info(f"PDF ingestion for {filename} completed in {total_time:.2f} seconds")
            
            return {
                "filename": filename,
                "status": "success",
                "chunks_added": chunks_added,
                "message": f"Successfully processed {filename}"
            }
            
        except Exception as e:
            self.logger.error(f"Error processing {filename}: {str(e)}")
            return {
                "filename": filename,
                "status": "error",
                "message": f"Error processing {filename}: {str(e)}",
                "chunks_added": 0
            }
    
    def _get_filtered_qa_chain(self, filter_filenames: List[str]):
        """Get or create cached QA chain for specific filename filters."""
        cache_key = tuple(sorted(filter_filenames))
        
        if cache_key not in self._filtered_chains_cache:
            self.logger.info(f"Creating new filtered QA chain for files: {filter_filenames}")
            chain_start = time.time()
            retriever = self.vector_store.get_filtered_retriever(filter_filenames)
            self._filtered_chains_cache[cache_key] = RetrievalQA.from_chain_type(
                llm=self.llm,
                chain_type="stuff",
                retriever=retriever,
                return_source_documents=True,
                chain_type_kwargs={"prompt": self.prompt_template}
            )
            chain_time = time.time() - chain_start
            self.logger.info(f"Filtered QA chain created in {chain_time:.2f} seconds")
        else:
            self.logger.info(f"Using cached filtered QA chain for files: {filter_filenames}")
        
        return self._filtered_chains_cache[cache_key]
    
    def query(self, question: str, filter_filenames: Optional[List[str]] = None) -> Dict[str, Any]:
        """Query the knowledge base with optional filename filtering."""
        self.logger.info(f"Processing query with {len(filter_filenames) if filter_filenames else 0} file filters")
        start_time = time.time()
        
        try:
            # Use cached filtered chain if filenames specified
            if filter_filenames:
                chain_start = time.time()
                qa_chain = self._get_filtered_qa_chain(filter_filenames)
                chain_time = time.time() - chain_start
                self.logger.info(f"QA chain retrieval took {chain_time:.2f} seconds")
                
                invoke_start = time.time()
                result = qa_chain.invoke({"query": question})
                invoke_time = time.time() - invoke_start
                self.logger.info(f"Filtered query invocation took {invoke_time:.2f} seconds")
            else:
                invoke_start = time.time()
                result = self.qa_chain.invoke({"query": question})
                invoke_time = time.time() - invoke_start
                self.logger.info(f"Standard query invocation took {invoke_time:.2f} seconds")
            
            # Format response
            format_start = time.time()
            answer = result.get("result", "")
            source_docs = result.get("source_documents", [])
            self.logger.info(f"Retrieved {len(source_docs)} source documents")
            
            sources = []
            for doc in source_docs:
                sources.append({
                    "content": doc.page_content[:500] + "..." if len(doc.page_content) > 500 else doc.page_content,
                    "metadata": doc.metadata,
                    "filename": doc.metadata.get("filename", "unknown")
                })
            
            format_time = time.time() - format_start
            total_time = time.time() - start_time
            self.logger.info(f"Response formatting took {format_time:.2f} seconds")
            self.logger.info(f"Total query processing took {total_time:.2f} seconds")
            
            return {
                "answer": answer,
                "sources": sources,
                "status": "success"
            }
            
        except Exception as e:
            self.logger.error(f"Error processing query: {str(e)}")
            return {
                "answer": f"Error processing query: {str(e)}",
                "sources": [],
                "status": "error"
            }
    
    def get_document_stats(self) -> Dict[str, Any]:
        """Get statistics about indexed documents."""
        self.logger.info("Retrieving document statistics")
        try:
            stats = self.vector_store.get_stats()
            self.logger.info(f"Document stats retrieved: {stats}")
            return {
                "status": "success",
                "message": "Vector store is operational",
                "stats": stats
            }
        except Exception as e:
            self.logger.error(f"Error getting stats: {str(e)}")
            return {
                "status": "error",
                "message": f"Error getting stats: {str(e)}"
            }

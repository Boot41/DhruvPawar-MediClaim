from typing import List, Dict, Any, Optional
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from config.settings import get_settings
import threading
import logging
import time


class VectorStoreManager:
    """Manages Chroma vector database operations for document embeddings."""
    
    _embeddings = None
    _lock = threading.Lock()
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.logger.info("Initializing VectorStoreManager...")
        
        start_time = time.time()
        self.settings = get_settings()
        
        embed_start = time.time()
        self.embeddings = self._get_embeddings()
        embed_time = time.time() - embed_start
        self.logger.info(f"Embeddings initialized in {embed_time:.2f} seconds")
        
        chroma_start = time.time()
        self.vectorstore = Chroma(
            persist_directory=self.settings.chroma_persist_dir,
            embedding_function=self.embeddings,
            collection_name=self.settings.collection_name,
        )
        chroma_time = time.time() - chroma_start
        
        total_time = time.time() - start_time
        self.logger.info(f"Chroma vector store initialized in {chroma_time:.2f} seconds")
        self.logger.info(f"VectorStoreManager fully initialized in {total_time:.2f} seconds")
    
    def _get_embeddings(self):
        """Get singleton embeddings instance for better performance."""
        if VectorStoreManager._embeddings is None:
            with VectorStoreManager._lock:
                if VectorStoreManager._embeddings is None:
                    self.logger.info(f"Loading embedding model: {self.settings.embedding_model}")
                    model_start = time.time()
                    VectorStoreManager._embeddings = HuggingFaceEmbeddings(
                        model_name=self.settings.embedding_model,
                        model_kwargs={'device': 'cpu'},
                        encode_kwargs={'normalize_embeddings': True}
                    )
                    model_time = time.time() - model_start
                    self.logger.info(f"Embedding model loaded in {model_time:.2f} seconds")
        else:
            self.logger.info("Using cached embedding model")
        return VectorStoreManager._embeddings
    
    def add_documents(self, chunks: List[str], filename: str) -> int:
        """Add text chunks to the vector store with metadata."""
        if not chunks:
            self.logger.warning("No chunks provided for document addition")
            return 0
        
        self.logger.info(f"Adding {len(chunks)} chunks for {filename} to vector store")
        start_time = time.time()
        
        # Create metadata for each chunk
        metadata_start = time.time()
        metadatas = [
            {
                "filename": filename,
                "chunk_index": i,
                "source": filename
            }
            for i in range(len(chunks))
        ]
        metadata_time = time.time() - metadata_start
        
        # Add to vector store
        embed_start = time.time()
        self.vectorstore.add_texts(texts=chunks, metadatas=metadatas)
        embed_time = time.time() - embed_start
        
        total_time = time.time() - start_time
        self.logger.info(f"Document addition completed: metadata={metadata_time:.2f}s, embedding={embed_time:.2f}s, total={total_time:.2f}s")
        return len(chunks)
    
    def get_retriever(self, k: Optional[int] = None):
        """Get a retriever for the vector store."""
        search_k = k or self.settings.top_k
        self.logger.info(f"Creating retriever with k={search_k}")
        return self.vectorstore.as_retriever(search_kwargs={"k": search_k})
    
    def get_filtered_retriever(self, filenames: List[str], k: Optional[int] = None):
        """Get a retriever filtered to specific filenames."""
        search_k = k or self.settings.top_k
        self.logger.info(f"Creating filtered retriever for {filenames} with k={search_k}")
        search_kwargs = {
            "k": search_k,
            "filter": {"filename": {"$in": filenames}}
        }
        return self.vectorstore.as_retriever(search_kwargs=search_kwargs)
    
    def search_similar(self, query: str, k: Optional[int] = None) -> List[Dict[str, Any]]:
        """Search for similar documents and return with metadata."""
        search_k = k or self.settings.top_k
        self.logger.info(f"Searching for similar documents with k={search_k}")
        start_time = time.time()
        
        docs = self.vectorstore.similarity_search_with_score(query, k=search_k)
        search_time = time.time() - start_time
        
        results = []
        for doc, score in docs:
            results.append({
                "content": doc.page_content,
                "metadata": doc.metadata,
                "similarity_score": score
            })
        
        self.logger.info(f"Similarity search completed in {search_time:.2f} seconds, found {len(results)} results")
        return results
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the vector store."""
        try:
            collection = self.vectorstore._collection
            count = collection.count()
            return {
                "document_count": count,
                "collection_name": self.settings.collection_name,
                "embedding_model": self.settings.embedding_model
            }
        except Exception as e:
            self.logger.error(f"Error getting vector store stats: {str(e)}")
            return {"error": str(e)}

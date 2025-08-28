from typing import List, Dict, Any, Optional
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from config.settings import get_settings


class VectorStoreManager:
    """Manages Chroma vector database operations for document embeddings."""
    
    def __init__(self):
        self.settings = get_settings()
        self.embeddings = HuggingFaceEmbeddings(
            model_name=self.settings.embedding_model
        )
        self.vectorstore = Chroma(
            persist_directory=self.settings.chroma_persist_dir,
            embedding_function=self.embeddings,
            collection_name=self.settings.collection_name,
        )
    
    def add_documents(self, chunks: List[str], filename: str) -> int:
        """Add text chunks to the vector store with metadata."""
        if not chunks:
            return 0
        
        # Create metadata for each chunk
        metadatas = [
            {
                "filename": filename,
                "chunk_index": i,
                "source": filename
            }
            for i in range(len(chunks))
        ]
        
        # Add to vector store
        self.vectorstore.add_texts(texts=chunks, metadatas=metadatas)
        return len(chunks)
    
    def get_retriever(self, k: Optional[int] = None):
        """Get a retriever for the vector store."""
        search_k = k or self.settings.top_k
        return self.vectorstore.as_retriever(search_kwargs={"k": search_k})
    
    def get_filtered_retriever(self, filenames: List[str], k: Optional[int] = None):
        """Get a retriever filtered to specific filenames."""
        search_k = k or self.settings.top_k
        search_kwargs = {
            "k": search_k,
            "filter": {"filename": {"$in": filenames}}
        }
        return self.vectorstore.as_retriever(search_kwargs=search_kwargs)
    
    def search_similar(self, query: str, k: Optional[int] = None) -> List[Dict[str, Any]]:
        """Search for similar documents and return with metadata."""
        search_k = k or self.settings.top_k
        docs = self.vectorstore.similarity_search_with_score(query, k=search_k)
        
        results = []
        for doc, score in docs:
            results.append({
                "content": doc.page_content,
                "metadata": doc.metadata,
                "similarity_score": score
            })
        return results

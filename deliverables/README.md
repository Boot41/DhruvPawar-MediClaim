https://www.loom.com/share/d3c050bfe1ad4f26b60037ef734f66a0?sid=ad659fa3-f7ff-420f-8d86-e5df3e73109f
# MedClaim AI - Document Understanding and Generation System

## Overview

MedClaim AI is an intelligent document processing system designed for medical claim validation and analysis. It uses RAG (Retrieval-Augmented Generation) technology to understand medical documents, extract key information, and answer questions about claims, policies, and procedures.

## Features

- **PDF Document Processing**: Upload and process medical claim documents, policy documents, and medical reports
- **Intelligent Q&A**: Ask natural language questions about uploaded documents
- **Multi-document Search**: Filter queries across specific documents or search all uploaded content
- **Real-time Processing**: Optimized for fast document ingestion and query responses
- **RESTful API**: Clean API endpoints for integration with other systems
- **Streamlit UI**: User-friendly web interface for document upload and querying

## Architecture

### Core Components

1. **FastAPI Backend** (`src/api/main.py`)
   - RESTful API endpoints for document upload and querying
   - Asynchronous processing with ThreadPoolExecutor
   - Comprehensive logging and error handling

2. **RAG Service** (`src/services/rag_service.py`)
   - Document processing and vector storage
   - Query processing with LangChain
   - Cached QA chains for performance optimization

3. **Vector Store Manager** (`src/utils/vector_store.py`)
   - ChromaDB integration for document embeddings
   - Singleton embedding model for memory efficiency
   - Filtered retrieval for document-specific queries

4. **Document Processor** (`src/utils/document_processor.py`)
   - PDF text extraction and chunking
   - Optimized chunk sizes for better retrieval

## Technology Stack

- **Backend**: FastAPI, Python 3.8+
- **LLM**: Ollama (Gemma 2B model)
- **Embeddings**: HuggingFace BGE-small-en-v1.5
- **Vector Database**: ChromaDB
- **Document Processing**: LangChain
- **Frontend**: Streamlit
- **Deployment**: Uvicorn ASGI server

### Performance Metrics
- **Service initialization**: ~4-5 seconds
- **Document upload**: Varies by document size
- **Query processing**: Optimized from 2+ minutes to 15-30 seconds
- **Embedding model load**: ~4 seconds (one-time)

## API Endpoints

### Health Check
```
GET /health
```
Returns service status and health information.

### Document Upload
```
POST /upload
Content-Type: multipart/form-data
```
Upload a PDF document for processing and indexing.

**Response:**
```json
{
  "filename": "document.pdf",
  "status": "success",
  "chunks_added": 25,
  "message": "Successfully processed document.pdf"
}
```

### Query Documents
```
POST /query
Content-Type: application/json
```

**Request:**
```json
{
  "question": "What is the policy number for John Doe?",
  "filter_filenames": ["policy.pdf"] // Optional
}
```

**Response:**
```json
{
  "answer": "The policy number for John Doe is POL-123456.",
  "sources": [
    {
      "content": "Policy holder: John Doe, Policy Number: POL-123456...",
      "metadata": {"filename": "policy.pdf", "chunk_index": 0},
      "filename": "policy.pdf"
    }
  ],
  "status": "success"
}
```

### System Statistics
```
GET /stats
```
Returns document count and system information.

## Installation and Setup

### Prerequisites
- Python 3.8+
- Ollama installed and running
- Git

### Installation Steps

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd medclaim-ai
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up Ollama**
   ```bash
   # Install Ollama (if not already installed)
   curl -fsSL https://ollama.ai/install.sh | sh
   
   # Pull the required model
   ollama pull gemma:2b-instruct-q4_K_M
   
   # Start Ollama service
   ollama serve
   ```

5. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env file with your configuration
   ```

6. **Run the application**
   ```bash
   # Start API server
   uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
   
   # Or start Streamlit UI
   streamlit run src/ui/streamlit_app.py
   ```

## Configuration

### Environment Variables (.env)
```bash
# LLM Configuration
OLLAMA_MODEL=gemma:2b-instruct-q4_K_M
OLLAMA_BASE_URL=http://localhost:11434
REQUEST_TIMEOUT=60

# Embedding Configuration
EMBEDDING_MODEL=BAAI/bge-small-en-v1.5

# Vector Database
CHROMA_PERSIST_DIR=data/chroma_db
COLLECTION_NAME=medclaim-docs

# Retrieval Settings
TOP_K=2
CHUNK_SIZE=500
CHUNK_OVERLAP=100

# API Settings
MAX_FILE_SIZE_MB=50
```

### Performance Tuning
- **num_ctx**: Context window size (4096 recommended)
- **num_threads**: CPU threads for LLM (8 recommended)
- **max_tokens**: Maximum response length (512 recommended)
- **top_k**: Number of documents to retrieve (2 recommended)
- **chunk_size**: Document chunk size (500 recommended)

## Usage Examples

### Upload a Document
```bash
curl -X POST "http://localhost:8000/upload" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@sample_claim.pdf"
```

### Query Documents
```bash
curl -X POST "http://localhost:8000/query" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is the total claim amount?",
    "filter_filenames": ["sample_claim.pdf"]
  }'
```

## Logging and Monitoring

The system provides comprehensive logging for monitoring and debugging:

- **Console output**: Real-time logs during development
- **File logging**: Persistent logs in `medclaim_api.log`
- **Performance metrics**: Detailed timing for all operations
- **Error tracking**: Comprehensive error logging with stack traces

### Log Levels
- **INFO**: General operation information
- **WARNING**: Non-critical issues
- **ERROR**: Error conditions
- **DEBUG**: Detailed debugging information

## Troubleshooting

### Common Issues

1. **Ollama Connection Error**
   - Ensure Ollama is running: `ollama serve`
   - Check if model is available: `ollama list`
   - Verify base URL in configuration

2. **Embedding Dimension Mismatch**
   - Clear vector database: `rm -rf data/chroma_db`
   - Restart the service to rebuild with correct dimensions

3. **Slow Query Performance**
   - Check Ollama model size and system resources
   - Reduce context window or chunk sizes
   - Enable streaming for better perceived performance

4. **Memory Issues**
   - Use smaller embedding models
   - Reduce chunk sizes and overlap
   - Monitor system memory usage

### Performance Optimization Tips

1. **Use appropriate model sizes** for your hardware
2. **Optimize chunk sizes** based on document types
3. **Enable caching** for frequently accessed documents
4. **Monitor resource usage** and adjust thread counts
5. **Use streaming** for real-time response delivery

## Development

### Project Structure
```
medclaim-ai/
├── src/
│   ├── api/          # FastAPI application
│   ├── services/     # Core business logic
│   ├── utils/        # Utility functions
│   ├── config/       # Configuration management
│   └── ui/           # Streamlit interface
├── data/             # Vector database storage
├── tests/            # Unit and integration tests
├── requirements.txt  # Python dependencies
└── README.md         # This file
```

### Adding New Features

1. **New API endpoints**: Add to `src/api/main.py`
2. **Business logic**: Implement in `src/services/`
3. **Utilities**: Add helper functions to `src/utils/`
4. **Configuration**: Update `src/config/settings.py`

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions:
- Create an issue in the repository
- Check the troubleshooting section
- Review the logs for error details

## Changelog

### v1.0.0 (Current)
- Initial release with core RAG functionality
- FastAPI backend with async processing
- Streamlit UI for document interaction
- Performance optimizations for query speed
- Comprehensive logging and monitoring
- Support for PDF document processing
- Multi-document filtering and search

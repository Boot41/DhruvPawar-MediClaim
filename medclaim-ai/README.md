# MedClaim AI Validator

AI-powered medical claim document processing and validation system that automates document understanding, summarization, and compliance checking for health insurance claims.

## Features

- **Document Processing**: Extract text from PDFs using PyMuPDF with Docling fallback
- **AI-Powered Analysis**: BGE embeddings + Gemma 7B LLM for intelligent document understanding
- **Vector Search**: Chroma DB for semantic document retrieval
- **Interactive UI**: Streamlit frontend for easy document upload and querying
- **API Access**: FastAPI backend for programmatic integration
- **Agentic Approach**: LangChain-based RAG system for contextual responses

## Architecture

Based on the workflow diagram:
1. **Document Upload** (PDF, Scans, DOCX)
2. **AI Processing** (Text Extraction & Understanding)
3. **Knowledge Base** (Insurance Policy Rules & Medical Codes)
4. **Cross-Referencing** (Validation Against Rules)
5. **Summary Generation** (Claim Report Draft)
6. **Human Review & Editing** (Adjust & Approve)
7. **Final Report Generation** (PDF/JSON)

## Quick Start

### Prerequisites

- Python 3.10+
- Ollama installed with Gemma 7B model
- 8GB+ RAM recommended

### Installation

1. **Clone and setup**:
```bash
cd medclaim-ai
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

2. **Install Ollama model**:
```bash
ollama pull gemma:7b
```

3. **Configure environment**:
```bash
# .env file is already configured with defaults
# Modify if needed for your setup
```

### Running the Application

#### Streamlit UI (Recommended)
```bash
streamlit run src/ui/streamlit_app.py
```
Access at: http://localhost:8501

#### FastAPI (For API access)
```bash
cd src
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```
API docs at: http://localhost:8000/docs

## Usage

### Upload & Process Documents
1. Open the Streamlit interface
2. Upload PDF documents (claim forms, policy documents, medical reports)
3. Click "Process Documents" to extract and index content
4. Documents are chunked and embedded into Chroma DB

### Query Documents
1. Enter questions in natural language
2. Examples:
   - "What is the patient's policy number?"
   - "What procedures were performed?"
   - "Are there any missing documents?"
   - "What is the total claim amount?"
3. Get AI-powered answers with source references

### API Usage
```python
import requests

# Upload document
with open("claim.pdf", "rb") as f:
    response = requests.post("http://localhost:8000/upload", files={"file": f})

# Query
response = requests.post("http://localhost:8000/query", json={
    "question": "What is the patient's policy number?"
})
```

## Project Structure

```
medclaim-ai/
├── src/
│   ├── config/
│   │   └── settings.py          # Configuration management
│   ├── services/
│   │   └── rag_service.py       # Main RAG service
│   ├── utils/
│   │   ├── document_processor.py # PDF extraction & chunking
│   │   └── vector_store.py      # Chroma DB operations
│   ├── ui/
│   │   └── streamlit_app.py     # Streamlit frontend
│   └── api/
│       └── main.py              # FastAPI backend
├── data/
│   ├── uploads/                 # Uploaded files
│   ├── processed/               # Processed documents
│   └── chroma_db/               # Vector database
├── requirements.txt
├── .env
└── README.md
```

## Configuration

Key settings in `.env`:

```bash
# LLM Configuration
OLLAMA_MODEL=gemma:7b
OLLAMA_BASE_URL=http://localhost:11434

# Embedding Configuration
EMBEDDING_MODEL=BAAI/bge-base-en-v1.5

# Vector Database
CHROMA_PERSIST_DIR=data/chroma_db
COLLECTION_NAME=medclaim-docs

# Retrieval Settings
TOP_K=5
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
```

## Key Components

### Document Processing
- **PyMuPDF**: Fast PDF text extraction
- **Docling**: Fallback for complex/scanned PDFs
- **RecursiveCharacterTextSplitter**: Intelligent text chunking

### Vector Storage
- **Chroma DB**: Vector database for embeddings
- **BGE Embeddings**: High-quality sentence embeddings
- **Metadata**: Filename and chunk tracking

### RAG System
- **LangChain**: Framework for RAG implementation
- **Gemma 7B**: Local LLM via Ollama
- **Custom Prompts**: Medical domain-specific prompting

## Troubleshooting

### Common Issues

1. **Ollama connection error**:
   - Ensure Ollama is running: `ollama serve`
   - Check model is installed: `ollama list`

2. **Memory issues**:
   - Use smaller model: `ollama pull gemma:2b`
   - Reduce chunk size in `.env`

3. **PDF extraction issues**:
   - System automatically falls back to Docling
   - Check file is not corrupted

## Development

### Adding New Features
1. Document processors: Extend `DocumentProcessor` class
2. New embeddings: Modify `VectorStoreManager`
3. Custom prompts: Update `MedClaimRAGService`

### Testing
```bash
# Run tests (when implemented)
pytest tests/
```

## License

Open source - see product documentation for details.

## Contributing

1. Fork the repository
2. Create feature branch
3. Submit pull request

## Support

For issues and questions, refer to the project documentation in the `product/` directory.

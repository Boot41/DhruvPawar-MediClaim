# MedClaim AI Validator – Technical Specifications

## 1. Core Components
1. **Document Ingestion**
   - PDF Parsing: `PyMuPDF` or `pdfplumber`
   - OCR for scanned files: `Tesseract OCR`

2. **Information Extraction & NLP**
   - Base Model: `LLaMA 3`, `Mistral`, or `Phi-3-mini` (open-source)
   - Text Embeddings & Retrieval: `FAISS` or `LanceDB`
   - Named Entity Recognition (NER): `spaCy` or `HuggingFace Transformers`

3. **Summarization & Context Reasoning**
   - Lightweight Summarizer: `BART` or `Pegasus`
   - Context management: `LangChain` or `Haystack`

4. **Policy Cross-Referencing**
   - Knowledge Base: `LanceDB` or `Weaviate` for vector storage
   - Rule Engine: `Durable Rules` or custom Python logic

5. **User Interface**
   - Backend: `FastAPI` for API endpoints
   - Frontend: `Streamlit` or `Gradio` for quick UI prototyping

6. **Human-in-the-Loop Editing**
   - Document viewer + highlights
   - Feedback interface via `Gradio` or `Streamlit`

7. **Output Generation**
   - Structured Output: `Jinja2` templates for PDFs
   - Final Export: `pdfplumber` / `reportlab`

---

## 2. System Architecture
- **Frontend:** Streamlit/Gradio for document upload & review dashboard
- **Backend:** FastAPI serving AI models, retrieval pipeline, and validation logic
- **Vector Database:** FAISS for embedding-based retrieval
- **Storage:** PostgreSQL or SQLite for claim metadata
- **Models:** HuggingFace transformers for summarization, extraction, and reasoning
- **Deployment:** Docker for containerized setup

---

## 3. Open-Source Tools Summary
| Component | Tool |
|-----------|------|
| OCR | Tesseract |
| Parsing | pdfplumber, PyMuPDF |
| NLP Models | HuggingFace (BART, Pegasus, LLaMA 3) |
| Retrieval | FAISS / LanceDB |
| UI | Streamlit / Gradio |
| Backend API | FastAPI |
| Rule Engine | Durable Rules |
| Output | ReportLab |

---

## 4. Development Roadmap (2 Weeks)
**Week 1:**
- Set up document ingestion (PDF + OCR)
- Implement basic information extraction & summarization pipeline
- Integrate vector database for context management

**Week 2:**
- Add policy rule cross-referencing
- Build UI for document review & human-in-the-loop editing
- Generate final structured output (PDF)
- Test with sample insurance claim datasets

---

## 5. Expected Deliverables
- Working MVP with end-to-end document understanding & compliance check.
- Open-source GitHub repository with documentation & test cases.
- Demo UI for uploading claims & viewing AI-processed summaries.

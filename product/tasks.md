# 10-Day Development Plan for AI-Powered Insurance Claim Validation

## Goal
Develop an MVP system that:
- Extracts data from insurance claim documents (PDF, scans, DOCX)
- Cross-references claims against policy rules and medical codes
- Generates draft claim reports and assists with human review & editing
- Produces final structured outputs (PDF/JSON)

---

## Day 1 – Project Setup & Dataset Preparation
- Create repository structure:
  - `/src` for core code
  - `/data` for datasets and sample documents
  - `/notebooks` for exploratory work (EDA, testing parsers)
  - `/docs` for research and technical documentation
- Set up virtual environment with `pyproject.toml`
- Select real dataset (e.g., Mendeley Insurance Claim Dataset)
- Perform basic EDA to understand claim patterns and fields
- Define JSON schema for structured document output

---

## Day 2 – Document Upload & Management
- Implement file upload system (support PDF, scans, DOCX)
- Handle multi-page claims, embedded images, tables
- Add basic file validation (type, size, corruption checks)
- Store raw and processed files separately

---

## Day 3 – Text Extraction & Parsing (PDF, Scans, DOCX)
- Integrate **pdfplumber** or **PyMuPDF** for digital PDF extraction
- Integrate **Tesseract OCR** or **PaddleOCR** for scanned documents
- Normalize text outputs into predefined JSON schema
- Extract metadata (policy number, incident date, expenses, etc.)

---

## Day 4 – Document Structure Understanding
- Identify key sections: Patient Details, Policy Details, Expenses, Incident Info
- Use **regex + rule-based parsing** for structured fields
- Implement fallback text matching for partially extracted data
- Store extracted fields in structured format (JSON)

---

## Day 5 – Knowledge Base Setup
- Define base insurance rules (per-day cost limits, coverage types)
- Store rules in a structured YAML or JSON format for easy updates
- Create mappings to medical codes (ICD-10) for future integration
- Prepare reference module to fetch applicable rules for each claim

---

## Day 6 – Cross-Referencing (Validation Against Rules)
- Implement logic to compare extracted data with policy rules
- Examples:
  - Flag expenses exceeding daily policy limits
  - Detect missing documents for claims (hospital vs medicine bills)
- Generate a validation report (flags, suggestions, compliance notes)

---

## Day 7 – Claim Summary Generation
- Draft summary of claim including:
  - Policyholder info
  - Claimed amount vs eligible amount
  - Flagged discrepancies
- Use LLM for clean and concise report generation (structured prompt design)
- Store summaries in JSON for downstream use

---

## Day 8 – Human Review & Editing Layer
- Create interface for insurance agents to:
  - Review flagged claims
  - Edit extracted text or suggested corrections
- Enable re-validation after edits to confirm compliance

---

## Day 9 – Final Report Generation
- Generate final outputs:
  - Structured JSON for system integration
  - PDF report for compliance/legal purposes
- Include status indicators (Approved, Needs Revision, Rejected)

---

## Day 10 – Integration, Testing & Documentation
- End-to-end testing with sample claims
- Evaluate extraction accuracy and rule validation performance
- Write developer and user documentation
- Prepare demo flow for MVP presentation

---


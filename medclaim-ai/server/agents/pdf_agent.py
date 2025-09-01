# agents/pdf_agent.py
from pathlib import Path
from server.utils.pdf_utils import pdf_to_markdown_file
from server.agents.base_agent import BaseAgent

class PDFAgent(BaseAgent):
    async def preprocess(self, file_path: Path) -> Path:
        # Convert PDF to Markdown or use OCR if no text
        md_path = pdf_to_markdown_file(file_path, file_path.parent / "markdown")
        return md_path

    async def extract(self, file_path: Path) -> dict:
        # Actual extraction will be done by GeminiAgent
        return {"info": f"Preprocessed PDF at {file_path}"}

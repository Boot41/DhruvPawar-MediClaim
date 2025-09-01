# orchestrator.py
from pathlib import Path
from server.agents.pdf_agent import PDFAgent
from server.agents.image_agent import ImageAgent
from server.agents.text_agent import TextAgent
from server.agents.gemini_agent import GeminiAgent
from server.agents.verification_agent import VerificationAgent

class DocumentOrchestrator:
    def __init__(self):
        self.pdf_agent = PDFAgent()
        self.image_agent = ImageAgent()
        self.text_agent = TextAgent()
        self.gemini_agent = GeminiAgent()
        self.verification_agent = VerificationAgent()

    async def process_document(self, file_path: Path):
        ext = file_path.suffix.lower()
        if ext == ".pdf":
            preprocessed_path = await self.pdf_agent.preprocess(file_path)
        elif ext in [".jpg", ".jpeg", ".png"]:
            preprocessed_path = await self.image_agent.preprocess(file_path)
        elif ext in [".txt", ".md"]:
            preprocessed_path = await self.text_agent.preprocess(file_path)
        else:
            raise Exception("Unsupported file type")

        extracted_data = await self.gemini_agent.extract(preprocessed_path)
        verified_data = await self.verification_agent.verify(extracted_data)
        return verified_data
document_agent_orchestrator = DocumentOrchestrator()
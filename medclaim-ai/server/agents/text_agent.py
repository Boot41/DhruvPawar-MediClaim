# agents/text_agent.py
from pathlib import Path
from server.agents.base_agent import BaseAgent
from server.utils.text_utils import clean_text_file

class TextAgent(BaseAgent):
    async def preprocess(self, file_path: Path) -> Path:
        cleaned_path = clean_text_file(file_path)
        return cleaned_path

    async def extract(self, file_path: Path) -> dict:
        return {"info": f"Preprocessed Text at {file_path}"}

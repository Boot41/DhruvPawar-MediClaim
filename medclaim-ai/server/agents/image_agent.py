# agents/image_agent.py
from pathlib import Path
from server.agents.base_agent import BaseAgent
from server.utils.image_utils import preprocess_image

class ImageAgent(BaseAgent):
    async def preprocess(self, file_path: Path) -> Path:
        processed_path = await preprocess_image(file_path)
        return processed_path

    async def extract(self, file_path: Path) -> dict:
        return {"info": f"Preprocessed Image at {file_path}"}

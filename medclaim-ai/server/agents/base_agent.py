# agents/base_agent.py
from abc import ABC, abstractmethod
from pathlib import Path

class BaseAgent(ABC):
    @abstractmethod
    async def preprocess(self, file_path: Path) -> Path:
        """Preprocess the file before AI extraction"""
        pass

    @abstractmethod
    async def extract(self, file_path: Path) -> dict:
        """Perform AI extraction"""
        pass

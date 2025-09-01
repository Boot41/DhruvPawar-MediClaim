# agents/gemini_agent.py
from pathlib import Path
import google.generativeai as genai
import os

GEN_API_KEY = os.getenv("GEN_API_KEY")
genai.configure(api_key=GEN_API_KEY)

class GeminiAgent:
    async def extract(self, file_path: Path) -> dict:
        text = file_path.read_text(encoding="utf-8") if file_path.suffix in [".txt", ".md"] else ""
        prompt = f"Extract structured medical info from this document:\n{text}"
        response = genai.generate([prompt])
        return {"gemini_output": response.text}

import google.generativeai as genai
from typing import Optional, List, Dict, Any
import logging
import os
import json
import re
logger = logging.getLogger(__name__)

class GeminiClient:
    """
    Wrapper for Google's Gemini model to handle text, image and multimodal prompts.
    """

    def __init__(self, api_key: Optional[str] = None, model_name: str = "gemini-2.0-flash"):
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("Google API key not set. Use env var GOOGLE_API_KEY or pass explicitly.")

        genai.configure(api_key=self.api_key)
        self.model_name = model_name
        self.model = genai.GenerativeModel(self.model_name)
    
    async def generate_text(self, prompt: str, temperature: float = 0.2, max_output_tokens: int = 1024) -> str:
        """
        Generate text output from prompt.
        """
        try:
            response = self.model.generate_content(
                prompt,
                generation_config={
                    "temperature": temperature,
                    "max_output_tokens": max_output_tokens,
                }
            )
            return response.text.strip() if response and response.text else ""
        except Exception as e:
            logger.error(f"Gemini text generation failed: {e}")
            return ""

    async def generate_multimodal(
        self,
        prompt: str,
        images: Optional[List[str]] = None,
        temperature: float = 0.2
    ) -> str:
        """
        Generate text output from a prompt and optional images (file paths).
        """
        try:
            parts: List[Any] = [prompt]
            if images:
                for img_path in images:
                    parts.append(genai.upload_file(img_path))
            response = self.model.generate_content(parts)
            return response.text.strip() if response and response.text else ""
        except Exception as e:
            logger.error(f"Gemini multimodal generation failed: {e}")
            return ""

    async def summarize_text(self, text: str, summary_type: str = "short") -> str:
        """
        Summarize text with different styles (short, detailed, bullet).
        """
        prompt = f"Summarize the following text in a {summary_type} form:\n\n{text}"
        return await self.generate_text(prompt)
gemini_client = GeminiClient()

async def call_gemini(prompt: str, model: str = "gemini-2.0-flash", max_tokens: int = 1024) -> Dict[str, Any]:
    text = await gemini_client.generate_text(prompt, max_output_tokens=max_tokens)
    return {"text": text}

def safe_parse_json(text: str) -> Optional[Dict[str, Any]]:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None

def safe_parse_json(text: str):
    try:
        # Remove code fences like ```json ... ```
        clean = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.MULTILINE).strip()
        return json.loads(clean)
    except Exception:
        return None

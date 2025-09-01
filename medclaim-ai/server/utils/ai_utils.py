from pathlib import Path
import json
from server.utils import pdf_utils, image_utils, text_utils

async def extract_from_image(image_path: Path) -> dict:
    """
    Extract info from an image using AI.
    Replace with your actual AI integration.
    """
    # placeholder
    return {
        "document_type": "image",
        "confidence": 0.9,
        "raw_text": "AI placeholder text from image"
    }

async def extract_from_text_file(text_file_path: Path) -> dict:
    text = text_utils.read_text_file(text_file_path)
    text = text_utils.clean_text(text)
    # Replace with your AI model integration
    return {
        "document_type": "text",
        "confidence": 0.9,
        "raw_text": text
    }

async def extract_from_pdf(pdf_path: Path, markdown_output_dir: Path) -> dict:
    """
    Convert PDF to Markdown, then extract AI info.
    """
    md_path = pdf_utils.pdf_to_markdown_file(pdf_path, markdown_output_dir)
    extracted_data = await extract_from_text_file(md_path)
    return extracted_data

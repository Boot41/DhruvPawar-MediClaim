from pathlib import Path
from PIL import Image
import fitz
import uuid
import io
import pytesseract
import logging

logger = logging.getLogger(__name__)

def pdf_to_markdown_file(pdf_path: Path, output_dir: Path) -> Path:
    """
    Extracts text from all pages of a PDF and saves it as a Markdown file.
    Falls back to OCR for pages without selectable text.
    """
    output_dir.mkdir(exist_ok=True)
    all_text = []

    try:
        with fitz.open(pdf_path) as doc:
            for i, page in enumerate(doc):
                text = page.get_text("text").strip()
                if not text:
                    # Fallback to OCR for image-based pages
                    pix = page.get_pixmap()
                    img_data = pix.tobytes("png")
                    image = Image.open(io.BytesIO(img_data))
                    text = pytesseract.image_to_string(image)

                all_text.append(f"### Page {i+1}\n\n{text}\n")

        combined_text = "\n".join(all_text)

        md_filename = f"{pdf_path.stem}_{uuid.uuid4().hex}.md"
        md_path = output_dir / md_filename
        md_path.write_text(combined_text, encoding="utf-8")

        logger.info(f"PDF converted to markdown: {md_path}")
        return md_path

    except Exception as e:
        logger.error(f"Failed to convert {pdf_path} to markdown: {e}")
        raise

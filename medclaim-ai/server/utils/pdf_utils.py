from pathlib import Path
from PIL import Image
import fitz
import uuid
import io
import pytesseract

def pdf_to_markdown_file(pdf_path: Path, output_dir: Path) -> Path:
    """
    Convert PDF to Markdown file.
    1. Try extracting text using PyMuPDF.
    2. If empty, fallback to OCR on first page.
    3. Save result as a .md file in output_dir.
    Returns path to the markdown file.
    """
    output_dir.mkdir(exist_ok=True)

    doc = fitz.open(pdf_path)
    page = doc[0]  # first page
    text = page.get_text("text").strip()

    if not text:
        # No text found, use OCR
        pix = page.get_pixmap()
        img_data = pix.tobytes("png")
        image = Image.open(io.BytesIO(img_data))
        text = pytesseract.image_to_string(image)

    doc.close()

    # Create markdown file
    md_filename = f"{pdf_path.stem}_{uuid.uuid4().hex}.md"
    md_path = output_dir / md_filename

    with open(md_path, "w", encoding="utf-8") as f:
        f.write(text)

    return md_path

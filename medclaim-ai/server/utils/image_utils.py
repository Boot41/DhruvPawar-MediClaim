from PIL import Image
from pathlib import Path

def open_image(image_path: Path) -> Image.Image:
    return Image.open(image_path)

def preprocess_image(image: Image.Image) -> Image.Image:
    """Convert to RGB, resize or normalize if needed"""
    if image.mode != "RGB":
        image = image.convert("RGB")
    return image

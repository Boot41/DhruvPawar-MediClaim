from pathlib import Path

def read_text_file(file_path: Path) -> str:
    """Read plain text from a file"""
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()

def clean_text(text: str) -> str:
    """Basic cleanup: remove extra spaces, newlines"""
    return " ".join(text.split())

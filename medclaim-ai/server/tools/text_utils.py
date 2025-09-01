def read_and_clean_text(file_path: str) -> str:
    """
    Reads a text file and returns cleaned text (whitespace normalized).
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read()
        return " ".join(text.split())  # normalize whitespace
    except Exception:
        return ""

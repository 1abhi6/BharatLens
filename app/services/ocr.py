# app/services/ocr.py
from PIL import Image
import pytesseract

def extract_text_from_image(file_path: str) -> str:
    try:
        text = pytesseract.image_to_string(Image.open(file_path))
        return text.strip()
    except Exception as e:
        return f"[OCR Error: {str(e)}]"

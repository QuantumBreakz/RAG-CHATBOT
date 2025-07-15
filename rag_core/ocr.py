import os
from typing import List
from pdf2image import convert_from_path
import pytesseract
from PyPDF2 import PdfReader


def is_scanned_pdf(pdf_path: str, max_pages: int = 3) -> bool:
    """
    Heuristically determine if a PDF is scanned (image-based) by checking if the first few pages contain extractable text.
    Returns True if no text is found in the first `max_pages` pages.
    """
    reader = PdfReader(pdf_path)
    for i, page in enumerate(reader.pages[:max_pages]):
        text = page.extract_text()
        if text and text.strip():
            return False  # Found text, likely not scanned
    return True  # No text found, likely scanned


def ocr_pdf(pdf_path: str, dpi: int = 300, lang: str = 'eng') -> str:
    """
    Extract text from a scanned PDF using OCR (offline, via Tesseract).
    Returns the concatenated text from all pages.
    """
    # Convert PDF pages to images
    images = convert_from_path(pdf_path, dpi=dpi)
    text_pages: List[str] = []
    for img in images:
        text = pytesseract.image_to_string(img, lang=lang)
        text_pages.append(text)
    return '\n'.join(text_pages)


def extract_text_from_pdf(pdf_path: str, dpi: int = 300, lang: str = 'eng') -> str:
    """
    Extract text from a PDF, using OCR if it is scanned, or text extraction otherwise.
    """
    if is_scanned_pdf(pdf_path):
        return ocr_pdf(pdf_path, dpi=dpi, lang=lang)
    else:
        # Use PyPDF2 for text-based PDFs
        reader = PdfReader(pdf_path)
        return '\n'.join([page.extract_text() or '' for page in reader.pages])


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python ocr.py <pdf_path>")
        sys.exit(1)
    pdf_path = sys.argv[1]
    text = extract_text_from_pdf(pdf_path)
    print(text) 
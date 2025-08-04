import os
from typing import List
from pdf2image import convert_from_path
import pytesseract
from PyPDF2 import PdfReader

# Import the new multi-OCR system
from .multi_ocr import (
    MultiOCREngine, 
    extract_text_from_pdf_enhanced,
    is_scanned_pdf as is_scanned_pdf_enhanced,
    OCRConfidence
)

def is_scanned_pdf(pdf_path: str, max_pages: int = 3) -> bool:
    """
    Heuristically determine if a PDF is scanned (image-based) by checking if the first few pages contain extractable text.
    Returns True if no text is found in the first `max_pages` pages.
    """
    # Use enhanced detection from multi-OCR system
    return is_scanned_pdf_enhanced(pdf_path, max_pages)


def ocr_pdf(pdf_path: str, dpi: int = 300, lang: str = 'eng') -> str:
    """
    Extract text from a scanned PDF using OCR (offline, via Tesseract).
    Returns the concatenated text from all pages.
    """
    # Use enhanced multi-OCR system
    multi_ocr = MultiOCREngine()
    results = multi_ocr.process_pdf(pdf_path)
    return '\n\n'.join([r.text for r in results if r.text])


def extract_text_from_pdf(pdf_path: str, dpi: int = 300, lang: str = 'eng') -> str:
    """
    Extract text from a PDF, using OCR if it is scanned, or text extraction otherwise.
    Enhanced with multi-OCR support for better accuracy.
    """
    # Use enhanced extraction with multi-OCR support
    return extract_text_from_pdf_enhanced(pdf_path, use_multi_ocr=True)


def extract_text_from_pdf_legacy(pdf_path: str, dpi: int = 300, lang: str = 'eng') -> str:
    """
    Legacy PDF text extraction (original implementation).
    Use extract_text_from_pdf() for enhanced multi-OCR support.
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
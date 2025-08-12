"""
Content Detection Module for Backend
Detects images, mathematical expressions, and blueprints in uploaded files
"""

import re
import logging
from typing import Dict, Any, List, Tuple
from pathlib import Path
import mimetypes
from PIL import Image
import fitz  # PyMuPDF

logger = logging.getLogger(__name__)

class ContentDetector:
    """Detects content types in uploaded files"""
    
    @staticmethod
    def detect_content_type(file_bytes: bytes, filename: str) -> Dict[str, Any]:
        """
        Detect content type from file bytes and filename
        
        Returns:
            Dict with keys: type, confidence, details, model_recommendation
        """
        try:
            # Get MIME type
            mime_type, _ = mimetypes.guess_type(filename)
            
            # Image detection
            if mime_type and mime_type.startswith('image/'):
                return {
                    "type": "image",
                    "confidence": 0.95,
                    "details": f"Detected image file: {filename} ({mime_type})",
                    "model_recommendation": "openai"
                }
            
            # PDF detection
            if filename.lower().endswith('.pdf') or (mime_type and 'pdf' in mime_type):
                return ContentDetector._analyze_pdf_content(file_bytes, filename)
            
            # Text file detection
            if filename.lower().endswith(('.txt', '.md', '.csv', '.json', '.xml', '.html', '.htm')):
                return ContentDetector._analyze_text_content(file_bytes, filename)
            
            # Default: no special content detected
            return {
                "type": None,
                "confidence": 0.0,
                "details": "No special content detected",
                "model_recommendation": "local"
            }
            
        except Exception as e:
            logger.error(f"Error detecting content type for {filename}: {e}")
            return {
                "type": None,
                "confidence": 0.0,
                "details": f"Error during detection: {str(e)}",
                "model_recommendation": "local"
            }
    
    @staticmethod
    def _analyze_pdf_content(file_bytes: bytes, filename: str) -> Dict[str, Any]:
        """Analyze PDF content for images, mathematical expressions, and blueprints"""
        try:
            # Open PDF with PyMuPDF
            doc = fitz.open(stream=file_bytes, filetype="pdf")
            
            total_pages = len(doc)
            image_count = 0
            text_content = ""
            has_mathematical = False
            has_blueprint_keywords = False
            
            # Analyze each page
            for page_num in range(min(total_pages, 5)):  # Limit to first 5 pages for performance
                page = doc[page_num]
                
                # Check for images
                image_list = page.get_images()
                if image_list:
                    image_count += len(image_list)
                
                # Extract text
                text = page.get_text()
                text_content += text + "\n"
                
                # Check for mathematical expressions
                if ContentDetector._has_mathematical_content(text):
                    has_mathematical = True
                
                # Check for blueprint keywords
                if ContentDetector._has_blueprint_keywords(text):
                    has_blueprint_keywords = True
            
            doc.close()
            
            # Determine content type based on analysis
            if image_count > 0:
                return {
                    "type": "image",
                    "confidence": min(0.9, 0.7 + (image_count * 0.1)),
                    "details": f"PDF contains {image_count} images across {total_pages} pages",
                    "model_recommendation": "openai"
                }
            
            if has_blueprint_keywords:
                return {
                    "type": "blueprint",
                    "confidence": 0.8,
                    "details": "PDF contains blueprint/technical drawing keywords",
                    "model_recommendation": "openai"
                }
            
            if has_mathematical:
                return {
                    "type": "mathematical",
                    "confidence": 0.75,
                    "details": "PDF contains mathematical expressions",
                    "model_recommendation": "openai"
                }
            
            return {
                "type": None,
                "confidence": 0.0,
                "details": "PDF contains only text content",
                "model_recommendation": "local"
            }
            
        except Exception as e:
            logger.error(f"Error analyzing PDF content: {e}")
            return {
                "type": None,
                "confidence": 0.0,
                "details": f"Error analyzing PDF: {str(e)}",
                "model_recommendation": "local"
            }
    
    @staticmethod
    def _analyze_text_content(file_bytes: bytes, filename: str) -> Dict[str, Any]:
        """Analyze text content for mathematical expressions and blueprint keywords"""
        try:
            text = file_bytes.decode('utf-8', errors='ignore')
            text_lower = text.lower()
            
            # Check for mathematical expressions
            has_mathematical = ContentDetector._has_mathematical_content(text)
            
            # Check for blueprint keywords
            has_blueprint_keywords = ContentDetector._has_blueprint_keywords(text)
            
            # Determine content type
            if has_blueprint_keywords:
                return {
                    "type": "blueprint",
                    "confidence": 0.8,
                    "details": "Text contains blueprint/technical drawing keywords",
                    "model_recommendation": "openai"
                }
            
            if has_mathematical:
                return {
                    "type": "mathematical",
                    "confidence": 0.75,
                    "details": "Text contains mathematical expressions",
                    "model_recommendation": "openai"
                }
            
            return {
                "type": None,
                "confidence": 0.0,
                "details": "Text contains no special content",
                "model_recommendation": "local"
            }
            
        except Exception as e:
            logger.error(f"Error analyzing text content: {e}")
            return {
                "type": None,
                "confidence": 0.0,
                "details": f"Error analyzing text: {str(e)}",
                "model_recommendation": "local"
            }
    
    @staticmethod
    def _has_mathematical_content(text: str) -> bool:
        """Check if text contains mathematical expressions"""
        math_patterns = [
            r'\d+\s*[+\-*/]\s*\d+',  # Basic arithmetic
            r'\d+\s*[=]\s*\d+',  # Equations
            r'[a-zA-Z]\s*[=]\s*\d+',  # Variable assignments
            r'\d+\s*[%]',  # Percentages
            r'sqrt|log|sin|cos|tan|exp',  # Mathematical functions
            r'\d+\s*x\s*\d+',  # 25X54 pattern
            r'[a-zA-Z]\s*[+\-*/]\s*[a-zA-Z]',  # Variable arithmetic
            r'\d+\.\d+\s*[+\-*/]\s*\d+\.\d+',  # Decimal arithmetic
            r'[∫∑∏√∞±≤≥≠≈]',  # Mathematical symbols
            r'[αβγδεθλμπσφω]',  # Greek letters
        ]
        
        for pattern in math_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        
        return False
    
    @staticmethod
    def _has_blueprint_keywords(text: str) -> bool:
        """Check if text contains blueprint/technical drawing keywords"""
        blueprint_keywords = [
            'blueprint', 'drawing', 'schematic', 'diagram', 'plan', 'layout', 'technical',
            'engineering', 'architectural', 'floorplan', 'circuit', 'wiring', 'mechanical',
            'dimension', 'scale', 'measurement', 'specification', 'technical drawing',
            'assembly', 'component', 'part', 'section', 'detail', 'elevation', 'section',
            'isometric', 'orthographic', 'projection', 'tolerance', 'datum', 'reference'
        ]
        
        text_lower = text.lower()
        for keyword in blueprint_keywords:
            if keyword in text_lower:
                return True
        
        return False
    
    @staticmethod
    def should_use_openai(detection_result: Dict[str, Any]) -> bool:
        """Determine if OpenAI should be used based on detection result"""
        return (
            detection_result.get("type") is not None and 
            detection_result.get("confidence", 0) > 0.6 and
            detection_result.get("model_recommendation") == "openai"
        )

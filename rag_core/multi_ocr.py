"""
Multi-OCR Pipeline with Text Validation System

A robust document processing system using multiple OCR engines to minimize 
hallucinations and improve text extraction accuracy through consensus-based validation.
"""

import os
import tempfile
import logging
from typing import List, Dict, Any, Optional, Tuple, Set
from dataclasses import dataclass
from enum import Enum
import re
import hashlib
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
from pathlib import Path
import threading
from functools import lru_cache

# OCR Engine imports
import pytesseract
from pdf2image import convert_from_path
from PyPDF2 import PdfReader
import cv2
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter

# Text processing imports
from difflib import SequenceMatcher
from Levenshtein import distance as levenshtein_distance
import nltk
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.corpus import stopwords

# Configure logging
logger = logging.getLogger(__name__)

# Global cache for OCR engines
_ocr_engines_cache = {}
_engine_lock = threading.Lock()

class OCRConfidence(Enum):
    """OCR confidence levels based on consensus"""
    HIGH = "high"      # 2+ engines agree with >90% similarity
    MEDIUM = "medium"  # 2+ engines agree with 70-90% similarity
    LOW = "low"        # Single engine or <70% similarity
    REJECTED = "rejected"  # Contradictory or nonsensical text

@dataclass
class OCRResult:
    """Result from a single OCR engine"""
    engine_name: str
    text: str
    confidence: float
    processing_time: float
    metadata: Dict[str, Any]

@dataclass
class ConsensusResult:
    """Final consensus result from multiple OCR engines"""
    text: str
    confidence: OCRConfidence
    contributing_engines: List[str]
    agreement_score: float
    processing_time: float
    quality_flags: List[str]
    metadata: Dict[str, Any]

class MultiOCREngine:
    """Multi-OCR pipeline with consensus-based validation and performance optimizations"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or self._get_default_config()
        self.engines = self._initialize_engines()
        self._download_nltk_data()
        self._setup_offline_models()
        
        # Performance optimizations
        self._cache = {}
        self._cache_lock = threading.Lock()
        self._max_workers = min(4, len(self.engines))  # Limit concurrent engines
        
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration for multi-OCR pipeline with performance optimizations"""
        return {
            "engines": {
                "tesseract": {
                    "enabled": True,
                    "priority": 1,
                    "languages": ["eng"],
                    "config": "--oem 1 --psm 6"  # Faster engine mode
                },
                "paddleocr": {
                    "enabled": False,  # Temporarily disable PaddleOCR due to configuration issues
                    "priority": 2,
                    "languages": ["en"]
                },
                "easyocr": {
                    "enabled": True,  # Enable EasyOCR for better consensus
                    "priority": 3,
                    "languages": ["en"]
                }
            },
            "consensus": {
                "high_confidence_threshold": 0.85,  # Lowered for speed
                "medium_confidence_threshold": 0.65,  # Lowered for speed
                "min_agreement_engines": 2,
                "fuzzy_match_threshold": 0.80
            },
            "preprocessing": {
                "deskew": False,  # Disabled for speed
                "denoise": True,
                "enhance_contrast": False,  # Disabled for speed
                "dpi": 200  # Lower DPI for speed
            },
            "validation": {
                "check_semantic_coherence": False,  # Disabled for speed
                "check_language_consistency": True,
                "check_format_preservation": False,  # Disabled for speed
                "min_text_length": 5  # Lower minimum length
            },
            "performance": {
                "enable_caching": True,
                "cache_size": 1000,
                "parallel_processing": False,  # Disable parallel processing to avoid connection issues
                "max_workers": 1,
                "timeout_seconds": 15,  # Reduce timeout
                "enable_offline_mode": True
            }
        }
    
    def _initialize_engines(self) -> Dict[str, Any]:
        """Initialize available OCR engines"""
        engines = {}
        
        # Tesseract (Primary)
        if self.config["engines"]["tesseract"]["enabled"]:
            try:
                # Test Tesseract availability
                pytesseract.get_tesseract_version()
                engines["tesseract"] = {
                    "name": "Tesseract",
                    "priority": self.config["engines"]["tesseract"]["priority"],
                    "languages": self.config["engines"]["tesseract"]["languages"],
                    "config": self.config["engines"]["tesseract"]["config"]
                }
                logger.info("Tesseract OCR engine initialized successfully")
            except Exception as e:
                logger.warning(f"Tesseract not available: {e}")
        
        # PaddleOCR (Secondary) - Fixed configuration
        if self.config["engines"]["paddleocr"]["enabled"]:
            try:
                # Import PaddleOCR
                from paddleocr import PaddleOCR
                
                # Initialize PaddleOCR with minimal configuration
                paddle_config = {
                    "use_textline_orientation": True,  # Fixed deprecated parameter
                    "lang": "en"
                }
                
                # Create PaddleOCR instance
                paddle_ocr = PaddleOCR(**paddle_config)
                
                engines["paddleocr"] = {
                    "name": "PaddleOCR",
                    "priority": self.config["engines"]["paddleocr"]["priority"],
                    "languages": self.config["engines"]["paddleocr"]["languages"],
                    "instance": paddle_ocr,
                    "config": paddle_config
                }
                logger.info("PaddleOCR engine initialized successfully")
            except ImportError:
                logger.warning("PaddleOCR not available - install with: pip install paddleocr")
            except Exception as e:
                logger.warning(f"PaddleOCR initialization failed: {e}")
        
        # EasyOCR (Tertiary) - Optimized configuration
        if self.config["engines"]["easyocr"]["enabled"]:
            try:
                # Import EasyOCR
                import easyocr
                
                # Initialize EasyOCR with optimized configuration
                easy_config = {
                    "lang_list": ['en'],
                    "gpu": False,  # Set to True if GPU available
                    "model_storage_directory": None,
                    "user_network_directory": None,
                    "recog_network": 'standard',
                    "detect_network": 'craft',
                    "quantize": True,  # Enable quantization for speed
                    "download_enabled": True,  # Allow model downloads
                    "verbose": False,  # Reduce logging
                }
                
                # Create EasyOCR instance
                easy_ocr = easyocr.Reader(**easy_config)
                
                engines["easyocr"] = {
                    "name": "EasyOCR",
                    "priority": self.config["engines"]["easyocr"]["priority"],
                    "languages": self.config["engines"]["easyocr"]["languages"],
                    "instance": easy_ocr,
                    "config": easy_config
                }
                logger.info("EasyOCR engine initialized successfully")
            except ImportError:
                logger.warning("EasyOCR not available - install with: pip install easyocr")
            except Exception as e:
                logger.warning(f"EasyOCR initialization failed: {e}")
        
        if not engines:
            raise ValueError("No OCR engines available. Please install at least one OCR engine.")
        
        return engines
    
    def _download_nltk_data(self):
        """Download required NLTK data for text processing"""
        try:
            nltk.data.find('tokenizers/punkt')
        except LookupError:
            nltk.download('punkt')
        
        try:
            nltk.data.find('corpora/stopwords')
        except LookupError:
            nltk.download('stopwords')
    
    def _setup_offline_models(self):
        """Setup offline models for OCR engines"""
        try:
            # Create offline model directory
            offline_dir = Path.home() / ".ocr_models"
            offline_dir.mkdir(exist_ok=True)
            
            # Set environment variables for offline mode
            os.environ["PADDLE_HOME"] = str(offline_dir / "paddle")
            os.environ["EASYOCR_HOME"] = str(offline_dir / "easyocr")
            
            logger.info(f"Offline models directory: {offline_dir}")
            
        except Exception as e:
            logger.warning(f"Failed to setup offline models: {e}")
    
    def preprocess_image(self, image: Image.Image) -> Image.Image:
        """Preprocess image for better OCR results"""
        # Convert to RGB if needed
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Convert to numpy array for OpenCV operations
        img_array = np.array(image)
        
        # Deskew if enabled
        if self.config["preprocessing"]["deskew"]:
            img_array = self._deskew_image(img_array)
        
        # Denoise if enabled
        if self.config["preprocessing"]["denoise"]:
            img_array = self._denoise_image(img_array)
        
        # Enhance contrast if enabled
        if self.config["preprocessing"]["enhance_contrast"]:
            img_array = self._enhance_contrast(img_array)
        
        # Convert back to PIL Image
        return Image.fromarray(img_array)
    
    def _deskew_image(self, img_array: np.ndarray) -> np.ndarray:
        """Deskew image to correct rotation"""
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
            
            # Find the angle of rotation
            coords = np.column_stack(np.where(gray > 0))
            angle = cv2.minAreaRect(coords)[-1]
            
            if angle < -45:
                angle = 90 + angle
            
            # Rotate the image
            (h, w) = img_array.shape[:2]
            center = (w // 2, h // 2)
            M = cv2.getRotationMatrix2D(center, angle, 1.0)
            rotated = cv2.warpAffine(img_array, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
            
            return rotated
        except Exception as e:
            logger.warning(f"Deskew failed: {e}")
            return img_array
    
    def _denoise_image(self, img_array: np.ndarray) -> np.ndarray:
        """Remove noise from image"""
        try:
            # Apply bilateral filter for noise reduction
            denoised = cv2.bilateralFilter(img_array, 9, 75, 75)
            return denoised
        except Exception as e:
            logger.warning(f"Denoising failed: {e}")
            return img_array
    
    def _enhance_contrast(self, img_array: np.ndarray) -> np.ndarray:
        """Enhance image contrast"""
        try:
            # Convert to LAB color space
            lab = cv2.cvtColor(img_array, cv2.COLOR_RGB2LAB)
            l, a, b = cv2.split(lab)
            
            # Apply CLAHE to L channel
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
            l = clahe.apply(l)
            
            # Merge channels and convert back
            enhanced = cv2.merge([l, a, b])
            enhanced = cv2.cvtColor(enhanced, cv2.COLOR_LAB2RGB)
            
            return enhanced
        except Exception as e:
            logger.warning(f"Contrast enhancement failed: {e}")
            return img_array
    
    def _extract_text_tesseract(self, image: Image.Image, lang: str = 'eng') -> OCRResult:
        """Extract text using Tesseract OCR"""
        start_time = time.time()
        
        try:
            # Configure Tesseract
            config = self.engines["tesseract"]["config"]
            
            # Extract text with confidence scores
            data = pytesseract.image_to_data(image, lang=lang, config=config, output_type=pytesseract.Output.DICT)
            
            # Combine text and calculate average confidence
            text_parts = []
            confidences = []
            
            for i, conf in enumerate(data['conf']):
                if conf > 0:  # Filter out low confidence results
                    text_parts.append(data['text'][i])
                    confidences.append(conf)
            
            text = ' '.join(text_parts)
            avg_confidence = np.mean(confidences) if confidences else 0.0
            
            processing_time = time.time() - start_time
            
            return OCRResult(
                engine_name="Tesseract",
                text=text,
                confidence=avg_confidence / 100.0,  # Normalize to 0-1
                processing_time=processing_time,
                metadata={
                    "language": lang,
                    "config": config,
                    "word_count": len(text.split()),
                    "avg_word_confidence": avg_confidence
                }
            )
            
        except Exception as e:
            logger.error(f"Tesseract OCR failed: {e}")
            return OCRResult(
                engine_name="Tesseract",
                text="",
                confidence=0.0,
                processing_time=time.time() - start_time,
                metadata={"error": str(e)}
            )
    
    def _extract_text_paddleocr(self, image: Image.Image, lang: str = 'en') -> OCRResult:
        """Extract text using PaddleOCR"""
        start_time = time.time()
        
        try:
            # Get cached PaddleOCR instance
            paddle_ocr = self._get_cached_engine("paddleocr")
            if paddle_ocr is None:
                raise Exception("PaddleOCR not available")
            
            # Convert PIL image to numpy array
            img_array = np.array(image)
            
            # Perform OCR
            results = paddle_ocr.ocr(img_array, cls=True)
            
            # Extract text and confidence scores
            text_parts = []
            confidences = []
            
            if results and results[0]:
                for line in results[0]:
                    if line and len(line) >= 2:
                        text = line[1][0]  # Text content
                        confidence = line[1][1]  # Confidence score
                        
                        if text.strip() and confidence > 0:
                            text_parts.append(text)
                            confidences.append(confidence)
            
            text = ' '.join(text_parts)
            avg_confidence = np.mean(confidences) if confidences else 0.0
            
            processing_time = time.time() - start_time
            
            return OCRResult(
                engine_name="PaddleOCR",
                text=text,
                confidence=avg_confidence,
                processing_time=processing_time,
                metadata={
                    "language": lang,
                    "word_count": len(text.split()),
                    "avg_word_confidence": avg_confidence,
                    "num_text_boxes": len(text_parts)
                }
            )
            
        except Exception as e:
            logger.error(f"PaddleOCR failed: {e}")
            return OCRResult(
                engine_name="PaddleOCR",
                text="",
                confidence=0.0,
                processing_time=time.time() - start_time,
                metadata={"error": str(e)}
            )
    
    def _extract_text_easyocr(self, image: Image.Image, lang: str = 'en') -> OCRResult:
        """Extract text using EasyOCR"""
        start_time = time.time()
        
        try:
            # Get cached EasyOCR instance
            easy_ocr = self._get_cached_engine("easyocr")
            if easy_ocr is None:
                raise Exception("EasyOCR not available")
            
            # Convert PIL image to numpy array
            img_array = np.array(image)
            
            # Perform OCR
            results = easy_ocr.readtext(img_array)
            
            # Extract text and confidence scores
            text_parts = []
            confidences = []
            
            for (bbox, text, confidence) in results:
                if text.strip() and confidence > 0:
                    text_parts.append(text)
                    confidences.append(confidence)
            
            text = ' '.join(text_parts)
            avg_confidence = np.mean(confidences) if confidences else 0.0
            
            processing_time = time.time() - start_time
            
            return OCRResult(
                engine_name="EasyOCR",
                text=text,
                confidence=avg_confidence,
                processing_time=processing_time,
                metadata={
                    "language": lang,
                    "word_count": len(text.split()),
                    "avg_word_confidence": avg_confidence,
                    "num_text_boxes": len(text_parts)
                }
            )
            
        except Exception as e:
            logger.error(f"EasyOCR failed: {e}")
            return OCRResult(
                engine_name="EasyOCR",
                text="",
                confidence=0.0,
                processing_time=time.time() - start_time,
                metadata={"error": str(e)}
            )
    
    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two text strings"""
        if not text1 or not text2:
            return 0.0
        
        # Tokenize texts
        tokens1 = set(word_tokenize(text1.lower()))
        tokens2 = set(word_tokenize(text2.lower()))
        
        # Calculate Jaccard similarity
        intersection = len(tokens1.intersection(tokens2))
        union = len(tokens1.union(tokens2))
        
        if union == 0:
            return 0.0
        
        jaccard_similarity = intersection / union
        
        # Calculate Levenshtein similarity
        max_len = max(len(text1), len(text2))
        if max_len == 0:
            levenshtein_similarity = 1.0
        else:
            levenshtein_similarity = 1 - (levenshtein_distance(text1, text2) / max_len)
        
        # Calculate sequence similarity
        sequence_similarity = SequenceMatcher(None, text1, text2).ratio()
        
        # Weighted average of all similarity measures
        weighted_similarity = (jaccard_similarity * 0.4 + 
                             levenshtein_similarity * 0.3 + 
                             sequence_similarity * 0.3)
        
        return weighted_similarity
    
    def _build_consensus(self, results: List[OCRResult]) -> ConsensusResult:
        """Build consensus from multiple OCR results"""
        if not results:
            return ConsensusResult(
                text="",
                confidence=OCRConfidence.REJECTED,
                contributing_engines=[],
                agreement_score=0.0,
                processing_time=0.0,
                quality_flags=["No OCR results"],
                metadata={}
            )
        
        # Filter out empty results
        valid_results = [r for r in results if r.text.strip()]
        if not valid_results:
            return ConsensusResult(
                text="",
                confidence=OCRConfidence.REJECTED,
                contributing_engines=[],
                agreement_score=0.0,
                processing_time=0.0,
                quality_flags=["No valid OCR results"],
                metadata={}
            )
        
        # Calculate pairwise similarities
        similarities = []
        for i, result1 in enumerate(valid_results):
            for j, result2 in enumerate(valid_results[i+1:], i+1):
                similarity = self._calculate_text_similarity(result1.text, result2.text)
                similarities.append(similarity)
        
        avg_similarity = np.mean(similarities) if similarities else 0.0
        
        # Determine confidence level
        if avg_similarity >= self.config["consensus"]["high_confidence_threshold"]:
            confidence = OCRConfidence.HIGH
        elif avg_similarity >= self.config["consensus"]["medium_confidence_threshold"]:
            confidence = OCRConfidence.MEDIUM
        else:
            confidence = OCRConfidence.LOW
        
        # Select best text (highest confidence or most common)
        if len(valid_results) == 1:
            best_result = valid_results[0]
        else:
            # Find the result with highest average similarity to others
            best_result = max(valid_results, key=lambda r: np.mean([
                self._calculate_text_similarity(r.text, other.text)
                for other in valid_results if other != r
            ]))
        
        # Quality validation
        quality_flags = self._validate_text_quality(best_result.text)
        
        # Calculate processing time
        total_time = sum(r.processing_time for r in results)
        
        return ConsensusResult(
            text=best_result.text,
            confidence=confidence,
            contributing_engines=[r.engine_name for r in valid_results],
            agreement_score=avg_similarity,
            processing_time=total_time,
            quality_flags=quality_flags,
            metadata={
                "avg_similarity": avg_similarity,
                "num_engines": len(valid_results),
                "best_engine": best_result.engine_name,
                "best_confidence": best_result.confidence
            }
        )
    
    def _validate_text_quality(self, text: str) -> List[str]:
        """Validate text quality and return quality flags"""
        flags = []
        
        # Check minimum length
        if len(text.strip()) < self.config["validation"]["min_text_length"]:
            flags.append("text_too_short")
        
        # Check for semantic coherence
        if self.config["validation"]["check_semantic_coherence"]:
            sentences = sent_tokenize(text)
            if len(sentences) > 1:
                # Check if sentences are coherent
                words = word_tokenize(text.lower())
                stop_words = set(stopwords.words('english'))
                content_words = [w for w in words if w not in stop_words and len(w) > 2]
                
                if len(content_words) < len(sentences) * 2:
                    flags.append("low_semantic_coherence")
        
        # Check for language consistency
        if self.config["validation"]["check_language_consistency"]:
            # Simple heuristic: check for mixed character sets
            ascii_chars = sum(1 for c in text if ord(c) < 128)
            total_chars = len(text)
            if total_chars > 0 and ascii_chars / total_chars < 0.8:
                flags.append("mixed_language_content")
        
        # Check for format preservation
        if self.config["validation"]["check_format_preservation"]:
            # Check for excessive whitespace or formatting issues
            if text.count('\n\n\n') > text.count('\n') * 0.3:
                flags.append("formatting_issues")
        
        return flags
    
    def process_image(self, image: Image.Image, languages: List[str] = None) -> ConsensusResult:
        """Process image with multiple OCR engines and return consensus result"""
        start_time = time.time()
        
        # Check cache first
        if self.config["performance"]["enable_caching"]:
            image_hash = self._get_image_hash(image)
            with self._cache_lock:
                if image_hash in self._cache:
                    logger.info("Using cached OCR result")
                    return self._cache[image_hash]
        
        # Preprocess image (optimized for speed)
        processed_image = self.preprocess_image(image)
        
        # Use default languages if none specified
        if languages is None:
            languages = ['eng']
        
        # Process with all available engines sequentially (safer)
        results = []
        for engine_name, engine_config in self.engines.items():
            try:
                if engine_name == "tesseract":
                    for lang in languages:
                        if lang in engine_config["languages"]:
                            result = self._extract_text_tesseract(processed_image, lang)
                            if result and result.text.strip():
                                results.append(result)
                elif engine_name == "paddleocr":
                    for lang in languages:
                        if lang in engine_config["languages"]:
                            result = self._extract_text_paddleocr(processed_image, lang)
                            if result and result.text.strip():
                                results.append(result)
                elif engine_name == "easyocr":
                    for lang in languages:
                        if lang in engine_config["languages"]:
                            result = self._extract_text_easyocr(processed_image, lang)
                            if result and result.text.strip():
                                results.append(result)
            except Exception as e:
                logger.warning(f"Error processing with {engine_name}: {e}")
                continue
        
        # Build consensus
        consensus = self._build_consensus(results)
        consensus.processing_time = time.time() - start_time
        
        # Cache result
        if self.config["performance"]["enable_caching"]:
            with self._cache_lock:
                if len(self._cache) < self.config["performance"]["cache_size"]:
                    self._cache[image_hash] = consensus
        
        return consensus
    
    def process_pdf(self, pdf_path: str, max_pages: int = None) -> List[ConsensusResult]:
        """Process PDF file with multi-OCR pipeline"""
        results = []
        
        try:
            # Convert PDF to images with error handling
            try:
                images = convert_from_path(
                    pdf_path, 
                    dpi=self.config["preprocessing"]["dpi"],
                    first_page=1,
                    last_page=max_pages
                )
                logger.info(f"Successfully converted PDF to {len(images)} images")
            except Exception as e:
                logger.error(f"Failed to convert PDF to images: {e}")
                # Fallback: create a single document with error message
                error_result = ConsensusResult(
                    text=f"Error processing PDF: {str(e)}",
                    confidence=OCRConfidence.REJECTED,
                    contributing_engines=[],
                    agreement_score=0.0,
                    processing_time=0.0,
                    quality_flags=["conversion_failed"],
                    metadata={"error": str(e)}
                )
                return [error_result]
            
            # Process each page
            for page_num, image in enumerate(images, 1):
                try:
                    logger.info(f"Processing page {page_num}")
                    result = self.process_image(image)
                    result.metadata["page_number"] = page_num
                    results.append(result)
                    
                    # Log confidence levels
                    logger.info(f"Page {page_num} - Confidence: {result.confidence.value}, "
                              f"Agreement: {result.agreement_score:.2f}")
                except Exception as e:
                    logger.warning(f"Error processing page {page_num}: {e}")
                    # Continue with next page instead of failing completely
                    continue
        
        except Exception as e:
            logger.error(f"Error processing PDF {pdf_path}: {e}")
            # Return error result instead of raising
            error_result = ConsensusResult(
                text=f"Error processing PDF: {str(e)}",
                confidence=OCRConfidence.REJECTED,
                contributing_engines=[],
                agreement_score=0.0,
                processing_time=0.0,
                quality_flags=["processing_failed"],
                metadata={"error": str(e)}
            )
            return [error_result]
        
        return results
    
    def is_scanned_pdf(self, pdf_path: str, max_pages: int = 3) -> bool:
        """Enhanced scanned PDF detection"""
        try:
            reader = PdfReader(pdf_path)
            text_content = ""
            
            for i, page in enumerate(reader.pages[:max_pages]):
                text = page.extract_text()
                if text:
                    text_content += text
            
            # If very little text is found, likely scanned
            if len(text_content.strip()) < 100:
                return True
            
            # Check for common scanned PDF indicators
            scanned_indicators = [
                "image", "scan", "scanned", "ocr", "optical character recognition"
            ]
            
            text_lower = text_content.lower()
            if any(indicator in text_lower for indicator in scanned_indicators):
                return True
            
            return False
            
        except Exception as e:
            logger.warning(f"Error detecting scanned PDF: {e}")
            return True  # Assume scanned if detection fails

def extract_text_from_pdf_enhanced(pdf_path: str, use_multi_ocr: bool = True) -> str:
    """
    Enhanced PDF text extraction with multi-OCR support for scanned documents.
    
    Args:
        pdf_path: Path to PDF file
        use_multi_ocr: Whether to use multi-OCR pipeline for scanned PDFs
    
    Returns:
        Extracted text from PDF
    """
    multi_ocr = MultiOCREngine()
    
    # Check if PDF is scanned
    if multi_ocr.is_scanned_pdf(pdf_path):
        logger.info(f"PDF {pdf_path} detected as scanned. Using multi-OCR pipeline.")
        
        if use_multi_ocr:
            # Use multi-OCR pipeline
            results = multi_ocr.process_pdf(pdf_path)
            
            # Combine results with confidence weighting
            combined_text = []
            total_confidence = 0.0
            
            for result in results:
                if result.confidence != OCRConfidence.REJECTED:
                    # Weight text by confidence
                    weight = {
                        OCRConfidence.HIGH: 1.0,
                        OCRConfidence.MEDIUM: 0.7,
                        OCRConfidence.LOW: 0.3
                    }.get(result.confidence, 0.0)
                    
                    if weight > 0:
                        combined_text.append(result.text)
                        total_confidence += weight
            
            if combined_text:
                final_text = '\n\n'.join(combined_text)
                
                # Log quality metrics
                avg_confidence = total_confidence / len(combined_text) if combined_text else 0.0
                logger.info(f"Multi-OCR completed. Average confidence: {avg_confidence:.2f}")
                
                return final_text
            else:
                logger.warning("No valid OCR results obtained")
                return ""
        else:
            # Fallback to single OCR
            return extract_text_from_pdf(pdf_path)
    else:
        # Use native PDF text extraction
        reader = PdfReader(pdf_path)
        return '\n'.join([page.extract_text() or '' for page in reader.pages])

# Backward compatibility functions
def is_scanned_pdf(pdf_path: str, max_pages: int = 3) -> bool:
    """Check if PDF is scanned (image-based)"""
    multi_ocr = MultiOCREngine()
    return multi_ocr.is_scanned_pdf(pdf_path, max_pages)

def ocr_pdf(pdf_path: str, dpi: int = 300, lang: str = 'eng') -> str:
    """Extract text from scanned PDF using single OCR (legacy function)"""
    multi_ocr = MultiOCREngine()
    results = multi_ocr.process_pdf(pdf_path)
    return '\n\n'.join([r.text for r in results if r.text])

def extract_text_from_pdf(pdf_path: str, dpi: int = 300, lang: str = 'eng') -> str:
    """Extract text from PDF with OCR fallback (legacy function)"""
    return extract_text_from_pdf_enhanced(pdf_path, use_multi_ocr=False)
    
    @lru_cache(maxsize=1000)
    def _get_cached_engine(self, engine_name: str):
        """Get cached OCR engine instance"""
        with _engine_lock:
            if engine_name not in _ocr_engines_cache:
                # Initialize engine (this will be cached)
                if engine_name == "tesseract":
                    _ocr_engines_cache[engine_name] = "tesseract_available"
                elif engine_name == "paddleocr":
                    try:
                        from paddleocr import PaddleOCR
                        _ocr_engines_cache[engine_name] = PaddleOCR(
                            use_textline_orientation=True,
                            lang='en',
                            use_gpu=False,
                            use_mp=True,
                            total_process_num=4,
                            enable_mkldnn=True,
                            cpu_threads=4,
                            det_db_thresh=0.3,
                            det_db_box_thresh=0.5,
                            det_db_unclip_ratio=1.6,
                            rec_batch_num=6,
                            cls_batch_num=6
                        )
                    except Exception as e:
                        logger.warning(f"PaddleOCR not available: {e}")
                        _ocr_engines_cache[engine_name] = None
                elif engine_name == "easyocr":
                    try:
                        import easyocr
                        _ocr_engines_cache[engine_name] = easyocr.Reader(
                            ['en'],
                            gpu=False,
                            quantize=True,
                            download_enabled=True,
                            verbose=False
                        )
                    except Exception as e:
                        logger.warning(f"EasyOCR not available: {e}")
                        _ocr_engines_cache[engine_name] = None
            
            return _ocr_engines_cache[engine_name]
    
    def _process_image_parallel(self, image: Image.Image, languages: List[str] = None) -> List[OCRResult]:
        """Process image with multiple OCR engines in parallel"""
        if languages is None:
            languages = ['eng']
        
        results = []
        
        # Prepare tasks for parallel processing
        tasks = []
        for engine_name, engine_config in self.engines.items():
            if engine_name == "tesseract":
                for lang in languages:
                    if lang in engine_config["languages"]:
                        tasks.append(("tesseract", lang, image))
            elif engine_name == "paddleocr":
                for lang in languages:
                    if lang in engine_config["languages"]:
                        tasks.append(("paddleocr", lang, image))
            elif engine_name == "easyocr":
                for lang in languages:
                    if lang in engine_config["languages"]:
                        tasks.append(("easyocr", lang, image))
        
        # Process tasks in parallel with timeout
        with ThreadPoolExecutor(max_workers=self._max_workers) as executor:
            future_to_task = {
                executor.submit(self._process_single_engine, task[0], task[1], task[2]): task 
                for task in tasks
            }
            
            for future in as_completed(future_to_task, timeout=self.config["performance"]["timeout_seconds"]):
                try:
                    result = future.result()
                    if result:
                        results.append(result)
                except Exception as e:
                    task = future_to_task[future]
                    logger.warning(f"Engine {task[0]} failed: {e}")
        
        return results
    
    def _process_single_engine(self, engine_name: str, lang: str, image: Image.Image) -> Optional[OCRResult]:
        """Process image with a single OCR engine"""
        try:
            if engine_name == "tesseract":
                return self._extract_text_tesseract(image, lang)
            elif engine_name == "paddleocr":
                return self._extract_text_paddleocr(image, lang)
            elif engine_name == "easyocr":
                return self._extract_text_easyocr(image, lang)
        except Exception as e:
            logger.error(f"Error processing with {engine_name}: {e}")
            return None 
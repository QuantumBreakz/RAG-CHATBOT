"""
Document Layout Analysis System

This module provides advanced document layout analysis capabilities to enhance OCR processing
by understanding document structure, detecting tables, forms, and other layout elements.
Similar to RAGFlow's DeepDoc but integrated with our existing multi-OCR pipeline.
"""

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import logging
from typing import List, Dict, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
import json
import time
from pathlib import Path
import re
from collections import defaultdict

logger = logging.getLogger(__name__)

class LayoutElementType(Enum):
    """Types of layout elements that can be detected"""
    TEXT_BLOCK = "text_block"
    TABLE = "table"
    FORM_FIELD = "form_field"
    HEADER = "header"
    FOOTER = "footer"
    IMAGE = "image"
    SIGNATURE = "signature"
    CHECKBOX = "checkbox"
    RADIO_BUTTON = "radio_button"
    LIST = "list"
    PARAGRAPH = "paragraph"
    TITLE = "title"
    SUBTITLE = "subtitle"
    CAPTION = "caption"
    MARGIN = "margin"
    COLUMN = "column"
    ROW = "row"

class TableStructure(Enum):
    """Types of table structures"""
    REGULAR = "regular"
    IRREGULAR = "irregular"
    MERGED_CELLS = "merged_cells"
    NESTED = "nested"
    HEADER_ONLY = "header_only"

@dataclass
class BoundingBox:
    """Bounding box for layout elements"""
    x: int
    y: int
    width: int
    height: int
    
    @property
    def area(self) -> int:
        return self.width * self.height
    
    @property
    def center(self) -> Tuple[int, int]:
        return (self.x + self.width // 2, self.y + self.height // 2)
    
    def intersects(self, other: 'BoundingBox') -> bool:
        """Check if this bounding box intersects with another"""
        return not (self.x + self.width <= other.x or 
                   other.x + other.width <= self.x or
                   self.y + self.height <= other.y or
                   other.y + other.height <= self.y)

@dataclass
class LayoutElement:
    """A detected layout element"""
    element_type: LayoutElementType
    bounding_box: BoundingBox
    confidence: float
    text_content: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    children: List['LayoutElement'] = field(default_factory=list)
    parent: Optional['LayoutElement'] = None

@dataclass
class TableInfo:
    """Information about a detected table"""
    bounding_box: BoundingBox
    rows: int
    columns: int
    structure: TableStructure
    has_header: bool
    cell_contents: List[List[str]]
    confidence: float
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class FormField:
    """Information about a detected form field"""
    field_type: str  # text, checkbox, radio, signature, etc.
    label: str
    bounding_box: BoundingBox
    is_required: bool
    default_value: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class DocumentLayout:
    """Complete layout analysis of a document"""
    page_width: int
    page_height: int
    elements: List[LayoutElement]
    tables: List[TableInfo]
    form_fields: List[FormField]
    text_blocks: List[LayoutElement]
    images: List[LayoutElement]
    processing_time: float
    confidence: float
    metadata: Dict[str, Any] = field(default_factory=dict)

class LayoutAnalyzer:
    """Advanced document layout analysis system"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or self._get_default_config()
        self.logger = logging.getLogger(__name__)
        
        # Initialize OpenCV models for layout detection
        self._initialize_models()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration for layout analysis"""
        return {
            "table_detection": {
                "enabled": True,
                "min_table_area": 1000,
                "min_cells": 4,
                "line_threshold": 0.8
            },
            "form_detection": {
                "enabled": True,
                "min_field_area": 100,
                "text_field_height_ratio": 0.1
            },
            "text_block_detection": {
                "enabled": True,
                "min_block_area": 200,
                "min_text_height": 10
            },
            "image_detection": {
                "enabled": True,
                "min_image_area": 500
            },
            "performance": {
                "max_processing_time": 30.0,
                "parallel_processing": True
            }
        }
    
    def _initialize_models(self):
        """Initialize OpenCV models for layout detection"""
        try:
            # Initialize table detection model
            self.table_detector = cv2.createLineSegmentDetector(0)
            
            # Initialize text detection model (if available)
            try:
                self.text_detector = cv2.dnn.readNet(
                    "models/text_detection.pb",
                    "models/text_detection.pbtxt"
                )
            except:
                self.text_detector = None
                self.logger.warning("Text detection model not available")
            
            self.logger.info("Layout analysis models initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize layout analysis models: {e}")
            self.table_detector = None
            self.text_detector = None
    
    def analyze_layout(self, image: Image.Image) -> DocumentLayout:
        """Analyze the layout of a document image"""
        start_time = time.time()
        
        self.logger.info("Starting layout analysis...")
        
        # Convert PIL image to OpenCV format
        cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        
        # Initialize layout elements
        elements = []
        tables = []
        form_fields = []
        text_blocks = []
        images = []
        
        # Detect different layout elements
        if self.config["table_detection"]["enabled"]:
            tables = self._detect_tables(cv_image)
            elements.extend([self._table_to_element(table) for table in tables])
        
        if self.config["form_detection"]["enabled"]:
            form_fields = self._detect_form_fields(cv_image)
            elements.extend([self._form_field_to_element(field) for field in form_fields])
        
        if self.config["text_block_detection"]["enabled"]:
            text_blocks = self._detect_text_blocks(cv_image)
            elements.extend(text_blocks)
        
        if self.config["image_detection"]["enabled"]:
            images = self._detect_images(cv_image)
            elements.extend(images)
        
        # Organize elements hierarchically
        organized_elements = self._organize_elements(elements)
        
        # Calculate overall confidence
        confidence = self._calculate_layout_confidence(organized_elements)
        
        processing_time = time.time() - start_time
        
        layout = DocumentLayout(
            page_width=image.width,
            page_height=image.height,
            elements=organized_elements,
            tables=tables,
            form_fields=form_fields,
            text_blocks=text_blocks,
            images=images,
            processing_time=processing_time,
            confidence=confidence
        )
        
        self.logger.info(f"Layout analysis completed in {processing_time:.2f}s with confidence {confidence:.2f}")
        
        return layout
    
    def _detect_tables(self, cv_image: np.ndarray) -> List[TableInfo]:
        """Detect tables in the document"""
        tables = []
        
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
            
            # Detect lines
            lines = self.table_detector.detect(gray)
            
            if lines is not None:
                # Find rectangular regions that might be tables
                table_regions = self._find_table_regions(lines, gray)
                
                for region in table_regions:
                    table_info = self._analyze_table_structure(region, gray)
                    if table_info:
                        tables.append(table_info)
            
        except Exception as e:
            self.logger.error(f"Table detection failed: {e}")
        
        return tables
    
    def _find_table_regions(self, lines: np.ndarray, gray_image: np.ndarray) -> List[BoundingBox]:
        """Find potential table regions based on line detection"""
        regions = []
        
        try:
            # Create a mask for detected lines
            line_mask = np.zeros_like(gray_image)
            
            for line in lines:
                x1, y1, x2, y2 = line[0]
                cv2.line(line_mask, (x1, y1), (x2, y2), 255, 2)
            
            # Find contours in the line mask
            contours, _ = cv2.findContours(line_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            for contour in contours:
                area = cv2.contourArea(contour)
                if area > self.config["table_detection"]["min_table_area"]:
                    x, y, w, h = cv2.boundingRect(contour)
                    regions.append(BoundingBox(x, y, w, h))
        
        except Exception as e:
            self.logger.error(f"Table region detection failed: {e}")
        
        return regions
    
    def _analyze_table_structure(self, region: BoundingBox, gray_image: np.ndarray) -> Optional[TableInfo]:
        """Analyze the structure of a detected table region"""
        try:
            # Extract the table region
            table_roi = gray_image[region.y:region.y+region.height, region.x:region.x+region.width]
            
            # Detect horizontal and vertical lines
            horizontal_lines = self._detect_horizontal_lines(table_roi)
            vertical_lines = self._detect_vertical_lines(table_roi)
            
            # Determine table structure
            rows = len(horizontal_lines) - 1
            columns = len(vertical_lines) - 1
            
            if rows < 1 or columns < 1:
                return None
            
            # Determine table type
            structure = self._determine_table_structure(horizontal_lines, vertical_lines, table_roi)
            
            # Extract cell contents (simplified)
            cell_contents = self._extract_cell_contents(table_roi, horizontal_lines, vertical_lines)
            
            # Check if table has header
            has_header = self._detect_table_header(cell_contents)
            
            table_info = TableInfo(
                bounding_box=region,
                rows=rows,
                columns=columns,
                structure=structure,
                has_header=has_header,
                cell_contents=cell_contents,
                confidence=0.8  # Simplified confidence calculation
            )
            
            return table_info
            
        except Exception as e:
            self.logger.error(f"Table structure analysis failed: {e}")
            return None
    
    def _detect_horizontal_lines(self, image: np.ndarray) -> List[int]:
        """Detect horizontal lines in the image"""
        # Use morphological operations to detect horizontal lines
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (image.shape[1]//10, 1))
        horizontal_lines = cv2.morphologyEx(image, cv2.MORPH_OPEN, kernel)
        
        # Find line positions
        line_positions = []
        for i in range(horizontal_lines.shape[0]):
            if np.sum(horizontal_lines[i]) > 0:
                line_positions.append(i)
        
        return line_positions
    
    def _detect_vertical_lines(self, image: np.ndarray) -> List[int]:
        """Detect vertical lines in the image"""
        # Use morphological operations to detect vertical lines
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, image.shape[0]//10))
        vertical_lines = cv2.morphologyEx(image, cv2.MORPH_OPEN, kernel)
        
        # Find line positions
        line_positions = []
        for i in range(vertical_lines.shape[1]):
            if np.sum(vertical_lines[:, i]) > 0:
                line_positions.append(i)
        
        return line_positions
    
    def _determine_table_structure(self, horizontal_lines: List[int], 
                                 vertical_lines: List[int], 
                                 image: np.ndarray) -> TableStructure:
        """Determine the type of table structure"""
        # Simple heuristic-based classification
        if len(horizontal_lines) == 2 and len(vertical_lines) == 2:
            return TableStructure.HEADER_ONLY
        elif len(horizontal_lines) > 3 and len(vertical_lines) > 3:
            return TableStructure.REGULAR
        else:
            return TableStructure.IRREGULAR
    
    def _extract_cell_contents(self, image: np.ndarray, 
                              horizontal_lines: List[int], 
                              vertical_lines: List[int]) -> List[List[str]]:
        """Extract text content from table cells"""
        cell_contents = []
        
        # For now, return empty cell contents
        # This would be enhanced with OCR processing
        for i in range(len(horizontal_lines) - 1):
            row = []
            for j in range(len(vertical_lines) - 1):
                row.append("")  # Placeholder for cell content
            cell_contents.append(row)
        
        return cell_contents
    
    def _detect_table_header(self, cell_contents: List[List[str]]) -> bool:
        """Detect if the table has a header row"""
        if not cell_contents or not cell_contents[0]:
            return False
        
        # Simple heuristic: check if first row has more non-empty cells
        first_row = cell_contents[0]
        non_empty_count = sum(1 for cell in first_row if cell.strip())
        
        return non_empty_count > len(first_row) // 2
    
    def _detect_form_fields(self, cv_image: np.ndarray) -> List[FormField]:
        """Detect form fields in the document"""
        form_fields = []
        
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
            
            # Detect rectangular regions that might be form fields
            contours, _ = cv2.findContours(gray, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            for contour in contours:
                area = cv2.contourArea(contour)
                if area > self.config["form_detection"]["min_field_area"]:
                    x, y, w, h = cv2.boundingRect(contour)
                    
                    # Determine field type based on shape and size
                    field_type = self._classify_form_field(w, h, gray[y:y+h, x:x+w])
                    
                    if field_type:
                        form_field = FormField(
                            field_type=field_type,
                            label="",  # Would be extracted from nearby text
                            bounding_box=BoundingBox(x, y, w, h),
                            is_required=False  # Would be determined from context
                        )
                        form_fields.append(form_field)
        
        except Exception as e:
            self.logger.error(f"Form field detection failed: {e}")
        
        return form_fields
    
    def _classify_form_field(self, width: int, height: int, roi: np.ndarray) -> Optional[str]:
        """Classify the type of form field based on shape and characteristics"""
        aspect_ratio = width / height if height > 0 else 0
        
        # Simple classification based on aspect ratio and size
        if aspect_ratio > 5:  # Very wide
            return "text"
        elif aspect_ratio < 0.5:  # Very tall
            return "text"
        elif width < 50 and height < 50:  # Small square
            return "checkbox"
        elif width < 30 and height < 30:  # Very small
            return "radio_button"
        else:
            return "text"
    
    def _detect_text_blocks(self, cv_image: np.ndarray) -> List[LayoutElement]:
        """Detect text blocks in the document"""
        text_blocks = []
        
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
            
            # Use morphological operations to detect text regions
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (20, 5))
            text_regions = cv2.morphologyEx(gray, cv2.MORPH_CLOSE, kernel)
            
            # Find contours
            contours, _ = cv2.findContours(text_regions, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            for contour in contours:
                area = cv2.contourArea(contour)
                if area > self.config["text_block_detection"]["min_block_area"]:
                    x, y, w, h = cv2.boundingRect(contour)
                    
                    # Determine text block type
                    block_type = self._classify_text_block(w, h, gray[y:y+h, x:x+w])
                    
                    text_block = LayoutElement(
                        element_type=block_type,
                        bounding_box=BoundingBox(x, y, w, h),
                        confidence=0.7,
                        text_content=""
                    )
                    text_blocks.append(text_block)
        
        except Exception as e:
            self.logger.error(f"Text block detection failed: {e}")
        
        return text_blocks
    
    def _classify_text_block(self, width: int, height: int, roi: np.ndarray) -> LayoutElementType:
        """Classify the type of text block"""
        aspect_ratio = width / height if height > 0 else 0
        
        # Simple classification based on position and size
        if height < 30:  # Very short
            return LayoutElementType.TITLE
        elif aspect_ratio > 3:  # Very wide
            return LayoutElementType.PARAGRAPH
        else:
            return LayoutElementType.TEXT_BLOCK
    
    def _detect_images(self, cv_image: np.ndarray) -> List[LayoutElement]:
        """Detect images in the document"""
        images = []
        
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
            
            # Use edge detection to find image regions
            edges = cv2.Canny(gray, 50, 150)
            
            # Find contours
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            for contour in contours:
                area = cv2.contourArea(contour)
                if area > self.config["image_detection"]["min_image_area"]:
                    x, y, w, h = cv2.boundingRect(contour)
                    
                    image_element = LayoutElement(
                        element_type=LayoutElementType.IMAGE,
                        bounding_box=BoundingBox(x, y, w, h),
                        confidence=0.8
                    )
                    images.append(image_element)
        
        except Exception as e:
            self.logger.error(f"Image detection failed: {e}")
        
        return images
    
    def _organize_elements(self, elements: List[LayoutElement]) -> List[LayoutElement]:
        """Organize layout elements hierarchically"""
        # Sort elements by position (top to bottom, left to right)
        sorted_elements = sorted(elements, key=lambda e: (e.bounding_box.y, e.bounding_box.x))
        
        # Simple hierarchical organization
        organized = []
        for element in sorted_elements:
            # Find parent element (if any)
            parent = self._find_parent_element(element, organized)
            if parent:
                parent.children.append(element)
                element.parent = parent
            else:
                organized.append(element)
        
        return organized
    
    def _find_parent_element(self, element: LayoutElement, 
                           existing_elements: List[LayoutElement]) -> Optional[LayoutElement]:
        """Find the parent element for a given element"""
        for existing in existing_elements:
            if existing.bounding_box.intersects(element.bounding_box):
                # Check if existing element contains the new element
                if (existing.bounding_box.x <= element.bounding_box.x and
                    existing.bounding_box.y <= element.bounding_box.y and
                    existing.bounding_box.x + existing.bounding_box.width >= 
                    element.bounding_box.x + element.bounding_box.width and
                    existing.bounding_box.y + existing.bounding_box.height >= 
                    element.bounding_box.y + element.bounding_box.height):
                    return existing
        
        return None
    
    def _calculate_layout_confidence(self, elements: List[LayoutElement]) -> float:
        """Calculate overall confidence for the layout analysis"""
        if not elements:
            return 0.0
        
        # Calculate average confidence of all elements
        total_confidence = sum(element.confidence for element in elements)
        return total_confidence / len(elements)
    
    def _table_to_element(self, table: TableInfo) -> LayoutElement:
        """Convert TableInfo to LayoutElement"""
        return LayoutElement(
            element_type=LayoutElementType.TABLE,
            bounding_box=table.bounding_box,
            confidence=table.confidence,
            metadata={
                "rows": table.rows,
                "columns": table.columns,
                "structure": table.structure.value,
                "has_header": table.has_header
            }
        )
    
    def _form_field_to_element(self, field: FormField) -> LayoutElement:
        """Convert FormField to LayoutElement"""
        return LayoutElement(
            element_type=LayoutElementType.FORM_FIELD,
            bounding_box=field.bounding_box,
            confidence=0.8,
            metadata={
                "field_type": field.field_type,
                "label": field.label,
                "is_required": field.is_required
            }
        )

class LayoutEnhancedOCR:
    """Enhanced OCR system that uses layout analysis to improve text extraction"""
    
    def __init__(self, multi_ocr_engine, layout_analyzer: LayoutAnalyzer):
        self.multi_ocr_engine = multi_ocr_engine
        self.layout_analyzer = layout_analyzer
        self.logger = logging.getLogger(__name__)
    
    def process_document_with_layout(self, image: Image.Image) -> Dict[str, Any]:
        """Process document with layout-aware OCR"""
        start_time = time.time()
        
        # First, analyze the layout
        layout = self.layout_analyzer.analyze_layout(image)
        
        # Extract text with layout awareness
        text_results = self._extract_text_with_layout(image, layout)
        
        # Combine results
        result = {
            "layout": layout,
            "text_results": text_results,
            "processing_time": time.time() - start_time,
            "confidence": layout.confidence
        }
        
        return result
    
    def _extract_text_with_layout(self, image: Image.Image, layout: DocumentLayout) -> Dict[str, Any]:
        """Extract text with layout awareness"""
        text_results = {
            "tables": [],
            "form_fields": [],
            "text_blocks": [],
            "images": []
        }
        
        # Process each layout element type
        for element in layout.elements:
            if element.element_type == LayoutElementType.TABLE:
                table_text = self._extract_table_text(image, element)
                text_results["tables"].append(table_text)
            
            elif element.element_type == LayoutElementType.FORM_FIELD:
                field_text = self._extract_form_field_text(image, element)
                text_results["form_fields"].append(field_text)
            
            elif element.element_type in [LayoutElementType.TEXT_BLOCK, LayoutElementType.PARAGRAPH, 
                                        LayoutElementType.TITLE, LayoutElementType.SUBTITLE]:
                block_text = self._extract_text_block_text(image, element)
                text_results["text_blocks"].append(block_text)
            
            elif element.element_type == LayoutElementType.IMAGE:
                image_info = self._extract_image_info(image, element)
                text_results["images"].append(image_info)
        
        return text_results
    
    def _extract_table_text(self, image: Image.Image, table_element: LayoutElement) -> Dict[str, Any]:
        """Extract text from table regions"""
        # Crop the table region
        bbox = table_element.bounding_box
        table_image = image.crop((bbox.x, bbox.y, bbox.x + bbox.width, bbox.y + bbox.height))
        
        # Use multi-OCR to extract text
        ocr_result = self.multi_ocr_engine.process_image(table_image)
        
        return {
            "text": ocr_result.text,
            "confidence": ocr_result.confidence,
            "metadata": table_element.metadata
        }
    
    def _extract_form_field_text(self, image: Image.Image, field_element: LayoutElement) -> Dict[str, Any]:
        """Extract text from form field regions"""
        # Crop the form field region
        bbox = field_element.bounding_box
        field_image = image.crop((bbox.x, bbox.y, bbox.x + bbox.width, bbox.y + bbox.height))
        
        # Use multi-OCR to extract text
        ocr_result = self.multi_ocr_engine.process_image(field_image)
        
        return {
            "text": ocr_result.text,
            "confidence": ocr_result.confidence,
            "metadata": field_element.metadata
        }
    
    def _extract_text_block_text(self, image: Image.Image, text_element: LayoutElement) -> Dict[str, Any]:
        """Extract text from text block regions"""
        # Crop the text block region
        bbox = text_element.bounding_box
        text_image = image.crop((bbox.x, bbox.y, bbox.x + bbox.width, bbox.y + bbox.height))
        
        # Use multi-OCR to extract text
        ocr_result = self.multi_ocr_engine.process_image(text_image)
        
        return {
            "text": ocr_result.text,
            "confidence": ocr_result.confidence,
            "element_type": text_element.element_type.value,
            "metadata": text_element.metadata
        }
    
    def _extract_image_info(self, image: Image.Image, image_element: LayoutElement) -> Dict[str, Any]:
        """Extract information about image regions"""
        bbox = image_element.bounding_box
        
        return {
            "position": {"x": bbox.x, "y": bbox.y, "width": bbox.width, "height": bbox.height},
            "area": bbox.area,
            "metadata": image_element.metadata
        }

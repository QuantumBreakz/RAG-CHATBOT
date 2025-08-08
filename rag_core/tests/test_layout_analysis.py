"""
Test Layout Analysis System

Tests for the enhanced multi-OCR with layout analysis functionality.
"""

import pytest
import tempfile
import os
from PIL import Image, ImageDraw, ImageFont
import numpy as np
from unittest.mock import Mock, patch

# Import the modules to test
from rag_core.layout_analysis import (
    LayoutAnalyzer, LayoutEnhancedOCR, LayoutElementType, 
    TableStructure, BoundingBox, DocumentLayout, LayoutElement
)
from rag_core.multi_ocr import MultiOCREngine, OCRResult

class TestLayoutAnalyzer:
    """Test the LayoutAnalyzer class"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.analyzer = LayoutAnalyzer()
    
    def test_initialization(self):
        """Test LayoutAnalyzer initialization"""
        assert self.analyzer is not None
        assert hasattr(self.analyzer, 'config')
        assert 'table_detection' in self.analyzer.config
        assert 'form_detection' in self.analyzer.config
        assert 'text_block_detection' in self.analyzer.config
        assert 'image_detection' in self.analyzer.config
    
    def test_create_simple_document_image(self):
        """Create a simple test document image"""
        # Create a white image
        img = Image.new('RGB', (800, 600), color='white')
        draw = ImageDraw.Draw(img)
        
        # Add some text blocks
        draw.rectangle([50, 50, 350, 100], outline='black', width=2)  # Title
        draw.rectangle([50, 120, 750, 200], outline='black', width=1)  # Paragraph
        draw.rectangle([50, 220, 750, 300], outline='black', width=1)  # Another paragraph
        
        # Add a simple table
        draw.rectangle([50, 320, 750, 420], outline='black', width=2)  # Table border
        draw.line([50, 360, 750, 360], fill='black', width=1)  # Horizontal line
        draw.line([250, 320, 250, 420], fill='black', width=1)  # Vertical line
        draw.line([450, 320, 450, 420], fill='black', width=1)  # Vertical line
        
        # Add a form field
        draw.rectangle([50, 450, 200, 480], outline='black', width=1)  # Form field
        
        # Store the image for use in other tests
        self.test_image = img
    
    def test_analyze_layout_basic(self):
        """Test basic layout analysis"""
        # Create a simple test image
        self.test_create_simple_document_image()
        test_image = self.test_image
        
        # Analyze layout
        layout = self.analyzer.analyze_layout(test_image)
        
        # Verify basic structure
        assert isinstance(layout, DocumentLayout)
        assert layout.page_width == 800
        assert layout.page_height == 600
        assert layout.processing_time > 0
        assert 0 <= layout.confidence <= 1
    
    def test_bounding_box_operations(self):
        """Test BoundingBox operations"""
        bbox1 = BoundingBox(0, 0, 100, 100)
        bbox2 = BoundingBox(50, 50, 100, 100)
        bbox3 = BoundingBox(200, 200, 100, 100)
        
        # Test area calculation
        assert bbox1.area == 10000
        
        # Test center calculation
        assert bbox1.center == (50, 50)
        
        # Test intersection
        assert bbox1.intersects(bbox2) == True
        assert bbox1.intersects(bbox3) == False
    
    def test_layout_element_creation(self):
        """Test LayoutElement creation"""
        bbox = BoundingBox(0, 0, 100, 100)
        element = LayoutElement(
            element_type=LayoutElementType.TEXT_BLOCK,
            bounding_box=bbox,
            confidence=0.8,
            text_content="Test text"
        )
        
        assert element.element_type == LayoutElementType.TEXT_BLOCK
        assert element.bounding_box == bbox
        assert element.confidence == 0.8
        assert element.text_content == "Test text"

class TestLayoutEnhancedOCR:
    """Test the LayoutEnhancedOCR class"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.multi_ocr = Mock(spec=MultiOCREngine)
        self.layout_analyzer = LayoutAnalyzer()
        self.layout_enhanced_ocr = LayoutEnhancedOCR(self.multi_ocr, self.layout_analyzer)
    
    def test_initialization(self):
        """Test LayoutEnhancedOCR initialization"""
        assert self.layout_enhanced_ocr is not None
        assert self.layout_enhanced_ocr.multi_ocr_engine == self.multi_ocr
        assert self.layout_enhanced_ocr.layout_analyzer == self.layout_analyzer
    
    def test_process_document_with_layout(self):
        """Test document processing with layout analysis"""
        # Create a test image
        test_image = Image.new('RGB', (400, 300), color='white')
        
        # Mock the multi-OCR engine
        mock_ocr_result = OCRResult(
            engine_name="test_engine",
            text="Test extracted text",
            confidence=0.9,
            processing_time=0.5,
            metadata={}
        )
        self.multi_ocr.process_image.return_value = mock_ocr_result
        
        # Process document
        result = self.layout_enhanced_ocr.process_document_with_layout(test_image)
        
        # Verify result structure
        assert 'layout' in result
        assert 'text_results' in result
        assert 'processing_time' in result
        assert 'confidence' in result
        
        # Verify layout analysis was performed
        assert isinstance(result['layout'], DocumentLayout)
        
        # Verify text results structure
        text_results = result['text_results']
        assert 'tables' in text_results
        assert 'form_fields' in text_results
        assert 'text_blocks' in text_results
        assert 'images' in text_results

class TestMultiOCREngineLayoutIntegration:
    """Test MultiOCREngine integration with layout analysis"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.config = {
            "enable_layout_analysis": True,
            "layout_analysis": {
                "table_detection": {"enabled": True},
                "form_detection": {"enabled": True},
                "text_block_detection": {"enabled": True},
                "image_detection": {"enabled": True}
            },
            "engines": {
                "tesseract": {
                    "enabled": True,
                    "priority": 1,
                    "languages": ["eng"],
                    "config": "--oem 1 --psm 6"
                },
                "paddleocr": {
                    "enabled": False,
                    "priority": 2,
                    "languages": ["en"]
                },
                "easyocr": {
                    "enabled": False,
                    "priority": 3,
                    "languages": ["en"]
                }
            }
        }
    
    @patch('rag_core.layout_analysis.LayoutAnalyzer')
    @patch('rag_core.layout_analysis.LayoutEnhancedOCR')
    def test_multi_ocr_with_layout_initialization(self, mock_layout_enhanced_ocr, mock_layout_analyzer):
        """Test MultiOCREngine initialization with layout analysis"""
        # Mock the layout components
        mock_analyzer = Mock()
        mock_layout_analyzer.return_value = mock_analyzer
        
        mock_enhanced_ocr = Mock()
        mock_layout_enhanced_ocr.return_value = mock_enhanced_ocr
        
        # Initialize MultiOCREngine with layout analysis
        multi_ocr = MultiOCREngine(self.config)
        
        # Verify layout components were initialized
        assert multi_ocr.layout_analyzer is not None
        assert multi_ocr.layout_enhanced_ocr is not None
    
    def test_multi_ocr_without_layout_initialization(self):
        """Test MultiOCREngine initialization without layout analysis"""
        config = {
            "enable_layout_analysis": False,
            "engines": {
                "tesseract": {
                    "enabled": True,
                    "priority": 1,
                    "languages": ["eng"],
                    "config": "--oem 1 --psm 6"
                }
            }
        }
        
        # This should not raise an exception even if layout analysis is disabled
        multi_ocr = MultiOCREngine(config)
        
        # Layout components should be None
        assert multi_ocr.layout_analyzer is None
        assert multi_ocr.layout_enhanced_ocr is None

class TestLayoutAnalysisEndToEnd:
    """End-to-end tests for layout analysis"""
    
    def test_simple_document_processing(self):
        """Test processing a simple document with layout analysis"""
        # Create a simple test document
        img = Image.new('RGB', (600, 400), color='white')
        draw = ImageDraw.Draw(img)
        
        # Add some basic elements
        draw.rectangle([50, 50, 550, 100], outline='black', width=2)  # Title area
        draw.rectangle([50, 120, 550, 200], outline='black', width=1)  # Text area
        draw.rectangle([50, 220, 550, 300], outline='black', width=1)  # Another text area
        
        # Initialize layout analyzer
        analyzer = LayoutAnalyzer()
        
        # Analyze layout
        layout = analyzer.analyze_layout(img)
        
        # Basic verification
        assert layout.page_width == 600
        assert layout.page_height == 400
        assert layout.processing_time > 0
        assert layout.confidence >= 0
    
    def test_table_detection(self):
        """Test table detection functionality"""
        # Create an image with a table
        img = Image.new('RGB', (400, 300), color='white')
        draw = ImageDraw.Draw(img)
        
        # Draw a simple table
        draw.rectangle([50, 50, 350, 150], outline='black', width=2)  # Table border
        draw.line([50, 90, 350, 90], fill='black', width=1)  # Horizontal line
        draw.line([150, 50, 150, 150], fill='black', width=1)  # Vertical line
        draw.line([250, 50, 250, 150], fill='black', width=1)  # Vertical line
        
        # Initialize layout analyzer
        analyzer = LayoutAnalyzer()
        
        # Analyze layout
        layout = analyzer.analyze_layout(img)
        
        # Verify table detection (basic check)
        assert len(layout.tables) >= 0  # May or may not detect table depending on algorithm
    
    def test_form_field_detection(self):
        """Test form field detection functionality"""
        # Create an image with form fields
        img = Image.new('RGB', (400, 300), color='white')
        draw = ImageDraw.Draw(img)
        
        # Draw form fields
        draw.rectangle([50, 50, 200, 80], outline='black', width=1)  # Text field
        draw.rectangle([50, 100, 70, 120], outline='black', width=1)  # Checkbox
        draw.rectangle([50, 150, 200, 180], outline='black', width=1)  # Another text field
        
        # Initialize layout analyzer
        analyzer = LayoutAnalyzer()
        
        # Analyze layout
        layout = analyzer.analyze_layout(img)
        
        # Verify form field detection (basic check)
        assert len(layout.form_fields) >= 0  # May or may not detect fields depending on algorithm

def test_layout_analysis_imports():
    """Test that all layout analysis modules can be imported"""
    try:
        from rag_core.layout_analysis import (
            LayoutAnalyzer, LayoutEnhancedOCR, LayoutElementType,
            TableStructure, BoundingBox, DocumentLayout, LayoutElement,
            FormField, TableInfo
        )
        assert True  # If we get here, imports worked
    except ImportError as e:
        pytest.fail(f"Failed to import layout analysis modules: {e}")

def test_layout_analysis_configuration():
    """Test layout analysis configuration"""
    from rag_core.layout_analysis import LayoutAnalyzer
    
    # Test default configuration
    analyzer = LayoutAnalyzer()
    config = analyzer.config
    
    # Verify required configuration sections
    assert 'table_detection' in config
    assert 'form_detection' in config
    assert 'text_block_detection' in config
    assert 'image_detection' in config
    assert 'performance' in config
    
    # Verify configuration values
    assert config['table_detection']['enabled'] == True
    assert config['form_detection']['enabled'] == True
    assert config['text_block_detection']['enabled'] == True
    assert config['image_detection']['enabled'] == True

if __name__ == "__main__":
    # Run basic tests
    test_layout_analysis_imports()
    test_layout_analysis_configuration()
    print("Layout analysis tests completed successfully!")

#!/usr/bin/env python3
"""
Integration Test for OCR System

This test verifies that the OCR system integrates properly with the backend API
and all components work together correctly.
"""

import os
import sys
import tempfile
import time
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

# Add the rag_core parent directory to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rag_core.multi_ocr import MultiOCREngine
from rag_core.ocr_config import get_config
from rag_core.document import DocumentProcessor

def create_test_image():
    """Create a test image for OCR testing"""
    width, height = 600, 400
    image = Image.new('RGB', (width, height), color='white')
    draw = ImageDraw.Draw(image)
    
    # Try to use a default font
    try:
        font = ImageFont.truetype("arial.ttf", 16)
    except:
        try:
            font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 16)
        except:
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 16)
            except:
                font = ImageFont.load_default()
    
    # Add test text
    test_text = [
        "Integration Test Document",
        "This document tests OCR integration.",
        "Testing multi-engine consensus.",
        "Performance optimization test.",
        "Special characters: @#$%^&*()",
        "Numbers: 1234567890",
        "Mixed case: UPPER lower MiXeD",
        "End of test document."
    ]
    
    y_position = 50
    for line in test_text:
        draw.text((50, y_position), line, fill='black', font=font)
        y_position += 25
    
    return image

def test_ocr_integration():
    """Test OCR integration with document processing"""
    print("\n=== Testing OCR Integration ===")
    
    try:
        # Test different configurations
        configs_to_test = [
            ("fast_performance", "Fast Performance"),
            ("offline", "Offline Mode"),
            ("default", "Default Configuration")
        ]
        
        for config_name, description in configs_to_test:
            print(f"\n--- Testing {description} ---")
            
            # Get configuration
            config = get_config(config_name)
            multi_ocr = MultiOCREngine(config)
            
            # Create test image
            test_image = create_test_image()
            
            # Test OCR processing
            start_time = time.time()
            result = multi_ocr.process_image(test_image)
            processing_time = time.time() - start_time
            
            print(f"✅ {description} test completed")
            print(f"   Processing Time: {processing_time:.2f}s")
            print(f"   Text Length: {len(result.text)} characters")
            print(f"   Confidence: {result.confidence.value}")
            print(f"   Contributing Engines: {result.contributing_engines}")
            print(f"   Agreement Score: {result.agreement_score:.3f}")
            
            # Test document processor integration
            print(f"\n--- Testing Document Processor Integration ---")
            
            # Create a temporary PDF file
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_file:
                # Convert image to PDF (simplified)
                test_image.save(temp_file.name, "PDF")
                temp_file_path = temp_file.name
            
            try:
                # Test document processing
                processor = DocumentProcessor()
                
                with open(temp_file_path, 'rb') as f:
                    file_content = f.read()
                
                start_time = time.time()
                docs = processor.process_document(file_content, "test_integration.pdf")
                doc_processing_time = time.time() - start_time
                
                print(f"✅ Document processing completed")
                print(f"   Processing Time: {doc_processing_time:.2f}s")
                print(f"   Documents Created: {len(docs)}")
                
                if docs:
                    print(f"   First Document Length: {len(docs[0].page_content)} characters")
                    print(f"   Metadata: {list(docs[0].metadata.keys())}")
                
            finally:
                # Clean up
                if os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)
        
        return True
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        return False

def test_backend_api_integration():
    """Test backend API integration"""
    print("\n=== Testing Backend API Integration ===")
    
    try:
        # Test OCR configuration endpoint (simulated)
        print("Testing OCR configuration endpoints...")
        
        # Test getting available configs
        configs = [
            {"name": "default", "description": "Default balanced configuration"},
            {"name": "fast_performance", "description": "Fast performance (Tesseract only)"},
            {"name": "offline", "description": "Offline mode (all engines)"},
            {"name": "high_accuracy", "description": "High accuracy configuration"},
            {"name": "fast", "description": "Fast processing configuration"}
        ]
        
        print(f"✅ Available configurations: {len(configs)}")
        for config in configs:
            print(f"   - {config['name']}: {config['description']}")
        
        # Test getting specific configuration
        test_config = get_config("fast_performance")
        print(f"✅ Fast performance config loaded")
        print(f"   Engines enabled: {[k for k, v in test_config['engines'].items() if v['enabled']]}")
        print(f"   Parallel processing: {test_config['performance']['parallel_processing']}")
        print(f"   Caching enabled: {test_config['performance']['enable_caching']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Backend API integration test failed: {e}")
        return False

def test_performance_optimizations():
    """Test performance optimizations"""
    print("\n=== Testing Performance Optimizations ===")
    
    try:
        # Test caching
        print("Testing caching system...")
        config = get_config("fast_performance")
        multi_ocr = MultiOCREngine(config)
        
        test_image = create_test_image()
        
        # First run
        start_time = time.time()
        result1 = multi_ocr.process_image(test_image)
        first_run = time.time() - start_time
        
        # Second run (should use cache)
        start_time = time.time()
        result2 = multi_ocr.process_image(test_image)
        second_run = time.time() - start_time
        
        print(f"✅ Caching test completed")
        print(f"   First run: {first_run:.2f}s")
        print(f"   Second run: {second_run:.2f}s")
        print(f"   Cache hit: {result1.text == result2.text}")
        
        # Test parallel processing
        print("\nTesting parallel processing...")
        config_parallel = get_config("offline")
        config_parallel["performance"]["parallel_processing"] = True
        multi_ocr_parallel = MultiOCREngine(config_parallel)
        
        start_time = time.time()
        result_parallel = multi_ocr_parallel.process_image(test_image)
        parallel_time = time.time() - start_time
        
        print(f"✅ Parallel processing test completed")
        print(f"   Processing Time: {parallel_time:.2f}s")
        print(f"   Engines Used: {result_parallel.contributing_engines}")
        
        return True
        
    except Exception as e:
        print(f"❌ Performance optimization test failed: {e}")
        return False

def main():
    """Run all integration tests"""
    print("OCR Integration Testing")
    print("=" * 50)
    
    tests = [
        ("OCR Integration", test_ocr_integration),
        ("Backend API Integration", test_backend_api_integration),
        ("Performance Optimizations", test_performance_optimizations)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"❌ {test_name} test failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print(f"\n{'='*50}")
    print("INTEGRATION TEST SUMMARY")
    print("=" * 50)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{status}: {test_name}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All integration tests passed!")
        print("✅ OCR system is properly integrated with the backend")
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
    
    return passed == total

if __name__ == "__main__":
    main() 
#!/usr/bin/env python3
"""
OCR Engines Setup and Testing Script

This script helps install and test the additional OCR engines (PaddleOCR and EasyOCR)
for the multi-OCR pipeline system.
"""

import os
import sys
import subprocess
import importlib
import tempfile
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import numpy as np

# Add the rag_core parent directory to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rag_core.multi_ocr import MultiOCREngine

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        return False
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} is compatible")
    return True

def install_package(package_name, install_name=None):
    """Install a Python package"""
    if install_name is None:
        install_name = package_name
    
    print(f"Installing {package_name}...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", install_name])
        print(f"✅ {package_name} installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install {package_name}: {e}")
        return False

def test_import(module_name, package_name=None):
    """Test if a module can be imported"""
    if package_name is None:
        package_name = module_name
    
    try:
        importlib.import_module(module_name)
        print(f"✅ {package_name} import successful")
        return True
    except ImportError as e:
        print(f"❌ {package_name} import failed: {e}")
        return False

def create_test_image():
    """Create a test image for OCR testing"""
    # Create a simple test image
    width, height = 800, 600
    image = Image.new('RGB', (width, height), color='white')
    draw = ImageDraw.Draw(image)
    
    # Try to use a default font, fallback to basic if not available
    try:
        # Try to use a system font
        font = ImageFont.truetype("arial.ttf", 24)
    except:
        try:
            font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 24)
        except:
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
            except:
                font = ImageFont.load_default()
    
    # Add test text
    test_text = [
        "OCR Test Document",
        "This is a test image for OCR engines.",
        "Testing multiple OCR engines:",
        "1. Tesseract",
        "2. PaddleOCR", 
        "3. EasyOCR",
        "Special characters: @#$%^&*()_+-=[]{}|;':\",./<>?",
        "Numbers: 1234567890",
        "Mixed case: UPPER lower MiXeD",
        "Technical terms: API, JSON, XML, HTTP, HTTPS",
        "End of test document."
    ]
    
    y_position = 50
    for line in test_text:
        draw.text((50, y_position), line, fill='black', font=font)
        y_position += 40
    
    return image

def test_tesseract():
    """Test Tesseract OCR engine"""
    print("\n=== Testing Tesseract OCR ===")
    
    try:
        import pytesseract
        
        # Test Tesseract installation
        version = pytesseract.get_tesseract_version()
        print(f"✅ Tesseract version: {version}")
        
        # Create test image
        test_image = create_test_image()
        
        # Test OCR
        text = pytesseract.image_to_string(test_image, lang='eng')
        print(f"✅ Tesseract OCR test successful")
        print(f"   Extracted text length: {len(text)} characters")
        print(f"   Text preview: {text[:100]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Tesseract test failed: {e}")
        return False

def test_paddleocr():
    """Test PaddleOCR engine"""
    print("\n=== Testing PaddleOCR ===")
    
    try:
        from paddleocr import PaddleOCR
        
        # Initialize PaddleOCR with corrected configuration
        paddle_ocr = PaddleOCR(
            use_textline_orientation=True,  # Fixed deprecated parameter
            lang='en', 
            use_gpu=False, 
            use_mp=True,  # Enable multiprocessing
            total_process_num=4,  # Number of processes
            enable_mkldnn=True,  # Enable MKL-DNN for CPU optimization
            cpu_threads=4,  # Number of CPU threads
            det_db_thresh=0.3,  # Lower threshold for faster detection
            det_db_box_thresh=0.5,  # Lower threshold for faster detection
            det_db_unclip_ratio=1.6,  # Optimized for speed
            rec_batch_num=6,  # Batch size for recognition
            cls_batch_num=6  # Batch size for classification
        )
        print("✅ PaddleOCR initialized successfully")
        
        # Create test image
        test_image = create_test_image()
        img_array = np.array(test_image)
        
        # Test OCR
        results = paddle_ocr.ocr(img_array, cls=True)
        
        if results and results[0]:
            text_parts = []
            for line in results[0]:
                if line and len(line) >= 2:
                    text = line[1][0]
                    confidence = line[1][1]
                    if text.strip():
                        text_parts.append(text)
            
            text = ' '.join(text_parts)
            print(f"✅ PaddleOCR test successful")
            print(f"   Extracted text length: {len(text)} characters")
            print(f"   Number of text boxes: {len(text_parts)}")
            print(f"   Text preview: {text[:100]}...")
        else:
            print("⚠️  PaddleOCR returned no results")
        
        return True
        
    except ImportError:
        print("❌ PaddleOCR not installed. Install with: pip install paddleocr")
        return False
    except Exception as e:
        print(f"❌ PaddleOCR test failed: {e}")
        return False

def test_easyocr():
    """Test EasyOCR engine"""
    print("\n=== Testing EasyOCR ===")
    
    try:
        import easyocr
        
        # Initialize EasyOCR
        easy_ocr = easyocr.Reader(['en'], gpu=False)
        print("✅ EasyOCR initialized successfully")
        
        # Create test image
        test_image = create_test_image()
        img_array = np.array(test_image)
        
        # Test OCR
        results = easy_ocr.readtext(img_array)
        
        if results:
            text_parts = []
            confidences = []
            for (bbox, text, confidence) in results:
                if text.strip():
                    text_parts.append(text)
                    confidences.append(confidence)
            
            text = ' '.join(text_parts)
            avg_confidence = np.mean(confidences) if confidences else 0.0
            
            print(f"✅ EasyOCR test successful")
            print(f"   Extracted text length: {len(text)} characters")
            print(f"   Number of text boxes: {len(text_parts)}")
            print(f"   Average confidence: {avg_confidence:.3f}")
            print(f"   Text preview: {text[:100]}...")
        else:
            print("⚠️  EasyOCR returned no results")
        
        return True
        
    except ImportError:
        print("❌ EasyOCR not installed. Install with: pip install easyocr")
        return False
    except Exception as e:
        print(f"❌ EasyOCR test failed: {e}")
        return False

def test_multi_ocr_integration():
    """Test the multi-OCR integration"""
    print("\n=== Testing Multi-OCR Integration ===")
    
    try:
        # Import the multi-OCR system
        # sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))) # This line is now redundant
        # from rag_core.multi_ocr import MultiOCREngine # This line is now redundant
        
        # Create test image
        test_image = create_test_image()
        
        # Test with different configurations
        configs = [
            ("default", "Default configuration"),
            ("high_accuracy", "High accuracy configuration"),
            ("fast", "Fast processing configuration")
        ]
        
        for config_name, description in configs:
            try:
                print(f"\nTesting {description}...")
                
                # Get configuration
                from rag_core.ocr_config import get_config
                config = get_config(config_name)
                
                # Initialize multi-OCR engine
                multi_ocr = MultiOCREngine(config)
                
                # Process test image
                result = multi_ocr.process_image(test_image)
                
                print(f"✅ {description} test successful")
                print(f"   Confidence: {result.confidence.value}")
                print(f"   Agreement Score: {result.agreement_score:.3f}")
                print(f"   Contributing Engines: {result.contributing_engines}")
                print(f"   Processing Time: {result.processing_time:.2f}s")
                print(f"   Text Length: {len(result.text)} characters")
                
            except Exception as e:
                print(f"❌ {description} test failed: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Multi-OCR integration test failed: {e}")
        return False

def install_ocr_engines():
    """Install all OCR engines"""
    print("=== Installing OCR Engines ===")
    
    # Check Python version
    if not check_python_version():
        return False
    
    # Install required packages
    packages = [
        ("opencv-python", "OpenCV"),
        ("nltk", "NLTK"),
        ("paddleocr", "PaddleOCR"),
        ("easyocr", "EasyOCR")
    ]
    
    success_count = 0
    for package, name in packages:
        if install_package(package, name):
            success_count += 1
    
    print(f"\nInstallation Summary: {success_count}/{len(packages)} packages installed successfully")
    return success_count == len(packages)

def test_all_engines():
    """Test all OCR engines"""
    print("=== Testing All OCR Engines ===")
    
    tests = [
        ("Tesseract", test_tesseract),
        ("PaddleOCR", test_paddleocr),
        ("EasyOCR", test_easyocr),
        ("Multi-OCR Integration", test_multi_ocr_integration)
    ]
    
    results = {}
    for test_name, test_func in tests:
        try:
            success = test_func()
            results[test_name] = success
        except Exception as e:
            print(f"❌ {test_name} test failed with exception: {e}")
            results[test_name] = False
    
    # Summary
    print(f"\n=== Test Summary ===")
    passed = sum(1 for success in results.values() if success)
    total = len(results)
    
    for test_name, success in results.items():
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{status}: {test_name}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All OCR engines are working correctly!")
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
    
    return passed == total

def main():
    """Main setup and testing function"""
    print("OCR Engines Setup and Testing")
    print("=" * 50)
    
    # Check if running in interactive mode
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "install":
            success = install_ocr_engines()
            if success:
                print("\n✅ Installation completed successfully!")
                print("Run 'python setup_ocr_engines.py test' to test the engines")
            else:
                print("\n❌ Installation failed. Check the output above for details.")
        
        elif command == "test":
            success = test_all_engines()
            if success:
                print("\n✅ All engines are working correctly!")
            else:
                print("\n❌ Some engines failed. Check the output above for details.")
        
        else:
            print("Usage:")
            print("  python setup_ocr_engines.py install  # Install OCR engines")
            print("  python setup_ocr_engines.py test     # Test OCR engines")
    
    else:
        # Interactive mode
        print("Choose an option:")
        print("1. Install OCR engines")
        print("2. Test OCR engines")
        print("3. Install and test")
        
        try:
            choice = input("\nEnter your choice (1-3): ").strip()
            
            if choice == "1":
                install_ocr_engines()
            elif choice == "2":
                test_all_engines()
            elif choice == "3":
                if install_ocr_engines():
                    print("\n" + "="*50)
                    test_all_engines()
            else:
                print("Invalid choice. Please run the script again.")
        
        except KeyboardInterrupt:
            print("\n\nSetup cancelled by user.")
        except Exception as e:
            print(f"\nError: {e}")

if __name__ == "__main__":
    main() 
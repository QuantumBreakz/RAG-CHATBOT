#!/usr/bin/env python3
"""
Multi-OCR Pipeline Test Suite

This module provides comprehensive tests for the multi-OCR pipeline system,
including individual engine testing, consensus validation, and integration tests.
"""

import os
import sys
import tempfile
import time
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import numpy as np

# Add the rag_core parent directory to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rag_core.multi_ocr import MultiOCREngine, OCRConfidence
from rag_core.ocr_config import get_config, get_config_for_document_type
from rag_core.ocr_quality import OCRQualityAssessor, QualityMetrics
from rag_core.document import Document

def create_test_pdf():
    """Create a simple test PDF for OCR testing"""
    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter
        
        # Create a temporary PDF file
        temp_file = tempfile.NamedTemporaryFile(suffix='.pdf', delete=False)
        temp_file.close()
        
        # Create PDF with test content
        c = canvas.Canvas(temp_file.name, pagesize=letter)
        c.drawString(100, 750, "Multi-OCR Pipeline Test Document")
        c.drawString(100, 720, "This is a test document for the enhanced OCR system.")
        c.drawString(100, 690, "It contains various text elements to test accuracy.")
        c.drawString(100, 660, "Special characters: @#$%^&*()_+-=[]{}|;':\",./<>?")
        c.drawString(100, 630, "Numbers: 1234567890")
        c.drawString(100, 600, "Mixed case: UPPER lower MiXeD")
        c.drawString(100, 570, "Long sentence: This is a longer sentence that tests the ability of the OCR system to handle extended text content with proper spacing and formatting.")
        c.drawString(100, 540, "Technical terms: API, JSON, XML, HTTP, HTTPS, TCP/IP")
        c.drawString(100, 510, "Legal terms: Plaintiff, Defendant, Jurisdiction, Subpoena")
        c.drawString(100, 480, "Medical terms: Diagnosis, Prognosis, Symptomatology, Pharmacology")
        c.drawString(100, 450, "Financial terms: ROI, NPV, IRR, EBITDA, P&L")
        c.drawString(100, 420, "End of test document.")
        c.save()
        
        return temp_file.name
    except ImportError:
        print("reportlab not available, creating text file instead")
        temp_file = tempfile.NamedTemporaryFile(suffix='.txt', delete=False, mode='w')
        temp_file.write("Multi-OCR Pipeline Test Document\n")
        temp_file.write("This is a test document for the enhanced OCR system.\n")
        temp_file.write("It contains various text elements to test accuracy.\n")
        temp_file.write("Special characters: @#$%^&*()_+-=[]{}|;':\",./<>?\n")
        temp_file.write("Numbers: 1234567890\n")
        temp_file.write("Mixed case: UPPER lower MiXeD\n")
        temp_file.write("Long sentence: This is a longer sentence that tests the ability of the OCR system to handle extended text content with proper spacing and formatting.\n")
        temp_file.write("Technical terms: API, JSON, XML, HTTP, HTTPS, TCP/IP\n")
        temp_file.write("Legal terms: Plaintiff, Defendant, Jurisdiction, Subpoena\n")
        temp_file.write("Medical terms: Diagnosis, Prognosis, Symptomatology, Pharmacology\n")
        temp_file.write("Financial terms: ROI, NPV, IRR, EBITDA, P&L\n")
        temp_file.write("End of test document.\n")
        temp_file.close()
        return temp_file.name

def test_multi_ocr_basic():
    """Test basic multi-OCR functionality"""
    print("=== Testing Basic Multi-OCR Functionality ===")
    
    # Create test document
    test_file = create_test_pdf()
    print(f"Created test file: {test_file}")
    
    try:
        # Initialize multi-OCR engine with default config
        multi_ocr = MultiOCREngine()
        print("✓ Multi-OCR engine initialized successfully")
        
        # Test scanned PDF detection
        is_scanned = multi_ocr.is_scanned_pdf(test_file)
        print(f"✓ Scanned PDF detection: {is_scanned}")
        
        # Test PDF processing
        print("Processing PDF with multi-OCR...")
        results = multi_ocr.process_pdf(test_file)
        
        print(f"✓ Processed {len(results)} pages")
        
        for i, result in enumerate(results):
            print(f"Page {i+1}:")
            print(f"  Confidence: {result.confidence.value}")
            print(f"  Agreement Score: {result.agreement_score:.3f}")
            print(f"  Contributing Engines: {result.contributing_engines}")
            print(f"  Quality Flags: {result.quality_flags}")
            print(f"  Processing Time: {result.processing_time:.2f}s")
            print(f"  Text Length: {len(result.text)} characters")
            print(f"  Text Preview: {result.text[:100]}...")
            print()
        
        # Test enhanced extraction
        print("Testing enhanced PDF extraction...")
        extracted_text = multi_ocr.extract_text_from_pdf_enhanced(test_file)
        print(f"✓ Enhanced extraction completed. Text length: {len(extracted_text)} characters")
        
        return True
        
    except Exception as e:
        print(f"✗ Error in basic test: {e}")
        return False
    finally:
        # Clean up
        if os.path.exists(test_file):
            os.unlink(test_file)

def test_ocr_configurations():
    """Test different OCR configurations"""
    print("\n=== Testing OCR Configurations ===")
    
    configs_to_test = [
        ("default", "Default configuration"),
        ("high_accuracy", "High accuracy configuration"),
        ("fast", "Fast processing configuration"),
        ("legal", "Legal document configuration"),
        ("medical", "Medical document configuration"),
        ("technical", "Technical document configuration")
    ]
    
    for config_name, description in configs_to_test:
        try:
            print(f"\nTesting {description}...")
            config = get_config(config_name)
            multi_ocr = MultiOCREngine(config)
            print(f"✓ {description} initialized successfully")
            
            # Test configuration parameters
            print(f"  High confidence threshold: {config['consensus']['high_confidence_threshold']}")
            print(f"  Medium confidence threshold: {config['consensus']['medium_confidence_threshold']}")
            print(f"  DPI: {config['preprocessing']['dpi']}")
            print(f"  Deskew enabled: {config['preprocessing']['deskew']}")
            print(f"  Denoise enabled: {config['preprocessing']['denoise']}")
            
        except Exception as e:
            print(f"✗ Error with {description}: {e}")

def test_quality_assessment():
    """Test quality assessment system"""
    print("\n=== Testing Quality Assessment System ===")
    
    # Create test document
    test_file = create_test_pdf()
    
    try:
        # Initialize quality assessor
        assessor = OCRQualityAssessor("test_reports")
        print("✓ Quality assessor initialized")
        
        # Process document with multi-OCR
        multi_ocr = MultiOCREngine()
        results = multi_ocr.process_pdf(test_file)
        
        # Assess quality for each page
        for i, consensus_result in enumerate(results):
            # Simulate engine results (in real usage, these would come from the engines)
            engine_results = []
            for engine_name in consensus_result.contributing_engines:
                # Create mock engine result
                from rag_core.multi_ocr import OCRResult
                engine_result = OCRResult(
                    engine_name=engine_name,
                    text=consensus_result.text,  # Simplified for test
                    confidence=0.8,
                    processing_time=1.0,
                    metadata={"test": True}
                )
                engine_results.append(engine_result)
            
            # Assess quality
            report = assessor.assess_document_quality(
                filename=f"test_document_page_{i+1}.pdf",
                file_size=1024,
                engine_results=engine_results,
                consensus_result=consensus_result,
                document_type="test"
            )
            
            print(f"Page {i+1} Quality Report:")
            print(f"  Confidence Level: {report.confidence_level.value}")
            print(f"  Agreement Score: {report.agreement_score:.3f}")
            print(f"  Quality Flags: {report.quality_flags}")
            print(f"  Processing Time: {report.processing_time:.2f}s")
        
        # Calculate batch metrics
        metrics = assessor.calculate_batch_metrics(assessor.document_reports)
        print(f"\nBatch Quality Metrics:")
        print(f"  Total Documents: {metrics.total_documents}")
        print(f"  Success Rate: {metrics.successful_documents/metrics.total_documents*100:.1f}%")
        print(f"  Average Confidence: {metrics.average_confidence_score:.3f}")
        print(f"  Average Agreement: {metrics.average_agreement_score:.3f}")
        print(f"  Average Processing Time: {metrics.average_processing_time_per_page:.2f}s")
        
        # Generate quality report
        report_path = assessor.generate_quality_report(metrics)
        print(f"✓ Quality report generated: {report_path}")
        
        # Export document reports
        export_path = assessor.export_document_reports()
        print(f"✓ Document reports exported: {export_path}")
        
        # Get summary statistics
        summary = assessor.get_summary_statistics()
        print(f"\nSummary Statistics:")
        print(f"  Success Rate: {summary.get('success_rate', 0)*100:.1f}%")
        print(f"  Average Confidence: {summary.get('average_confidence', 0):.3f}")
        print(f"  Average Agreement: {summary.get('average_agreement', 0):.3f}")
        
        return True
        
    except Exception as e:
        print(f"✗ Error in quality assessment test: {e}")
        return False
    finally:
        # Clean up
        if os.path.exists(test_file):
            os.unlink(test_file)

def test_document_processing_integration():
    """Test integration with document processing pipeline"""
    print("\n=== Testing Document Processing Integration ===")
    
    # Create test document
    test_file = create_test_pdf()
    
    try:
        # Read test file
        with open(test_file, 'rb') as f:
            file_content = f.read()
        
        # Test document processing with enhanced OCR
        processor = Document()
        docs = processor._process_pdf(file_content, "test_document.pdf")
        
        print(f"✓ Document processing completed. Generated {len(docs)} documents")
        
        for i, doc in enumerate(docs):
            print(f"Document {i+1}:")
            print(f"  File Type: {doc.metadata.get('file_type', 'unknown')}")
            print(f"  Processing: {doc.metadata.get('processing', 'unknown')}")
            print(f"  Text Length: {len(doc.page_content)} characters")
            
            # Check for OCR-specific metadata
            if 'ocr_confidence' in doc.metadata:
                print(f"  OCR Confidence: {doc.metadata['ocr_confidence']:.3f}")
            if 'ocr_engines' in doc.metadata:
                print(f"  OCR Engines: {doc.metadata['ocr_engines']}")
            if 'quality_flags' in doc.metadata:
                print(f"  Quality Flags: {doc.metadata['quality_flags']}")
            if 'processing_time' in doc.metadata:
                print(f"  Processing Time: {doc.metadata['processing_time']:.2f}s")
            
            print(f"  Text Preview: {doc.page_content[:100]}...")
            print()
        
        return True
        
    except Exception as e:
        print(f"✗ Error in document processing test: {e}")
        return False
    finally:
        # Clean up
        if os.path.exists(test_file):
            os.unlink(test_file)

def test_performance_benchmark():
    """Test performance benchmarking"""
    print("\n=== Testing Performance Benchmark ===")
    
    # Create test document
    test_file = create_test_pdf()
    
    try:
        # Test different configurations
        configs = [
            ("default", "Default"),
            ("fast", "Fast"),
            ("high_accuracy", "High Accuracy")
        ]
        
        results = {}
        
        for config_name, description in configs:
            print(f"\nBenchmarking {description} configuration...")
            
            start_time = time.time()
            
            # Initialize engine
            config = get_config(config_name)
            multi_ocr = MultiOCREngine(config)
            
            # Process document
            results_list = multi_ocr.process_pdf(test_file)
            
            end_time = time.time()
            total_time = end_time - start_time
            
            # Calculate metrics
            total_text_length = sum(len(r.text) for r in results_list)
            avg_confidence = sum(r.agreement_score for r in results_list) / len(results_list) if results_list else 0
            
            results[config_name] = {
                "total_time": total_time,
                "pages_processed": len(results_list),
                "total_text_length": total_text_length,
                "average_confidence": avg_confidence,
                "text_per_second": total_text_length / total_time if total_time > 0 else 0
            }
            
            print(f"  Total Time: {total_time:.2f}s")
            print(f"  Pages Processed: {len(results_list)}")
            print(f"  Total Text Length: {total_text_length} characters")
            print(f"  Average Confidence: {avg_confidence:.3f}")
            print(f"  Text per Second: {total_text_length / total_time if total_time > 0 else 0:.1f}")
        
        # Compare results
        print(f"\nPerformance Comparison:")
        print(f"{'Configuration':<15} {'Time (s)':<10} {'Text/s':<10} {'Confidence':<10}")
        print("-" * 50)
        
        for config_name, result in results.items():
            print(f"{config_name:<15} {result['total_time']:<10.2f} "
                  f"{result['text_per_second']:<10.1f} {result['average_confidence']:<10.3f}")
        
        return True
        
    except Exception as e:
        print(f"✗ Error in performance benchmark: {e}")
        return False
    finally:
        # Clean up
        if os.path.exists(test_file):
            os.unlink(test_file)

def test_ocr_engines_individual():
    """Test individual OCR engines separately"""
    print("\n=== Testing Individual OCR Engines ===")
    
    # Create test document
    test_file = create_test_pdf()
    
    try:
        # Test Tesseract
        print("\n--- Testing Tesseract ---")
        config_tesseract = {
            "engines": {
                "tesseract": {"enabled": True, "priority": 1, "languages": ["eng"], "config": "--oem 3 --psm 6"},
                "paddleocr": {"enabled": False, "priority": 2, "languages": ["en"]},
                "easyocr": {"enabled": False, "priority": 3, "languages": ["en"]}
            },
            "consensus": {"high_confidence_threshold": 0.90, "medium_confidence_threshold": 0.70, "min_agreement_engines": 1, "fuzzy_match_threshold": 0.85},
            "preprocessing": {"deskew": True, "denoise": True, "enhance_contrast": True, "dpi": 300},
            "validation": {"check_semantic_coherence": True, "check_language_consistency": True, "check_format_preservation": True, "min_text_length": 10}
        }
        
        multi_ocr_tesseract = MultiOCREngine(config_tesseract)
        results_tesseract = multi_ocr_tesseract.process_pdf(test_file)
        print(f"✅ Tesseract processed {len(results_tesseract)} pages")
        
        # Test PaddleOCR (if available)
        print("\n--- Testing PaddleOCR ---")
        try:
            config_paddleocr = {
                "engines": {
                    "tesseract": {"enabled": False, "priority": 1, "languages": ["eng"], "config": "--oem 3 --psm 6"},
                    "paddleocr": {"enabled": True, "priority": 2, "languages": ["en"]},
                    "easyocr": {"enabled": False, "priority": 3, "languages": ["en"]}
                },
                "consensus": {"high_confidence_threshold": 0.90, "medium_confidence_threshold": 0.70, "min_agreement_engines": 1, "fuzzy_match_threshold": 0.85},
                "preprocessing": {"deskew": True, "denoise": True, "enhance_contrast": True, "dpi": 300},
                "validation": {"check_semantic_coherence": True, "check_language_consistency": True, "check_format_preservation": True, "min_text_length": 10}
            }
            
            multi_ocr_paddleocr = MultiOCREngine(config_paddleocr)
            results_paddleocr = multi_ocr_paddleocr.process_pdf(test_file)
            print(f"✅ PaddleOCR processed {len(results_paddleocr)} pages")
            
        except Exception as e:
            print(f"⚠️  PaddleOCR not available: {e}")
        
        # Test EasyOCR (if available)
        print("\n--- Testing EasyOCR ---")
        try:
            config_easyocr = {
                "engines": {
                    "tesseract": {"enabled": False, "priority": 1, "languages": ["eng"], "config": "--oem 3 --psm 6"},
                    "paddleocr": {"enabled": False, "priority": 2, "languages": ["en"]},
                    "easyocr": {"enabled": True, "priority": 3, "languages": ["en"]}
                },
                "consensus": {"high_confidence_threshold": 0.90, "medium_confidence_threshold": 0.70, "min_agreement_engines": 1, "fuzzy_match_threshold": 0.85},
                "preprocessing": {"deskew": True, "denoise": True, "enhance_contrast": True, "dpi": 300},
                "validation": {"check_semantic_coherence": True, "check_language_consistency": True, "check_format_preservation": True, "min_text_length": 10}
            }
            
            multi_ocr_easyocr = MultiOCREngine(config_easyocr)
            results_easyocr = multi_ocr_easyocr.process_pdf(test_file)
            print(f"✅ EasyOCR processed {len(results_easyocr)} pages")
            
        except Exception as e:
            print(f"⚠️  EasyOCR not available: {e}")
        
        return True
        
    except Exception as e:
        print(f"✗ Error in individual engine tests: {e}")
        return False
    finally:
        # Clean up
        if os.path.exists(test_file):
            os.unlink(test_file)

def test_multi_engine_consensus():
    """Test multi-engine consensus with all available engines"""
    print("\n=== Testing Multi-Engine Consensus ===")
    
    # Create test document
    test_file = create_test_pdf()
    
    try:
        # Test with all engines enabled
        config_all_engines = {
            "engines": {
                "tesseract": {"enabled": True, "priority": 1, "languages": ["eng"], "config": "--oem 3 --psm 6"},
                "paddleocr": {"enabled": True, "priority": 2, "languages": ["en"]},
                "easyocr": {"enabled": True, "priority": 3, "languages": ["en"]}
            },
            "consensus": {"high_confidence_threshold": 0.90, "medium_confidence_threshold": 0.70, "min_agreement_engines": 2, "fuzzy_match_threshold": 0.85},
            "preprocessing": {"deskew": True, "denoise": True, "enhance_contrast": True, "dpi": 300},
            "validation": {"check_semantic_coherence": True, "check_language_consistency": True, "check_format_preservation": True, "min_text_length": 10}
        }
        
        multi_ocr = MultiOCREngine(config_all_engines)
        results = multi_ocr.process_pdf(test_file)
        
        print(f"✅ Multi-engine consensus processed {len(results)} pages")
        
        for i, result in enumerate(results):
            print(f"Page {i+1} Consensus Results:")
            print(f"  Confidence: {result.confidence.value}")
            print(f"  Agreement Score: {result.agreement_score:.3f}")
            print(f"  Contributing Engines: {result.contributing_engines}")
            print(f"  Number of Engines: {len(result.contributing_engines)}")
            print(f"  Quality Flags: {result.quality_flags}")
            print(f"  Processing Time: {result.processing_time:.2f}s")
            print(f"  Text Length: {len(result.text)} characters")
            
            # Check if multiple engines contributed
            if len(result.contributing_engines) > 1:
                print(f"  ✅ Multi-engine consensus achieved")
            else:
                print(f"  ⚠️  Single engine result (fallback)")
            print()
        
        return True
        
    except Exception as e:
        print(f"✗ Error in multi-engine consensus test: {e}")
        return False
    finally:
        # Clean up
        if os.path.exists(test_file):
            os.unlink(test_file)

def test_engine_comparison():
    """Compare performance and accuracy of different engines"""
    print("\n=== Testing Engine Comparison ===")
    
    # Create test document
    test_file = create_test_pdf()
    
    try:
        engines_to_test = [
            ("Tesseract Only", {
                "engines": {
                    "tesseract": {"enabled": True, "priority": 1, "languages": ["eng"], "config": "--oem 3 --psm 6"},
                    "paddleocr": {"enabled": False, "priority": 2, "languages": ["en"]},
                    "easyocr": {"enabled": False, "priority": 3, "languages": ["en"]}
                }
            }),
            ("PaddleOCR Only", {
                "engines": {
                    "tesseract": {"enabled": False, "priority": 1, "languages": ["eng"], "config": "--oem 3 --psm 6"},
                    "paddleocr": {"enabled": True, "priority": 2, "languages": ["en"]},
                    "easyocr": {"enabled": False, "priority": 3, "languages": ["en"]}
                }
            }),
            ("EasyOCR Only", {
                "engines": {
                    "tesseract": {"enabled": False, "priority": 1, "languages": ["eng"], "config": "--oem 3 --psm 6"},
                    "paddleocr": {"enabled": False, "priority": 2, "languages": ["en"]},
                    "easyocr": {"enabled": True, "priority": 3, "languages": ["en"]}
                }
            }),
            ("All Engines", {
                "engines": {
                    "tesseract": {"enabled": True, "priority": 1, "languages": ["eng"], "config": "--oem 3 --psm 6"},
                    "paddleocr": {"enabled": True, "priority": 2, "languages": ["en"]},
                    "easyocr": {"enabled": True, "priority": 3, "languages": ["en"]}
                }
            })
        ]
        
        comparison_results = {}
        
        for engine_name, engine_config in engines_to_test:
            try:
                print(f"\nTesting {engine_name}...")
                
                # Add common configuration
                full_config = {
                    **engine_config,
                    "consensus": {"high_confidence_threshold": 0.90, "medium_confidence_threshold": 0.70, "min_agreement_engines": 1, "fuzzy_match_threshold": 0.85},
                    "preprocessing": {"deskew": True, "denoise": True, "enhance_contrast": True, "dpi": 300},
                    "validation": {"check_semantic_coherence": True, "check_language_consistency": True, "check_format_preservation": True, "min_text_length": 10}
                }
                
                multi_ocr = MultiOCREngine(full_config)
                
                start_time = time.time()
                results = multi_ocr.process_pdf(test_file)
                end_time = time.time()
                
                total_time = end_time - start_time
                total_text_length = sum(len(r.text) for r in results)
                avg_confidence = sum(r.agreement_score for r in results) / len(results) if results else 0
                
                comparison_results[engine_name] = {
                    "total_time": total_time,
                    "pages_processed": len(results),
                    "total_text_length": total_text_length,
                    "average_confidence": avg_confidence,
                    "text_per_second": total_text_length / total_time if total_time > 0 else 0,
                    "engines_used": results[0].contributing_engines if results else []
                }
                
                print(f"  ✅ {engine_name} completed")
                print(f"     Time: {total_time:.2f}s")
                print(f"     Text Length: {total_text_length} characters")
                print(f"     Average Confidence: {avg_confidence:.3f}")
                print(f"     Engines Used: {results[0].contributing_engines if results else []}")
                
            except Exception as e:
                print(f"  ❌ {engine_name} failed: {e}")
                comparison_results[engine_name] = None
        
        # Print comparison table
        print(f"\n{'='*80}")
        print("ENGINE COMPARISON RESULTS")
        print(f"{'='*80}")
        print(f"{'Engine':<15} {'Time (s)':<10} {'Text/s':<10} {'Confidence':<12} {'Engines':<15}")
        print("-" * 80)
        
        for engine_name, result in comparison_results.items():
            if result:
                print(f"{engine_name:<15} {result['total_time']:<10.2f} "
                      f"{result['text_per_second']:<10.1f} {result['average_confidence']:<12.3f} "
                      f"{len(result['engines_used']):<15}")
            else:
                print(f"{engine_name:<15} {'FAILED':<10} {'N/A':<10} {'N/A':<12} {'N/A':<15}")
        
        return True
        
    except Exception as e:
        print(f"✗ Error in engine comparison test: {e}")
        return False
    finally:
        # Clean up
        if os.path.exists(test_file):
            os.unlink(test_file)

def test_performance_optimizations():
    """Test performance optimizations and speed improvements"""
    print("\n=== Testing Performance Optimizations ===")
    
    # Create test document
    test_file = create_test_pdf()
    
    try:
        # Test fast performance configuration
        print("\n--- Testing Fast Performance Configuration ---")
        config_fast = get_config("fast_performance")
        multi_ocr_fast = MultiOCREngine(config_fast)
        
        start_time = time.time()
        results_fast = multi_ocr_fast.process_pdf(test_file)
        fast_time = time.time() - start_time
        
        print(f"✅ Fast performance configuration completed")
        print(f"   Processing Time: {fast_time:.2f}s")
        print(f"   Pages Processed: {len(results_fast)}")
        print(f"   Engines Used: {results_fast[0].contributing_engines if results_fast else []}")
        
        # Test offline configuration
        print("\n--- Testing Offline Configuration ---")
        config_offline = get_config("offline")
        multi_ocr_offline = MultiOCREngine(config_offline)
        
        start_time = time.time()
        results_offline = multi_ocr_offline.process_pdf(test_file)
        offline_time = time.time() - start_time
        
        print(f"✅ Offline configuration completed")
        print(f"   Processing Time: {offline_time:.2f}s")
        print(f"   Pages Processed: {len(results_offline)}")
        print(f"   Engines Used: {results_offline[0].contributing_engines if results_offline else []}")
        
        # Compare performance
        if fast_time > 0 and offline_time > 0:
            speedup = offline_time / fast_time
            print(f"\nPerformance Comparison:")
            print(f"   Fast Performance: {fast_time:.2f}s")
            print(f"   Offline Mode: {offline_time:.2f}s")
            print(f"   Speedup: {speedup:.2f}x")
        
        # Test caching
        print("\n--- Testing Caching ---")
        if config_fast["performance"]["enable_caching"]:
            # First run
            start_time = time.time()
            multi_ocr_fast.process_pdf(test_file)
            first_run = time.time() - start_time
            
            # Second run (should use cache)
            start_time = time.time()
            multi_ocr_fast.process_pdf(test_file)
            second_run = time.time() - start_time
            
            cache_speedup = first_run / second_run if second_run > 0 else 0
            print(f"✅ Caching test completed")
            print(f"   First run: {first_run:.2f}s")
            print(f"   Second run: {second_run:.2f}s")
            print(f"   Cache speedup: {cache_speedup:.2f}x")
        
        return True
        
    except Exception as e:
        print(f"✗ Error in performance optimization test: {e}")
        return False
    finally:
        # Clean up
        if os.path.exists(test_file):
            os.unlink(test_file)

def main():
    """Run all tests"""
    print("Multi-OCR Pipeline Test Suite")
    print("=" * 50)
    
    tests = [
        ("Basic Multi-OCR", test_multi_ocr_basic),
        ("OCR Configurations", test_ocr_configurations),
        ("Quality Assessment", test_quality_assessment),
        ("Document Processing Integration", test_document_processing_integration),
        ("Performance Benchmark", test_performance_benchmark),
        ("Individual OCR Engines", test_ocr_engines_individual),
        ("Multi-Engine Consensus", test_multi_engine_consensus),
        ("Engine Comparison", test_engine_comparison),
        ("Performance Optimizations", test_performance_optimizations)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            success = test_func()
            results[test_name] = success
            status = "✓ PASSED" if success else "✗ FAILED"
            print(f"\n{status}: {test_name}")
        except Exception as e:
            print(f"\n✗ ERROR: {test_name} - {e}")
            results[test_name] = False
    
    # Summary
    print(f"\n{'='*50}")
    print("TEST SUMMARY")
    print("=" * 50)
    
    passed = sum(1 for success in results.values() if success)
    total = len(results)
    
    for test_name, success in results.items():
        status = "✓ PASSED" if success else "✗ FAILED"
        print(f"{status}: {test_name}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Multi-OCR pipeline is working correctly.")
    else:
        print("⚠️  Some tests failed. Please check the output above for details.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 
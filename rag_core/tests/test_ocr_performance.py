#!/usr/bin/env python3
"""
OCR Performance Testing Script

This script benchmarks the optimized OCR pipeline and compares different configurations
for speed and accuracy trade-offs.
"""

import os
import sys
import time
import tempfile
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import numpy as np

# Add the rag_core parent directory to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rag_core.multi_ocr import MultiOCREngine
from rag_core.ocr_config import get_config

def create_performance_test_image():
    """Create a test image for performance benchmarking"""
    # Create a simple test image
    width, height = 800, 600
    image = Image.new('RGB', (width, height), color='white')
    draw = ImageDraw.Draw(image)
    
    # Try to use a default font
    try:
        font = ImageFont.truetype("arial.ttf", 20)
    except:
        try:
            font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 20)
        except:
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 20)
            except:
                font = ImageFont.load_default()
    
    # Add test text
    test_text = [
        "Performance Test Document",
        "This document is designed to test OCR performance.",
        "It contains various text elements for benchmarking.",
        "Testing speed and accuracy trade-offs.",
        "Special characters: @#$%^&*()_+-=[]{}|;':\",./<>?",
        "Numbers: 1234567890",
        "Mixed case: UPPER lower MiXeD",
        "Technical terms: API, JSON, XML, HTTP, HTTPS",
        "Legal terms: Plaintiff, Defendant, Jurisdiction",
        "Medical terms: Diagnosis, Prognosis, Symptomatology",
        "Financial terms: ROI, NPV, IRR, EBITDA, P&L",
        "Long sentence: This is a longer sentence that tests the ability of the OCR system to handle extended text content with proper spacing and formatting for performance evaluation.",
        "End of performance test document."
    ]
    
    y_position = 50
    for line in test_text:
        draw.text((50, y_position), line, fill='black', font=font)
        y_position += 30
    
    return image

def benchmark_configuration(config_name: str, description: str, iterations: int = 5):
    """Benchmark a specific configuration"""
    print(f"\n=== Benchmarking {description} ===")
    
    try:
        # Get configuration
        config = get_config(config_name)
        
        # Initialize multi-OCR engine
        multi_ocr = MultiOCREngine(config)
        
        # Create test image
        test_image = create_performance_test_image()
        
        # Benchmark processing times
        processing_times = []
        text_lengths = []
        confidence_scores = []
        
        for i in range(iterations):
            print(f"  Iteration {i+1}/{iterations}...")
            
            start_time = time.time()
            result = multi_ocr.process_image(test_image)
            end_time = time.time()
            
            processing_time = end_time - start_time
            processing_times.append(processing_time)
            text_lengths.append(len(result.text))
            confidence_scores.append(result.agreement_score)
            
            print(f"    Time: {processing_time:.2f}s")
            print(f"    Text Length: {len(result.text)} characters")
            print(f"    Confidence: {result.confidence.value}")
            print(f"    Agreement Score: {result.agreement_score:.3f}")
            print(f"    Contributing Engines: {result.contributing_engines}")
        
        # Calculate statistics
        avg_time = sum(processing_times) / len(processing_times)
        avg_text_length = sum(text_lengths) / len(text_lengths)
        avg_confidence = sum(confidence_scores) / len(confidence_scores)
        min_time = min(processing_times)
        max_time = max(processing_times)
        
        return {
            "config_name": config_name,
            "description": description,
            "avg_time": avg_time,
            "min_time": min_time,
            "max_time": max_time,
            "avg_text_length": avg_text_length,
            "avg_confidence": avg_confidence,
            "iterations": iterations,
            "engines_used": result.contributing_engines if result else []
        }
        
    except Exception as e:
        print(f"❌ {description} benchmark failed: {e}")
        return None

def test_offline_mode():
    """Test offline mode functionality"""
    print("\n=== Testing Offline Mode ===")
    
    try:
        # Test offline configuration
        config = get_config("offline")
        multi_ocr = MultiOCREngine(config)
        
        # Create test image
        test_image = create_performance_test_image()
        
        # Test processing
        start_time = time.time()
        result = multi_ocr.process_image(test_image)
        processing_time = time.time() - start_time
        
        print(f"✅ Offline mode test successful")
        print(f"   Processing Time: {processing_time:.2f}s")
        print(f"   Text Length: {len(result.text)} characters")
        print(f"   Confidence: {result.confidence.value}")
        print(f"   Contributing Engines: {result.contributing_engines}")
        
        # Check if models are cached
        offline_dir = Path.home() / ".ocr_models"
        if offline_dir.exists():
            print(f"   Offline models directory: {offline_dir}")
            print(f"   Models cached: {list(offline_dir.glob('*'))}")
        
        return True
        
    except Exception as e:
        print(f"❌ Offline mode test failed: {e}")
        return False

def test_caching_performance():
    """Test caching performance"""
    print("\n=== Testing Caching Performance ===")
    
    try:
        # Get configuration with caching enabled
        config = get_config("fast_performance")
        multi_ocr = MultiOCREngine(config)
        
        # Create test image
        test_image = create_performance_test_image()
        
        # First run (no cache)
        print("  First run (no cache)...")
        start_time = time.time()
        result1 = multi_ocr.process_image(test_image)
        first_run_time = time.time() - start_time
        
        # Second run (with cache)
        print("  Second run (with cache)...")
        start_time = time.time()
        result2 = multi_ocr.process_image(test_image)
        second_run_time = time.time() - start_time
        
        # Calculate speedup
        speedup = first_run_time / second_run_time if second_run_time > 0 else 0
        
        print(f"✅ Caching performance test successful")
        print(f"   First run time: {first_run_time:.2f}s")
        print(f"   Second run time: {second_run_time:.2f}s")
        print(f"   Speedup: {speedup:.2f}x")
        print(f"   Cache hit: {result1.text == result2.text}")
        
        return True
        
    except Exception as e:
        print(f"❌ Caching performance test failed: {e}")
        return False

def test_parallel_processing():
    """Test parallel processing performance"""
    print("\n=== Testing Parallel Processing ===")
    
    try:
        # Test with parallel processing enabled
        config_parallel = get_config("offline")
        config_parallel["performance"]["parallel_processing"] = True
        multi_ocr_parallel = MultiOCREngine(config_parallel)
        
        # Test with parallel processing disabled
        config_sequential = get_config("offline")
        config_sequential["performance"]["parallel_processing"] = False
        multi_ocr_sequential = MultiOCREngine(config_sequential)
        
        # Create test image
        test_image = create_performance_test_image()
        
        # Test parallel processing
        print("  Testing parallel processing...")
        start_time = time.time()
        result_parallel = multi_ocr_parallel.process_image(test_image)
        parallel_time = time.time() - start_time
        
        # Test sequential processing
        print("  Testing sequential processing...")
        start_time = time.time()
        result_sequential = multi_ocr_sequential.process_image(test_image)
        sequential_time = time.time() - start_time
        
        # Calculate speedup
        speedup = sequential_time / parallel_time if parallel_time > 0 else 0
        
        print(f"✅ Parallel processing test successful")
        print(f"   Sequential time: {sequential_time:.2f}s")
        print(f"   Parallel time: {parallel_time:.2f}s")
        print(f"   Speedup: {speedup:.2f}x")
        print(f"   Parallel engines: {result_parallel.contributing_engines}")
        print(f"   Sequential engines: {result_sequential.contributing_engines}")
        
        return True
        
    except Exception as e:
        print(f"❌ Parallel processing test failed: {e}")
        return False

def main():
    """Run performance benchmarks"""
    print("OCR Performance Testing")
    print("=" * 50)
    
    # Test configurations
    configs_to_test = [
        ("fast_performance", "Fast Performance (Tesseract only)"),
        ("offline", "Offline Mode (All engines)"),
        ("default", "Default Configuration"),
        ("high_accuracy", "High Accuracy Configuration")
    ]
    
    results = []
    
    # Benchmark each configuration
    for config_name, description in configs_to_test:
        result = benchmark_configuration(config_name, description, iterations=3)
        if result:
            results.append(result)
    
    # Print comparison table
    print(f"\n{'='*80}")
    print("PERFORMANCE COMPARISON RESULTS")
    print(f"{'='*80}")
    print(f"{'Configuration':<25} {'Avg Time (s)':<12} {'Min Time (s)':<12} {'Max Time (s)':<12} {'Text Length':<12} {'Confidence':<10}")
    print("-" * 80)
    
    for result in results:
        print(f"{result['description']:<25} {result['avg_time']:<12.2f} {result['min_time']:<12.2f} "
              f"{result['max_time']:<12.2f} {result['avg_text_length']:<12.0f} {result['avg_confidence']:<10.3f}")
    
    # Test specific features
    print(f"\n{'='*50}")
    print("FEATURE TESTS")
    print("=" * 50)
    
    # Test offline mode
    offline_success = test_offline_mode()
    
    # Test caching performance
    caching_success = test_caching_performance()
    
    # Test parallel processing
    parallel_success = test_parallel_processing()
    
    # Summary
    print(f"\n{'='*50}")
    print("SUMMARY")
    print("=" * 50)
    
    feature_tests = [
        ("Offline Mode", offline_success),
        ("Caching Performance", caching_success),
        ("Parallel Processing", parallel_success)
    ]
    
    for test_name, success in feature_tests:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{status}: {test_name}")
    
    # Recommendations
    print(f"\n{'='*50}")
    print("RECOMMENDATIONS")
    print("=" * 50)
    
    if results:
        fastest_config = min(results, key=lambda x: x['avg_time'])
        most_accurate_config = max(results, key=lambda x: x['avg_confidence'])
        
        print(f"Fastest Configuration: {fastest_config['description']}")
        print(f"  Average Time: {fastest_config['avg_time']:.2f}s")
        print(f"  Confidence: {fastest_config['avg_confidence']:.3f}")
        
        print(f"\nMost Accurate Configuration: {most_accurate_config['description']}")
        print(f"  Average Time: {most_accurate_config['avg_time']:.2f}s")
        print(f"  Confidence: {most_accurate_config['avg_confidence']:.3f}")
        
        print(f"\nRecommendations:")
        print(f"  - For speed: Use 'fast_performance' configuration")
        print(f"  - For accuracy: Use 'high_accuracy' configuration")
        print(f"  - For balance: Use 'offline' configuration")
        print(f"  - Enable caching for repeated documents")
        print(f"  - Use parallel processing for multiple engines")

if __name__ == "__main__":
    main() 
#!/usr/bin/env python3
"""
OCR Test Runner

This script runs all OCR-related tests from the project root.
"""

import os
import sys
import subprocess
from pathlib import Path

def run_test(test_name: str, test_path: str):
    """Run a specific test"""
    print(f"\n{'='*60}")
    print(f"Running {test_name}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run([
            sys.executable, test_path
        ], capture_output=True, text=True, cwd=os.getcwd())
        
        if result.returncode == 0:
            print("✅ Test passed")
            print(result.stdout)
        else:
            print("❌ Test failed")
            print(result.stdout)
            print(result.stderr)
        
        return result.returncode == 0
        
    except Exception as e:
        print(f"❌ Error running {test_name}: {e}")
        return False

def main():
    """Run all OCR tests"""
    print("OCR Test Runner")
    print("=" * 60)
    
    # Define tests to run
    tests = [
        ("Multi-OCR Tests", "rag_core/tests/test_multi_ocr.py"),
        ("Performance Tests", "rag_core/tests/test_ocr_performance.py"),
        ("Integration Tests", "rag_core/tests/test_integration.py"),
        ("Setup Tests", "rag_core/tests/setup_ocr_engines.py")
    ]
    
    results = []
    
    for test_name, test_path in tests:
        if os.path.exists(test_path):
            success = run_test(test_name, test_path)
            results.append((test_name, success))
        else:
            print(f"⚠️  Test file not found: {test_path}")
            results.append((test_name, False))
    
    # Summary
    print(f"\n{'='*60}")
    print("TEST SUMMARY")
    print(f"{'='*60}")
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{status}: {test_name}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All OCR tests passed!")
        print("✅ OCR system is working correctly")
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
    
    return passed == total

if __name__ == "__main__":
    main() 
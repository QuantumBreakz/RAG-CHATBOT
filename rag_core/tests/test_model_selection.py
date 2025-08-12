#!/usr/bin/env python3
"""
Test script for model selection feature
"""

import asyncio
import aiohttp
import json
from pathlib import Path

async def test_model_selection():
    """Test the model selection feature"""
    
    # Test cases
    test_cases = [
        {
            "name": "Mathematical Document",
            "filename": "calculation_25X54.txt",
            "content": "The area calculation is 25X54 = 1350 square meters. Additional calculations: 100 + 200 = 300, sqrt(16) = 4"
        },
        {
            "name": "Blueprint Document", 
            "filename": "technical_blueprint.txt",
            "content": "Technical drawing specifications: Assembly diagram, component layout, engineering dimensions, scale 1:100"
        },
        {
            "name": "Regular Document",
            "filename": "normal_document.txt", 
            "content": "This is a regular document with normal text content. No special mathematical or technical content."
        }
    ]
    
    async with aiohttp.ClientSession() as session:
        base_url = "http://localhost:8000"
        
        print("🧪 Testing Model Selection Feature")
        print("=" * 50)
        
        for test_case in test_cases:
            print(f"\n📄 Testing: {test_case['name']}")
            print(f"   File: {test_case['filename']}")
            print(f"   Content: {test_case['content'][:50]}...")
            
            # Create a temporary file
            test_file_path = Path(f"temp_{test_case['filename']}")
            test_file_path.write_text(test_case['content'])
            
            try:
                # Test upload with content detection
                with open(test_file_path, 'rb') as f:
                    data = aiohttp.FormData()
                    data.add_field('file', f, filename=test_case['filename'])
                    data.add_field('chunk_size', '1000')
                    data.add_field('document_type', 'default')
                    data.add_field('preferred_model', 'local')
                    
                    async with session.post(f"{base_url}/upload", data=data) as response:
                        if response.status == 200:
                            result = await response.json()
                            print(f"   ✅ Upload successful")
                            print(f"   📊 Model used: {result.get('model_used', 'unknown')}")
                            print(f"   📊 Content detection: {result.get('content_detection', {}).get('type', 'none')}")
                            print(f"   📊 Confidence: {result.get('content_detection', {}).get('confidence', 0):.2f}")
                            print(f"   📊 Details: {result.get('content_detection', {}).get('details', 'No details')}")
                        else:
                            print(f"   ❌ Upload failed: {response.status}")
                            error_text = await response.text()
                            print(f"   Error: {error_text}")
                
                # Clean up test file
                test_file_path.unlink()
                
            except Exception as e:
                print(f"   ❌ Test failed: {e}")
                if test_file_path.exists():
                    test_file_path.unlink()
        
        print("\n" + "=" * 50)
        print("✅ Model selection test completed!")

if __name__ == "__main__":
    asyncio.run(test_model_selection())

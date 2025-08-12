#!/usr/bin/env python3
"""
Test script for chat model selection feature
Tests the model selection for chat attachments (not knowledge base uploads)
"""

import asyncio
import aiohttp
import json
from pathlib import Path

async def test_chat_model_selection():
    """Test the chat model selection feature"""
    
    # Test cases for chat attachments
    test_cases = [
        {
            "name": "Mathematical Document",
            "filename": "calculation_25X54.txt",
            "content": "The area calculation is 25X54 = 1350 square meters. Additional calculations: 100 + 200 = 300, sqrt(16) = 4",
            "expected_detection": "mathematical"
        },
        {
            "name": "Blueprint Document", 
            "filename": "technical_blueprint.txt",
            "content": "Technical drawing specifications: Assembly diagram, component layout, engineering dimensions, scale 1:100",
            "expected_detection": "blueprint"
        },
        {
            "name": "Regular Document",
            "filename": "normal_document.txt", 
            "content": "This is a regular document with normal text content. No special mathematical or technical content.",
            "expected_detection": None
        }
    ]
    
    async with aiohttp.ClientSession() as session:
        base_url = "http://localhost:8000"
        
        print("🧪 Testing Chat Model Selection Feature")
        print("=" * 60)
        print("Note: This tests chat attachments, not knowledge base uploads")
        print()
        
        for test_case in test_cases:
            print(f"📄 Testing: {test_case['name']}")
            print(f"   File: {test_case['filename']}")
            print(f"   Content: {test_case['content'][:50]}...")
            print(f"   Expected Detection: {test_case['expected_detection']}")
            
            # Create a temporary file
            test_file_path = Path(f"temp_{test_case['filename']}")
            test_file_path.write_text(test_case['content'])
            
            try:
                # Test chat query with attached file
                with open(test_file_path, 'rb') as f:
                    data = aiohttp.FormData()
                    data.add_field('question', 'What is this document about?')
                    data.add_field('n_results', '3')
                    data.add_field('expand', '2')
                    data.add_field('conversation_history', '[]')
                    data.add_field('session_id', 'test-session-123')
                    data.add_field('file', f, filename=test_case['filename'])
                    
                    async with session.post(f"{base_url}/query", data=data) as response:
                        if response.status == 200:
                            result = await response.json()
                            print(f"   ✅ Query successful")
                            print(f"   📊 Model used: {result.get('model_used', 'unknown')}")
                            print(f"   📊 Answer: {result.get('answer', 'No answer')[:100]}...")
                            
                            # Check if the model selection worked as expected
                            if test_case['expected_detection']:
                                if result.get('model_used') == 'openai':
                                    print(f"   ✅ Correctly used OpenAI for {test_case['expected_detection']} content")
                                else:
                                    print(f"   ⚠️  Used {result.get('model_used')} instead of OpenAI for {test_case['expected_detection']} content")
                            else:
                                if result.get('model_used') == 'local':
                                    print(f"   ✅ Correctly used Local model for regular content")
                                else:
                                    print(f"   ⚠️  Used {result.get('model_used')} instead of Local for regular content")
                        else:
                            print(f"   ❌ Query failed: {response.status}")
                            error_text = await response.text()
                            print(f"   Error: {error_text}")
                
                # Clean up test file
                test_file_path.unlink()
                
            except Exception as e:
                print(f"   ❌ Test failed: {e}")
                if test_file_path.exists():
                    test_file_path.unlink()
            
            print()
        
        print("=" * 60)
        print("✅ Chat model selection test completed!")
        print()
        print("📋 Summary:")
        print("- Modal should appear for mathematical/blueprint content")
        print("- Modal should NOT appear for regular content")
        print("- Selected model should be used for entire chat session")
        print("- Toast notification should show current model")
        print("- Model should reset when starting new conversation")

if __name__ == "__main__":
    asyncio.run(test_chat_model_selection())

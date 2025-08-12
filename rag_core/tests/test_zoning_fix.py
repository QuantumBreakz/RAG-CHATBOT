#!/usr/bin/env python3
"""
Test script to verify the zoning search fix
"""

import asyncio
import aiohttp
import json

async def test_zoning_queries():
    """Test zoning queries to verify the fix works"""
    
    print("🧪 Testing Zoning Query Fix")
    print("=" * 50)
    
    # Test queries
    test_queries = [
        "what is zoning?",
        "define zoning",
        "zoning definition",
        "what are special area zones?",
        "how many types of zone are there?"
    ]
    
    async with aiohttp.ClientSession() as session:
        base_url = "http://localhost:8000"
        
        for query in test_queries:
            print(f"\n📝 Testing Query: '{query}'")
            print("-" * 30)
            
            try:
                data = aiohttp.FormData()
                data.add_field('question', query)
                data.add_field('n_results', '10')  # Use increased results
                data.add_field('expand', '2')
                data.add_field('conversation_history', '[]')
                data.add_field('session_id', 'test-session-123')
                
                async with session.post(f"{base_url}/query", data=data) as response:
                    if response.status == 200:
                        result = await response.json()
                        answer = result.get('answer', 'No answer')
                        sources = result.get('sources', [])
                        
                        print(f"   ✅ Query successful")
                        print(f"   📊 Answer: {answer[:200]}...")
                        print(f"   📄 Sources found: {len(sources)}")
                        
                        # Check if the answer contains zoning information
                        if 'zoning' in answer.lower() or 'town' in answer.lower() or 'municipal' in answer.lower():
                            print(f"   ✅ Answer contains zoning-related information")
                        else:
                            print(f"   ⚠️  Answer may not contain zoning information")
                            
                        # Show source details
                        for i, source in enumerate(sources[:3]):  # Show first 3 sources
                            filename = source.get('title', 'Unknown')
                            confidence = source.get('confidence', 0.0)
                            print(f"      Source {i+1}: {filename} (confidence: {confidence:.3f})")
                            
                    else:
                        print(f"   ❌ Query failed: {response.status}")
                        error_text = await response.text()
                        print(f"   Error: {error_text}")
                        
            except Exception as e:
                print(f"   ❌ Test failed: {e}")
            
            print()

if __name__ == "__main__":
    asyncio.run(test_zoning_queries())

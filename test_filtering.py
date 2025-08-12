#!/usr/bin/env python3
"""
Simple test to check current filtering behavior
"""

import requests

def test_current_filtering():
    """Test the current filtering with a simple query"""
    
    print("🧪 Testing Current Filtering")
    print("=" * 40)
    
    # Test the query
    api_url = "http://localhost:8000/query"
    
    data = {
        "question": "who was maman",
        "n_results": "10"
    }
    
    try:
        response = requests.post(api_url, data=data)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Response received")
            print(f"   Answer length: {len(result.get('answer', ''))}")
            print(f"   Sources count: {len(result.get('sources', []))}")
            
            # Check sources
            sources = result.get('sources', [])
            stranger_sources = [s for s in sources if 'stranger' in s.get('title', '').lower()]
            other_sources = [s for s in sources if 'stranger' not in s.get('title', '').lower()]
            
            print(f"   📚 Sources from The Stranger: {len(stranger_sources)}")
            print(f"   📚 Other sources: {len(other_sources)}")
            
            if other_sources:
                print("   ⚠️  Found irrelevant sources:")
                for s in other_sources[:3]:  # Show first 3
                    print(f"      - {s.get('title', 'Unknown')}")
            
            # Check answer quality
            answer = result.get('answer', '').lower()
            if 'mother' in answer and 'stranger' in answer:
                print("   ✅ Answer correctly identifies Maman")
            else:
                print("   ❌ Answer may be incorrect")
                print(f"      Answer preview: {result.get('answer', '')[:200]}...")
                
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"   Response: {response.text}")
    
    except Exception as e:
        print(f"❌ Exception: {str(e)}")
    
    print("\n" + "=" * 40)

if __name__ == "__main__":
    test_current_filtering()

#!/usr/bin/env python3
"""
Debug script to check what's actually in the vectorstore and why documents aren't being listed.
"""

import requests
import json

def test_vectorstore_contents():
    """Test what's actually in the vectorstore"""
    try:
        # Get vectorstore statistics
        response = requests.get('http://localhost:8000/vectorstore/statistics', timeout=5)
        if response.status_code == 200:
            stats = response.json()
            print(f"📊 Vectorstore Statistics: {stats}")
        else:
            print(f"❌ Failed to get vectorstore statistics: {response.status_code}")
            return
        
        # Try to query the vectorstore directly
        response = requests.post('http://localhost:8000/query', data={
            'question': 'test',
            'n_results': '10'
        }, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            print(f"🔍 Query test result: {result}")
            
            # Check if there are any sources
            if 'sources' in result and result['sources']:
                print(f"✅ Found {len(result['sources'])} sources in query")
                for i, source in enumerate(result['sources']):
                    print(f"   Source {i+1}: {source}")
            else:
                print("❌ No sources found in query")
        else:
            print(f"❌ Query test failed: {response.status_code}")
            print(f"Response: {response.text}")
        
        # Test documents endpoint again
        response = requests.get('http://localhost:8000/documents', timeout=5)
        if response.status_code == 200:
            docs = response.json()
            print(f"📄 Documents endpoint: {docs}")
        else:
            print(f"❌ Documents endpoint failed: {response.status_code}")
        
        # Test enhanced documents endpoint
        response = requests.get('http://localhost:8000/documents/enhanced', timeout=5)
        if response.status_code == 200:
            enhanced_docs = response.json()
            print(f"📄 Enhanced documents: {enhanced_docs}")
        else:
            print(f"❌ Enhanced documents failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error testing vectorstore contents: {e}")

def test_direct_vectorstore_query():
    """Test a direct query to see what's in the vectorstore"""
    try:
        # Try a simple query to see what's available
        response = requests.post('http://localhost:8000/query', data={
            'question': 'hello',
            'n_results': '5'
        }, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            print(f"🔍 Direct query result: {json.dumps(result, indent=2)}")
        else:
            print(f"❌ Direct query failed: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error in direct query: {e}")

def main():
    """Run debug tests"""
    print("🔍 Debugging Vectorstore Contents")
    print("=" * 50)
    
    test_vectorstore_contents()
    print("\n" + "=" * 50)
    test_direct_vectorstore_query()

if __name__ == "__main__":
    main() 